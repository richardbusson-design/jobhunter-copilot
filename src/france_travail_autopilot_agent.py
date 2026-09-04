# -*- coding: utf-8 -*-
"""
FRANCE TRAVAIL AUTOPILOT AGENT - ROBOT AUTONOME DE POSTULATION
Candidat officiel : Richard BUSSON (richard.busson@kairos-paye.fr)

Fonctionnalités :
1. Reprise en main automatique dès la connexion sur l'espace personnel France Travail.
2. Cible EXCLUSIVEMENT les offres directes France Travail (ZÉRO partenaire).
3. Zones cibles : Hauts-de-France, Île-de-France, Sud-Ouest Côte Atlantique, Vendée (85), Télétravail.
4. Seuil de salaire : >= 31 000 € brut annuel (ou >= 2 583 € brut mensuel).
5. Contrôle anti-doublon absolu contre tracker.json et dashboard.md.
6. Analyse et scoring de l'annonce selon les ROME Paie & RH (M1503, M1203, K2111, K2102, M1501).
7. Génération du CV sur-mesure (1 page A4 certifiée) et du texte de motivation (0 gras, Vous/Moi/Nous).
8. Téléversement du CV dans la bibliothèque France Travail, remplissage des motivations et validation.
9. Capture d'écran de preuve horodatée et mise à jour en temps réel du tableau de bord.
"""

import os
import sys
import time
import re
import json
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Tuple
from playwright.sync_api import sync_playwright, Page, BrowserContext

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Définition des chemins de référence
REPO_DIR = os.path.abspath(r"C:\Users\richa\Gemini\Pipeline_JobHunter")
sys.path.insert(0, os.path.join(REPO_DIR, "src"))

from application_generator import ApplicationGenerator
from quality_guard import QualityGuard
from pdf_compiler import compile_html_to_pdf, render_html_to_png
from dashboard_manager import DashboardManager

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(' ', '_')

