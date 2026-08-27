# -*- coding: utf-8 -*-
import os
import sys
import unittest
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from quality_guard import QualityGuard
from application_generator import ApplicationGenerator

class TestJobHunterQualityGuard(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.guard = QualityGuard(config_dir=os.path.join(self.base_dir, "config"))
        self.generator = ApplicationGenerator(base_dir=self.base_dir)

    def test_three_trials_tournament_selection(self):
        """Vérifie que la procédure à 3 essais génère 3 variantes et sélectionne la meilleure."""
        test_job = {
            "title": "Formateur en gestion de paie et RH",
            "company": "Afpa Normandie",
            "contact_name": "Monsieur le Directeur",
            "contact_title": "Direction du Centre",
            "address_1": "Rue de la République",
            "postal_code": "76000",
            "city": "ROUEN",
            "description": "Animation Titre pro Gestionnaire de paie, outil Métis, Silae et ECF."
        }
        best_html, best_score, best_idx = self.generator.generate_best_of_three_letter(test_job)
        self.assertIn(best_idx, [1, 2, 3])
        self.assertGreaterEqual(best_score, 80.0)
        
        # Vérification de conformité stricte de la version retenue
        is_ok, msg = self.guard.validate_html_letter(best_html)
        self.assertTrue(is_ok, f"La meilleure variante retenue doit être 100% conforme : {msg}")

    def test_salary_filter_rejection_below_30k(self):
        low_salary_job = {"title": "Assistant Paie", "city": "Creil", "postal_code": "60100", "salary": "24 000 €"}
        is_valid, reason = self.guard.validate_job_criteria(low_salary_job)
        self.assertFalse(is_valid)

    def test_salary_filter_acceptance_above_30k(self):
        good_salary_job = {"title": "Formateur Paie", "city": "Beauvais", "postal_code": "60000", "salary": "36 000 €"}
        is_valid, reason = self.guard.validate_job_criteria(good_salary_job)
        self.assertTrue(is_valid)

    def test_letter_zero_bold_in_body(self):
        test_job = {"title": "Formateur Paie et RH", "company": "Afpa", "postal_code": "60000", "city": "BEAUVAIS"}
        rendered = self.generator.render_letter_html(test_job)
        is_ok, msg = self.guard.validate_html_letter(rendered)
        self.assertTrue(is_ok)

    def test_cv_sections_integrity(self):
        test_job = {"title": "Formateur en gestion de paie"}
        cv_html = self.generator.render_cv_html(test_job)
        is_ok, msg = self.guard.validate_html_cv(cv_html)
        self.assertTrue(is_ok)

if __name__ == "__main__":
    unittest.main()
