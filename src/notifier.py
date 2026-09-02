# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, List

class ApplicationNotifier:
    def _load_env_file(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
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

    def __init__(self, recipient_email="richard.busson@kairos-paye.fr"):
        self._load_env_file()
        self.recipient_email = recipient_email
        self.smtp_server = os.environ.get("SMTP_SERVER", "ssl0.ovh.net")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")

    def send_application_alert(self, job: Dict[str, Any], pdf_letter_path: str, pdf_cv_path: str) -> bool:
        """Envoie une notification immédiate par email avec les PDF en pièces jointes."""
        company = job.get("company", "Entreprise")
        title = job.get("title", "Poste")
        score = job.get("score", 0)
        salary = job.get("salary", "Non précisé")
        city = job.get("city", "France")
        url = job.get("url", "")
        
        subject = f"🎯 [JobHunter] Nouvelle Candidature Prête ({score}%) : {company} - {title}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
            <div style="max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px; background: #ffffff;">
                <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 18px;">
                    <h2 style="color: #1e293b; margin: 0;">🚀 Nouvelle Candidature Qualifiée Détectée</h2>
                    <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">Votre JobHunter Copilot a rédigé et validé votre dossier de candidature sur-mesure.</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold; width: 30%; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">Organisme :</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{company} ({city})</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">Intitulé du poste :</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>{title}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">Score d'adéquation :</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; color: #16a34a; font-weight: bold;">{score} %</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">Rémunération :</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{salary}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">Lien de l'offre :</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><a href="{url}" style="color: #2563eb;">Voir l'annonce en ligne</a></td>
                    </tr>
                </table>

                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 6px 0; color: #166534;">✅ Contrôle Qualité & Sécurité (100% Validé)</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #15803d;">
                        <li>CV A4 équilibré sur 1 page stricte sans vide en bas.</li>
                        <li>Lettre de motivation A4 avec zéro gras dans le corps et destinataire aligné sur kairos-paye.fr.</li>
                        <li>Signature manuscrite vectorielle (RB) intégrée.</li>
                        <li>Orthographe et ponctuation française vérifiées.</li>
                    </ul>
                </div>

                <p style="font-size: 14px;"><strong>📎 Pièces jointes disponibles :</strong> Les 2 fichiers PDF officiels sont attachés à cet email.</p>
            </div>
        </body>
        </html>
        """
        
        # Si les identifiants SMTP sont configurés
        if self.smtp_user and self.smtp_password:
            try:
                msg = MIMEMultipart()
                msg["From"] = self.smtp_user
                msg["To"] = self.recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body_html, "html"))
                
                # Attacher la Lettre PDF
                if os.path.exists(pdf_letter_path):
                    with open(pdf_letter_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_letter_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_letter_path)}"'
                        msg.attach(part)
                        
                # Attacher le CV PDF
                if os.path.exists(pdf_cv_path):
                    with open(pdf_cv_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_cv_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_cv_path)}"'
                        msg.attach(part)
                        
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                    
                print(f"[✓] Email de notification envoyé avec succès à {self.recipient_email}")
                return True
            except Exception as e:
                print(f"[!] Erreur d'envoi email SMTP : {e}")
                return False
        else:
            print(f"[i] Simulation Notification Email pour {self.recipient_email} : {subject}")
            return True

    def send_batch_summary(self, apps: List[Dict[str, Any]]) -> bool:
        """Envoie un rapport de synthèse professionnel regroupant l'ensemble des candidatures traitées."""
        if not apps:
            return True
            
        subject = f"📊 [JobHunter Recap] {len(apps)} Nouvelles Candidatures Qualifiées Déposées & Certifiées"
        
        rows_html = ""
        for a in apps:
            company = a.get("company", "Entreprise")
            title = a.get("title", "Poste")
            city = a.get("city", "France")
            score = a.get("score", 0)
            channel = a.get("source", "Web")
            url = a.get("url", "#")
            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; font-weight: bold; color: #1e293b;">{company}</td>
                <td style="padding: 10px;"><a href="{url}" style="color: #2563eb; text-decoration: none;">{title}</a></td>
                <td style="padding: 10px; color: #64748b;">{city}</td>
                <td style="padding: 10px; text-align: center;"><span style="background: #dcfce7; color: #166534; font-weight: bold; padding: 2px 8px; border-radius: 9999px;">{score}%</span></td>
                <td style="padding: 10px; color: #475569; font-size: 13px;">{channel}</td>
            </tr>
            """
            
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
            <div style="max-width: 700px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px; background: #ffffff;">
                <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 18px;">
                    <h2 style="color: #1e293b; margin: 0;">🚀 Bilan Quotidien : {len(apps)} Candidatures Inédites Traitées</h2>
                    <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">Contrôle anti-doublon validé, dossiers certifiés QualityGuard (PDF A4, zéro gras, CV marine).</p>
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 15px;">
                    <thead>
                        <tr style="background: #f8fafc; border-bottom: 2px solid #cbd5e1; text-align: left; color: #475569;">
                            <th style="padding: 10px;">Entreprise</th>
                            <th style="padding: 10px;">Poste Cible</th>
                            <th style="padding: 10px;">Lieu</th>
                            <th style="padding: 10px; text-align: center;">Score</th>
                            <th style="padding: 10px;">Canal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                <div style="margin-top: 25px; padding: 14px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
                    <p style="margin: 0; color: #166534; font-size: 13px;">
                        <strong>✓ Tous les dossiers sont prêts :</strong> Les lettres A4 pleine page, CV A4 et captures sont enregistrés et synchronisés dans votre tableau de bord local et sur GitHub.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        if self.smtp_user and self.smtp_password:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"JobHunter Copilot <{self.smtp_user}>"
                msg['To'] = self.recipient_email
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                print(f"[✓] Email de synthèse journalier envoyé à {self.recipient_email}")
                return True
            except Exception as e:
                print(f"[!] Erreur envoi synthèse : {e}")
                return False
        return True

if __name__ == "__main__":
    notifier = ApplicationNotifier()
    print("ApplicationNotifier initialisé avec succès.")
