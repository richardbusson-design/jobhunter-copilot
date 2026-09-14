# -*- coding: utf-8 -*-
"""
Module d'automatisation intégrale pour recrutement.education.gouv.fr avec Playwright.
Fonctionne aussi bien sur PC local qu'en Cloud 24h/24 via GitHub Actions.
"""

import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

class EducationGouvBot:
    def __init__(self, base_dir="."):
        self.base_dir = os.path.abspath(base_dir)
        self.is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true" or sys.platform != "win32"
        if not self.is_ci and sys.platform == "win32":
            self.profile_dir = os.path.abspath(r"C:\Users\richa\JobHunter\browser_profile")
            self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        else:
            self.profile_dir = os.path.join(self.base_dir, "browser_profile")
            self.chrome_exe = None
        os.makedirs(self.profile_dir, exist_ok=True)
        self.load_env_credentials()

    def load_env_credentials(self):
        """Charge les identifiants depuis l'environnement ou le fichier .env."""
        self.username = os.environ.get("EDUCATION_GOUV_USER")
        self.password = os.environ.get("EDUCATION_GOUV_PASSWORD")
        if not self.username or not self.password:
            env_path = os.path.join(self.base_dir, ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("EDUCATION_GOUV_USER="):
                            self.username = line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("EDUCATION_GOUV_PASSWORD="):
                            self.password = line.split("=", 1)[1].strip().strip('"').strip("'")

    def has_credentials(self) -> bool:
        return bool(self.username and self.password)

    def apply_to_offer(self, offer_url: str, folder_abs: str) -> bool:
        """Postule automatiquement à une offre sur recrutement.education.gouv.fr."""
        cv_pdf = os.path.join(folder_abs, "CV_Richard_BUSSON.pdf")
        lettre_pdf = os.path.join(folder_abs, "Lettre_Motivation_Richard_BUSSON.pdf")

        if not os.path.exists(cv_pdf) or not os.path.exists(lettre_pdf):
            print(f"[!] Fichiers PDF manquants dans {folder_abs}")
            return False

        print(f"[*] Démarrage de la postulation automatique pour : {offer_url}")
        with sync_playwright() as p:
            if self.is_ci:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1280, "height": 900})
                page = context.new_page()
            else:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    channel="chrome" if os.path.exists(self.chrome_exe or "") else None,
                    headless=False,
                    viewport={"width": 1280, "height": 900}
                )
                page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(offer_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(5)

                # Si non connecté et identifiants disponibles, on se connecte
                conn_btn = page.locator("button:has-text('Je me connecte pour postuler'), a:has-text('Je me connecte pour postuler')").first
                if conn_btn.count() > 0:
                    if self.has_credentials():
                        print(f"[*] Connexion Cloud avec l'identifiant : {self.username}...")
                        conn_btn.click()
                        time.sleep(4)
                        user_input = page.locator("input[type='email'], input[name*='user'], input[name*='login']").first
                        pass_input = page.locator("input[type='password']").first
                        if user_input.count() > 0 and pass_input.count() > 0:
                            user_input.fill(self.username)
                            pass_input.fill(self.password)
                            submit_login = page.locator("button[type='submit'], button:has-text('Connexion'), input[type='submit']").first
                            if submit_login.count() > 0:
                                submit_login.click()
                                time.sleep(6)
                    else:
                        print("[!] Aucun identifiant renseigné pour la connexion Cloud automatique.")

                # Clic sur Je postule
                postuler_btn = page.locator("button:has-text('Je postule'), a:has-text('Je postule')").first
                if postuler_btn.count() > 0:
                    print("[+] Clic sur 'Je postule'...")
                    postuler_btn.click()
                    time.sleep(5)

                # Remplissage des coordonnées officielles
                inputs = page.locator("input").all()
                for inp in inputs:
                    name = (inp.get_attribute("name") or "").lower()
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    type_attr = (inp.get_attribute("type") or "").lower()
                    if "prenom" in name or "first" in name or "prénom" in ph:
                        inp.fill("Richard")
                    elif "nom" in name or "last" in name:
                        inp.fill("BUSSON")
                    elif type_attr == "email" or "mail" in name:
                        inp.fill("richard.busson@kairos-paye.fr")
                    elif type_attr == "tel" or "phone" in name or "mobile" in name:
                        inp.fill("07 61 96 15 46")
                    elif "ville" in name or "city" in name:
                        inp.fill("Creil")
                    elif "cp" in name or "postal" in name or "zip" in name:
                        inp.fill("60100")

                # Téléversement des PDF
                file_inputs = page.locator("input[type='file']").all()
                if len(file_inputs) >= 2:
                    file_inputs[0].set_input_files(cv_pdf)
                    file_inputs[1].set_input_files(lettre_pdf)
                elif len(file_inputs) == 1:
                    file_inputs[0].set_input_files(cv_pdf)

                # Capture de preuve
                proof_path = os.path.join(folder_abs, "preuve_soumission_education.png")
                page.screenshot(path=proof_path, full_page=True)
                print(f"[✓] Preuve enregistrée : {proof_path}")

                # Tentative de soumission si bouton final présent
                submit_final = page.locator("button:has-text('Envoyer ma candidature'), button:has-text('Confirmer'), button:has-text('Valider ma candidature')").first
                if submit_final.count() > 0:
                    submit_final.click()
                    time.sleep(5)
                    page.screenshot(path=proof_path, full_page=True)
                    print("[✓] Candidature officiellement soumise avec succès !")

                if not self.is_ci:
                    context.close()
                else:
                    browser.close()
                return True
            except Exception as e:
                print(f"[!] Erreur lors de la postulation : {e}")
                try:
                    if not self.is_ci:
                        context.close()
                    else:
                        browser.close()
                except Exception:
                    pass
                return False
