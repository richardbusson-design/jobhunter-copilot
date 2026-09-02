# -*- coding: utf-8 -*-
import os
import sys
import json
import re
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from job_searcher import JobSearcher
from application_generator import ApplicationGenerator
from quality_guard import QualityGuard
from pdf_compiler import compile_html_to_pdf
from dashboard_manager import DashboardManager
from notifier import ApplicationNotifier
from recruiter_dispatcher import RecruiterDispatcher
from france_travail_bot import FranceTravailBot

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(' ', '_')

def ensure_desktop_app_installed():
    """Garantit que l'application et le raccourci Bureau avec l'icône 3D restent installés de façon permanente."""
    try:
        install_dir = r"C:\Users\richa\JobHunter"
        os.makedirs(install_dir, exist_ok=True)
        
        # 1. Copie de sécurité de l'icône
        ico_src = r"C:\Users\richa\Gemini\red_button.ico"
        ico_dest = os.path.join(install_dir, "app_icon.ico")
        if os.path.exists(ico_src) and not os.path.exists(ico_dest):
            import shutil
            shutil.copy(ico_src, ico_dest)
            
        # 2. Vérification des raccourcis Bureau
        desktop_paths = [
            r"C:\Users\richa\OneDrive\Archives\Bureau 2021\Tableau de Bord - Candidatures.lnk",
            r"C:\Users\richa\Desktop\Tableau de Bord - Candidatures.lnk",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Tableau de Bord - Candidatures.lnk")
        ]
        
        for sc_path in desktop_paths:
            if not os.path.exists(sc_path):
                import subprocess
                ps_cmd = f'''
                $w = New-Object -ComObject WScript.Shell
                $s = $w.CreateShortcut("{sc_path}")
                $s.TargetPath = "wscript.exe"
                $s.Arguments = '"""C:\\Users\\richa\\JobHunter\\launch.vbs"""'
                $s.WorkingDirectory = "C:\\Users\\richa\\JobHunter"
                $s.IconLocation = "C:\\Users\\richa\\JobHunter\\app_icon.ico, 0"
                $s.Save()
                '''
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
    except Exception:
        pass

