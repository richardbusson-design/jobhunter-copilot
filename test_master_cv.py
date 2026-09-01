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

job_cma = {
    "company": "CMA Hauts-de-France",
    "title": "Formateur en paie et ressources humaines",
    "description": "Animation ADEA, Titre pro paie, Qualiopi, droit social."
}

html_cv = gen.render_cv_html(job_cma)
with open("test_cv.html", "w", encoding="utf-8") as f:
    f.write(html_cv)

compile_html_to_pdf("test_cv.html", "test_cv.pdf")
render_html_to_png("test_cv.html", "test_cv.png")

r_cv = PdfReader("test_cv.pdf")
print(f"[+] Test CV : {len(r_cv.pages)} page(s) A4 générée(s).")
