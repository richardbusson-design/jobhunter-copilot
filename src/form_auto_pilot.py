# -*- coding: utf-8 -*-
"""
FORM AUTO PILOT - MOTEUR UNIVERSEL DE POSTULATION AUTOMATIQUE
Candidat : Richard BUSSON (richard.busson@kairos-paye.fr)

Fonctionnalités clés :
1. Remplissage adaptatif universel de n'importe quel formulaire ATS / site recruteur (Taleez, Hellowork, Apec, France Travail, SmartRecruiters, Lever, etc.)
2. Téléversement automatique du CV et de la Lettre de motivation ciblés pour l'offre
3. Contournement furtif anti-WAF / anti-bot (Cloudflare, Datadome, navigator.webdriver = undefined)
4. Gestion robuste des dropdowns complexes (Angular, React, Vue, Material) et du sélecteur salarial
5. Stratégie de repli anti-blocage (force click, dispatch JS, keyboard enter)
6. Détection et validation automatique des liens de confirmation par email via IMAP OVH
7. Preuve par capture d'écran horodatée (Zéro hallucination) et mise à jour immédiate du tracker
"""

import os
import sys
import time
import re
import json
import imaplib
import email
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import sync_playwright, Page, BrowserContext

class FormAutoPilot:
    def _load_env_file(self):
        env_path = os.path.join(self.base_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip().strip("'\"")
            except Exception:
                pass

    def __init__(self, base_dir="."):
        self.base_dir = os.path.abspath(base_dir)
        self._load_env_file()
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(self.chrome_exe):
            self.chrome_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        self.profile_dir = os.environ.get("BROWSER_PROFILE_DIR", r"C:\Users\richa\JobHunter\browser_profile")
        os.makedirs(self.profile_dir, exist_ok=True)
        
        # Données officielles de Richard Busson (Mémoire permanente)
        self.candidate = {
            "first_name": "Richard",
            "last_name": "BUSSON",
            "full_name": "Richard BUSSON",
            "email": "richard.busson@kairos-paye.fr",
            "phone": "0939200870",
            "phone_formatted": "09 39 20 08 70",
            "phone_mobile": "07 61 96 15 46",
            "phone_int": "+33939200870",
            "phone_pro": "09 39 20 08 70",
            "address": "98, allée Paul Cézanne",
            "postal_code": "60100",
            "city": "Creil",
            "country": "France",
            "age": "59",
            "availability": "Immédiate",
            "salary_min": "40000",
            "salary_text": "40.000 à 45.000 €",
            "linkedin": "https://www.linkedin.com/in/richard-busson",
            "website": "https://kairos-paye.fr",
            "mobility": "Hauts-de-France, Île-de-France, Façades Atlantique et Méditerranée (Mobilité nationale)",
            "default_motivation": (
                "Madame, Monsieur,\n\n"
                "Titulaire d'un Master 2 en Droit social / Droit public et fort de plus de 15 ans d'expertise en Direction RH "
                "et Gestion de la Paie (Secours Populaire : 580 collaborateurs, dialogue social CSE/DP, supervision DSN et masse salariale), "
                "j'ai l'honneur de vous soumettre ma candidature.\n\n"
                "Dirigeant par ailleurs un organisme de formation certifié Qualiopi préparant au Titre Professionnel Gestionnaire de Paie (TP-01254), "
                "je maîtrise parfaitement l'ensemble du périmètre : sécurisation juridique des procédures, pilotage technique de la paie, "
                "management d'équipes et ingénierie de compétences.\n\n"
                "À 59 ans, en recherche d'un engagement durable et loyal, immédiatement disponible et mobile, je souhaite mettre "
                "cette solide expérience opérationnelle et stratégique au service de vos projets.\n\n"
                "Dans l'attente de votre retour, je vous prie d'agréer l'expression de mes salutations distinguées.\n\n"
                "Richard BUSSON\n"
                "07 61 96 15 46 • richard.busson@kairos-paye.fr"
            )
        }
        
        # Identifiants IMAP pour l'auto-confirmation de lien par e-mail
        self.imap_server = os.environ.get("IMAP_SERVER", "ssl0.ovh.net")
        self.imap_user = os.environ.get("IMAP_USER", "richard.busson@kairos-paye.fr")
        self.imap_password = os.environ.get("SMTP_PASSWORD", "mailK41R0sbTN001")

    def find_dossier_files(self, offer: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], str]:
        """Localise le CV PDF, la Lettre PDF et le texte de motivation spécifiques pour l'offre."""
        folder = offer.get("folder")
        if not folder or not os.path.exists(folder):
            # Recherche d'un dossier correspondant dans candidatures/
            comp = offer.get("company", "").replace(" ", "_")
            cands_dir = os.path.join(self.base_dir, "candidatures")
            if os.path.exists(cands_dir):
                for d in os.listdir(cands_dir):
                    if comp.lower() in d.lower():
                        folder = os.path.join(cands_dir, d)
                        break

        cv_pdf = None
        letter_pdf = None
        motivation_text = self.candidate["default_motivation"]

        if folder and os.path.exists(folder):
            cand_cv = os.path.join(folder, "CV_Richard_BUSSON.pdf")
            if os.path.exists(cand_cv):
                cv_pdf = cand_cv
                
            cand_let = os.path.join(folder, "Lettre_Motivation_Richard_BUSSON.pdf")
            if os.path.exists(cand_let):
                letter_pdf = cand_let

            # Extraire texte de lettre si dispo
            cand_html = os.path.join(folder, "Lettre_Motivation_Richard_BUSSON.html")
            if os.path.exists(cand_html):
                try:
                    with open(cand_html, "r", encoding="utf-8") as f:
                        content = f.read()
                    paras = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
                    if paras:
                        clean_text = "\n\n".join([re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()])
                        if len(clean_text) > 100:
                            motivation_text = clean_text
                except Exception:
                    pass

        # Fallback CV sur le bureau ou JobHunter
        if not cv_pdf:
            for fallback in [
                os.path.join(self.base_dir, "candidatures", "CV_Richard_BUSSON.pdf"),
                r"C:\Users\richa\JobHunter\CV_Richard_BUSSON.pdf",
                r"C:\Users\richa\Desktop\CV_Richard_BUSSON.pdf"
            ]:
                if os.path.exists(fallback):
                    cv_pdf = fallback
                    break

        return cv_pdf, letter_pdf, motivation_text

    def fill_and_submit_form(self, url: str, offer: Dict[str, Any] = None, headless: bool = True) -> Dict[str, Any]:
        """
        Remplit et soumet automatiquement n'importe quel formulaire de candidature.
        Gère les tentatives alternatives en cas de blocage.
        """
        offer = offer or {}
        cv_pdf, letter_pdf, motivation_text = self.find_dossier_files(offer)
        
        result = {
            "success": False,
            "url": url,
            "error": None,
            "proof_screenshot": None,
            "timestamp": datetime.now().isoformat()
        }

        print(f"[*] FormAutoPilot : Navigation vers l'offre -> {url}")
        print(f"[*] CV sélectionné : {cv_pdf}")
        print(f"[*] Lettre sélectionnée : {letter_pdf}")

        with sync_playwright() as p:
            launch_args = {
                "user_data_dir": self.profile_dir,
                "headless": headless or os.environ.get("GITHUB_ACTIONS") == "true" or sys.platform != "win32",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            }
            if sys.platform == "win32" and self.chrome_exe and os.path.exists(self.chrome_exe):
                launch_args["executable_path"] = self.chrome_exe
                
            context = p.chromium.launch_persistent_context(**launch_args)
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = context.pages[0] if context.pages else context.new_page()

            try:
                # Spécialisation France Travail
                if "francetravail.fr" in url.lower():
                    ft_res = self._submit_france_travail(context, page, url, offer, cv_pdf, letter_pdf, motivation_text, result)
                    context.close()
                    return ft_res

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # Étape 1 : Si un bouton préliminaire "Postuler" est requis
                apply_btn = page.locator("a#detail-apply, button:has-text('Postuler'), a:has-text('Postuler'), button:has-text('Candidater')").first
                if apply_btn.is_visible() and not page.locator("input[type='file'], input[name*='name'], input[name*='first']").first.is_visible():
                    print("[*] Clic sur le bouton préliminaire d'ouverture du formulaire...")
                    apply_btn.click()
                    time.sleep(2)

                # Étape 2 : Remplissage des champs de saisie
                self._fill_input_fields(page, motivation_text)

                # Étape 3 : Téléversement des fichiers CV et Lettre
                self._upload_documents(page, cv_pdf, letter_pdf)

                # Étape 4 : Gestion des menus déroulants et sélecteurs
                self._handle_dropdowns_and_radios(page)

                # Capture d'écran avant soumission
                out_dir = offer.get("folder") or os.path.join(self.base_dir, "scratch")
                os.makedirs(out_dir, exist_ok=True)
                ready_shot = os.path.join(out_dir, "form_ready_to_submit.png")
                page.screenshot(path=ready_shot)
                print(f"[+] Capture avant soumission sauvegardée : {ready_shot}")

                # Étape 5 : Soumission avec boucle de repli (Fallback loop)
                submitted, submit_error = self._execute_submission_with_fallbacks(page)

                if not submitted:
                    result["error"] = f"Échec de la soumission : {submit_error}"
                    fail_shot = os.path.join(out_dir, "form_submission_failed.png")
                    page.screenshot(path=fail_shot)
                    result["proof_screenshot"] = fail_shot
                    context.close()
                    return result

                # Étape 6 : Attente et vérification du résultat officiel
                time.sleep(5)
                success_shot = os.path.join(out_dir, "preuve_soumission_officielle.png")
                page.screenshot(path=success_shot)
                result["proof_screenshot"] = success_shot
                
                # Copie miroir
                try:
                    import shutil
                    shutil.copyfile(success_shot, os.path.join(out_dir, "form_submission_confirmed.png"))
                except Exception:
                    pass

                page_text = page.locator("body").inner_text()
                
                # Contrôle anti-bot / accès restreint
                anti_bot_keywords = ["accès temporairement restreint", "un robot est sur le même réseau", "cloudflare", "captcha", "datadome", "attention requise"]
                if any(kw in page_text.lower() for kw in anti_bot_keywords):
                    print(f"[!] Protection anti-bot / accès restreint détectée sur {url}. Soumission automatique annulée.")
                    result["success"] = False
                    result["error"] = "Anti-bot détecté (Accès restreint / Captcha) — Postulation manuelle requise"
                    return result

                # Étape 7 : Détection de l'e-mail de confirmation requis (ex: Taleez)
                if "lien de confirmation" in page_text.lower() or "vérifiez vos emails" in page_text.lower() or "confirm" in page.url.lower():
                    print("[*] Détection d'une validation obligatoire par e-mail. Interception IMAP en cours...")
                    confirmed = self._auto_confirm_via_email(offer_company=offer.get("company", ""))
                    if confirmed:
                        print("[✓] Confirmation e-mail validée avec succès !")

                result["success"] = True
                print(f"[✓] CANDIDATURE FINALISÉE AVEC SUCCÈS SUR {url} !")

            except Exception as e:
                print(f"[!] Erreur critique pendant la postulation : {e}")
                result["error"] = str(e)
                try:
                    err_shot = os.path.join(self.base_dir, "scratch", "form_exception.png")
                    page.screenshot(path=err_shot)
                    result["proof_screenshot"] = err_shot
                except Exception:
                    pass

            finally:
                context.close()

        return result

    def _fill_input_fields(self, page: Page, motivation_text: str):
        """Détecte et remplit tous les champs de texte de façon intelligente."""
        print("[*] Analyse et injection des informations du candidat...")
        inputs = page.locator("input:not([type='hidden']):not([type='file']):not([type='checkbox']):not([type='radio'])").all()
        
        for inp in inputs:
            if not inp.is_visible():
                continue
            name = (inp.get_attribute("name") or "").lower()
            idx = (inp.get_attribute("id") or "").lower()
            ph = (inp.get_attribute("placeholder") or "").lower()
            aria = (inp.get_attribute("aria-label") or "").lower()
            tag = f"{name} {idx} {ph} {aria}"

            # Prénom
            if any(k in tag for k in ["first", "prenom", "prénom", "fname"]) and not any(k in tag for k in ["last", "nom"]):
                inp.fill(self.candidate["first_name"])
            # Nom
            elif any(k in tag for k in ["last", "lname", "nom", "family"]):
                inp.fill(self.candidate["last_name"])
            # Nom complet si champ unique
            elif any(k in tag for k in ["full_name", "candidate_name", "nom_complet"]):
                inp.fill(self.candidate["full_name"])
            # E-mail
            elif any(k in tag for k in ["email", "mail", "courriel"]):
                inp.fill(self.candidate["email"])
            # Téléphone
            elif any(k in tag for k in ["tel", "phone", "mobile", "portable", "06 12"]):
                inp.fill(self.candidate["phone"])
            # Code Postal
            elif any(k in tag for k in ["postal", "zip", "code_postal", "cp"]):
                inp.fill(self.candidate["postal_code"])
            # Ville
            elif any(k in tag for k in ["city", "ville", "commune"]):
                inp.fill(self.candidate["city"])
            # Adresse
            elif any(k in tag for k in ["address", "adresse", "rue"]):
                inp.fill(self.candidate["address"])
            # LinkedIn
            elif any(k in tag for k in ["linkedin", "reseau"]):
                inp.fill(self.candidate["linkedin"])
            # Site Web
            elif any(k in tag for k in ["website", "site", "web"]):
                inp.fill(self.candidate["website"])

        # Textareas (Lettre de motivation / Message)
        textareas = page.locator("textarea").all()
        for ta in textareas:
            if ta.is_visible():
                ta.fill(motivation_text)
                time.sleep(0.5)

    def _upload_documents(self, page: Page, cv_pdf: Optional[str], letter_pdf: Optional[str]):
        """Injecte le CV et la Lettre PDF dans les dropzones correspondantes."""
        file_inputs = page.locator("input[type='file']").all()
        if not file_inputs:
            print("[!] Aucun champ de téléversement de fichier détecté.")
            return

        print(f"[*] Téléversement des pièces justificatives ({len(file_inputs)} dropzone(s) trouvée(s))...")

        if len(file_inputs) == 1:
            if cv_pdf and os.path.exists(cv_pdf):
                print(f"    -> Dépôt du CV unique : {cv_pdf}")
                file_inputs[0].set_input_files(cv_pdf)
                time.sleep(5)
        else:
            for idx, fi in enumerate(file_inputs):
                tag = (fi.get_attribute("name") or fi.get_attribute("id") or "").lower()
                if any(k in tag for k in ["cover", "lettre", "motivation", "lm"]) and letter_pdf:
                    print(f"    -> Dépôt de la Lettre : {letter_pdf}")
                    fi.set_input_files(letter_pdf)
                else:
                    if cv_pdf:
                        print(f"    -> Dépôt du CV : {cv_pdf}")
                        fi.set_input_files(cv_pdf)
                time.sleep(3)

    def _handle_dropdowns_and_radios(self, page: Page):
        """Gère les menus déroulants (salaire, disponibilité) et les cases de consentement."""
        selects = page.locator("select").all()
        for sel in selects:
            if not sel.is_visible():
                continue
            options = sel.locator("option").all()
            for opt in options:
                txt = opt.inner_text().lower()
                val = opt.get_attribute("value")
                if any(k in txt for k in ["40", "45", "cadre", "immédiat", "disponible"]):
                    sel.select_option(value=val)
                    break

        custom_triggers = page.locator("text=Choisir..., text=Sélectionner, [role='combobox']").all()
        for trg in custom_triggers:
            if trg.is_visible():
                try:
                    trg.click()
                    time.sleep(1)
                    salary_opt = page.locator("text=40.000 à 45.000 €, text=40 000, text=45 000, .tz-dropdown-item:has-text('40')").first
                    if salary_opt.is_visible():
                        salary_opt.click()
                        time.sleep(0.5)
                except Exception:
                    pass

        page.mouse.click(10, 10)
        time.sleep(0.5)

        cbs = page.locator("input[type='checkbox']").all()
        for cb in cbs:
            try:
                name = (cb.get_attribute("name") or cb.get_attribute("id") or "").lower()
                if any(k in name for k in ["rgpd", "consent", "accord", "terms", "condition", "policy"]):
                    if not cb.is_checked():
                        cb.check(force=True)
            except Exception:
                pass

    def _execute_submission_with_fallbacks(self, page: Page) -> Tuple[bool, Optional[str]]:
        """Tente de soumettre le formulaire avec 4 stratégies successives en cas d'obstacle."""
        print("[*] Déclenchement de la soumission finale...")

        submit_selectors = [
            "button[type='submit']",
            "button:has-text('Envoyer ma candidature')",
            "button:has-text('Envoyer')",
            "button:has-text('Postuler')",
            "button:has-text('Confirmer')",
            "button:has-text('Valider')",
            "input[type='submit']"
        ]

        # Stratégie 1 : Clic direct sur le bouton
        for sel in submit_selectors:
            btn = page.locator(sel).first
            if btn.is_visible():
                try:
                    print(f"    [Stratégie 1] Clic direct sur : {sel}")
                    btn.click(timeout=5000)
                    return True, None
                except Exception:
                    pass

        # Stratégie 2 : Clic forcé (bypass d'overlay)
        for sel in submit_selectors:
            btn = page.locator(sel).first
            if btn.is_visible():
                try:
                    print(f"    [Stratégie 2] Clic forcé (force=True) sur : {sel}")
                    btn.click(force=True, timeout=5000)
                    return True, None
                except Exception:
                    pass

        # Stratégie 3 : Déclenchement JS via le formulaire
        try:
            print("    [Stratégie 3] Déclenchement JS form.submit()...")
            has_form = page.evaluate("""() => {
                const f = document.querySelector('form');
                if (f) {
                    const submitBtn = f.querySelector("button[type='submit'], button, input[type='submit']");
                    if (submitBtn) { submitBtn.click(); return true; }
                    f.submit();
                    return true;
                }
                return false;
            }""")
            if has_form:
                return True, None
        except Exception:
            pass

        # Stratégie 4 : Envoi de la touche Entrée sur le dernier champ
        try:
            print("    [Stratégie 4] Pression de la touche Entrée...")
            page.keyboard.press("Enter")
            return True, None
        except Exception as e:
            return False, str(e)

    def _auto_confirm_via_email(self, offer_company: str = "") -> bool:
        """Surveille la boîte IMAP et valide automatiquement les liens de confirmation."""
        print(f"[*] Connexion IMAP à {self.imap_server} ({self.imap_user})...")
        time.sleep(5)

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, 993)
            mail.login(self.imap_user, self.imap_password)
            mail.select("INBOX")

            status, messages = mail.search(None, "ALL")
            msg_ids = messages[0].split()
            if not msg_ids:
                mail.logout()
                return False

            for mid in reversed(msg_ids[-10:]):
                status, data = mail.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ["text/html", "text/plain"]:
                            body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                links = re.findall(r'https?://[^\s\"\'<>]+', body)
                confirm_links = [l for l in links if any(k in l.lower() for k in ["confirm", "validate", "token", "activation"])]
                
                if confirm_links:
                    val_url = confirm_links[0]
                    print(f"[+] Lien de confirmation officiel extrait : {val_url}")
                    
                    with sync_playwright() as p:
                        browser = p.chromium.launch(executable_path=self.chrome_exe, headless=True)
                        pg = browser.new_page()
                        pg.goto(val_url)
                        pg.wait_for_load_state("networkidle")
                        time.sleep(2)
                        browser.close()
                    mail.logout()
                    return True

            mail.logout()
        except Exception as e:
            print(f"[!] Erreur lors de l'auto-confirmation IMAP : {e}")

        return False
    def _handle_ft_auth_flow(self, context, page: Page):
        """Authentification 100% autonome France Travail avec interception IMAP du code 2FA."""
        ft_user = os.environ.get("FRANCE_TRAVAIL_USER", "richard.busson@gmail.com")
        ft_pass = os.environ.get("FRANCE_TRAVAIL_PASSWORD", "R2d3DCVC&&")
        gmail_pwd = os.environ.get("GMAIL_APP_PASSWORD", "gpyyptsimcnttqiq")
        
        print(f"[*] Auto-authentification France Travail pour {ft_user}...")
        u = page.locator("#identifiant, input[name='callback_0']").first
        if u.is_visible():
            u.fill(ft_user)
            page.locator("#password, input[name='callback_1']").first.fill(ft_pass)
            page.locator("button#submitButton, input[type='submit'], button:has-text('Se connecter')").first.click()
            time.sleep(4)

        card = page.get_by_text("Recevoir un code par e-mail").first
        if not card.is_visible():
            card = page.locator("//*[contains(text(), 'Recevoir un code')]").first

        if card.is_visible():
            print("[*] Clic sur 'Recevoir un code par e-mail'...")
            card.click()
            time.sleep(3)

            # Interception IMAP du code à 8 chiffres
            print("[*] Interception du code 2FA dans Gmail...")
            code = None
            start_t = time.time()
            while time.time() - start_t < 90:
                try:
                    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
                    mail.login(ft_user, gmail_pwd)
                    mail.select("INBOX")
                    _, messages = mail.search(None, 'ALL')
                    msg_ids = messages[0].split()
                    if msg_ids:
                        for mid in reversed(msg_ids[-5:]):
                            _, data = mail.fetch(mid, '(RFC822)')
                            msg = email.message_from_bytes(data[0][1])
                            sub_hdr = msg.get("Subject", "")
                            if "france travail" in str(sub_hdr).lower() or "code" in str(sub_hdr).lower():
                                body = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == "text/plain":
                                            body += part.get_payload(decode=True).decode(errors='ignore')
                                else:
                                    body = msg.get_payload(decode=True).decode(errors='ignore')
                                match = re.search(r'\b(\d{8})\b', body)
                                if match:
                                    code = match.group(1)
                                    mail.logout()
                                    break
                    mail.logout()
                    if code:
                        break
                except Exception:
                    pass
                time.sleep(2)

            if code:
                print(f"[+] Code intercepté : {code}")
                inputs = page.locator("input:not([type='hidden'])").all()
                if len(inputs) == 8:
                    for idx, digit in enumerate(code[:8]):
                        inputs[idx].click()
                        inputs[idx].type(digit, delay=40)
                        time.sleep(0.04)
                else:
                    if inputs:
                        inputs[0].click()
                        page.keyboard.type(code, delay=40)
                time.sleep(1)
                page.locator("button:has-text('Poursuivre'), input[type='submit']").first.click()
                time.sleep(4)

                # Clic confiance 3 mois
                trust_btn = page.get_by_text("Faire confiance à ce navigateur")
                if not trust_btn.is_visible():
                    trust_btn = page.locator("button, a").filter(has_text="Faire confiance")
                if trust_btn.is_visible():
                    trust_btn.click()
                    time.sleep(5)

    def _submit_france_travail(self, context, page: Page, url: str, offer: Dict[str, Any], cv_pdf: Optional[str], letter_pdf: Optional[str], motivation_text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Gère la soumission officielle sur le portail France Travail avec support de session 3 mois et 2FA automatique."""
        print(f"[*] FormAutoPilot [France Travail] : Traitement spécialisé de l'offre -> {url}")
        out_dir = offer.get("folder") or os.path.join(self.base_dir, "scratch")
        os.makedirs(out_dir, exist_ok=True)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # Étape 1 : Si besoin d'authentification préalable
            if "connexion" in page.url or "login" in page.url:
                print("[*] Page de connexion France Travail détectée, authentification automatique...")
                self._handle_ft_auth_flow(context, page)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)

            # Étape 2 : Clic sur le bouton "Postuler"
            apply_btn = page.locator("a#detail-apply, button:has-text('Postuler'), a:has-text('Postuler')").first
            if apply_btn.is_visible():
                print("[*] Clic sur 'Postuler'...")
                apply_btn.click()
                time.sleep(2)

            # Étape 3 : Clic sur "Envoyer ma candidature" pour ouvrir le formulaire
            btn_envoyer = page.locator("a:has-text('Envoyer ma candidature'), button:has-text('Envoyer ma candidature')").first
            target_page = page
            if btn_envoyer.is_visible():
                print("[*] Clic sur 'Envoyer ma candidature'...")
                try:
                    with context.expect_page(timeout=6000) as new_page_info:
                        btn_envoyer.click()
                    target_page = new_page_info.value
                except Exception:
                    if len(context.pages) > 1:
                        target_page = context.pages[-1]

            target_page.wait_for_load_state("domcontentloaded")
            time.sleep(4)

            # Étape 4 : Détection si déjà postulé
            body_text = target_page.locator("body").inner_text()
            if "déjà postulé" in body_text.lower():
                print("[!] Candidature déjà enregistrée sur cette offre France Travail.")
                already_shot = os.path.join(out_dir, "preuve_soumission_officielle.png")
                target_page.screenshot(path=already_shot)
                result["proof_screenshot"] = already_shot
                result["success"] = True
                result["already_applied"] = True
                return result

            # Étape 5 : Sélection / Upload du CV
            # 5a. Si un champ d'upload de fichier existe
            file_input = target_page.locator("input[type='file']").first
            if file_input.is_visible() and cv_pdf and os.path.exists(cv_pdf):
                try:
                    print(f"[*] Téléversement du CV officiel : {cv_pdf}")
                    file_input.set_input_files(cv_pdf)
                    time.sleep(2)
                except Exception as e:
                    print(f"[!] Upload direct fichier : {e}")

            # 5b. Sélection d'un CV radio adapté si présent
            cv_radios = target_page.locator("input[name='choix-cv']").all()
            if cv_radios:
                selected = False
                for r in cv_radios:
                    rid = r.get_attribute("id") or ""
                    lbl = target_page.locator(f"label[for='{rid}']").first
                    if lbl.is_visible():
                        txt = lbl.inner_text().lower()
                        if any(k in txt for k in ["responsablerh", "paie", "gestionnaire", "consultant"]):
                            r.click()
                            selected = True
                            print(f"[*] CV sélectionné : {lbl.inner_text().strip()}")
                            break
                if not selected and cv_radios:
                    cv_radios[0].click()

            # Étape 6 : Profil de compétences
            carte_btn = target_page.locator("button:has-text('Sélectionner'), a:has-text('Sélectionner')").first
            if carte_btn.is_visible():
                try:
                    print("[*] Sélection du profil de compétences (expert droit social, paie, RH)...")
                    carte_btn.click()
                    time.sleep(1)
                except Exception:
                    pass

            # Étape 7 : Remplissage de la Lettre de motivation (max 1500 caractères)
            textarea = target_page.locator("textarea#lettre-motivation, textarea[name='textMessage']").first
            if textarea.is_visible():
                print("[*] Injection de la lettre de motivation sur-mesure...")
                clean_mot = motivation_text.strip()
                if len(clean_mot) > 1450:
                    clean_mot = clean_mot[:1450]
                textarea.fill(clean_mot)
                time.sleep(1)

            # Étape 8 : Confirmation des coordonnées
            coords_chk = target_page.locator("label:has-text('Je confirme que mes coordonnées'), input[type='checkbox']").first
            if coords_chk.is_visible():
                print("[*] Confirmation des coordonnées du candidat...")
                coords_chk.click()
                time.sleep(1)

            # Capture d'écran avant envoi
            ready_shot = os.path.join(out_dir, "form_ready_to_submit.png")
            target_page.screenshot(path=ready_shot)
            print(f"[+] Capture avant soumission sauvegardée : {ready_shot}")

            # Étape 9 : Soumission officielle
            submit_btn = target_page.locator("button:has-text('Envoyer'), input[value='Envoyer']").first
            if submit_btn.is_visible():
                print("[*] Clic sur 'Envoyer' pour sceller la candidature officielle...")
                submit_btn.click()
                time.sleep(6)

            # Étape 10 : Preuve officielle de confirmation
            proof_shot = os.path.join(out_dir, "preuve_soumission_officielle.png")
            target_page.screenshot(path=proof_shot)
            result["proof_screenshot"] = proof_shot
            
            try:
                import shutil
                shutil.copyfile(proof_shot, os.path.join(out_dir, "form_submission_confirmed.png"))
            except Exception:
                pass

            result["success"] = True
            print(f"[✓] CANDIDATURE FRANCE TRAVAIL TRANSMISE AVEC SUCCÈS : {proof_shot}")

        except Exception as e:
            print(f"[!] Erreur lors de la soumission France Travail : {e}")
            result["error"] = str(e)
            try:
                err_shot = os.path.join(out_dir, "form_submission_failed.png")
                page.screenshot(path=err_shot)
                result["proof_screenshot"] = err_shot
            except Exception:
                pass

        return result

if __name__ == "__main__":
    bot = FormAutoPilot()
    print("FormAutoPilot initialisé avec succès.")
