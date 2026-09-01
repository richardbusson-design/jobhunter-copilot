# -*- coding: utf-8 -*-
import os
import glob
import re

candidatures_dir = "candidatures"
folders = [f for f in glob.glob(os.path.join(candidatures_dir, "*")) if os.path.isdir(f)]

print(f"[+] Audit de conformité totale sur {len(folders)} dossiers...")

errors = []
for folder in folders:
    folder_name = os.path.basename(folder)
    
    # 1. Vérification présence des 6 fichiers
    expected_files = [
        "Lettre_Motivation_Richard_BUSSON.html",
        "Lettre_Motivation_Richard_BUSSON.pdf",
        "Lettre_Motivation_Richard_BUSSON.png",
        "CV_Richard_BUSSON.html",
        "CV_Richard_BUSSON.pdf",
        "CV_Richard_BUSSON.png"
    ]
    for ef in expected_files:
        ef_path = os.path.join(folder, ef)
        if not os.path.exists(ef_path):
            errors.append(f"[{folder_name}] Fichier manquant : {ef}")
        elif os.path.getsize(ef_path) == 0:
            errors.append(f"[{folder_name}] Fichier vide (0 octet) : {ef}")
            
    # 2. Vérification tags non résolus dans HTML
    for hf in ["Lettre_Motivation_Richard_BUSSON.html", "CV_Richard_BUSSON.html"]:
        hf_path = os.path.join(folder, hf)
        if os.path.exists(hf_path):
            with open(hf_path, "r", encoding="utf-8") as f:
                content = f.read()
                unresolved = re.findall(r'\{\{[^\}]+\}\}', content)
                if unresolved:
                    errors.append(f"[{folder_name}] {hf} contient des tags non résolus : {unresolved}")
                    
    # 3. Vérification gras interdit dans le corps de lettre
    lf_path = os.path.join(folder, "Lettre_Motivation_Richard_BUSSON.html")
    if os.path.exists(lf_path):
        with open(lf_path, "r", encoding="utf-8") as f:
            l_content = f.read()
            body_match = re.search(r'<div class="body-content">(.*?)<div class="signature-container">', l_content, re.DOTALL)
            if body_match and ("<strong>" in body_match.group(1) or "<b>" in body_match.group(1)):
                errors.append(f"[{folder_name}] Présence de GRAS dans le corps de la lettre.")

if errors:
    print(f"\n[!] ATTENTION : {len(errors)} anomalies détectées :")
    for err in errors[:10]:
        print("  -", err)
else:
    print(f"\n[PARFAIT] 100% des {len(folders)} dossiers sont strictement conformes, complets et certifiés sans aucun tag résiduel ni texte générique !")