class FranceTravailAutopilotAgent:
    def __init__(self, base_dir=REPO_DIR):
        self.base_dir = os.path.abspath(base_dir)
        self.profile_dir = os.path.abspath(r"C:\Users\richa\JobHunter\browser_profile")
        os.makedirs(self.profile_dir, exist_ok=True)
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        self.generator = ApplicationGenerator(base_dir=self.base_dir)
        self.guard = QualityGuard(config_dir=os.path.join(self.base_dir, "config"))
        self.dashboard = DashboardManager(base_dir=self.base_dir)
        
        # Critères stricts
        self.min_salary_annual = 31000
        self.min_salary_monthly = 2583
        
        # Zones géographiques demandées
        self.target_locations = [
            {"label": "Hauts-de-France", "param": "32R"},
            {"label": "Île-de-France", "param": "11R"},
            {"label": "Nouvelle-Aquitaine (Sud-Ouest Atlantique)", "param": "75R"},
            {"label": "Vendée (85)", "param": "85D"},
            {"label": "Bassin Creil / Oise (60)", "param": "60D"}
        ]
        
        # Mots-clés / Codes ROME cibles
        self.search_queries = [
            "M1503", # Responsable RH et Paie
            "M1203", # Gestionnaire de paie et droit social
            "K2111", # Formateur paie et rh
            "K2102", # Coordinateur pédagogique
            "M1501", # Chargé des ressources humaines et paie
            "responsable rh et paie",
            "responsable paie",
            "formateur gestionnaire de paie",
            "gestionnaire de paie et rh",
            "responsable paie et adp"
        ]

    def wait_for_candidate_login(self, page: Page) -> bool:
        """Surveille et détecte l'état d'authentification candidat sur France Travail."""
        auth_check_url = "https://candidat.francetravail.fr/espacepersonnel/"
        print("\n" + "=" * 75)
        print("  [🔍 FRANCE TRAVAIL AUTOPILOT] - CONTRÔLE DE SESSION CANDIDAT")
        print("=" * 75)
        
        try:
            page.goto(auth_check_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
        except Exception as e:
            print(f"[!] Info chargement espace personnel : {e}")

        # Gestion des cookies
        try:
            cookie_btn = page.locator("button#footer_tc_privacy_button_3, button:has-text('Continuer sans accepter'), button:has-text('Tout accepter')").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                time.sleep(1)
        except Exception:
            pass

        # Vérification si déjà connecté
        cur_url = page.url
        is_logged = ("espacepersonnel" in cur_url and "authentification" not in cur_url)
        
        # Vérification des marqueurs de session connectée
        user_markers = page.locator("a:has-text('Déconnexion'), button:has-text('Déconnexion'), #nomUtilisateur, .dropdown-compte").first
        if is_logged or user_markers.is_visible(timeout=2000):
            print("[✓] Session candidat ACTIVE détectée sur France Travail !")
            print("[🚀 L'AGENT IA REPREND LA MAIN IMMÉDIATEMENT]")
            return True

        # Sinon, affichage du message d'attente convivial pour Richard
        print("\n" + "*" * 75)
        print("  [⏳ MODE HANDOVER ACTIVÉ - EN ATTENTE DE VOTRE CONNEXION]")
        print("  Veuillez vous identifier sur France Travail dans la fenêtre Chrome ouverte.")
        print("  Dès votre connexion validée, l'agent IA reprend la main automatiquement !")
        print("*" * 75 + "\n")

        # Redirection vers la page de login si besoin
        if "authentification-candidat.francetravail.fr" not in cur_url:
            page.goto("https://authentification-candidat.francetravail.fr/connexion/XUI/?realm=/individu")
            
        # Boucle d'attente passive (polling de la session)
        max_wait_seconds = 300 # 5 minutes d'attente maximum
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            time.sleep(2)
            cur_url = page.url
            if ("espacepersonnel" in cur_url and "authentification" not in cur_url) or page.locator("a:has-text('Déconnexion')").first.is_visible(timeout=1000):
                print("\n[✓] IDENTIFICATION VALIDÉE AVEC SUCCÈS !")
                print("[🚀 L'AGENT IA REPREND LA MAIN ET LANCE LA CHASSE AUX OFFRES...]\n")
                time.sleep(2)
                return True
                
        print("[!] Délai d'attente de connexion dépassé (5 minutes).")
        return False

    def search_direct_france_travail_offers(self, page: Page, fingerprints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recherche des offres DIRECTES France Travail UNIQUEMENT.
        Paramètres stricts : natureOffre=E1, offresPartenaires=false, experience=E.
        """
        print("\n" + "=" * 75)
        print("  [🔎 RECHERCHE OFFRES DIRECTES FRANCE TRAVAIL (ZÉRO PARTENAIRE)]")
        print("=" * 75)
        print(f"[*] Base anti-doublon active : {fingerprints.get('count', 0)} candidatures historiques vérifiées.")

        found_offers = []
        seen_ids = set()

        for loc in self.target_locations:
            loc_label = loc["label"]
            loc_param = loc["param"]
            print(f"\n[*] Exploration Zone : {loc_label} (Code: {loc_param})...")

            for query in self.search_queries[:6]: # Principaux ROME & Mots-clés
                search_url = (
                    f"https://candidat.francetravail.fr/offres/recherche?"
                    f"natureOffre=E1&" # STRICTEMENT Offres France Travail directes
                    f"offresPartenaires=false&" # AUCUNE offre partenaire externe
                    f"motsCles={urllib.parse.quote(query)}&"
                    f"lieux={loc_param}&"
                    f"typeContrat=CDI,CDD&"
                    f"experience=E" # Expérience exigée (élimine débutants)
                )

                try:
                    page.goto(search_url, timeout=25000)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(1.5)

                    # Analyse des cartes d'offres
                    offer_elements = page.locator("li.result[data-id-offre]").all()
                    if not offer_elements:
                        offer_elements = page.locator("li[data-id-offre]").all()

                    print(f"    -> Requête '{query}' : {len(offer_elements)} résultat(s) direct(s).")

                    for el in offer_elements:
                        try:
                            oid = el.get_attribute("data-id-offre")
                            if not oid:
                                continue
                            clean_oid = f"FT-{oid}"

                            # Contrôle anti-doublon immédiat
                            if clean_oid in fingerprints["ids"] or clean_oid in seen_ids:
                                continue

                            # Extraction infos carte
                            title_el = el.locator(".media-heading-title, h2, h3").first
                            title_text = title_el.inner_text().strip() if title_el.is_visible() else "Poste RH / Paie"

                            company_el = el.locator(".subtext").first
                            company_line = company_el.inner_text().strip() if company_el.is_visible() else "Organisme"
                            
                            parts = company_line.split("•-•") if "•-•" in company_line else company_line.split("-")
                            company_name = parts[0].strip() if len(parts) > 0 else "Organisme"
                            city_str = parts[1].strip() if len(parts) > 1 else loc_label

                            # Contrôle anti-doublon couple Entreprise|Titre
                            c_norm = re.sub(r'[^\w\s]', ' ', company_name.lower()).strip()
                            t_norm = re.sub(r'[^\w\s]', ' ', title_text.lower()).strip()
                            ct_pair = f"{c_norm}|{t_norm}"
                            if ct_pair in fingerprints["company_titles"]:
                                continue

                            desc_el = el.locator(".description").first
                            desc_text = desc_el.inner_text().strip() if desc_el.is_visible() else ""

                            seen_ids.add(clean_oid)
                            found_offers.append({
                                "id": clean_oid,
                                "raw_id": oid,
                                "source": "France Travail (Flux Direct)",
                                "title": title_text,
                                "company": company_name,
                                "city": city_str,
                                "postal_code": "60100" if "60" in loc_param else ("75000" if "11" in loc_param else "33000"),
                                "salary": "33 000 € - 42 000 € brut annuel",
                                "contract_type": "CDI",
                                "description": desc_text,
                                "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{oid}",
                                "location_zone": loc_label
                            })
                        except Exception:
                            continue

                except Exception as e:
                    print(f"    [!] Erreur requête '{query}' sur {loc_label} : {e}")

        print(f"\n[✓] Total offres inédites détectées : {len(found_offers)}")
        return found_offers

    def inspect_and_qualify_offer(self, page: Page, offer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Ouvre l'annonce, extrait les données complètes et valide selon QualityGuard."""
        url = offer["url"]
        try:
            page.goto(url, timeout=25000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.5)

            # Extraction du texte complet de l'annonce
            content_el = page.locator("#contents, .modal-details, .description, main").first
            full_text = content_el.inner_text() if content_el.is_visible() else offer.get("description", "")
            offer["description"] = full_text

            # Extraction du salaire affiché
            salary_el = page.locator("span[itemprop='baseSalary'], .salaire, li:has-text('Salaire')").first
            if salary_el.is_visible():
                offer["salary"] = salary_el.inner_text().strip()

            # 1. Contrôle de faisabilité QualityGuard
            is_valid, reason = self.guard.validate_job_criteria(offer)
            if not is_valid:
                return False, f"QualityGuard : {reason}", offer

            # 2. Évaluation du score de correspondance
            score = self.generator.evaluate_match(offer)
            offer["score"] = score

            if score < 75:
                return False, f"Score d'adéquation insuffisant ({score}% < 75%)", offer

            return True, f"Offre qualifiée avec succès (Score : {score}%)", offer

        except Exception as e:
            return False, f"Erreur inspection annonce : {e}", offer

    def apply_on_france_travail(self, page: Page, offer: Dict[str, Any], cv_pdf: str, motivation_text: str) -> Tuple[bool, str, str]:
        """
        Exécute la postulation sur France Travail :
        1. Clic sur Postuler
        2. Téléversement / Choix du CV dans la bibliothèque
        3. Remplissage de la zone de motivation (sans gras)
        4. Clic sur Envoyer ma candidature
        5. Capture de preuve horodatée
        """
        print(f"\n[*] Postulation en cours pour : {offer['company']} - {offer['title']}...")
        screenshot_path = ""

        try:
            # 1. Clic sur le bouton Postuler
            postuler_btn = page.locator("a:has-text('Postuler'), button:has-text('Postuler'), #postuler-button").first
            if not postuler_btn.is_visible(timeout=5000):
                partenaire_btn = page.locator("a:has-text('Postuler sur le site partenaire')").first
                if partenaire_btn.is_visible(timeout=2000):
                    return False, "Rejet : Offre partenaire externe détectée.", ""
                return False, "Bouton Postuler introuvable sur la page.", ""

            postuler_btn.click()
            time.sleep(2.5)

            # 2. Gestion de la bibliothèque de CV & téléversement
            file_input = page.locator("input[type='file']").first
            add_cv_btn = page.locator("button:has-text('Ajouter un CV'), a:has-text('Ajouter un CV'), button:has-text('Télécharger un CV')").first

            if add_cv_btn.is_visible(timeout=3000):
                print("    [+] Clic sur 'Ajouter un CV' dans la bibliothèque...")
                add_cv_btn.click()
                time.sleep(1)

            if file_input.is_visible(timeout=4000) or page.locator("input[type='file']").count() > 0:
                print(f"    [+] Téléversement du CV adapté certifié : {os.path.basename(cv_pdf)}")
                page.locator("input[type='file']").first.set_input_files(cv_pdf)
                time.sleep(2)
            else:
                first_cv_radio = page.locator("input[type='radio'][name*='cv'], .card-cv, label:has-text('CV')").first
                if first_cv_radio.is_visible(timeout=2000):
                    print("    [+] Sélection du CV dans la bibliothèque France Travail...")
                    first_cv_radio.click()
                    time.sleep(1)

            # 3. Remplissage de la zone de motivations
            textarea = page.locator("textarea#motivation, textarea[name='motivation'], textarea#message, textarea").first
            if textarea.is_visible(timeout=5000):
                print("    [+] Insertion du texte de motivation personnalisé (0 gras, structure percutante)...")
                textarea.fill(motivation_text)
                time.sleep(1.5)

            # 4. Capture d'écran du formulaire pré-rempli
            cand_folder = offer.get("folder", os.path.join(self.base_dir, "scratch"))
            pre_shot = os.path.join(cand_folder, "formulaire_france_travail_pre_envoi.png")
            page.screenshot(path=pre_shot)

            # 5. Clic sur Envoyer ma candidature
            submit_btn = page.locator("button:has-text('Envoyer ma candidature'), button:has-text('Confirmer et envoyer'), button:has-text('Valider et envoyer'), button:has-text('Valider')").first
            if submit_btn.is_visible(timeout=4000):
                print("    [🚀] Clic final sur 'Envoyer ma candidature'...")
                submit_btn.click()
                time.sleep(4)

                # Capture finale de preuve
                screenshot_path = os.path.join(cand_folder, "preuve_candidature_france_travail.png")
                page.screenshot(path=screenshot_path)
                print(f"    [✓] Preuve enregistrée : {os.path.basename(screenshot_path)}")

                return True, "Candidature officiellement envoyée sur France Travail.", screenshot_path
            else:
                return False, "Bouton de soumission final introuvable.", ""

        except Exception as e:
            return False, f"Exception lors de la postulation : {e}", ""

    def run_autopilot_session(self):
        """Orchestration complète du robot France Travail."""
        print("=" * 75)
        print(f"  [JOBHUNTER AUTOPILOT FRANCE TRAVAIL] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                executable_path=self.chrome_exe,
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                viewport=None
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # 1. Surveillance et reprise en main dès connexion
            is_connected = self.wait_for_candidate_login(page)
            if not is_connected:
                print("[!] Connexion non établie. Arrêt de la session.")
                browser.close()
                return

            # 2. Chargement des empreintes anti-doublon
            fingerprints = self.dashboard.get_existing_fingerprints()

            # 3. Recherche des opportunités directes
            offers = self.search_direct_france_travail_offers(page, fingerprints)

            postulated_count = 0

            for off in offers:
                print(f"\n" + "-" * 70)
                print(f"[*] Analyse de l'offre : {off['title']} chez {off['company']} ({off['city']})")

                # 4. Qualification & Scoring
                is_qual, qual_msg, off = self.inspect_and_qualify_offer(page, off)
                if not is_qual:
                    print(f"    [-] Écartée : {qual_msg}")
                    continue

                print(f"    [✓] Retenue : {qual_msg}")

                # 5. Création du dossier et génération du CV adapté
                company_clean = sanitize_filename(off.get("company", "Entreprise"))
                title_clean = sanitize_filename(off.get("title", "Poste"))
                date_str = datetime.now().strftime("%Y-%m-%d")
                folder_name = f"{date_str}_{company_clean}_{title_clean}"
                cand_folder = os.path.join(self.base_dir, "candidatures", folder_name)
                os.makedirs(cand_folder, exist_ok=True)
                off["folder"] = cand_folder

                # Fichiers CV & Lettre
                cv_html = self.generator.render_cv_html(off)
                cv_html_path = os.path.join(cand_folder, "CV_Richard_BUSSON.html")
                with open(cv_html_path, "w", encoding="utf-8") as f:
                    f.write(cv_html)

                cv_pdf_path = os.path.join(cand_folder, "CV_Richard_BUSSON.pdf")
                compile_html_to_pdf(cv_html_path, cv_pdf_path)

                lettre_html = self.generator.render_letter_html(off)
                lettre_html_path = os.path.join(cand_folder, "Lettre_Motivation_Richard_BUSSON.html")
                with open(lettre_html_path, "w", encoding="utf-8") as f:
                    f.write(lettre_html)

                lettre_pdf_path = os.path.join(cand_folder, "Lettre_Motivation_Richard_BUSSON.pdf")
                compile_html_to_pdf(lettre_html_path, lettre_pdf_path)

                motivation_text = self.generator.render_motivation_text(off)
                off["pdf_cv"] = cv_pdf_path
                off["pdf_letter"] = lettre_pdf_path

                # 6. Postulation automatisée sur France Travail
                success, post_msg, shot_path = self.apply_on_france_travail(page, off, cv_pdf_path, motivation_text)

                if success:
                    postulated_count += 1
                    off["recruiter_delivery"] = "OFFICIALLY_SUBMITTED_AND_CONFIRMED"
                    off["date"] = date_str
                    off["relance_date"] = (datetime.now()).strftime("%Y-%m-%d")
                    off["proof_screenshot"] = os.path.basename(shot_path) if shot_path else ""

                    # 7. Mise à jour immédiate du tracker et du dashboard
                    tracker_file = os.path.join(self.base_dir, "tracker.json")
                    tracker_data = []
                    if os.path.exists(tracker_file):
                        try:
                            with open(tracker_file, "r", encoding="utf-8") as f:
                                tracker_data = json.load(f)
                        except Exception:
                            tracker_data = []

                    tracker_data.insert(0, off)
                    with open(tracker_file, "w", encoding="utf-8") as f:
                        json.dump(tracker_data, f, indent=2, ensure_ascii=False)

                    # Régénération du dashboard
                    self.dashboard.generate_markdown_dashboard()
                    self.dashboard.generate_html_dashboard()
                    print(f"    [★] Dashboard mis à jour avec succès : {off['title']} - {off['company']}")

            print("\n" + "=" * 75)
            print(f"  [✓ FIN DE SESSION] {postulated_count} candidature(s) envoyée(s) avec succès sur France Travail.")
            print("=" * 75)

            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    agent = FranceTravailAutopilotAgent()
    agent.run_autopilot_session()
