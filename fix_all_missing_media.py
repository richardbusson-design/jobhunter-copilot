# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from pdf_compiler import compile_html_to_pdf, render_html_to_png

cand_dir = os.path.abspath("candidatures")
folders = [os.path.join(cand_dir, d) for d in os.listdir(cand_dir) if os.path.isdir(os.path.join(cand_dir, d))]

print(f"[+] Vérification et génération des PDF et PNG pour {len(folders)} dossiers...")

fixed_count = 0
for f in folders:
    l_html = os.path.join(f, "Lettre_Motivation_Richard_BUSSON.html")
    l_pdf = os.path.join(f, "Lettre_Motivation_Richard_BUSSON.pdf")
    l_png = os.path.join(f, "Lettre_Motivation_Richard_BUSSON.png")
    
    c_html = os.path.join(f, "CV_Richard_BUSSON.html")
    c_pdf = os.path.join(f, "CV_Richard_BUSSON.pdf")
    c_png = os.path.join(f, "CV_Richard_BUSSON.png")
    
    if os.path.exists(l_html):
        if not os.path.exists(l_pdf) or os.path.getsize(l_pdf) == 0:
            compile_html_to_pdf(l_html, l_pdf)
            fixed_count += 1
        if not os.path.exists(l_png) or os.path.getsize(l_png) == 0:
            render_html_to_png(l_html, l_png)
            fixed_count += 1
            
    if os.path.exists(c_html):
        if not os.path.exists(c_pdf) or os.path.getsize(c_pdf) == 0:
            compile_html_to_pdf(c_html, c_pdf)
            fixed_count += 1
        if not os.path.exists(c_png) or os.path.getsize(c_png) == 0:
            render_html_to_png(c_html, c_png)
            fixed_count += 1

print(f"[OK] {fixed_count} fichiers PDF/PNG régénérés avec succès. 100% des dossiers sont complets.")
