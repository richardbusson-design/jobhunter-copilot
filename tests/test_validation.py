# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from quality_guard import QualityGuard
from application_generator import ApplicationGenerator
from pdf_compiler import compile_html_to_pdf

class TestJobHunterQualityGuard(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.guard = QualityGuard(config_dir=os.path.join(self.base_dir, "config"))
        self.generator = ApplicationGenerator(base_dir=self.base_dir)

    def test_three_pass_audit_complete_success(self):
        """Vérifie l'exécution rigoureuse de la procédure de contrôle aux 3 passages."""
        test_job = {
            "title": "Formateur en gestion de paie et RH",
            "company": "Afpa Normandie",
            "contact_name": "Monsieur le Directeur",
            "contact_title": "Direction du Centre",
            "address_1": "Rue de la République",
            "postal_code": "76000",
            "city": "ROUEN",
            "salary": "35 000 €",
            "description": "Animation Titre pro Gestionnaire de paie, outil Métis, Silae et ECF."
        }
        
        # 1. Rendu
        letter_html = self.generator.render_letter_html(test_job)
        cv_html = self.generator.render_cv_html(test_job)
        
        # 2. Compilation
        temp_dir = os.path.join(self.base_dir, "tests", "temp_output")
        os.makedirs(temp_dir, exist_ok=True)
        l_html_path = os.path.join(temp_dir, "audit_lettre.html")
        c_html_path = os.path.join(temp_dir, "audit_cv.html")
        l_pdf_path = os.path.join(temp_dir, "audit_lettre.pdf")
        c_pdf_path = os.path.join(temp_dir, "audit_cv.pdf")
        
        with open(l_html_path, "w", encoding="utf-8") as f: f.write(letter_html)
        with open(c_html_path, "w", encoding="utf-8") as f: f.write(cv_html)
        
        compile_html_to_pdf(l_html_path, l_pdf_path)
        compile_html_to_pdf(c_html_path, c_pdf_path)
        
        # 3. Exécution de l'audit aux 3 passages
        is_valid, audit_logs = self.guard.execute_three_pass_audit(test_job, letter_html, cv_html, l_pdf_path, c_pdf_path)
        self.assertTrue(is_valid, f"L'audit aux 3 passages a échoué : {audit_logs}")
        self.assertEqual(len(audit_logs), 3)

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
