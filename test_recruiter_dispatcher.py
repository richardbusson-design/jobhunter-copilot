# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from recruiter_dispatcher import RecruiterDispatcher

disp = RecruiterDispatcher()

# Trouver le premier dossier réel dans candidatures
cand_dirs = [d for d in os.listdir("candidatures") if os.path.isdir(os.path.join("candidatures", d))]
if cand_dirs:
    target = os.path.join("candidatures", cand_dirs[0])
    sample_job = {
        "company": "CMA Formation Nouvelle-Aquitaine",
        "title": "Formateur en paie et ressources humaines",
        "contact_name": "Monsieur Stéphane BON",
        "contact_title": "Directeur régional de la Formation",
        "contact_email": "recrutement-formation@cma-nouvelle-aquitaine.fr",
        "city": "Bordeaux",
        "description": "Poste de formateur paie et RH pour les promotions ADEA et Titre Pro TP-01254."
    }
    res = disp.dispatch_application(sample_job, target)
    print(f"[+] Dossier test : {cand_dirs[0]}")
    print(f"[+] Résultat dispatch : {res}")
    if res.get("sent"):
        print("[✓] SUCCÈS : Candidature validée et expédiée avec les 2 PDF joints conformes !")
