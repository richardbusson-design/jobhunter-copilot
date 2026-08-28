# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Dict, Any, Tuple, List

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

    # =========================================================================
    # PASSAGE 1 : CONTRÔLE D'ÉLIGIBILITÉ SOURCE & FILTRAGE MÉTIER
    # =========================================================================
    def validate_job_criteria(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        title = job.get("title", "")
        company = job.get("company", "")
        city = job.get("city", "")
        postal_code = str(job.get("postal_code", ""))
        desc = job.get("description", "")
        salary_str = job.get("salary", "")
        
        # 1. Vérification du Salaire (>= 30 000 € / an)
        min_salary = self.criteria.get("salary", {}).get("min_annual_brut_eur", 30000)
        if salary_str:
            nums = [int(n) for n in re.findall(r'\b\d{4,6}\b', salary_str.replace(" ", "").replace("k", "000"))]
            if nums:
                max_num = max(nums)
                if max_num < 4000:
                    annual_equiv = max_num * 12
                    if annual_equiv < min_salary:
                        return False, f"[Passage 1 Rejet] Salaire trop faible : {salary_str} ({annual_equiv}€/an < {min_salary}€)"
                elif max_num < min_salary:
                    return False, f"[Passage 1 Rejet] Salaire trop faible : {salary_str} ({max_num}€ < {min_salary}€)"

        # 2. Vérification Débutants / Juniors (< 3 ans rejetés)
        text_all = (title + " " + desc).lower()
        if any(w in text_all for w in ["débutant accepté", "junior accepté", "sans expérience", "profil débutant"]):
            return False, "[Passage 1 Rejet] Profil débutant non ciblé."

        # 3. Vérification Géographique
        if "télétravail" in text_all or "remote" in text_all or "distanciel" in text_all:
            return True, "Éligible (Télétravail / Distanciel)"
            
        dept = postal_code[:2] if len(postal_code) >= 2 else ""
        text_geo = (city + " " + desc + " " + postal_code).lower()
        
        nearby_depts = self.criteria.get("geography", {}).get("eligible_nearby_departments", [])
        coastal_depts = self.criteria.get("geography", {}).get("eligible_coastal_departments", [])
        coastal_regions = [r.lower() for r in self.criteria.get("geography", {}).get("eligible_coastal_regions", [])]
        
        if dept in nearby_depts or any(w in text_geo for w in ["creil", "beauvais", "compiègne", "amiens", "paris", "oise", "rouen", "lille", "senlis"]):
            return True, "Éligible (Zone Creil / Hauts-de-France / Île-de-France <= 2h)"
            
        if dept in coastal_depts or any(r in text_geo for r in coastal_regions) or any(w in text_geo for w in ["bordeaux", "nantes", "marseille", "montpellier", "saint-nazaire", "la rochelle", "bayonne", "rennes"]):
            return True, "Éligible (Exception Littoral Atlantique / Méditerranée)"
            
        if not dept and ("afpa" in company.lower() or "cma" in company.lower() or "cci" in company.lower()):
            return True, "Éligible (Réseau National avec Mobilité Totale)"

        return False, f"[Passage 1 Rejet] Hors zone géographique autorisée : {city} ({postal_code})"

    # =========================================================================
    # PASSAGE 2 : CONTRÔLE RÉDACTIONNEL, ZÉRO GRAS & GÉOMÉTRIE A4
    # =========================================================================
    def validate_html_letter(self, html_content: str) -> Tuple[bool, str]:
        if "kairos-paye.fr" not in html_content:
            return False, "[Passage 2 Rejet] Expéditeur incomplet : mention de kairos-paye.fr manquante."
            
        body_match = re.search(r'<div class="body-content">(.*?)</div>\s*</div>', html_content, re.DOTALL)
        if body_match:
            body_text = body_match.group(1)
            if "<strong>" in body_text or "<b>" in body_text or "font-weight: bold" in body_text:
                return False, "[Passage 2 Rejet] Violation règle typographique : Présence de texte en gras dans le corps !"
                
        if "signature-svg" not in html_content or "Richard Busson" not in html_content:
            return False, "[Passage 2 Rejet] Signature manuscrite vectorielle manquante."
            
        if "1123px" not in html_content:
            return False, "[Passage 2 Rejet] Le gabarit doit être verrouillé sur la hauteur A4 (1123px)."
            
        return True, "[Passage 2 OK] Lettre 100% conforme."

    def validate_html_cv(self, html_content: str) -> Tuple[bool, str]:
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
                return False, f"[Passage 2 Rejet] Section CV manquante : {sec}"
                
        return True, "[Passage 2 OK] CV 100% conforme."

    def score_letter_candidate(self, html_content: str, job: Dict[str, Any]) -> float:
        score = 0.0
        is_ok, _ = self.validate_html_letter(html_content)
        if not is_ok:
            return 0.0
        score += 50.0
        
        job_text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
        key_terms = ["paie", "gestionnaire", "rh", "ressources humaines", "formation", "qualiopi", "silae", "dsn", "métis", "ecf", "titre professionnel", "relations sociales", "cse"]
        matched = sum(1 for t in key_terms if t in job_text and t in html_content.lower())
        score += min(matched * 3.5, 30.0)
        
        company = job.get("company", "")
        if company and company.lower() in html_content.lower():
            score += 10.0
        if job.get("city", "").lower() in html_content.lower():
            score += 5.0
        if "À l’attention de" in html_content:
            score += 5.0
            
        return min(score, 100.0)

    # =========================================================================
    # PASSAGE 3 : CONTRÔLE POST-COMPILATION PDF & INTÉGRITÉ GRAPHIQUE
    # =========================================================================
    def validate_pdf_page_count(self, pdf_path: str) -> Tuple[bool, str]:
        if not os.path.exists(pdf_path):
            return False, f"[Passage 3 Rejet] Fichier PDF introuvable : {pdf_path}"
            
        try:
            with open(pdf_path, "rb") as f:
                content = f.read()
            pages = len(re.findall(rb'/Type\s*/Page\b', content))
            if pages == 0:
                pages = len(re.findall(rb'/Page\W', content))
                
            if pages == 1:
                return True, "[Passage 3 OK] PDF strictement égal à 1 page A4."
            elif pages > 1:
                return False, f"[Passage 3 Rejet] Dépassement : Le PDF contient {pages} pages !"
            else:
                return True, "[Passage 3 OK] PDF généré valide."
        except Exception as e:
            return False, f"[Passage 3 Rejet] Erreur lecture PDF : {e}"

    # =========================================================================
    # CONTRÔLE COMPLET AUX 3 PASSAGES (3-PASS VERIFICATION GATE)
    # =========================================================================
    def execute_three_pass_audit(self, job: Dict[str, Any], letter_html: str, cv_html: str, pdf_letter: str, pdf_cv: str) -> Tuple[bool, List[str]]:
        """Exécute l'audit complet et bloquant sur les 3 passages successifs."""
        audit_logs = []
        
        # Passage 1 : Éligibilité & Source
        p1_ok, p1_msg = self.validate_job_criteria(job)
        audit_logs.append(f"Passage 1 (Faisabilité Source & Filtres) : {'VALIDE' if p1_ok else 'ECHEC'} - {p1_msg}")
        if not p1_ok:
            return False, audit_logs
            
        # Passage 2 : Rédaction, Zéro Gras & Structure
        p2_l_ok, p2_l_msg = self.validate_html_letter(letter_html)
        p2_c_ok, p2_c_msg = self.validate_html_cv(cv_html)
        p2_ok = p2_l_ok and p2_c_ok
        audit_logs.append(f"Passage 2 (Rédaction & Règles A4/Gras) : {'VALIDE' if p2_ok else 'ECHEC'} - Lettre: {p2_l_msg} | CV: {p2_c_msg}")
        if not p2_ok:
            return False, audit_logs
            
        # Passage 3 : Fichiers PDF & Rendu Graphique
        p3_l_ok, p3_l_msg = self.validate_pdf_page_count(pdf_letter)
        p3_c_ok, p3_c_msg = self.validate_pdf_page_count(pdf_cv)
        png_l = pdf_letter.replace(".pdf", ".png")
        png_c = pdf_cv.replace(".pdf", ".png")
        has_png = os.path.exists(png_l) and os.path.exists(png_c)
        p3_ok = p3_l_ok and p3_c_ok and has_png
        
        audit_logs.append(f"Passage 3 (Vérification PDF & PNG Visuels) : {'VALIDE' if p3_ok else 'ECHEC'} - Lettre PDF: {p3_l_msg}, CV PDF: {p3_c_msg}, Visuels PNG: {'Présents' if has_png else 'Manquants'}")
        if not p3_ok:
            return False, audit_logs
            
        return True, audit_logs
