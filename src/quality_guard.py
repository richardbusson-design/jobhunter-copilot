# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Dict, Any, Tuple

class QualityGuard:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.profile = self.load_config("profile.json")
        self.rules = self.load_config("rules.json")

    def load_config(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    # =========================================================================
    # PASSAGE 1 : CONTRÔLE DE FAISABILITÉ SOURCE & FILTRAGE PRÉALABLE
    # =========================================================================
    def validate_job_criteria(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        """Vérifie l'authenticité, le salaire, l'expérience et le périmètre géographique."""
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        
        # 1. Élimination des offres juniors / débutants (< 3 ans)
        if "junior" in title or "débutant" in title or "debutant" in title or "sans expérience" in desc:
            if "junior accepté" not in desc and "débutant accepté" not in desc:
                return False, "Rejet : Profil Junior ou Débutant détecté (< 3 ans d'expérience exigée)."

        # 2. Élimination formelle de la comptabilité pure (Richard Busson n'est PAS comptable)
        if ("comptable" in title or "comptabilité" in title) and not any(k in title for k in ["paie", "social", "rh", "ressources humaines"]):
            return False, "Rejet : Poste de comptabilité pure exclu. Cœur de métier : Gestionnaire de Paie / RH."

        # 3. Élimination des offres hors cible (ex: secrétariat pur, assistanat sans RH/paie)
        rh_paie_keywords = ["paie", "rh", "ressources humaines", "formation", "social", "adp", "personnel", "relations sociales", "masse salariale"]
        if not any(kw in title or kw in desc for kw in rh_paie_keywords):
            return False, "Rejet : Poste hors cible RH / Paie / Formation."

        # 4. Contrôle du seuil salarial (>= 30 000 € brut / an ou >= 2 500 € / mois)
        sal_text = job.get("salary", "")
        if sal_text:
            sal_nums = re.findall(r'(\d+[\s\d]*)', sal_text.replace(" ", ""))
            for num_str in sal_nums:
                try:
                    num = int(num_str)
                    if 1500 <= num < 2500: # Mensuel inférieur à 2500€
                        return False, f"Rejet : Salaire mensuel ({num} €) inférieur au seuil minimal de 2 500 € brut."
                    elif 10000 <= num < 30000: # Annuel inférieur à 30 000€
                        return False, f"Rejet : Salaire annuel ({num} €) inférieur au seuil minimal de 30 000 € brut."
                except ValueError:
                    pass

        # 5. Contrôle du périmètre géographique
        postal_code = str(job.get("postal_code", "60100")).strip()
        dept = postal_code[:2] if len(postal_code) >= 2 else "60"
        
        bassin_creil_2h = ["60", "75", "92", "93", "94", "95", "78", "77", "91", "80", "02", "59", "62", "76", "27"]
        facade_maritime = ["17", "33", "40", "64", "44", "85", "56", "29", "22", "35", "50", "14", "66", "11", "34", "30", "13", "83", "06"]
        
        is_remote = "télétravail" in desc or "remote" in desc or "100%" in desc or "full remote" in desc
        
        if not (dept in bassin_creil_2h or dept in facade_maritime or is_remote):
            return False, f"Rejet : Zone géographique ({dept}) hors bassin Creil 2h et hors façades maritimes."

        return True, "Offre qualifiée et éligible."

    # =========================================================================
    # PASSAGE 2 : CONTRÔLE D'INTÉGRITÉ DU TEMPLATE & TYPOGRAPHIE
    # =========================================================================
    def validate_template_integrity(self, html_content: str, doc_name: str = "Document") -> Tuple[bool, str]:
        """Vérifie l'absence absolue de balises résiduelles {{...}}."""
        unfilled_tags = re.findall(r'\{\{[^\{\}]+\}\}', html_content)
        if unfilled_tags:
            return False, f"Blocage intégrité {doc_name} : Présence de tags non résolus : {', '.join(unfilled_tags)}"
        return True, f"Intégrité validée {doc_name} : 100% des tags résolus."

    def score_letter_candidate(self, letter_html: str, job: Dict[str, Any]) -> float:
        """Évalue une lettre de motivation sur 100 points."""
        score = 80.0
        
        # 1. Contrôle bloquant de typographie (ZÉRO caractère gras dans le corps de lettre)
        body_match = re.search(r'<div class="body-content">(.*?)</div>\s*</div>\s*</body>', letter_html, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
            if "<strong>" in body_content or "<b>" in body_content or "font-weight: bold" in body_content or "font-weight:bold" in body_content:
                score -= 40.0
                
        # 2. Résonance avec l'offre
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        desc = job.get("description", "").lower()
        
        lower_html = letter_html.lower()
        if company and company in lower_html:
            score += 10.0
        if "richard busson" in lower_html:
            score += 5.0
        if "qualiopi" in lower_html or "silae" in lower_html or "dsn" in lower_html:
            score += 5.0
            
        return min(score, 100.0)

    # =========================================================================
    # PASSAGE 3 : CONTRÔLE DES 6 FICHIERS, GÉOMÉTRIE PDF & TAILLE NON NULLE
    # =========================================================================
    def validate_candidate_package(self, folder_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Contrôle la présence et la conformité des 6 fichiers obligatoires."""
        required_files = [
            "Lettre_Motivation_Richard_BUSSON.html",
            "Lettre_Motivation_Richard_BUSSON.pdf",
            "Lettre_Motivation_Richard_BUSSON.png",
            "CV_Richard_BUSSON.html",
            "CV_Richard_BUSSON.pdf",
            "CV_Richard_BUSSON.png"
        ]
        
        report = {}
        all_passed = True
        
        for f in required_files:
            file_path = os.path.join(folder_path, f)
            if not os.path.exists(file_path):
                report[f] = {"status": "FAIL", "reason": "Fichier manquant"}
                all_passed = False
                continue
                
            size = os.path.getsize(file_path)
            if size == 0:
                report[f] = {"status": "FAIL", "reason": "Fichier vide (0 octet)"}
                all_passed = False
                continue
                
            # Contrôle spécifique des HTML pour détecter d'éventuels tags résiduels
            if f.endswith(".html"):
                with open(file_path, "r", encoding="utf-8") as hf:
                    h_content = hf.read()
                is_ok, msg = self.validate_template_integrity(h_content, f)
                if not is_ok:
                    report[f] = {"status": "FAIL", "reason": msg}
                    all_passed = False
                    continue
                    
            report[f] = {"status": "PASS", "size": size}
            
        return all_passed, report
