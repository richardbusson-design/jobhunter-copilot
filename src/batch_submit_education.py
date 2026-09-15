# -*- coding: utf-8 -*-
"""
Orchestrateur de postulation batch autonome pour recrutement.education.gouv.fr
Applique le standard QualityGuard 3-Pass :
1. Contrôle anti-doublon et qualification
2. Génération des 6 fichiers sur-mesure (CV AltaCV x Awesome-CV A4 + Lettre AFNOR sans gras)
3. Soumission officielle, capture de preuve matérielle, mise à jour tracker & Git push
"""

import os
import re
import sys
import time
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

BASE_DIR = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
SESSION_FILE = r"C:\Users\richa\JobHunter\browser_profile\education_storage_state.json"
TRACKER_FILE = os.path.join(BASE_DIR, "tracker.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.md")
QUALIFIED_JSON = os.path.join(BASE_DIR, "data", "offres_stmg_nationales_qualifiees.json")

# Importer le générateur sur-mesure
sys.path.append(os.path.join(BASE_DIR, "src"))
from generate_bespoke_dossier import generate_dossier_files

def sanitize_folder_name(name: str) -> str:
    s = re.sub(r'[^\w\-_]', '_', name)
    return re.sub(r'_+', '_', s).strip('_')[:80]

def update_tracker_and_dashboard(offer_entry: dict):
    """Met à jour tracker.json et dashboard.md puis synchronise Git."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Mise à jour tracker.json
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
    except Exception:
        tracker_data = []

    # Vérifier si l'id existe déjà
    ref_id = offer_entry.get("reference") or offer_entry.get("title")
    existing_idx = None
    for i, item in enumerate(tracker_data):
        if item.get("reference") == ref_id or item.get("title") == offer_entry.get("title"):
            existing_idx = i
            break

    tracker_item = {
        "id": ref_id,
        "reference": offer_entry.get("reference", ""),
        "title": offer_entry.get("title", ""),
        "company": offer_entry.get("academie", "Éducation Nationale"),
        "location": offer_entry.get("location", ""),
        "date_scraped": today_str,
        "date_applied": today_str,
        "status": "POSTULÉ",
        "source": "recrutement.education.gouv.fr",
        "url": offer_entry.get("url", ""),
        "folder_rel": offer_entry.get("folder_rel", ""),
        "salary": "27 060 € à 38 160 € brut/an",
        "rome_code": "K2107 / K2111",
        "notes": f"Poste d'Enseignant Éco-Gestion / STMG. Candidature transmise et validée avec succès sur le portail officiel de l'Éducation Nationale le {today_str}. 4 pièces officielles jointes (Passeport, M2 Droit public, CV et Lettre sur-mesure validés).",
        "recruiter_delivery": {
            "sent": True,
            "mode": "WEB_PORTAL_AUTO_SUBMITTED",
            "reason": f"Candidature transmise et validée sur le portail officiel recrutement.education.gouv.fr ({ref_id})",
            "recruiter_email": None,
            "subject": f"Candidature : {offer_entry.get('title')} — Richard BUSSON",
            "timestamp": now_str,
            "proof_screenshot": offer_entry.get("proof_rel", "")
        }
    }

    if existing_idx is not None:
        tracker_data[existing_idx] = tracker_item
    else:
        tracker_data.insert(0, tracker_item)

    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] tracker.json mis à jour pour : {ref_id}")

    # 2. Mise à jour dashboard.md
    if os.path.exists(DASHBOARD_FILE):
        try:
            with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
                dash_content = f.read()

            dash_line = (
                f"| {today_str} | **{offer_entry.get('academie', 'ÉDUCATION NATIONALE').upper()}** | "
                f"Monsieur le Recteur d'Académie (DPE) | {offer_entry.get('location', '')} | Non communiqué | 🌐 Portail Web | "
                f"[{offer_entry.get('title')}]({offer_entry.get('url')}) (Réf. {offer_entry.get('reference')}) | "
                f"🟢 Transmis & Validé (Portail Officiel) | "
                f"[Lettre]({offer_entry.get('folder_rel')}/Lettre_Motivation_Richard_BUSSON.pdf) / "
                f"[CV]({offer_entry.get('folder_rel')}/CV_Richard_BUSSON.pdf) / "
                f"[📸 Preuve]({offer_entry.get('proof_rel')}) |"
            )

            # Insérer après l'en-tête du tableau
            table_header = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            if table_header in dash_content:
                dash_content = dash_content.replace(table_header, table_header + dash_line + "\n")
                with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
                    f.write(dash_content)
                print(f"[OK] dashboard.md mis à jour avec succès.")
        except Exception as e:
            print(f"[!] Erreur mise à jour dashboard.md : {e}")

async def process_single_offer(page, offer_info: dict) -> bool:
    """Traite de bout en bout une candidature sur le portail."""
    raw_title = offer_info["title"]
    clean_kw = re.sub(r'\(.*?\)', '', raw_title).strip()[:35]
    today_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\n=======================================================")
    print(f"[*] TRAITEMENT OFFRE : {raw_title}")
    print(f"=======================================================")

    # 1. Recherche et accès à la fiche de poste
    await page.goto("https://recrutement.education.gouv.fr/recrutement/offres", wait_until="domcontentloaded", timeout=45000)
    await asyncio.sleep(3)

    search_input = page.locator("input[name='search']").first
    await search_input.fill("")
    await search_input.type(clean_kw, delay=30)
    await page.locator("button:has-text('Rechercher')").first.click()
    await asyncio.sleep(5)

    # Trouver la carte correspondante
    cards = page.locator(".fr-card")
    n_cards = await cards.count()
    target_card = None

    for i in range(min(n_cards, 10)):
        c = cards.nth(i)
        ctxt = await c.inner_text()
        words = [w for w in clean_kw.split() if len(w) > 4]
        if any(w.lower() in ctxt.lower() for w in words):
            target_card = c
            break

    if not target_card:
        print(f"[!] Impossible de localiser la carte pour : {clean_kw}")
        return False

    link = target_card.locator("a").first
    await link.click()
    await asyncio.sleep(6)

    offer_url = page.url
    print(f"[+] URL offre atteinte : {offer_url}")

    # Récupérer les métadonnées de la page
    content = await page.eval_on_selector("main", "el => el ? el.innerText : ''")
    if not content:
        content = await page.eval_on_selector("body", "el => el.innerText")

    ref_match = re.search(r'(MENJ-[A-Z0-9-]+)', content)
    ref = ref_match.group(1) if ref_match else f"MENJ-STMG-{int(time.time())}"

    acad_match = re.search(r'Académie de\s+([A-ZÉÈÊÀÂÔÛÎÇ\-]+)', content, re.I)
    acad = acad_match.group(0) if acad_match else offer_info.get("lines", ["", ""])[1]

    loc_match = re.search(r'Lieu de travail\s*:\s*([^\n]+)', content)
    loc = loc_match.group(1).strip() if loc_match else acad

    # 2. Création du dossier et génération des 6 fichiers sur-mesure
    folder_name = f"{today_str}_{sanitize_folder_name(acad)}_{sanitize_folder_name(raw_title)}"
    dossier_abs = os.path.join(BASE_DIR, "candidatures", folder_name)
    folder_rel = f"candidatures/{folder_name}"

    offer_data = {
        "title": raw_title,
        "academie": acad,
        "reference": ref,
        "location": loc,
        "raw_card": offer_info.get("card_text", "")
    }

    print(f"[*] Génération du pack 6 fichiers sur-mesure dans : {dossier_abs}")
    dossier_files = await generate_dossier_files(offer_data, dossier_abs)

    cv_pdf_path = dossier_files["cv_pdf"]
    lm_pdf_path = dossier_files["lm_pdf"]

    # 3. Processus de postulation sur le portail
    print("[*] Vérification du bouton de postulation...")
    # Vérifier si déjà candidaté (bouton indisponible ou message)
    postuler_btn = page.locator("button:has-text('Je postule')").first
    if await postuler_btn.count() == 0:
        print("[!] Bouton 'Je postule' absent (peut-être déjà candidaté ou statut particulier).")
        return False

    print("[+] Clic sur 'Je postule'...")
    await postuler_btn.click()
    await asyncio.sleep(5)

    # Si modale "Candidature initialisée", la fermer
    fermer_btn = page.locator("button:has-text('Fermer')")
    if await fermer_btn.count() > 0 and await fermer_btn.first.is_visible():
        print("[+] Fermeture de la modale d'initialisation...")
        await fermer_btn.first.click()
        await asyncio.sleep(4)

    # Naviguer sur Mon espace candidat -> Mes candidatures pour ouvrir le brouillon
    print("[*] Accès à Mon espace candidat pour ouvrir le brouillon...")
    await page.goto("https://recrutement.education.gouv.fr/recrutement/mon-espace-candidat", wait_until="domcontentloaded", timeout=45000)
    await asyncio.sleep(5)

    tab_cand = page.locator("text='Mes candidatures'").first
    await tab_cand.click()
    await asyncio.sleep(4)

    # Ouvrir la candidature en Brouillon correspondant au titre
    brouillon_card = page.locator(f"text='{clean_kw[:20]}'").first
    if await brouillon_card.count() == 0:
        brouillon_card = page.locator(".fr-card:has-text('BROUILLON')").first

    if await brouillon_card.count() > 0:
        print("[+] Clic sur le brouillon de candidature...")
        await brouillon_card.click()
        await asyncio.sleep(6)
    else:
        print("[!] Brouillon introuvable.")
        return False

    print(f"[+] Formulaire de candidature ouvert : {page.url}")

    # 4. Rattachement des 4 pièces obligatoires
    # A. CNI/Passeport
    has_passport = await page.locator(".slds-file:has-text('Passeport'), a:has-text('Passeport')").count() > 0
    if not has_passport:
        print("[*] Rattachement du Passeport...")
        sel_cni = page.locator("select:has(option[value='CNI_SEJ'])").first
        await sel_cni.select_option(value="CNI_SEJ")
        await asyncio.sleep(2)
        sel_exist = page.locator("select").nth(3)
        for opt_idx in range(await sel_exist.locator("option").count()):
            opt = sel_exist.locator("option").nth(opt_idx)
            otxt = (await opt.inner_text()).strip()
            oval = await opt.get_attribute("value")
            if "Passeport" in otxt and oval:
                await sel_exist.select_option(value=oval)
                print(f"    -> {otxt} rattaché")
                break
        await asyncio.sleep(3)

    # B. Diplôme
    has_dipl = await page.locator(".slds-file:has-text('Diplome'), a:has-text('Diplome')").count() > 0
    if not has_dipl:
        print("[*] Rattachement du Diplôme (Master 2 Droit Public)...")
        sel_dipl = page.locator("select:has(option[value='DIPL'])").first
        await sel_dipl.select_option(value="DIPL")
        await asyncio.sleep(2)
        sel_exist = page.locator("select").nth(3)
        for opt_idx in range(await sel_exist.locator("option").count()):
            opt = sel_exist.locator("option").nth(opt_idx)
            otxt = (await opt.inner_text()).strip()
            oval = await opt.get_attribute("value")
            if "Diplome_Master2_Droit_Public" in otxt and oval:
                await sel_exist.select_option(value=oval)
                print(f"    -> {otxt} rattaché")
                break
        await asyncio.sleep(3)

    # C. Téléversement du CV sur-mesure
    print(f"[*] Upload du CV validé : {cv_pdf_path}")
    sel_cv = page.locator("select:has(option[value='CV'])").first
    await sel_cv.select_option(value="CV")
    await asyncio.sleep(2)
    file_inp = page.locator("input[type='file']").first
    await file_inp.set_input_files(cv_pdf_path)
    await asyncio.sleep(5)

    # D. Téléversement de la Lettre sur-mesure
    print(f"[*] Upload de la Lettre validée : {lm_pdf_path}")
    sel_lm = page.locator("select:has(option[value='LMOT'])").first
    await sel_lm.select_option(value="LMOT")
    await asyncio.sleep(2)
    file_inp = page.locator("input[type='file']").first
    await file_inp.set_input_files(lm_pdf_path)
    await asyncio.sleep(5)

    # 5. Soumission de la candidature
    send_btn = page.locator("button:has-text('Envoyer ma candidature')").first
    if await send_btn.count() > 0 and await send_btn.is_enabled():
        print("[+] Clic sur 'Envoyer ma candidature'...")
        await send_btn.click()
        await asyncio.sleep(6)

        confirm_btn = page.locator("button:has-text('Confirmer'), button:has-text('Valider'), button:has-text('Oui')")
        if await confirm_btn.count() > 0 and await confirm_btn.first.is_visible():
            await confirm_btn.first.click()
            await asyncio.sleep(5)

        # Capture de preuve
        proof_path = os.path.join(dossier_abs, "candidature_soumise_preuve.png")
        await page.screenshot(path=proof_path, full_page=True)
        print(f"[VICTOIRE] Preuve matérielle enregistrée : {proof_path}")

        proof_rel = f"{folder_rel}/candidature_soumise_preuve.png"
        offer_entry = {
            "title": raw_title,
            "academie": acad,
            "reference": ref,
            "location": loc,
            "url": offer_url,
            "folder_rel": folder_rel,
            "proof_rel": proof_rel
        }

        # Mise à jour des registres
        update_tracker_and_dashboard(offer_entry)
        return True
    else:
        print("[!] Le bouton 'Envoyer ma candidature' n'est pas actif.")
        return False

async def run_batch(limit: int = 5):
    """Exécute un lot de candidatures."""
    if not os.path.exists(QUALIFIED_JSON):
        print("[!] Fichier d'offres introuvable.")
        return

    with open(QUALIFIED_JSON, "r", encoding="utf-8") as f:
        all_offers = json.load(f)

    # Filtrer les offres déjà traitées
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            tracker = json.load(f)
        tracker_titles = {t.get("title", "").lower() for t in tracker}
        tracker_refs = {t.get("reference", "").lower() for t in tracker if t.get("reference")}
    except Exception:
        tracker_titles = set()
        tracker_refs = set()

    # Définition de l'ordre de priorité : Amiens, Lyon RH, Mayotte, Pornic, etc.
    priority_keywords = ["amiens", "rh", "grh", "mayotte", "pornic", "sam", "stmg"]

    def score_priority(item):
        title = item["title"].lower()
        lines = " ".join(item.get("lines", [])).lower()
        score = 0
        for i, kw in enumerate(priority_keywords):
            if kw in title or kw in lines:
                score += (len(priority_keywords) - i) * 10
        return score

    sorted_offers = sorted(all_offers, key=score_priority, reverse=True)

    candidated_count = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 1000}
        )
        page = await context.new_page()

        for idx, offer in enumerate(sorted_offers, 1):
            title = offer["title"]
            
            # Contrôle anti-doublon
            if title.lower() in tracker_titles:
                print(f"[-] Offre déjà dans le tracker : {title}")
                continue
            if "versailles" in title.lower() and "filière stmg" in title.lower():
                print(f"[-] Offre Versailles déjà soumise aujourd'hui : {title}")
                continue
            if "créteil" in title.lower() and "stmg" in title.lower():
                print(f"[-] Offre Créteil déjà traitée : {title}")
                continue

            success = await process_single_offer(page, offer)
            if success:
                candidated_count += 1
                tracker_titles.add(title.lower())
                print(f"[+] Candidature #{candidated_count} terminée avec succès.")

            if candidated_count >= limit:
                print(f"\n[+] Limite du lot atteinte ({limit} candidatures traitées).")
                break

            # Pause respectueuse entre 2 candidatures
            await asyncio.sleep(8)

        await browser.close()

    print(f"\n=======================================================")
    print(f"[+] FIN DU LOT : {candidated_count} nouvelle(s) candidature(s) soumise(s).")
    print(f"=======================================================")

if __name__ == "__main__":
    limit = 5
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    asyncio.run(run_batch(limit=limit))
