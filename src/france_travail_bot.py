# -*- coding: utf-8 -*-
"""
Module d'automatisation intégrale France Travail avec Playwright.
Gère :
- La connexion automatique avec identifiant & mot de passe (stockés dans .env local)
- La navigation vers les offres d'emploi
- L'importation du CV et de la Lettre de motivation PDF certifiés dans la candidature
- L'insertion automatique du texte de motivation adapté
- La validation et le clic sur Postuler
"""

import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

class FranceTravailBot:
    def __init__(self, base_dir="."):
        self.base_dir = os.path.abspath(base_dir)
        self.profile_dir = os.path.abspath("C:/Users/richa/JobHunter/browser_profile")
        os.makedirs(self.profile_dir, exist_ok=True)
        self.chrome_exe = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.load_env_credentials()
        
    def load_env_credentials(self):
        """Charge les identifiants France Travail depuis le .env local sécurisé."""
        env_path = os.path.join(self.base_dir, ".env")
        self.username = None
        self.password = None
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FRANCE_TRAVAIL_USER="):
                        self.username = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("FRANCE_TRAVAIL_PASSWORD="):
                        self.password = line.split("=", 1)[1].strip().strip('"').strip("'")

    def login_with_credentials(self, username: str = None, password: str = None) -> bool:
        """
        Connecte automatiquement le compte candidat France Travail
        avec les identifiants et enregistre la session dans le profil persistant.
        """
        user = username or self.username
        pwd = password or self.password
        
        if not user or not pwd:
            print("[!] Identifiants France Travail non fournis.")
            return False
            
        auth_url = "https://authentification-candidat.francetravail.fr/connexion/XUI/?realm=/individu"
        print(f"[*] Connexion automatique à France Travail pour : {user}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                executable_path=self.chrome_exe,
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                viewport=None
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto(auth_url)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Gestion cookies
            try:
                cookie_btn = page.locator("button#footer_tc_privacy_button_3, button:has-text('Continuer sans accepter'), button:has-text('Tout accepter')").first
                if cookie_btn.is_visible():
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                pass
                
            # Saisie identifiant
            print("[*] Saisie de l'identifiant...")
            identifiant_input = page.locator("#identifiant, input[name='callback_0']").first
            identifiant_input.wait_for(state="visible", timeout=10000)
            identifiant_input.fill(user)
            time.sleep(1)
            
            # Saisie mot de passe
            print("[*] Saisie du mot de passe...")
            password_input = page.locator("#password, input[name='callback_1']").first
            password_input.wait_for(state="visible", timeout=10000)
            password_input.fill(pwd)
            time.sleep(1)
            
            # Validation
            print("[*] Clic sur 'Se connecter'...")
            submit_btn = page.locator("#submit, button:has-text('Se connecter')").first
            submit_btn.click()
            
            # Attente de la validation (redirection hors de la page de login)
            print("[*] En attente de la validation du serveur...")
            logged_in = False
            for _ in range(30):
                time.sleep(2)
                cur_url = page.url
                if "authentification-candidat.francetravail.fr" not in cur_url or "espacepersonnel" in cur_url:
                    logged_in = True
                    print(f"[+] Connexion réussie ! Redirigé vers : {cur_url}")
                    break
                    
            time.sleep(3)
            browser.close()
            return logged_in

    def apply_to_offer(self, offer_url: str, cv_pdf_path: str, letter_pdf_path: str, motivation_text: str, auto_confirm: bool = True):
        """
        Navigue sur l'offre France Travail, clique sur Postuler,
        importe le CV et la lettre dans la candidature, insère le texte de motivation,
        et clique sur Envoyer la candidature.
        """
        print(f"\n[*] Lancement de la postulation automatisée sur : {offer_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                executable_path=self.chrome_exe,
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                viewport=None
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto(offer_url)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Cookies
            try:
                cookie_btn = page.locator("button#footer_tc_privacy_button_3, button:has-text('Continuer sans accepter')").first
                if cookie_btn.is_visible():
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                pass
                
            # Clic Postuler
            postuler_btn = page.locator("a:has-text('Postuler'), button:has-text('Postuler')").first
            if not postuler_btn.is_visible():
                print("[!] Bouton Postuler non visible.")
                browser.close()
                return False, "Bouton Postuler non visible"
                
            print("[+] Clic sur le bouton Postuler...")
            postuler_btn.click()
            time.sleep(2)
            
            # Si demande de connexion, se connecter automatiquement si identifiants présents
            connect_btn = page.locator("a:has-text('Se connecter'), button:has-text('Se connecter')").first
            if connect_btn.is_visible():
                print("[*] Clic sur 'Se connecter' depuis la fenêtre d'offre...")
                connect_btn.click()
                time.sleep(3)
                
                # Vérifier si champs de connexion présents
                if page.locator("#identifiant").is_visible() and self.username and self.password:
                    print("[*] Saisie automatique des identifiants...")
                    page.locator("#identifiant").fill(self.username)
                    page.locator("#password").fill(self.password)
                    page.locator("#submit").click()
                    time.sleep(4)
                    
            # Recherche des champs de formulaire
            print("[*] Remplissage du formulaire de candidature...")
            time.sleep(2)
            
            # Texte de motivation
            textarea = page.locator("textarea").first
            if textarea.is_visible():
                print("[+] Insertion du texte de motivation sur-mesure...")
                textarea.fill(motivation_text)
                time.sleep(1)
                
            # Fichiers CV & Lettre
            file_inputs = page.locator("input[type='file']").all()
            if file_inputs:
                print(f"[+] Détection de {len(file_inputs)} champ(s) de fichier.")
                if len(file_inputs) >= 1 and os.path.exists(cv_pdf_path):
                    file_inputs[0].set_input_files(cv_pdf_path)
                    print(f"    -> CV injecté : {os.path.basename(cv_pdf_path)}")
                if len(file_inputs) >= 2 and os.path.exists(letter_pdf_path):
                    file_inputs[1].set_input_files(letter_pdf_path)
                    print(f"    -> Lettre injectée : {os.path.basename(letter_pdf_path)}")
                    
            # Capture écran du formulaire pré-rempli
            shot_ready = os.path.join(self.base_dir, "scratch", "formulaire_france_travail_rempli.png")
            page.screenshot(path=shot_ready)
            print(f"[+] Capture du formulaire prêt enregistrée : {shot_ready}")
            
            # Clic sur Envoyer
            submit_btn = page.locator("button:has-text('Envoyer ma candidature'), button:has-text('Valider'), button:has-text('Confirmer et envoyer')").first
            if auto_confirm and submit_btn.is_visible():
                print("[+] Clic sur le bouton de validation finale 'Envoyer ma candidature'...")
                submit_btn.click()
                time.sleep(4)
                shot_final = os.path.join(self.base_dir, "scratch", "confirmation_envoi_france_travail.png")
                page.screenshot(path=shot_final)
                print(f"[+] Capture de confirmation : {shot_final}")
                browser.close()
                return True, "Candidature officiellement envoyée sur France Travail"
            else:
                print("[*] Formulaire prêt à l'écran. Attente de confirmation...")
                time.sleep(15)
                browser.close()
                return True, "Formulaire préparé"

if __name__ == "__main__":
    bot = FranceTravailBot()
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        bot.login_with_credentials()
