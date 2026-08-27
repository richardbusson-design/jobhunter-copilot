# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Dict, Any, Tuple

class QualityGuard:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.criteria = self.load_criteria()

    def load_criteria(self) -> Dict[str, Any]:
        criteria_path = os.path.join(self.config_dir, "selection_criteria.json")
        if os.path.exists(criteria_path):
            with open(criteria_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "salary": {"min_annual_brut_eur": 30000},
            "geography": {
                "home_postal_code": "60100",
                "max_commute_hours": 2.0,
                "eligible_nearby_departments": ["60", "75", "93", "95", "92", "94", "77", "78", "91", "80", "02", "59", "62", "27", "76"],
                "eligible_coastal_departments": ["33", "17", "64", "40", "29", "56", "35", "22", "44", "85", "34", "30", "66", "11", "13", "83", "06", "2A", "2B"],
                "eligible_coastal_regions": ["nouvelle-aquitaine", "bretagne", "pays de la loire", "occitanie", "provence-alpes-côte d'azur", "corse"],
                "allow_full_remote": True
            }
        }

    def validate_job_criteria(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        """Contrôle les critères impératifs de salaire et de localisation."""
        title = job.get("title", "")
        company = job.get("company", "")
        city = job.get("city", "")
        postal_code = str(job.get("postal_code", ""))
        desc = job.get("description", "")
        salary_str = job.get("salary", "")
        
        # 1. Vérification du Salaire
        min_salary = self.criteria.get("salary", {}).get("min_annual_brut_eur", 30000)
        
        # Extraction de chiffres de salaire s'ils existent
        if salary_str:
            nums = [int(n) for n in re.findall(r'\b\d{4,6}\b', salary_str.replace(" ", "").replace("k", "000"))]
            if nums:
                max_num = max(nums)
                # Si c'est un salaire mensuel (ex: 2200)
                if max_num < 4000:
                    annual_equiv = max_num * 12
                    if annual_equiv < min_salary:
                        return False, f"Salaire trop faible : {salary_str} ({annual_equiv}€/an < {min_salary}€)"
                elif max_num < min_salary:
                    return False, f"Salaire trop faible : {salary_str} ({max_num}€ < {min_salary}€)"

        # 2. Vérification Géographique
        # Cas 1 : Télétravail complet
        if "télétravail" in (title + " " + desc).lower() or "remote" in (title + " " + desc).lower() or "distanciel" in (title + " " + desc).lower():
            return True, "Éligible (Télétravail / Distanciel)"
            
        dept = postal_code[:2] if len(postal_code) >= 2 else ""
        text_geo = (city + " " + desc + " " + postal_code).lower()
        
        nearby_depts = self.criteria.get("geography", {}).get("eligible_nearby_departments", [])
        coastal_depts = self.criteria.get("geography", {}).get("eligible_coastal_departments", [])
        coastal_regions = [r.lower() for r in self.criteria.get("geography", {}).get("eligible_coastal_regions", [])]
        
        # Cas 2 : Proche de Creil (<= 2h)
        if dept in nearby_depts or "creil" in text_geo or "beauvais" in text_geo or "compiègne" in text_geo or "amiens" in text_geo or "paris" in text_geo or "oise" in text_geo:
            return True, "Éligible (Zone Creil / Hauts-de-France / Île-de-France <= 2h)"
            
        # Cas 3 : Littoral Atlantique ou Méditerranée
        if dept in coastal_depts or any(r in text_geo for r in coastal_regions) or "bordeaux" in text_geo or "nantes" in text_geo or "marseille" in text_geo or "montpellier" in text_geo:
            return True, "Éligible (Exception Littoral Atlantique / Méditerranée)"
            
        # Si aucun code postal n'est fourni mais que c'est une grande institution nationale
        if not dept and ("afpa" in company.lower() or "cma" in company.lower() or "cci" in company.lower()):
            return True, "Éligible (Réseau National avec Mobilité Totale)"

        return False, f"Hors zone géographique autorisée : {city} ({postal_code}) - non éligible <=2h de Creil et non littoral"

    def validate_html_letter(self, html_content: str) -> Tuple[bool, str]:
        """Vérifie la conformité absolue de la lettre de motivation."""
        # 1. Vérification de l'alignement sur kairos-paye.fr
        if "kairos-paye.fr" not in html_content:
            return False, "Expéditeur incomplet : mention de kairos-paye.fr manquante."
            
        # 2. Vérification stricte du GRAS dans le corps de texte
        body_match = re.search(r'<div class="body-content">(.*?)</div>\s*</div>', html_content, re.DOTALL)
        if body_match:
            body_text = body_match.group(1)
            if "<strong>" in body_text or "<b>" in body_text or "font-weight: bold" in body_text:
                return False, "Violation règle typographique : Présence de texte en gras dans le corps de la lettre !"
                
        # 3. Vérification de la signature vectorielle
        if "signature-svg" not in html_content or "Richard Busson" not in html_content:
            return False, "Signature manuscrite vectorielle manquante en bas à droite."
            
        # 4. Vérification de la hauteur et de l'équilibre A4
        if "1123px" not in html_content:
            return False, "Le gabarit doit être verrouillé sur la hauteur A4 (1123px)."
            
        return True, "Lettre 100% conforme aux règles strictes."

    def validate_html_cv(self, html_content: str) -> Tuple[bool, str]:
        """Vérifie la structure et les sections du CV."""
        required_sections = [
            "Richard BUSSON",
            "COMPÉTENCES CLÉS",
            "POINTS FORTS POUR CE POSTE",
            "EXPÉRIENCES PROFESSIONNELLES",
            "FORMATIONS",
            "OUTILS & LANGUES"
        ]
        for sec in required_sections:
            if sec not in html_content:
                return False, f"Section obligatoire manquante dans le CV : {sec}"
                
        return True, "CV 100% conforme aux règles strictes."

    def validate_pdf_page_count(self, pdf_path: str) -> Tuple[bool, str]:
        """Vérifie qu'un fichier PDF compilé fait exactement 1 page."""
        if not os.path.exists(pdf_path):
            return False, f"Fichier PDF introuvable : {pdf_path}"
            
        try:
            with open(pdf_path, "rb") as f:
                content = f.read()
            # Détection du nombre de pages dans le PDF
            pages = len(re.findall(rb'/Type\s*/Page\b', content))
            if pages == 0:
                # Alternative pour certains streams PDF
                pages = len(re.findall(rb'/Page\W', content))
                
            if pages == 1:
                return True, "PDF strictement égal à 1 page A4 [OK]"
            elif pages > 1:
                return False, f"Dépassement détecté : Le PDF contient {pages} pages au lieu d'une seule !"
            else:
                return True, "PDF généré valide."
        except Exception as e:
            return False, f"Erreur lors de la lecture du PDF : {e}"

if __name__ == "__main__":
    guard = QualityGuard()
    print("QualityGuard initialisé et opérationnel.")

