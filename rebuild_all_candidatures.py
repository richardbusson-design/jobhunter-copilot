# -*- coding: utf-8 -*-
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from application_generator import ApplicationGenerator
from pdf_compiler import compile_html_to_pdf, render_html_to_png
from dashboard_manager import DashboardManager

gen = ApplicationGenerator()
dm = DashboardManager()
apps = dm.load_tracker()

print(f"[+] Recompilation parallèle et personnalisation intégrale de {len(apps)} candidatures...")

def process_app(a):
    folder_rel = a.get("folder_rel", "").replace("\\", "/")
    if not folder_rel:
        return False
        
    folder_abs = os.path.abspath(folder_rel)
    os.makedirs(folder_abs, exist_ok=True)
    
    # 1. Génération de la Lettre personnalisée
    letter_html = gen.render_letter_html(a)
    letter_html_path = os.path.join(folder_abs, "Lettre_Motivation_Richard_BUSSON.html")
    with open(letter_html_path, "w", encoding="utf-8") as f:
        f.write(letter_html)
        
    # 2. Génération du CV personnalisé
    cv_html = gen.render_cv_html(a)
    cv_html_path = os.path.join(folder_abs, "CV_Richard_BUSSON.html")
    with open(cv_html_path, "w", encoding="utf-8") as f:
        f.write(cv_html)
        
    # 3. Compilation PDF & PNG pour la Lettre
    letter_pdf_path = os.path.join(folder_abs, "Lettre_Motivation_Richard_BUSSON.pdf")
    letter_png_path = os.path.join(folder_abs, "Lettre_Motivation_Richard_BUSSON.png")
    compile_html_to_pdf(letter_html_path, letter_pdf_path)
    render_html_to_png(letter_html_path, letter_png_path)
    
    # 4. Compilation PDF & PNG pour le CV
    cv_pdf_path = os.path.join(folder_abs, "CV_Richard_BUSSON.pdf")
    cv_png_path = os.path.join(folder_abs, "CV_Richard_BUSSON.png")
    compile_html_to_pdf(cv_html_path, cv_pdf_path)
    render_html_to_png(cv_html_path, cv_png_path)
    
    return True

with ThreadPoolExecutor(max_workers=6) as executor:
    results = list(executor.map(process_app, apps))

print(f"[✓] {sum(1 for r in results if r)}/{len(apps)} dossiers régénérés et synchronisés avec succès.")

# Régénération du tableau de bord
dm.generate_markdown_dashboard()
dm.generate_html_dashboard()
print("[✓] Tableau de bord régénéré avec succès.")
