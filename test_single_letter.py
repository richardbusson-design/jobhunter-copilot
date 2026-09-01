# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from application_generator import ApplicationGenerator
from pdf_compiler import compile_html_to_pdf, render_html_to_png
from pypdf import PdfReader

gen = ApplicationGenerator()

sample_job = {
    "company": "PARTNAIRE ILE DE FRANCE NORD OUEST",
    "title": "Gestionnaire de paie",
    "contact_name": "Monsieur le Directeur de Centre",
    "contact_title": "Direction de l'établissement",
    "address_1": "Service Recrutement & RH",
    "postal_code": "60000",
    "city": "BEAUVAIS",
    "description": "Gestion de la paie, DSN, administration du personnel, Silae, droit social."
}

letter_html = gen.render_letter_html(sample_job)
with open("test_letter.html", "w", encoding="utf-8") as f:
    f.write(letter_html)

compile_html_to_pdf("test_letter.html", "test_letter.pdf")
render_html_to_png("test_letter.html", "test_letter.png")

reader = PdfReader("test_letter.pdf")
page_count = len(reader.pages)

print(f"[+] Résultat Test Lettre : {page_count} page(s) A4 générée(s).")
if page_count == 1:
    print("[✓] PARFAIT : Strictement 1 page A4 pleine et équilibrée.")
else:
    print("[!] ALERTE : Débordement sur plusieurs pages !")
