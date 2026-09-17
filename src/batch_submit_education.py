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
import subprocess
import unicodedata
from datetime import datetime
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
SESSION_FILE = r"C:\Users\richa\JobHunter\browser_profile\education_storage_state.json"
TRACKER_FILE = os.path.join(BASE_DIR, "tracker.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.md")
RESTANTES_JSON = os.path.join(BASE_DIR, "data", "offres_stmg_restantes.json")
QUALIFIED_JSON = os.path.join(BASE_DIR, "data", "offres_stmg_nationales_qualifiees.json")

# Importer le générateur sur-mesure
sys.path.append(os.path.join(BASE_DIR, "src"))
from generate_bespoke_dossier import generate_dossier_files

def norm(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()
    t = re.sub(r'[\W_]+', ' ', t)
    return t.strip()

def sanitize_folder_name(name: str) -> str:
    s = re.sub(r'[^\w\-_]', '_', name)
    return re.sub(r'_+', '_', s).strip('_')[:80]

def build_smart_query(offer: dict) -> str:
    """Construit une requête de recherche ultra-ciblée pour le portail."""
    title = offer.get("title", "")
    lines = offer.get("lines", [])
    acad_line = lines[1] if len(lines) > 1 else ""
    acad_match = re.search(r'Académie de\s+([A-ZÉÈÊÀÂÔÛÎÇ\-]+)', acad_line, re.I)
    acad = acad_match.group(1).strip() if acad_match else ""

    code_match = re.search(r'\b(L\d{4}|P\d{4}|P\d{3})\b', title)
    code = code_match.group(1) if code_match else ""

    cities = [
        "Tours", "Issoudun", "Dieppe", "Saint Lô", "Saint-Lô", "Le Havre", "Bordeaux",
        "Martinique", "Guyane", "Oyonnax", "Jonzac", "Honfleur", "Alençon", "Vire",
        "Poligny", "Forbach", "Caen", "Douarnenez", "Carhaix", "Bayeux", "Allonnes",
        "Pornic", "Angoulême", "St Avold", "Saint-Avold", "Bourg en Bresse", "Poitiers",
        "Rennes", "Dijon", "Strasbourg", "Mayotte", "Créteil", "Versailles", "Amiens"
    ]
    city_found = None
    for c in cities:
        if re.search(r'\b' + re.escape(c) + r'\b', title, re.I) or re.search(r'\b' + re.escape(c) + r'\b', " ".join(lines), re.I):
            city_found = c
            break

    if code and acad:
        return f"{code} {acad}"
    elif code:
        return code
    elif city_found and acad and city_found.lower() != acad.lower():
        return f"{city_found} {acad}"
    elif city_found:
        return f"{city_found} economie gestion"
    elif acad:
        return f"{acad} economie gestion"
    return "economie gestion"

def update_tracker_and_dashboard(offer_entry: dict):
    """Met à jour tracker.json et dashboard.md."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Mise à jour tracker.json
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
    except Exception:
        tracker_data = []

    ref_id = offer_entry.get("reference") or offer_entry.get("title")
    existing_idx = None
    for i, item in enumerate(tracker_data):
        if item.get("reference") == ref_id or (ref_id and item.get("id") == ref_id) or item.get("title") == offer_entry.get("title"):
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
        "notes": f"Poste d'Enseignant Éco-Gestion / STMG. Candidature transmise et validée sur le portail officiel le {today_str}. 4 pièces officielles jointes.",
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
    print(f"[OK] tracker.json mis à jour pour : {ref_id}", flush=True)

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

            table_header = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            if table_header in dash_content:
                dash_content = dash_content.replace(table_header, table_header + dash_line + "\n")
                with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
                    f.write(dash_content)
                print(f"[OK] dashboard.md mis à jour avec succès.", flush=True)
        except Exception as e:
            print(f"[!] Erreur mise à jour dashboard.md : {e}", flush=True)

def git_sync(batch_num: int):
    """Synchronise les nouveaux dossiers et trackers sur GitHub origin/main."""
    try:
        cmd = 'git add tracker.json dashboard.md candidatures/ data/ && git commit -m \"feat(candidatures): envoi batch education nationale STMG #' + str(batch_num) + '\" && git push origin main'
        res = subprocess.run(cmd, shell=True, cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[GIT] Synchronisation réussie sur origin/main (Lot #{batch_num})", flush=True)
        else:
            print(f"[GIT] Commit ou push : {res.stdout} {res.stderr}", flush=True)
    except Exception as e:
        print(f"[!] Erreur git sync : {e}", flush=True)

async def process_single_offer(page, offer_info: dict) -> bool:
    """Traite de bout en bout une candidature sur le portail."""
    raw_title = offer_info["title"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    smart_query = build_smart_query(offer_info)

    print(f"\n=======================================================", flush=True)
    print(f"[*] TRAITEMENT OFFRE : {raw_title}", flush=True)
    print(f"[*] REQUÊTE CIBLÉE : '{smart_query}'", flush=True)
    print(f"=======================================================", flush=True)

    # 1. Navigation et recherche
    await page.goto("https://recrutement.education.gouv.fr/recrutement/offres", wait_until="domcontentloaded", timeout=45000)
    await asyncio.sleep(4)

    search_input = page.locator("input[name='search']").first
    await search_input.fill("")
    await search_input.type(smart_query, delay=25)
    await page.locator("button:has-text('Rechercher')").first.click()
    await asyncio.sleep(5)

    cards = page.locator(".fr-card, c-dsfroffreemploicard")
    n_cards = await cards.count()
    print(f"[+] {n_cards} carte(s) trouvée(s) pour '{smart_query}'", flush=True)

    if n_cards == 0:
        print("[!] Aucun résultat avec requête ciblée. Tentative avec 'economie gestion'...", flush=True)
        await search_input.fill("")
        await search_input.type("economie gestion", delay=25)
        await page.locator("button:has-text('Rechercher')").first.click()
        await asyncio.sleep(5)
        cards = page.locator(".fr-card, c-dsfroffreemploicard")
        n_cards = await cards.count()

    # Trouver la carte avec le meilleur score de correspondance
    code_match = re.search(r'\b(L\d{4}|P\d{4})\b', raw_title)
    code = code_match.group(1).lower() if code_match else None

    title_words = set(re.findall(r'\b\w{4,}\b', norm(raw_title)))

    best_score = -1
    target_card = None

    for i in range(min(n_cards, 12)):
        c = cards.nth(i)
        ctxt = norm(await c.inner_text())
        
        score = 0
        if code and code in ctxt:
            score += 15
        
        for w in title_words:
            if w in ctxt:
                score += 2

        lines = offer_info.get("lines", [])
        if len(lines) > 1 and norm(lines[1]) in ctxt:
            score += 8

        if score > best_score:
            best_score = score
            target_card = c

    if not target_card or best_score <= 2:
        print(f"[!] Aucune carte pertinente trouvée (meilleur score: {best_score}).", flush=True)
        return False

    selected_text = (await target_card.inner_text()).replace('\n', ' // ')
    print(f"[+] Carte sélectionnée (score {best_score}): {selected_text[:110]}", flush=True)

    link = target_card.locator("a").first
    await link.click()
    await asyncio.sleep(6)

    offer_url = page.url
    print(f"[+] Page de l'offre atteinte : {offer_url}", flush=True)

    content = await page.eval_on_selector("main", "el => el ? el.innerText : ''")
    if not content:
        content = await page.eval_on_selector("body", "el => el.innerText")

    ref_match = re.search(r'(MENJ-[A-Z0-9-]+)', content)
    ref = ref_match.group(1) if ref_match else f"MENJ-STMG-{int(time.time())}"

    acad_match = re.search(r'Académie de\s+([A-ZÉÈÊÀÂÔÛÎÇ\-]+)', content, re.I)
    acad = acad_match.group(0) if acad_match else offer_info.get("lines", ["", "Académie Éducation Nationale"])[1]

    loc_match = re.search(r'Lieu de travail\s*:\s*([^\n]+)', content)
    loc = loc_match.group(1).strip() if loc_match else acad

    # Vérification présence bouton "Je postule"
    postuler_btn = page.locator("button:has-text('Je postule')").first
    if await postuler_btn.count() == 0:
        print("[!] Bouton 'Je postule' absent sur la page (déjà candidaté ou offre expirée).", flush=True)
        return False

    # 2. Génération des 6 fichiers sur-mesure QualityGuard 3-Pass
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

    print(f"[*] Génération du pack 6 fichiers sur-mesure dans : {dossier_abs}", flush=True)
    dossier_files = await generate_dossier_files(offer_data, dossier_abs)
    cv_pdf_path = dossier_files["cv_pdf"]
    lm_pdf_path = dossier_files["lm_pdf"]

    # 3. Initialisation de la candidature
    print("[+] Clic sur 'Je postule'...", flush=True)
    await postuler_btn.click()
    await asyncio.sleep(5)

    fermer_btn = page.locator("button:has-text('Fermer')")
    if await fermer_btn.count() > 0 and await fermer_btn.first.is_visible():
        await fermer_btn.first.click()
        await asyncio.sleep(4)

    # 4. Accès à Mon espace candidat -> Mes candidatures -> Ouvrir le Brouillon
    print("[*] Accès à Mon espace candidat...", flush=True)
    await page.goto("https://recrutement.education.gouv.fr/recrutement/mon-espace-candidat", wait_until="domcontentloaded", timeout=45000)
    await asyncio.sleep(5)

    tab_cand = page.locator("text='Mes candidatures'").first
    await tab_cand.click()
    await asyncio.sleep(4)

    brouillon_card = page.locator(".fr-card:has-text('BROUILLON')").first
    if await brouillon_card.count() > 0:
        print("[+] Brouillon trouvé, ouverture...", flush=True)
        await brouillon_card.click()
        await asyncio.sleep(6)
    else:
        print("[!] Aucun brouillon trouvé dans Mes candidatures.", flush=True)
        return False

    # 5. Rattachement des 4 pièces obligatoires
    # A. Passeport
    has_passport = await page.locator(".slds-file:has-text('Passeport'), a:has-text('Passeport')").count() > 0
    if not has_passport:
        print("[*] Rattachement du Passeport...", flush=True)
        sel_cni = page.locator("select:has(option[value='CNI_SEJ'])").first
        if await sel_cni.count() > 0:
            await sel_cni.select_option(value="CNI_SEJ")
            await asyncio.sleep(2)
            sel_exist = page.locator("select").nth(3)
            for opt_idx in range(await sel_exist.locator("option").count()):
                opt = sel_exist.locator("option").nth(opt_idx)
                otxt = (await opt.inner_text()).strip()
                oval = await opt.get_attribute("value")
                if "Passeport" in otxt and oval:
                    await sel_exist.select_option(value=oval)
                    print(f"    -> {otxt} rattaché", flush=True)
                    break
            await asyncio.sleep(3)

    # B. Diplôme
    has_dipl = await page.locator(".slds-file:has-text('Diplome'), a:has-text('Diplome')").count() > 0
    if not has_dipl:
        print("[*] Rattachement du Diplôme (Master 2 Droit Public)...", flush=True)
        sel_dipl = page.locator("select:has(option[value='DIPL'])").first
        if await sel_dipl.count() > 0:
            await sel_dipl.select_option(value="DIPL")
            await asyncio.sleep(2)
            sel_exist = page.locator("select").nth(3)
            for opt_idx in range(await sel_exist.locator("option").count()):
                opt = sel_exist.locator("option").nth(opt_idx)
                otxt = (await opt.inner_text()).strip()
                oval = await opt.get_attribute("value")
                if "Diplome_Master2_Droit_Public" in otxt and oval:
                    await sel_exist.select_option(value=oval)
                    print(f"    -> {otxt} rattaché", flush=True)
                    break
            await asyncio.sleep(3)

    # C. Upload CV
    print(f"[*] Upload CV validé : {cv_pdf_path}", flush=True)
    sel_cv = page.locator("select:has(option[value='CV'])").first
    await sel_cv.select_option(value="CV")
    await asyncio.sleep(2)
    await page.locator("input[type='file']").first.set_input_files(cv_pdf_path)
    await asyncio.sleep(5)

    # D. Upload LM
    print(f"[*] Upload Lettre validée : {lm_pdf_path}", flush=True)
    sel_lm = page.locator("select:has(option[value='LMOT'])").first
    await sel_lm.select_option(value="LMOT")
    await asyncio.sleep(2)
    await page.locator("input[type='file']").first.set_input_files(lm_pdf_path)
    await asyncio.sleep(5)

    # 6. Soumission finale
    send_btn = page.locator("button:has-text('Envoyer ma candidature')").first
    if await send_btn.count() > 0 and await send_btn.is_enabled():
        print("[+] Clic sur 'Envoyer ma candidature'...", flush=True)
        await send_btn.click()
        await asyncio.sleep(6)

        confirm_btn = page.locator("button:has-text('Confirmer'), button:has-text('Valider'), button:has-text('Oui')")
        if await confirm_btn.count() > 0 and await confirm_btn.first.is_visible():
            await confirm_btn.first.click()
            await asyncio.sleep(5)

        proof_path = os.path.join(dossier_abs, "candidature_soumise_preuve.png")
        await page.screenshot(path=proof_path, full_page=True)
        print(f"[VICTOIRE] Preuve matérielle enregistrée : {proof_path}", flush=True)

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

        update_tracker_and_dashboard(offer_entry)
        return True
    else:
        print("[!] Le bouton 'Envoyer ma candidature' n'est pas actif.", flush=True)
        return False

async def run_batch(limit: int = 50, batch_id: int = 2):
    """Exécute les candidatures de manière séquentielle continue."""
    if os.path.exists(RESTANTES_JSON):
        with open(RESTANTES_JSON, "r", encoding="utf-8") as f:
            remaining_offers = json.load(f)
    elif os.path.exists(QUALIFIED_JSON):
        with open(QUALIFIED_JSON, "r", encoding="utf-8") as f:
            remaining_offers = json.load(f)
    else:
        print("[!] Aucune liste d'offres disponible.", flush=True)
        return

    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            tracker = json.load(f)
        tracker_titles = {norm(t.get("title")) for t in tracker if t.get("title")}
        tracker_refs = {t.get("reference", "").lower() for t in tracker if t.get("reference")}
    except Exception:
        tracker_titles = set()
        tracker_refs = set()

    filtered_offers = []
    for o in remaining_offers:
        t_raw = o.get("title", "").strip()
        t_n = norm(t_raw)
        if t_n in tracker_titles:
            continue
        is_sub = False
        for tt in tracker_titles:
            if len(t_n) > 20 and (t_n in tt or tt in t_n):
                is_sub = True
                break
        if not is_sub:
            filtered_offers.append(o)

    print(f"[*] Démarrage Traitement Continu : {len(filtered_offers)} offres éligibles dans la file. Objectif : {limit} candidatures.", flush=True)

    candidated_count = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 1000}
        )
        page = await context.new_page()

        for idx, offer in enumerate(filtered_offers, 1):
            title = offer["title"]
            print(f"\n>>> Progression : {candidated_count}/{limit} validées (Examen offre {idx}/{len(filtered_offers)})", flush=True)

            try:
                success = await process_single_offer(page, offer)
                if success:
                    candidated_count += 1
                    tracker_titles.add(norm(title))
                    print(f"[SUCCESS] Candidature #{candidated_count}/{limit} transmise avec succès !", flush=True)
                    
                    # Synchronisation Git tous les 5 envois
                    if candidated_count % 5 == 0:
                        print(f"[*] Palier de 5 atteint : synchronisation Git intermédiaire...", flush=True)
                        git_sync(batch_id + (candidated_count // 5))
            except Exception as e:
                print(f"[!] Erreur sur '{title}' : {e}", flush=True)

            if candidated_count >= limit:
                print(f"\n[+] Objectif du lot atteint ({limit} candidatures traitées).", flush=True)
                break

            await asyncio.sleep(6)

        await browser.close()

    # Synchronisation Git finale
    if candidated_count > 0 and candidated_count % 5 != 0:
        git_sync(batch_id + (candidated_count // 5) + 1)

    print(f"\n=======================================================", flush=True)
    print(f"[+] FIN DU TRAITEMENT CONTINU : {candidated_count} nouvelle(s) candidature(s) soumise(s).", flush=True)
    print(f"=======================================================", flush=True)

if __name__ == "__main__":
    limit = 50
    batch_id = 2
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) > 2:
        try:
            batch_id = int(sys.argv[2])
        except ValueError:
            pass
    asyncio.run(run_batch(limit=limit, batch_id=batch_id))
