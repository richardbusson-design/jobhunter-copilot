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
from pdf_compiler import compile_html_to_pdf, render_html_to_png
from dashboard_manager import DashboardManager
from notifier import ApplicationNotifier
from recruiter_dispatcher import RecruiterDispatcher

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(' ', '_')

def run_pipeline(base_dir=".", auto_notify=True):
    print("=" * 75)
    print("  [JOBHUNTER PIPELINE OFFICIEL] - EXECUTION & CONTROLE QUALITE STRICT")
    print("=" * 75)
    
    searcher = JobSearcher(base_dir=base_dir)
    generator = ApplicationGenerator(base_dir=base_dir)
    guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
    dashboard = DashboardManager(base_dir=base_dir)
    notifier = ApplicationNotifier()
    dispatcher = RecruiterDispatcher(base_dir=base_dir)
    
    # 1. Lecture intégrale du tableau de bord AVANT TOUTE RECHERCHE (Anti-doublon absolu)
    print("\n[+] 1. Lecture préalable intégrale du tableau de bord...")
    fingerprints = dashboard.get_existing_fingerprints()
    print(f"    -> {fingerprints['count']} candidatures historiques enregistrées en base.")
    print(f"    -> {len(fingerprints['ids'])} IDs, {len(fingerprints['urls'])} URLs et {len(fingerprints['company_titles'])} couples Entreprise/Poste chargés pour blocage amont.")
    
    # 2. Récupération des opportunités avec filtrage amont immédiat
    print("\n[+] 2. Recherche et filtrage strict des opportunités (Zéro doublon)...")
    offers = searcher.fetch_live_opportunities(existing_fingerprints=fingerprints)
    print(f"    -> {len(offers)} opportunités inédites et qualifiées retenues.")
    
    validated_count = 0
    batch_processed = []
    
    for job in offers:
        job_id = str(job.get("id", "")).strip()
        job_url = str(job.get("url", "")).strip()
        c_norm = dashboard.get_existing_fingerprints() # safety
        c_name = job.get("company", "")
        t_name = job.get("title", "")
        ct_pair = f"{re.sub(r'[^\w\s]', ' ', c_name.lower()).strip()}|{re.sub(r'[^\w\s]', ' ', t_name.lower()).strip()}"
        
        if (job_id and job_id in fingerprints["ids"]) or \
           (job_url and job_url in fingerprints["urls"]) or \
           (ct_pair in fingerprints["company_titles"]):
            print(f"    [!] Doublon détecté et bloqué : {c_name} - {t_name}")
            continue
            
        is_qual, qual_reason = guard.validate_job_criteria(job)
        if not is_qual:
            print(f"    [-] Écarté par QualityGuard : {c_name} - {t_name} -> {qual_reason}")
            continue
            
        score = generator.evaluate_match(job)
        job["score"] = score
        
        if score < 75:
            continue
            
        print(f"\n" + "-" * 70)
        print(f"[*] Analyse dossier : {job.get('company')} - {job.get('title')} (Score : {score}%)")
        
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
        
        letter_html_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
        cv_html_path = os.path.join(target_dir, "CV_Richard_BUSSON.html")
        
        with open(letter_html_path, "w", encoding="utf-8") as f:
            f.write(letter_html)
        with open(cv_html_path, "w", encoding="utf-8") as f:
            f.write(cv_html)
            
        # 5. Compilation PDF Vectoriel A4 et Capture PNG Haute Définition
        pdf_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
        pdf_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")
        png_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.png")
        png_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.png")
        
        compile_html_to_pdf(letter_html_path, pdf_letter_path)
        compile_html_to_pdf(cv_html_path, pdf_cv_path)
        render_html_to_png(letter_html_path, png_letter_path)
        render_html_to_png(cv_html_path, png_cv_path)
        
        # 6. CONTRÔLE DE SÉCURITÉ QUALITY GUARD BLOQUANT EN 3 PASSAGES
        is_valid, audit_report = guard.execute_three_pass_audit(
            job=job,
            letter_html=letter_html,
            cv_html=cv_html,
            pdf_letter_path=pdf_letter_path,
            pdf_cv_path=pdf_cv_path
        )
        
        if not is_valid:
            print(f"    [BLOCAGE ABSOLU QUALITYGUARD] Échec validation : {audit_report}")
            # Suppression des fichiers non conformes
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            continue
            
        print("    [✓] AUDIT 3 PASSAGES VALIDE : Dossier 100% sur-mesure, zéro tag résiduel, PDF 1 page A4 et PNG HD certifiés.")
        
        # 7. Expédition Directe au Recruteur (Module RecruiterDispatcher)
        dispatch_report = dispatcher.dispatch_application(job, target_dir)
        
        # 8. Enregistrement dans le CRM / Dashboard
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
            "folder": os.path.abspath(target_dir),
            "folder_rel": os.path.relpath(target_dir, base_dir),
            "pdf_letter": os.path.abspath(pdf_letter_path),
            "pdf_cv": os.path.abspath(pdf_cv_path),
            "recruiter_delivery": dispatch_report
        }
        dashboard.add_application(app_entry)
        batch_processed.append(app_entry)
            
        fingerprints["ids"].add(job_id)
        fingerprints["urls"].add(job_url)
        fingerprints["company_titles"].add(ct_pair)
        validated_count += 1
        
    print("\n" + "=" * 75)
    print(f"  [SUCCÈS GLOBAL] {validated_count} nouveau(x) dossier(s) certifié(s), expédié(s) et intégré(s) au tableau de bord.")
    print("=" * 75)
    
    # Envoi du rapport de synthèse par email à Richard Busson
    if auto_notify and batch_processed:
        print(f"\n[*] Envoi du rapport récapitulatif ({len(batch_processed)} candidatures) à richard.busson@kairos-paye.fr...")
        notifier.send_batch_summary(batch_processed)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    run_pipeline(base_dir=base_dir, auto_notify=True)
