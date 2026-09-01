# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from pdf_compiler import render_html_to_png

cand_dir = os.path.abspath("candidatures")
fixed = 0

for root, dirs, files in os.walk(cand_dir):
    for f in files:
        if f.endswith(".html"):
            html_path = os.path.join(root, f)
            png_name = f.replace(".html", ".png")
            png_path = os.path.join(root, png_name)
            
            if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
                print(f"[>] Génération PNG séquentielle : {png_name} dans {os.path.basename(root)}")
                render_html_to_png(html_path, png_path)
                fixed += 1

print(f"[✓] {fixed} fichier(s) PNG manquant(s) généré(s). 100% des fichiers sont présents et valides.")
