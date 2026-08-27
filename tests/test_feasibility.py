# -*- coding: utf-8 -*-
import os
import sys
import unittest
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from quality_guard import QualityGuard
from application_generator import ApplicationGenerator
from job_searcher import JobSearcher
from pdf_compiler import compile_html_to_pdf

class TestJobHunterFeasibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.guard = QualityGuard(config_dir=os.path.join(cls.base_dir, "config"))
        cls.generator = ApplicationGenerator(base_dir=cls.base_dir)

    # ---------------------------------------------------------
    # TEST DE FAISABILITÉ 1 : Les 4 Catégories de Métiers Cibles
    # ---------------------------------------------------------
    def test_category_1_gestionnaire_paie(self):
        """Faisabilité Catégorie 1 : Gestionnaire de Paie / DSN."""
        job = {
            "title": "Spécialiste Paie et Déclarations Sociales (H/F)",
            "company": "Cabinet Conseil Social",
            "city": "Creil",
            "postal_code": "60100",
            "salary": "36 000 €",
            "description": "Production de 350 bulletins, DSN mensuelles, paramétrage Silae et contrôle d'audit de paie."
        }
        score = self.generator.evaluate_match(job)
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)
        self.assertGreaterEqual(score, 80)

    def test_category_2_responsable_rh(self):
        """Faisabilité Catégorie 2 : Responsable RH / Relations Sociales."""
        job = {
            "title": "Responsable des Ressources Humaines (H/F)",
            "company": "Groupe Régional 500 salariés",
            "city": "Compiègne",
            "postal_code": "60200",
            "salary": "45 000 €",
            "description": "Management des relations sociales, présidence CSE, droit social et politique de rémunération."
        }
        score = self.generator.evaluate_match(job)
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)
        self.assertGreaterEqual(score, 85)

    def test_category_3_formateur_paie(self):
        """Faisabilité Catégorie 3 : Formateur Gestionnaire de Paie Qualiopi."""
        job = {
            "title": "Formateur Titre Professionnel Gestionnaire de Paie (H/F)",
            "company": "Organisme Certifiant Qualiopi",
            "city": "Beauvais",
            "postal_code": "60000",
            "salary": "35 000 €",
            "description": "Animation du TP-01254, ingénierie pédagogique Métis, ECF et conformité RNQ."
        }
        score = self.generator.evaluate_match(job)
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)
        self.assertGreaterEqual(score, 90)

    def test_category_4_gestionnaire_rh(self):
        """Faisabilité Catégorie 4 : Gestionnaire / Chargé RH Senior."""
        job = {
            "title": "Chargé des Ressources Humaines Confirmé (H/F)",
            "company": "Institution Consulaire",
            "city": "Paris",
            "postal_code": "75008",
            "salary": "38 000 €",
            "description": "Gestion des contrats de travail, suivi disciplinaire, temps de travail et veille juridique."
        }
        score = self.generator.evaluate_match(job)
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)
        self.assertGreaterEqual(score, 80)

    # ---------------------------------------------------------
    # TEST DE FAISABILITÉ 2 : Exclusions Strictes (Débutants / Hors Cible)
    # ---------------------------------------------------------
    def test_exclusion_junior_et_debutant(self):
        """Rejet systématique des offres débutants."""
        job = {
            "title": "Assistant Paie Débutant",
            "company": "Cabinet X",
            "city": "Creil",
            "postal_code": "60100",
            "salary": "24 000 €" # < 30k€
        }
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertFalse(is_ok, "L'offre débutant sous le seuil de 30k€ doit être rejetée.")

    # ---------------------------------------------------------
    # TEST DE FAISABILITÉ 3 : Filtres Géographiques & Mobilité Littorale
    # ---------------------------------------------------------
    def test_geography_nearby_creil(self):
        """Acceptation dans le rayon <= 2h de Creil (Oise, IdF, Somme, Aisne)."""
        job = {"city": "Senlis", "postal_code": "60300", "salary": "35 000 €"}
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)

    def test_geography_coastal_atlantic_exception(self):
        """Acceptation de l'exception Façade Atlantique (Bordeaux, Nantes, La Rochelle, Bayonne)."""
        job = {"city": "La Rochelle", "postal_code": "17000", "salary": "37 000 €"}
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)

    def test_geography_coastal_mediterranean_exception(self):
        """Acceptation de l'exception Façade Méditerranée (Marseille, Montpellier, Nice)."""
        job = {"city": "Montpellier", "postal_code": "34000", "salary": "36 000 €"}
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)

    def test_geography_inland_far_rejection(self):
        """Rejet des zones éloignées non côtières (> 2h de Creil : ex: Lyon, Strasbourg, Clermont-Ferrand)."""
        job = {"city": "Clermont-Ferrand", "postal_code": "63000", "salary": "36 000 €"}
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertFalse(is_ok, "Clermont-Ferrand (> 2h et non littoral) doit être rejeté.")

    def test_geography_full_remote(self):
        """Acceptation automatique du 100% télétravail."""
        job = {"title": "Formateur Paie (Télétravail 100%)", "city": "Toute France", "postal_code": "00000", "salary": "38 000 €", "description": "Poste en distanciel intégral."}
        is_ok, reason = self.guard.validate_job_criteria(job)
        self.assertTrue(is_ok)

    # ---------------------------------------------------------
    # TEST DE FAISABILITÉ 4 : Rigueur Typographique & QualityGuard
    # ---------------------------------------------------------
    def test_qualityguard_zero_bold_enforcement(self):
        """Le QualityGuard doit bloquer immédiatement si du gras est injecté dans le corps."""
        fake_tampered_html = """
        <div class="body-content">
            <p>Madame, Monsieur,</p>
            <p>Voici un texte avec <strong>du gras interdit</strong> dans le corps.</p>
        </div></div>
        """
        is_ok, msg = self.guard.validate_html_letter(fake_tampered_html)
        self.assertFalse(is_ok, "Le QualityGuard doit détecter et rejeter le gras dans le corps de lettre.")

    def test_real_pdf_generation_single_page(self):
        """Vérifie que la compilation produit exactement 1 page A4."""
        test_job = {
            "title": "Formateur en gestion de paie et RH",
            "company": "Afpa Test Centre",
            "contact_name": "Monsieur le Directeur",
            "contact_title": "Directeur de Centre",
            "address_1": "34 rue de Tillé",
            "postal_code": "60000",
            "city": "BEAUVAIS"
        }
        letter_html = self.generator.render_letter_html(test_job)
        cv_html = self.generator.render_cv_html(test_job)
        
        temp_dir = os.path.join(self.base_dir, "tests", "temp_output")
        os.makedirs(temp_dir, exist_ok=True)
        
        l_html_path = os.path.join(temp_dir, "test_lettre.html")
        c_html_path = os.path.join(temp_dir, "test_cv.html")
        l_pdf_path = os.path.join(temp_dir, "test_lettre.pdf")
        c_pdf_path = os.path.join(temp_dir, "test_cv.pdf")
        
        with open(l_html_path, "w", encoding="utf-8") as f: f.write(letter_html)
        with open(c_html_path, "w", encoding="utf-8") as f: f.write(cv_html)
        
        compile_html_to_pdf(l_html_path, l_pdf_path)
        compile_html_to_pdf(c_html_path, c_pdf_path)
        
        is_l_ok, msg_l = self.guard.validate_pdf_page_count(l_pdf_path)
        is_c_ok, msg_c = self.guard.validate_pdf_page_count(c_pdf_path)
        
        self.assertTrue(is_l_ok, f"Lettre PDF : {msg_l}")
        self.assertTrue(is_c_ok, f"CV PDF : {msg_c}")

if __name__ == "__main__":
    unittest.main()
