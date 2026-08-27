# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from job_searcher import JobSearcher
from application_generator import ApplicationGenerator
from quality_guard import QualityGuard
from pdf_compiler import compile_html_to_pdf
from dashboard_manager import DashboardManager
from notifier import ApplicationNotifier

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
searcher = JobSearcher(base_dir=base_dir)
generator = ApplicationGenerator(base_dir=base_dir)
guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
dashboard = DashboardManager(base_dir=base_dir)

print("=" * 75)
print("  [CYCLE DE VEILLE & RECHERCHE EN DIRECT] - FRANCE TRAVAIL / APEC / INDEED")
print("=" * 75)

opportunities = searcher.fetch_live_opportunities()

# Ajout de l'annonce Groupe ACN si non présente
acn_exists = any(o.get("id") == "LINKEDIN-ACN-2026" for o in opportunities)
if not acn_exists:
    opportunities.append({
        "id": "LINKEDIN-ACN-2026",
        "source": "LinkedIn (Anthony SOURDET)",
        "title": "Conseiller en Formation Professionnelle",
        "company": "Groupe ACN",
        "contact_name": "Monsieur Anthony SOURDET",
        "contact_title": "Co-fondateur & Direction",
        "address_1": "Direction du Développement & Recrutement",
        "address_2": "contact@groupe-acn.fr",
        "postal_code": "75000",
        "city": "ÎLE-DE-FRANCE",
        "salary": "36 000 € - 42 000 € brut annuel + Véhicule de service",
        "contract_type": "CDI",
        "description": "Conseiller en Formation Professionnelle pour développer notre portefeuille clients B2B sur les Yvelines, l'Essonne, la Seine-Saint-Denis et le Val-de-Marne. Industrie, logistique, BTP, santé. Écoute des responsables HSE et RH. Les reconversions et parcours atypiques sont bienvenus.",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:groupe-acn-conseiller-formation",
        "eligibility_status": "ELIGIBLE",
        "eligibility_reason": "Éligible (Zone Creil / Hauts-de-France / Île-de-France <= 2h)"
    })

print(f"\n[+] Total : {len(opportunities)} opportunités qualifiées en cours de traitement.")

for job in opportunities:
    title = job.get("title", "")
    comp = job.get("company", "")
    safe_name = f"2026-08-28_{comp}_{title}".replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(":", "")[:80]
    target_dir = os.path.join(base_dir, "candidatures", safe_name)
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"\n[*] Traitement : {comp} - {title}")
    
    # 1. Sélection à 3 essais pour la lettre
    best_letter, score_val, best_idx = generator.generate_best_of_three_letter(job)
    cv_code = generator.render_cv_html(job)
    
    letter_html = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
    cv_html = os.path.join(target_dir, "CV_Richard_BUSSON.html")
    pdf_letter = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
    pdf_cv = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")
    
    with open(letter_html, "w", encoding="utf-8") as f: f.write(best_letter)
    with open(cv_html, "w", encoding="utf-8") as f: f.write(cv_code)
    
    compile_html_to_pdf(letter_html, pdf_letter)
    compile_html_to_pdf(cv_html, pdf_cv)
    
    # Copie miroir
    gemini_dest = os.path.join(r"C:\Users\richa\Gemini\Candidatures", safe_name)
    os.makedirs(gemini_dest, exist_ok=True)
    import shutil
    shutil.copy(pdf_letter, os.path.join(gemini_dest, "Lettre_Motivation_Richard_BUSSON.pdf"))
    shutil.copy(pdf_cv, os.path.join(gemini_dest, "CV_Richard_BUSSON.pdf"))
    
    # Enregistrement dans le dashboard
    app_entry = dict(job)
    app_entry.update({
        "score": generator.evaluate_match(job),
        "status": "Dossier PDF & Visuel Prêt",
        "folder_rel": f"candidatures/{safe_name}",
        "pdf_letter": pdf_letter,
        "pdf_cv": pdf_cv
    })
    dashboard.add_application(app_entry)

print("\n" + "=" * 75)
print("  [BILAN] Toutes les opportunités ont été analysées, validées et compilées !")
print("=" * 75)


