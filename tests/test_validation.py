# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from quality_guard import QualityGuard
from application_generator import ApplicationGenerator
from dashboard_manager import DashboardManager

class TestJobHunterQualityGuard(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.guard = QualityGuard(config_dir=os.path.join(self.base_dir, "config"))
        self.generator = ApplicationGenerator(base_dir=self.base_dir)
        self.dashboard = DashboardManager(base_dir=self.base_dir)

    def test_anti_duplicate_detection(self):
        """Vérifie que le système détecte et bloque strictement les doublons (ID, URL, Société+Titre)."""
        fps = {
            "ids": {"FT-2026-AFPA-ROUEN", "APEC-1758924W"},
            "urls": {"https://candidat.francetravail.fr/offres/detail/189TXWB"},
            "company_titles": {"afpa normandie___formateur gestionnaire de paie"},
            "total_count": 2
        }
        
        # Cas 1 : Même ID -> DOIT ÊTRE BLOQUÉ
        dup_job_id = {"id": "FT-2026-AFPA-ROUEN", "company": "Autre", "title": "Autre"}
        is_dup, reason = self.dashboard.is_duplicate(dup_job_id, fps)
        self.assertTrue(is_dup, "Un ID déjà présent doit être détecté comme doublon.")
        
        # Cas 2 : Même Société + Titre -> DOIT ÊTRE BLOQUÉ
        dup_job_ct = {"id": "NOUVEAU-ID", "company": "Afpa Normandie (Centre de Rouen)", "title": "Formateur / Formatrice Gestionnaire de paie (H/F)"}
        is_dup, reason = self.dashboard.is_duplicate(dup_job_ct, fps)
        self.assertTrue(is_dup, "Une offre avec même société et titre doit être bloquée.")
        
        # Cas 3 : Offre totalement nouvelle -> DOIT ÊTRE ACCEPTÉE
        new_job = {"id": "FT-NOUVEAU-999", "company": "Cabinet Conseil RH", "title": "Responsable des Ressources Humaines"}
        is_dup, reason = self.dashboard.is_duplicate(new_job, fps)
        self.assertFalse(is_dup, "Une nouvelle offre inédite ne doit pas être bloquée.")

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
