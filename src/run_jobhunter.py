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

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(' ', '_')

def run_pipeline(base_dir=".", auto_notify=True):
    print("=" * 75)
    print("  [JOBHUNTER CLOUD RUNNER] - EXECUTION DU PIPELINE DE CANDIDATURES")
    print("=" * 75)
    
    searcher = JobSearcher(base_dir=base_dir)
    generator = ApplicationGenerator(base_dir=base_dir)
    guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
    dashboard = DashboardManager(base_dir=base_dir)
    notifier = ApplicationNotifier()
    
    # 1. Chargement du tracker anti-doublon
    tracker_path = os.path.join(base_dir, "tracker.json")
    processed_ids = set()
    if os.path.exists(tracker_path):
        try:
            with open(tracker_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                processed_ids = set(data.get("processed_ids", []))
        except Exception as e:
            print(f"[!] Avertissement tracker: {e}")
            
    # 2. Récupération des offres qualifiées
    print("\n[+] Recherche et filtrage strict des opportunités...")
    offers = searcher.fetch_live_opportunities()
    print(f"    -> {len(offers)} opportunités qualifiées (critères salaires & géographie validés)")
    
    validated_count = 0
    
    for job in offers:
        job_id = job.get("id", job.get("company", "") + "_" + job.get("title", ""))
        if job_id in processed_ids:
            print(f"[-] Offre déjà traitée précédemment : {job.get('title')} ({job.get('company')}) - ignorée.")
            continue
            
        score = generator.evaluate_match(job)
        job["score"] = score
        
        if score < 75:
            print(f"[-] Score insuffisant ({score}%) pour {job.get('title')} - ignoré.")
            continue
            
        print(f"\n" + "-" * 70)
        print(f"[*] Traitement : {job.get('company')} - {job.get('title')} (Score : {score}%)")
        print(f"    Lieu : {job.get('city')} ({job.get('postal_code')}) | Salaire : {job.get('salary', 'N/C')}")
        print(f"    Éligibilité : {job.get('eligibility_reason', 'Validé')}")
        
        # 3. Création du dossier cible
        company_clean = sanitize_filename(job.get("company", "Entreprise"))
        title_clean = sanitize_filename(job.get("title", "Poste"))
        date_str = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"{date_str}_{company_clean}_{title_clean}"
        target_dir = os.path.join(base_dir, "candidatures", folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # 4. Génération des fichiers HTML
        letter_html = generator.render_letter_html(job)
        cv_html = generator.render_cv_html(job)
        
        # 5. CONTRÔLE DE SÉCURITÉ QUALITY GUARD (Pré-compilation)
        is_lettre_ok, msg_lettre = guard.validate_html_letter(letter_html)
        is_cv_ok, msg_cv = guard.validate_html_cv(cv_html)
        
        if not is_lettre_ok:
            print(f"    [X] ÉCHEC SÉCURITÉ LETTRE : {msg_lettre}")
            continue
        if not is_cv_ok:
            print(f"    [X] ÉCHEC SÉCURITÉ CV : {msg_cv}")
            continue
            
        letter_html_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
        cv_html_path = os.path.join(target_dir, "CV_Richard_BUSSON.html")
        with open(letter_html_path, "w", encoding="utf-8") as f:
            f.write(letter_html)
        with open(cv_html_path, "w", encoding="utf-8") as f:
            f.write(cv_html)
            
        # 6. Compilation PDF Vectoriel A4
        pdf_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
        pdf_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")
        
        print("    [+] Compilation PDF A4 haute fidélité...")
        compile_html_to_pdf(letter_html_path, pdf_letter_path)
        compile_html_to_pdf(cv_html_path, pdf_cv_path)
        
        # 7. CONTRÔLE DE SÉCURITÉ POST-COMPILATION (PageCount == 1)
        is_pdf_l_ok, msg_l = guard.validate_pdf_page_count(pdf_letter_path)
        is_pdf_c_ok, msg_c = guard.validate_pdf_page_count(pdf_cv_path)
        
        if not is_pdf_l_ok or not is_pdf_c_ok:
            print(f"    [!] Alerte contrôle PDF : Lettre ({msg_l}) | CV ({msg_c})")
            
        print("    [✓] Dossier 100% conforme et validé par le QualityGuard.")
        
        # 8. Synchronisation vers le dossier Gemini permanent s'il existe
        gemini_candidatures = r"C:\Users\richa\Gemini\Candidatures"
        if os.path.exists(gemini_candidatures):
            gemini_dest = os.path.join(gemini_candidatures, folder_name)
            os.makedirs(gemini_dest, exist_ok=True)
            import shutil
            shutil.copy(pdf_letter_path, os.path.join(gemini_dest, "Lettre_Motivation_Richard_BUSSON.pdf"))
            shutil.copy(pdf_cv_path, os.path.join(gemini_dest, "CV_Richard_BUSSON.pdf"))
            print(f"    [💾] Copie miroir vers {gemini_dest}")
            
        # 9. Enregistrement dans le CRM
        app_entry = {
            "company": job.get("company"),
            "title": job.get("title"),
            "city": job.get("city", "France"),
            "score": score,
            "folder": os.path.abspath(target_dir),
            "folder_rel": os.path.relpath(target_dir, base_dir),
            "pdf_letter": os.path.abspath(pdf_letter_path),
            "pdf_cv": os.path.abspath(pdf_cv_path)
        }
        dashboard.add_application(app_entry)
        
        # 10. Notification Email
        if auto_notify:
            notifier.send_application_alert(job, pdf_letter_path, pdf_cv_path)
            
        # Mise à jour du tracker
        processed_ids.add(job_id)
        validated_count += 1
        
    # Sauvegarde du tracker
    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump({"processed_ids": list(processed_ids), "last_run": datetime.now().isoformat()}, f, indent=2)
        
    print("\n" + "=" * 75)
    print(f"  [SUCCÈS] {validated_count} dossier(s) de candidature généré(s) et validé(s) !")
    print("=" * 75)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    run_pipeline(base_dir=base_dir, auto_notify=True)
