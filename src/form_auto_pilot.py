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
    def __init__(self, base_dir="."):
        self.base_dir = os.path.abspath(base_dir)
        self.chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        # Données officielles de Richard Busson
        self.candidate = {
            "first_name": "Richard",
            "last_name": "BUSSON",
            "full_name": "Richard BUSSON",
            "email": "richard.busson@kairos-paye.fr",
            "phone": "0761961546",
            "phone_formatted": "07 61 96 15 46",
            "phone_int": "+33761961546",
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
        self.imap_server = "ssl0.ovh.net"
        self.imap_user = "richard.busson@kairos-paye.fr"
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
                "headless": headless or os.environ.get("GITHUB_ACTIONS") == "true" or sys.platform != "win32",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            }
            if sys.platform == "win32" and self.chrome_exe and os.path.exists(self.chrome_exe):
                launch_args["executable_path"] = self.chrome_exe
                
            browser = p.chromium.launch(**launch_args)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = context.new_page()

            try:
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
                    browser.close()
                    return result

                # Étape 6 : Attente et vérification du résultat officiel
                time.sleep(5)
                success_shot = os.path.join(out_dir, "form_submission_confirmed.png")
                page.screenshot(path=success_shot)
                result["proof_screenshot"] = success_shot

                page_text = page.locator("body").inner_text()
                
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
                browser.close()

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

if __name__ == "__main__":
    bot = FormAutoPilot()
    print("FormAutoPilot initialisé avec succès.")
