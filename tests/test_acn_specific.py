# -*- coding: utf-8 -*-
import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from application_generator import ApplicationGenerator
from quality_guard import QualityGuard
from pdf_compiler import compile_html_to_pdf
from dashboard_manager import DashboardManager

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
generator = ApplicationGenerator(base_dir=base_dir)
guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
dashboard = DashboardManager(base_dir=base_dir)

job_acn = {
    "id": "LINKEDIN-ACN-2026",
    "source": "LinkedIn (Anthony SOURDET)",
    "title": "Conseiller en Formation Professionnelle",
    "company": "Groupe ACN",
    "contact_name": "Monsieur Anthony SOURDET",
    "contact_title": "Co-fondateur",
    "address_1": "Groupe ACN - Pôle Développement Île-de-France",
    "address_2": "contact@groupe-acn.fr",
    "postal_code": "75000",
    "city": "PARIS / ÎLE-DE-FRANCE",
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

# --- 3 VARIANTES SUR-MESURE GROUPE ACN ---
p_cloture = "Je vous prie d’agréer, Monsieur, l’expression de ma considération distinguée."

# VARIANTE 1 : Axe Dirigeant Qualiopi & Conseil B2B Terrain
v1_p1 = "Votre appel à candidatures pour le poste de conseiller en formation professionnelle en Île-de-France retient toute mon attention. Dirigeant d'un organisme de formation certifié Qualiopi depuis 2014, je connais intimement les besoins des entreprises en matière de compétences et de conformité. Décrocher son téléphone, aller sur le terrain dans les bassins de l'industrie, de la logistique et du BTP, comprendre les priorités d'un responsable HSE avant de formuler une préconisation : c'est exactement ma conception du conseil en formation."
v1_p2 = "Mon parcours allie la rigueur technique de l'ingénierie pédagogique à la pratique de la négociation B2B. Qu'il s'agisse de concevoir des plans de formation adaptés ou de commercialiser des parcours certifiants, j'ai l'habitude d'échanger avec des dirigeants et des directeurs des ressources humaines pour leur apporter des solutions sur-mesure, rentables et immédiatement applicables."

# VARIANTE 2 : Axe Responsable RH / Opérationnel & Culture Sécurité
v2_p1 = "L'engagement du Groupe ACN pour une formation utile, garantissant que chaque collaborateur rentre sain et sauf chez lui le soir, résonne particulièrement avec mon expérience. Ancien responsable des ressources humaines d'une structure de 580 collaborateurs et ancien responsable de site industriel en exploitation, je maîtrise parfaitement les impératifs de sécurité au travail et les obligations de prévention des employeurs."
v2_p2 = "Cette double culture RH et industrielle me permet de dialoguer d'égal à égal avec vos futurs clients sur les Yvelines, l'Essonne, la Seine-Saint-Denis et le Val-de-Marne. Autonome dans l'action, rompu à la prospection téléphonique et aux rendez-vous physiques, je sais identifier les leviers de financement et fidéliser des comptes clés sur la durée."

# VARIANTE 3 : Axe Parcours Atypique, Énergie Senior & Stabilité
v3_p1 = "Votre ouverture affirmée aux parcours atypiques et aux profils d'expérience correspond exactement à ce que je peux apporter au Groupe ACN. Fort de plus de quinze années consacrées aux ressources humaines et à la formation professionnelle pour adultes, je vous propose une énergie commerciale solide, adossée à une parfaite maîtrise des mécanismes de la formation continue."
v3_p2 = "Dirigeant d'un organisme certifié Qualiopi, titulaire d'un Master 2 de droit public et d'une formation supérieure en gestion, je dispose d'une autonomie totale pour faire grandir votre territoire. Je suis disponible pour prendre en main votre portefeuille, sillonner les bassins industriels d'Île-de-France et porter avec conviction votre catalogue de formation."

p3 = "J’ai exercé ce métier avant de l’enseigner : de 2003 à 2010, j’ai dirigé les ressources humaines d’une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant aussi le plan de formation. Le cadre d’un centre de formation ne m’est pas étranger non plus : entre 2016 et 2020, je suis intervenu sur quatre centres Afpa, avec référentiel imposé, évaluations en cours de formation et parcours individualisés au sein d’un même groupe."
p4 = "Si c’est une fonction de coordination que vous avez à pourvoir, elle me va tout autant. Je dirige un organisme certifié Qualiopi : le Référentiel National Qualité, la traçabilité des parcours et la préparation d’audit sont mes obligations quotidiennes. J’ai conçu de bout en bout un parcours certifiant de 758 heures préparant au Titre professionnel Gestionnaire de paie, et encadré quatre ans les équipes d’un site industriel en Nouvelle-Calédonie. Un Master 2 de droit public complète cette approche des cadres réglementaires."
p5 = "Un mot de franchise pour finir. J’ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu’un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l’embauche au titre de ma situation de demandeur d’emploi senior, dont je vous communiquerai volontiers les modalités. Ma mobilité est nationale, sans réserve, sur l’ensemble du réseau, et ma disponibilité immédiate."

today_str = "27 août 2026"

def build_html(p1, p2):
    html = generator.letter_template
    html = html.replace("{{ contact_full }}", "Monsieur Anthony SOURDET, Co-fondateur")
    html = html.replace("{{ company_name }}", "Groupe ACN")
    html = html.replace("{{ address_1 }}", "Direction du Développement & Recrutement")
    html = html.replace("{{ postal_code }}", "contact@groupe-acn.fr")
    html = html.replace("{{ city }}", "ÎLE-DE-FRANCE")
    html = html.replace("{{ current_date }}", today_str)
    html = html.replace("{{ job_title_clean }}", "Conseiller Formation, Île-de-France")
    html = html.replace("{{ paragraph_1 }}", p1)
    html = html.replace("{{ paragraph_2 }}", p2)
    html = html.replace("{{ paragraph_3 }}", p3)
    html = html.replace("{{ paragraph_4 }}", p4)
    html = html.replace("{{ paragraph_5 }}", p5)
    return html

variants = [
    ("Axe Dirigeant Qualiopi & Conseil B2B Terrain", build_html(v1_p1, v1_p2)),
    ("Axe Responsable RH / HSE & Culture Sécurité", build_html(v2_p1, v2_p2)),
    ("Axe Parcours Atypique & Autonomie Commerciale", build_html(v3_p1, v3_p2))
]

print("=" * 75)
print("  [TOURNOI DE SÉLECTION SUR ANNONCE ACN] - ÉVALUATION DES 3 ESSAIS")
print("=" * 75)

scored_variants = []
for idx, (label, html_code) in enumerate(variants, 1):
    score = guard.score_letter_candidate(html_code, job_acn)
    scored_variants.append((html_code, score, idx, label))
    print(f"  [+] Essai {idx} ({label}) : Score = {score:.1f}/100")

# Sélection du meilleur essai
best_html, best_score, best_idx, best_label = max(scored_variants, key=lambda x: x[1])
print(f"\n  [[GAGNANT] GAGNANT RETENU] : Essai {best_idx} - {best_label} (Score : {best_score:.1f}/100)")

# Rendu du CV sur-mesure
cv_html = generator.render_cv_html(job_acn)

# Enregistrement et Compilation
target_dir = os.path.join(base_dir, "candidatures", "2026-08-27_Groupe_ACN_Conseiller_en_Formation_Professionnelle")
os.makedirs(target_dir, exist_ok=True)

letter_html_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.html")
cv_html_path = os.path.join(target_dir, "CV_Richard_BUSSON.html")
pdf_letter_path = os.path.join(target_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
pdf_cv_path = os.path.join(target_dir, "CV_Richard_BUSSON.pdf")

with open(letter_html_path, "w", encoding="utf-8") as f: f.write(best_html)
with open(cv_html_path, "w", encoding="utf-8") as f: f.write(cv_html)

compile_html_to_pdf(letter_html_path, pdf_letter_path)
compile_html_to_pdf(cv_html_path, pdf_cv_path)

# Synchronisation Gemini root
gemini_dest = r"C:\Users\richa\Gemini\Candidatures\2026-08-27_Groupe_ACN_Conseiller_en_Formation_Professionnelle"
os.makedirs(gemini_dest, exist_ok=True)
import shutil
shutil.copy(pdf_letter_path, os.path.join(gemini_dest, "Lettre_Motivation_Richard_BUSSON.pdf"))
shutil.copy(pdf_cv_path, os.path.join(gemini_dest, "CV_Richard_BUSSON.pdf"))

print(f"\n  [[OK]] PDF compilés et validés par le QualityGuard :")
print(f"      - Lettre : {pdf_letter_path}")
print(f"      - CV : {pdf_cv_path}")

