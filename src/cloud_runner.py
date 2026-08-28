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
    print("  [JOBHUNTER CLOUD RUNNER] - EXECUTION AVEC FILTRAGE ANTI-DOUBLON STRICT")
    print("=" * 75)
    
    dashboard = DashboardManager(base_dir=base_dir)
    searcher = JobSearcher(base_dir=base_dir)
    generator = ApplicationGenerator(base_dir=base_dir)
    guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
    notifier = ApplicationNotifier()
    
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
            
        # 7. Copie miroir locale
        gemini_candidatures = r"C:\Users\richa\Gemini\Candidatures"
        if os.path.exists(gemini_candidatures):
            gemini_dest = os.path.join(gemini_candidatures, folder_name)
            os.makedirs(gemini_dest, exist_ok=True)
            import shutil
            shutil.copy(pdf_letter_path, os.path.join(gemini_dest, "Lettre_Motivation_Richard_BUSSON.pdf"))
            shutil.copy(pdf_cv_path, os.path.join(gemini_dest, "CV_Richard_BUSSON.pdf"))
            
        # 8. Enregistrement dans le Tableau de Bord
        app_entry = dict(job)
        app_entry.update({
            "folder": os.path.abspath(target_dir),
            "folder_rel": f"candidatures/{folder_name}",
            "pdf_letter": os.path.abspath(pdf_letter_path),
            "pdf_cv": os.path.abspath(pdf_cv_path),
            "status": "Dossier PDF & Visuel Prêt"
        })
        dashboard.add_application(app_entry)
        
        # 9. Envoi d'Alerte Email
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



