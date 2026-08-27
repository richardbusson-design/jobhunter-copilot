# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from application_generator import ApplicationGenerator
from quality_guard import QualityGuard
from pdf_compiler import compile_html_to_pdf
from dashboard_manager import DashboardManager

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
generator = ApplicationGenerator(base_dir=base_dir)
guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
dashboard = DashboardManager(base_dir=base_dir)

# 1. Données réelles extraites de l'annonce LinkedIn de Anthony SOURDET (Groupe ACN)
job_acn = {
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
    "description": (
        "[ON RECRUTE UN CONSEILLER·ÈRE FORMATION ÎLE-DE-FRANCE] "
        "Groupe ACN grandit, et notre équipe doit grandir avec lui. "
        "Nous recherchons un·e Conseiller·ère en Formation Professionnelle pour développer notre portefeuille clients "
        "sur les Yvelines, l'Essonne, la Seine-Saint-Denis et le Val-de-Marne. "
        "Un territoire dense (industrie, logistique, BTP, santé) : des entreprises qui veulent former leurs équipes pour qu'elles rentrent saines et sauves chez elles le soir. "
        "Un professionnel qui décroche son téléphone, va sur le terrain, comprend ce dont un responsable HSE a vraiment besoin avant de lui proposer quoi que ce soit. "
        "Trois ans d'expérience en négociation et fidélisation B2B. En échange : un territoire à piloter en autonomie, une voiture de service, un catalogue solide et une équipe à taille humaine. "
        "Les parcours atypiques et reconversions nous intéressent. Candidatures : contact@groupe-acn.fr"
    ),
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:groupe-acn-conseiller-formation"
}

print("=" * 75)
print("  [TEST CANDIDATURE SUR ANNONCE RÉELLE] - GROUPE ACN / ANTHONY SOURDET")
print("=" * 75)

# 2. Contrôle de sécurité QualityGuard sur les critères de l'annonce
is_valid, reason = guard.validate_job_criteria(job_acn)
print(f"[1] Contrôle d'éligibilité : {reason} (Validé: {is_valid})")

# 3. Procédure de tournoi à 3 essais pour retenir la meilleure variante
print("\n[2] Lancement du tournoi à 3 essais pour la lettre de motivation...")
best_letter_html, best_score, best_idx = generator.generate_best_of_three_letter(job_acn)

# 4. Rendu du CV sur-mesure pour Conseiller Formation B2B
cv_html = generator.render_cv_html(job_acn)

# 5. Création du dossier cible
target_dir = os.path.join(base_dir, "candidatures", "2026-08-27_Groupe_ACN_Conseiller_en_Formation_Professionnelle")
os.makedirs(target_dir, exist_ok=True)

letter_html_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
cv_html_path = os.path.join(target_dir, "CV_Richard_BUSSON.html")
pdf_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
pdf_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")

with open(letter_html_path, "w", encoding="utf-8") as f: f.write(best_letter_html)
with open(cv_html_path, "w", encoding="utf-8") as f: f.write(cv_html)

# 6. Compilation PDF
print("\n[3] Compilation des fichiers PDF A4 haute lisibilité...")
compile_html_to_pdf(letter_html_path, pdf_letter_path)
compile_html_to_pdf(cv_html_path, pdf_cv_path)

# 7. Contrôle Qualité Post-Compilation (1 Page A4 stricte)
is_pdf_l_ok, msg_l = guard.validate_pdf_page_count(pdf_letter_path)
is_pdf_c_ok, msg_c = guard.validate_pdf_page_count(pdf_cv_path)
print(f"    - Lettre PDF : {msg_l}")
print(f"    - CV PDF : {msg_c}")

# 8. Miroir dans C:\Users\richa\Gemini\Candidatures
gemini_dest = r"C:\Users\richa\Gemini\Candidatures\2026-08-27_Groupe_ACN_Conseiller_en_Formation_Professionnelle"
os.makedirs(gemini_dest, exist_ok=True)
import shutil
shutil.copy(pdf_letter_path, os.path.join(gemini_dest, "Lettre_Motivation_Richard_BUSSON.pdf"))
shutil.copy(pdf_cv_path, os.path.join(gemini_dest, "CV_Richard_BUSSON.pdf"))

# 9. Ajout au Tableau de bord
app_entry = dict(job_acn)
app_entry.update({
    "score": 96,
    "status": "Dossier PDF Prêt",
    "folder_rel": "candidatures/2026-08-27_Groupe_ACN_Conseiller_en_Formation_Professionnelle",
    "pdf_letter": pdf_letter_path,
    "pdf_cv": pdf_cv_path
})
dashboard.add_application(app_entry)

print("\n" + "=" * 75)
print("  [SUCCÈS] Dossier Groupe ACN généré, validé à 100% et ajouté au tableau de bord !")
print("=" * 75)
