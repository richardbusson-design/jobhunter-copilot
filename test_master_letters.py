# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from application_generator import ApplicationGenerator
from pdf_compiler import compile_html_to_pdf, render_html_to_png
from pypdf import PdfReader

gen = ApplicationGenerator()

# 1. Test CMA / CFA
job_cma = {
    "company": "CMA Hauts-de-France",
    "title": "Formateur en paie et ressources humaines",
    "contact_name": "Monsieur Stéphane BON",
    "contact_title": "Directeur régional de la Formation",
    "address_1": "46, rue Général de Larminat",
    "postal_code": "60000",
    "city": "BEAUVAIS",
    "description": "Animation ADEA, Titre pro paie, Qualiopi, droit social."
}

html_cma = gen.render_letter_html(job_cma)
with open("test_cma.html", "w", encoding="utf-8") as f:
    f.write(html_cma)

compile_html_to_pdf("test_cma.html", "test_cma.pdf")
render_html_to_png("test_cma.html", "test_cma.png")

r_cma = PdfReader("test_cma.pdf")
print(f"[+] Test CMA : {len(r_cma.pages)} page(s) A4 générée(s).")

# 2. Test Entreprise privée / RRH
job_rrh = {
    "company": "RATP Cap Ile-de-France",
    "title": "Responsable développement RH",
    "contact_name": "Direction des Ressources Humaines",
    "contact_title": "Service Recrutement & Talents",
    "address_1": "",
    "postal_code": "75012",
    "city": "PARIS",
    "description": "Pilotage des RH, relations sociales, CSE, paie, administration du personnel."
}

html_rrh = gen.render_letter_html(job_rrh)
with open("test_rrh.html", "w", encoding="utf-8") as f:
    f.write(html_rrh)

compile_html_to_pdf("test_rrh.html", "test_rrh.pdf")
render_html_to_png("test_rrh.html", "test_rrh.png")

r_rrh = PdfReader("test_rrh.pdf")
print(f"[+] Test RRH Entreprise : {len(r_rrh.pages)} page(s) A4 générée(s).")