def run_pipeline(base_dir=".", auto_notify=True):
    ensure_desktop_app_installed()

    print("=" * 75)
    print("  [JOBHUNTER CLOUD RUNNER] - EXECUTION AVEC FILTRAGE ANTI-DOUBLON STRICT")
    print("=" * 75)
    
    dashboard = DashboardManager(base_dir=base_dir)
    searcher = JobSearcher(base_dir=base_dir)
    generator = ApplicationGenerator(base_dir=base_dir)
    guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
    notifier = ApplicationNotifier()
    dispatcher = RecruiterDispatcher(base_dir=base_dir)
    ft_bot = FranceTravailBot(base_dir=base_dir)
    
    # 1. Lecture préalable de l'historique GitHub / Tracker (Anti-Doublon Préalable)
    existing_fps = dashboard.get_existing_fingerprints()
    print(f"\n[1] Lecture de l'historique des candidatures ({existing_fps['total_count']} dossiers déjà traités) :")
    print(f"    - {len(existing_fps['ids'])} identifiants uniques répertoriés")
    print(f"    - {len(existing_fps['company_titles'])} couples (Entreprise / Titre) mémorisés")
    print("    -> AUCUN doublon ne sera régénéré ni réexpédié.")
    
    # 2. Récupération des offres fraîches sur France Travail, Apec, Indeed
    print("\n[2] Interrogation des flux multi-sources en direct...")
    raw_offers = searcher.fetch_live_opportunities()
    
    new_qualified_jobs = []
    for job in raw_offers:
        is_dup, dup_reason = dashboard.is_duplicate(job, existing_fps)
        if is_dup:
            print(f"    [-] Doublon détecté et bloqué : {job.get('title')} ({job.get('company')}) -> {dup_reason}")
            continue
        new_qualified_jobs.append(job)
        
    print(f"\n[3] Bilan du filtrage : {len(new_qualified_jobs)} NOUVELLES offres inédites à traiter.")
    
    if len(new_qualified_jobs) == 0:
        print("\n[✓] Aucun nouvel envoi requis : Toutes les offres actuelles ont déjà été traitées.")
        return
        
    validated_count = 0
    
    for job in new_qualified_jobs[:3]:
        score = generator.evaluate_match(job)
        job["score"] = score
        
        if score < 75:
            print(f"[-] Score insuffisant ({score}%) pour {job.get('title')} - ignoré.")
            continue
            
        print(f"\n" + "-" * 70)
        print(f"[*] Traitement de la NOUVELLE offre : {job.get('company')} - {job.get('title')} (Score : {score}%)")
        print(f"    Lieu : {job.get('city')} ({job.get('postal_code')}) | Salaire : {job.get('salary', 'N/C')}")
        print(f"    Source : {job.get('source')} | URL : {job.get('url')}")
        
        # 3. Création du dossier cible
        company_clean = sanitize_filename(job.get("company", "Entreprise"))
        title_clean = sanitize_filename(job.get("title", "Poste"))
        date_str = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"{date_str}_{company_clean}_{title_clean}"[:80]
        target_dir = os.path.join(base_dir, "candidatures", folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # 4. Tournoi à 3 essais pour retenir la meilleure lettre
        best_letter_html, best_score, best_idx = generator.generate_best_of_three_letter(job)
        cv_html = generator.render_cv_html(job)
        
        letter_html_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
        cv_html_path = os.path.join(target_dir, "CV_Richard_BUSSON.html")
        pdf_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
        pdf_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")
        
        with open(letter_html_path, "w", encoding="utf-8") as f: f.write(best_letter_html)
        with open(cv_html_path, "w", encoding="utf-8") as f: f.write(cv_html)
        
        # 5. Compilation PDF & PNG
        compile_html_to_pdf(letter_html_path, pdf_letter_path)
        compile_html_to_pdf(cv_html_path, pdf_cv_path)
        
        # 6. Audit QualityGuard en 3 Passages
        is_valid, audit_logs = guard.execute_three_pass_audit(job, best_letter_html, cv_html, pdf_letter_path, pdf_cv_path)
        for alog in audit_logs:
            print(f"    {alog}")
            
        if not is_valid:
            print(f"    [!] Candidature rejetée lors de l'audit aux 3 passages.")
            continue
            
        # 7. Expédition Automatisée (Email Recruteur Direct OU Postulation France Travail)
        dispatch_report = {"sent": False, "mode": "PREPARED"}
        
        # Cas A: Offre avec adresse email recruteur directe
        if job.get("contact_email"):
            print(f"[*] Expédition directe au recruteur par email ({job.get('contact_email')})...")
            dispatch_report = dispatcher.dispatch_application(job, target_dir)
        # Cas B: Offre France Travail avec identifiants configurés dans le Cloud
        elif "francetravail.fr" in job.get("url", "") and os.environ.get("FRANCE_TRAVAIL_USER"):
            print(f"[*] Postulation automatisée sur France Travail dans le Cloud...")
            motivation_msg = generator.render_motivation_text(job)
            success, msg = ft_bot.apply_to_offer(
                offer_url=job.get("url"),
                cv_pdf_path=pdf_cv_path,
                letter_pdf_path=pdf_letter_path,
                motivation_text=motivation_msg,
                auto_confirm=True
            )
            dispatch_report = {
                "sent": success,
                "mode": "FRANCE_TRAVAIL_AUTO",
                "status": msg
            }
        else:
            dispatch_report = {
                "sent": False,
                "mode": "WEB_PORTAL_REQUIRED",
                "channel": job.get("source", "Portail Web")
            }
            
        # 8. Enregistrement dans le Tableau de Bord
        app_entry = {
            "id": job.get("id"),
            "source": job.get("source"),
            "company": job.get("company"),
            "contact_name": job.get("contact_name", "Monsieur le Responsable du Recrutement"),
            "contact_title": job.get("contact_title", "Direction des Ressources Humaines"),
            "title": job.get("title"),
            "city": job.get("city", "France"),
            "postal_code": job.get("postal_code", ""),
            "phone": job.get("phone", "Non communiqué"),
            "contact_email": job.get("contact_email") or (dispatch_report.get("recruiter_email") if dispatch_report else None),
            "salary": job.get("salary", "N/C"),
            "contract_type": job.get("contract_type", "CDI"),
            "url": job.get("url", ""),
            "description": job.get("description", ""),
            "score": score,
            "date": date_str,
            "folder": os.path.abspath(target_dir),
            "folder_rel": f"candidatures/{folder_name}",
            "pdf_letter": os.path.abspath(pdf_letter_path),
            "pdf_cv": os.path.abspath(pdf_cv_path),
            "recruiter_delivery": dispatch_report
        }
        dashboard.add_application(app_entry)
        
        # 9. Envoi d'Alerte Email personnelle à Richard Busson
        if auto_notify:
            notifier.send_application_alert(job, pdf_letter_path, pdf_cv_path)
            
        # Mise à jour immédiate des empreintes pour éviter les doublons intra-session
        existing_fps = dashboard.get_existing_fingerprints()
        validated_count += 1
        
    print("\n" + "=" * 75)
    print(f"  [SUCCÈS] {validated_count} nouvelle(s) candidature(s) inédite(s) traitée(s) !")
    print("=" * 75)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    run_pipeline(base_dir=base_dir, auto_notify=True)




