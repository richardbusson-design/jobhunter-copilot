# -*- coding: utf-8 -*-
import os
import sys
import unittest
import json
import re

# Ajouter src au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from quality_guard import QualityGuard
from application_generator import ApplicationGenerator

class TestJobHunterQualityGuard(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.guard = QualityGuard(config_dir=os.path.join(self.base_dir, "config"))
        self.generator = ApplicationGenerator(base_dir=self.base_dir)

    def test_salary_filter_rejection_below_30k(self):
        """Vérifie le rejet strict des offres avec salaire annuel inférieur à 30 000 €."""
        low_salary_job = {
            "title": "Assistant Paie",
            "company": "Entreprise X",
            "city": "Creil",
            "postal_code": "60100",
            "salary": "24 000 € brut annuel"
        }
        is_valid, reason = self.guard.validate_job_criteria(low_salary_job)
        self.assertFalse(is_valid, "Une offre < 30k€ doit être strictement rejetée.")
        self.assertIn("Salaire trop faible", reason)

    def test_salary_filter_acceptance_above_30k(self):
        """Vérifie l'acceptation des offres >= 30 000 €."""
        good_salary_job = {
            "title": "Formateur Gestionnaire de Paie",
            "company": "Afpa Beauvais",
            "city": "Beauvais",
            "postal_code": "60000",
            "salary": "36 000 € brut annuel"
        }
        is_valid, reason = self.guard.validate_job_criteria(good_salary_job)
        self.assertTrue(is_valid, f"Une offre >= 30k€ dans l'Oise doit être acceptée. Raison: {reason}")

    def test_geography_nearby_creil_accepted(self):
        """Vérifie l'acceptation des postes dans le bassin Creil / Oise / Île-de-France (<= 2h)."""
        paris_job = {
            "title": "Formateur RH",
            "company": "CFA Paris",
            "city": "Paris",
            "postal_code": "75010",
            "salary": "38 000 €"
        }
        is_valid, reason = self.guard.validate_job_criteria(paris_job)
        self.assertTrue(is_valid, "Paris est à moins de 2h de Creil et doit être accepté.")

    def test_geography_coastal_exception_accepted(self):
        """Vérifie l'acceptation de l'exception littorale (Atlantique / Méditerranée)."""
        bordeaux_job = {
            "title": "Coordinateur de formation",
            "company": "CMA Nouvelle-Aquitaine",
            "city": "Bordeaux",
            "postal_code": "33000",
            "salary": "40 000 €"
        }
        is_valid, reason = self.guard.validate_job_criteria(bordeaux_job)
        self.assertTrue(is_valid, "Bordeaux (façade Atlantique) doit être accepté par exception de mobilité.")

    def test_geography_far_non_coastal_rejected(self):
        """Vérifie le rejet des postes éloignés hors littoral."""
        strasbourg_job = {
            "title": "Formateur Paie",
            "company": "Centre Est",
            "city": "Strasbourg",
            "postal_code": "67000",
            "salary": "38 000 €"
        }
        is_valid, reason = self.guard.validate_job_criteria(strasbourg_job)
        self.assertFalse(is_valid, "Strasbourg (>2h de Creil et non littoral) doit être rejeté.")

    def test_letter_zero_bold_in_body(self):
        """Vérifie l'absence totale de balises grasses dans le corps de texte de la lettre."""
        test_job = {
            "title": "Formateur Paie et RH",
            "company": "Afpa Beauvais",
            "contact_name": "Monsieur le Directeur",
            "contact_title": "Directeur de Centre",
            "address_1": "34 rue de Tillé",
            "postal_code": "60000",
            "city": "BEAUVAIS"
        }
        rendered = self.generator.render_letter_html(test_job)
        is_ok, msg = self.guard.validate_html_letter(rendered)
        self.assertTrue(is_ok, f"La lettre doit être validée par le QualityGuard : {msg}")
        
        # Double vérification manuelle
        body_match = re.search(r'<div class="body-content">(.*?)</div>\s*</div>', rendered, re.DOTALL)
        self.assertIsNotNone(body_match)
        body_text = body_match.group(1)
        self.assertNotIn("<strong>", body_text)
        self.assertNotIn("<b>", body_text)
        self.assertNotIn("font-weight: bold", body_text)

    def test_cv_sections_integrity(self):
        """Vérifie la présence de toutes les sections clés sur le CV."""
        test_job = {"title": "Formateur en gestion de paie"}
        cv_html = self.generator.render_cv_html(test_job)
        is_ok, msg = self.guard.validate_html_cv(cv_html)
        self.assertTrue(is_ok, f"Le CV doit contenir les 7 sections : {msg}")

if __name__ == "__main__":
    unittest.main()
