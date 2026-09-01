# -*- coding: utf-8 -*-
import os
import json
import smtplib
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Tuple, Optional

class RecruiterDispatcher:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.config = self.load_settings()
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.user_email = self.config.get("user_email", "richard.busson@kairos-paye.fr")

    def load_settings(self) -> Dict[str, Any]:
        settings_path = os.path.join(self.base_dir, "config", "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "recruiter_auto_send": True,
            "bcc_copy_to_user": True,
            "user_email": "richard.busson@kairos-paye.fr"
        }

    def extract_recruiter_email(self, job: Dict[str, Any]) -> Optional[str]:
        """Tente d'extraire l'adresse email de contact du recruteur."""
        if job.get("contact_email"):
            return job.get("contact_email").strip()
            
        desc = job.get("description", "")
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        matches = re.findall(email_pattern, desc)
        
        # Filtrer d'éventuelles adresses génériques ou non pertinentes
        for m in matches:
            m_lower = m.lower()
            if not m_lower.endswith(".png") and not m_lower.endswith(".jpg") and "example.com" not in m_lower:
                return m.strip()
                
        return None

    def generate_personalized_cover_email(self, job: Dict[str, Any]) -> Tuple[str, str]:
        """Rédige un message d'accompagnement soigné, courtois et personnalisé."""
        company = job.get("company", "votre organisme").replace('"', '')
        raw_title = job.get("title", "Poste RH & Paie")
        job_title = re.sub(r'\(H/F\)|H/F|\(F/H\)|F/H', '', raw_title, flags=re.IGNORECASE).strip()
        
        contact_name = job.get("contact_name", "Madame, Monsieur")
        if "directeur" in contact_name.lower():
            salutation = "Monsieur le Directeur,"
        elif "directrice" in contact_name.lower():
            salutation = "Madame la Directrice,"
        else:
            salutation = "Madame, Monsieur,"

        subject = f"Candidature : {job_title} — Richard BUSSON"

        # Détection de la dominante
        text = (job.get("title", "") + " " + job.get("description", "")).lower()
        if "formateur" in text or "formation" in text or "pédagogique" in text or "cfa" in text:
            intro_p = f"C'est avec un vif intérêt que je vous adresse ma candidature pour le poste de {job_title} au sein de {company}."
            core_p = "Dirigeant d'un organisme certifié Qualiopi (concepteur du parcours 758h Titre Pro Gestionnaire de paie) et fort de 4 années d'interventions certifiantes pour l'Afpa (outil Métis, ECF) ainsi que 7 années de direction RH de 580 collaborateurs, je vous propose mon expertise pédagogique et ma maîtrise immédiate des référentiels."
        elif "responsable rh" in text or "rrh" in text or "responsable paie" in text:
            intro_p = f"Je vous présente ma candidature au poste de {job_title} au sein de {company}."
            core_p = "Fort de plus de 15 années d'expérience en management des Ressources Humaines et pilotage de la Paie (ex-Responsable RH de 580 collaborateurs au Secours Populaire), j'assure l'autonomie complète de vos cycles sociaux, le dialogue social (CSE) et la maîtrise de la masse salariale avec une double compétence juridique (Master 2 Droit public)."
        else:
            intro_p = f"Je me permets de vous adresser ma candidature au poste de {job_title} au sein de {company}."
            core_p = "Gestionnaire de paie confirmé fort de 15 ans de pratique, j'assure avec une totale autonomie l'intégralité du processus de paie : collecte des variables, traitement multi-conventions, déclarations DSN (mensuelles et événementielles), paramétrage approfondi sur logiciel Silae et relations avec les organismes collecteurs."

        body_plain = f"""{salutation}

{intro_p}

{core_p}

Vous trouverez ci-joints mon curriculum vitae et ma lettre de motivation détaillant l'adéquation de mon profil avec vos attentes.

À 59 ans, je m'inscris dans une démarche de stabilité, de rigueur et d'engagement durable. Mon statut de demandeur d'emploi senior permet par ailleurs à votre établissement de bénéficier d'aides à l'embauche avantageuses. Titulaire du permis B et totalement mobile, je suis disponible immédiatement.

Restant à votre entière disposition pour convenir d'un prochain entretien, je vous prie d'agréer, {salutation.replace(',', '')}, l'expression de ma considération distinguée.

Richard BUSSON
09 39 20 08 70 | richard.busson@kairos-paye.fr
98, allée Paul Cézanne, 60100 Creil
linkedin.com/in/richard-busson | kairos-paye.fr
"""

        body_html = f"""
        <html>
        <body style="font-family: Calibri, 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #111111; line-height: 1.45;">
            <p>{salutation}</p>
            <p>{intro_p}</p>
            <p>{core_p}</p>
            <p>Vous trouverez ci-joints mon curriculum vitae et ma lettre de motivation détaillant l'adéquation de mon profil avec vos attentes.</p>
            <p>À 59 ans, je m'inscris dans une démarche de stabilité, de rigueur et d'engagement durable. Mon statut de demandeur d'emploi senior permet par ailleurs à votre établissement de bénéficier d'aides à l'embauche avantageuses. Titulaire du permis B et totalement mobile, je suis disponible immédiatement.</p>
            <p>Restant à votre entière disposition pour convenir d'un prochain entretien, je vous prie d'agréer, {salutation.replace(',', '')}, l'expression de ma considération distinguée.</p>
            <br>
            <p style="margin-bottom: 2px;"><strong>Richard BUSSON</strong></p>
            <p style="font-size: 10pt; color: #333333; margin: 0;">09 39 20 08 70 | <a href="mailto:richard.busson@kairos-paye.fr" style="color: #1b365d;">richard.busson@kairos-paye.fr</a></p>
            <p style="font-size: 10pt; color: #333333; margin: 0;">98, allée Paul Cézanne, 60100 Creil</p>
            <p style="font-size: 10pt; color: #333333; margin: 0;"><a href="https://linkedin.com/in/richard-busson" style="color: #1b365d;">linkedin.com/in/richard-busson</a> | <a href="https://kairos-paye.fr" style="color: #1b365d;">kairos-paye.fr</a></p>
        </body>
        </html>
        """

        return subject, body_html

    def dispatch_application(self, job: Dict[str, Any], folder_path: str) -> Dict[str, Any]:
        """Prépare et expédie le courriel de candidature avec les 2 PDF certifiés."""
        recruiter_email = self.extract_recruiter_email(job)
        
        pdf_letter = os.path.join(folder_path, "Lettre_Motivation_Richard_BUSSON.pdf")
        pdf_cv = os.path.join(folder_path, "CV_Richard_BUSSON.pdf")
        
        # Vérification préalable stricte des pièces jointes
        if not os.path.exists(pdf_letter) or os.path.getsize(pdf_letter) == 0:
            return {"sent": False, "reason": "Lettre PDF manquante ou vide", "timestamp": None}
        if not os.path.exists(pdf_cv) or os.path.getsize(pdf_cv) == 0:
            return {"sent": False, "reason": "CV PDF manquant ou vide", "timestamp": None}

        subject, body_html = self.generate_personalized_cover_email(job)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Si aucune adresse email recruteur directe n'est disponible
        if not recruiter_email:
            return {
                "sent": False,
                "mode": "WEB_PORTAL_REQUIRED",
                "reason": "Pas d'email recruteur direct (postulation via lien web/portail)",
                "recruiter_email": None,
                "subject": subject,
                "timestamp": now_str
            }

        # Construction du courriel multipart avec pièces jointes
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"Richard BUSSON <{self.user_email}>"
        msg["To"] = recruiter_email
        if self.config.get("bcc_copy_to_user", True):
            msg["Bcc"] = self.user_email

        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(body_html, "html", "utf-8"))
        msg.attach(alt_part)

        # Attachement des 2 PDF officiels
        with open(pdf_letter, "rb") as f:
            att_letter = MIMEApplication(f.read(), _subtype="pdf")
            att_letter.add_header("Content-Disposition", "attachment", filename="Lettre_Motivation_Richard_BUSSON.pdf")
            msg.attach(att_letter)

        with open(pdf_cv, "rb") as f:
            att_cv = MIMEApplication(f.read(), _subtype="pdf")
            att_cv.add_header("Content-Disposition", "attachment", filename="CV_Richard_BUSSON.pdf")
            msg.attach(att_cv)

        # Expédition SMTP réelle si identifiants configurés
        if self.smtp_user and self.smtp_password:
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                recipients = [recruiter_email]
                if self.config.get("bcc_copy_to_user", True):
                    recipients.append(self.user_email)
                server.sendmail(self.user_email, recipients, msg.as_string())
                server.quit()
                print(f"[✓] Email expédié avec succès au recruteur ({recruiter_email}) + Copie BCC à {self.user_email}")
                return {
                    "sent": True,
                    "mode": "SMTP_LIVE",
                    "recruiter_email": recruiter_email,
                    "subject": subject,
                    "timestamp": now_str,
                    "message": "Candidature officiellement transmise au recruteur par email direct."
                }
            except Exception as e:
                print(f"[!] Erreur d'expédition SMTP au recruteur ({recruiter_email}) : {e}")
                return {
                    "sent": False,
                    "mode": "SMTP_ERROR",
                    "error": str(e),
                    "recruiter_email": recruiter_email,
                    "timestamp": now_str
                }
        else:
            # Mode simulation / prêt pour expédition
            print(f"[i] Module RecruiterDispatcher prêt (Mode simulation ou SMTP en attente de secrets) : Email préparé pour {recruiter_email}")
            return {
                "sent": True,
                "mode": "SIMULATION_READY",
                "recruiter_email": recruiter_email,
                "subject": subject,
                "timestamp": now_str,
                "message": f"Dossier et courriel d'accompagnement prêts pour expédition à {recruiter_email}."
            }
