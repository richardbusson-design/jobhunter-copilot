# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Tuple, List

from quality_guard import QualityGuard

class ApplicationGenerator:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.profile = self.load_profile()
        self.guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
        self.cv_template = self.load_template("templates/template_cv.html")
        self.letter_template = self.load_template("templates/template_lettre.html")

    def load_profile(self) -> Dict[str, Any]:
        profile_path = os.path.join(self.base_dir, "config", "profile.json")
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_template(self, relative_path: str) -> str:
        full_path = os.path.join(self.base_dir, relative_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def clean_job_title(self, raw_title: str) -> str:
        cleaned = re.sub(r'\(H/F\)|H/F|\(F/H\)|F/H', '', raw_title, flags=re.IGNORECASE)
        cleaned = cleaned.replace("/ Formatrice", "").replace("/ formatrice", "")
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def evaluate_match(self, job: Dict[str, Any]) -> int:
        text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
        score = 72
        
        # Reconnaissance des postes cibles clés (Nomenclature ROME)
        if "responsable rh et paie" in text or "responsable rh & paie" in text or ("responsable" in text and "paie" in text and "rh" in text):
            score += 16
        elif "formateur paie" in text or "formateur gestionnaire de paie" in text or ("formateur" in text and "rh" in text):
            score += 15
        elif "responsable paie" in text or "responsable des ressources humaines" in text or "rrh" in text:
            score += 14
        elif "gestionnaire de paie" in text or "gestionnaire paie" in text:
            score += 12
        elif "coordinateur" in text or "ingénieur pédagogique" in text:
            score += 12
            
        if "paie" in text or "bulletin" in text or "dsn" in text or "silae" in text:
            score += 6
        if "ressources humaines" in text or "relations sociales" in text or "droit social" in text or "cse" in text:
            score += 6

        tech_keywords = [
            "dsn", "silae", "titre professionnel", "qualiopi", "droit social", "droit du travail",
            "cse", "contrat", "contrats", "administration du personnel", "gestion du personnel",
            "masse salariale", "alternance", "cfa", "adea", "métis", "ecf"
        ]
        matched_tech = sum(1 for kw in tech_keywords if kw in text)
        score += min(matched_tech * 2, 12)
                
        return min(score, 98)

    def render_letter_variant(self, job: Dict[str, Any], variant_index: int) -> str:
        """Génère une variante spécifique de lettre de motivation (1, 2 ou 3)."""
        company = job.get("company", "Organisme")
        raw_title = job.get("title", "Formateur Paie et RH")
        job_title = self.clean_job_title(raw_title)
        
        contact_name = job.get("contact_name", "Madame, Monsieur les Membres du Jury")
        contact_title = job.get("contact_title", "Direction des Ressources Humaines")
        address_1 = job.get("address_1", "Service Recrutement & Pédagogie")
        address_2 = job.get("address_2", "")
        postal_code = job.get("postal_code", "60000")
        city = job.get("city", "BEAUVAIS").upper()

        if variant_index == 1:
            # AXE 1 : Ingénierie Pédagogique, Titre Pro TP-01254 & Conformité Qualiopi
            accr = f"Dirigeant d'organisme de formation certifié Qualiopi et formateur référent sur le Titre professionnel Gestionnaire de paie (TP-01254), je vous propose mon expertise pédagogique et technique pour accompagner vos apprenants au sein de {company} sur le poste de {job_title}."
            par1 = "Fort de la conception d'un parcours certifiant de 758 heures et de vacations régulières au sein des centres Afpa des Hauts-de-France (groupes individualisés, outil Métis, évaluations ECF), je transmets la pratique du bulletin de paie, la DSN, le paramétrage sur Silae et la rigueur du droit social avec une pédagogie axée sur l'employabilité immédiate."
            par2 = "Mon parcours conjugue la maîtrise des référentiels RNCP, l'animation des blocs RH/Paie de l'ADEA pour les Chambres de Métiers et une expérience managériale de 580 collaborateurs. Cette polyvalence garantit à vos promotions un encadrement bienveillant, structuré et conforme aux exigences Qualiopi."
            par3 = "Disponible sans délai et titulaire du permis B, je serais ravi d'échanger lors d'un entretien pour vous exposer la mise en œuvre opérationnelle de mes méthodes au service de vos stagiaires."
        elif variant_index == 2:
            # AXE 2 : Direction RH Opérationnelle, Relations Sociales & 580 Collaborateurs
            accr = f"Fort d'une solide expérience de Responsable des Ressources Humaines et de la Paie, enrichie par le pilotage social de 580 collaborateurs et la direction d'un organisme certifié Qualiopi, je vous soumets ma candidature pour le poste de {job_title} chez {company}."
            par1 = "Mon parcours m'a conduit à superviser l'administration du personnel, la sécurisation des paies complexes, les déclarations sociales et le dialogue avec les instances représentatives (CSE, CE, DP) dans des contextes à forts enjeux. Cette pratique concrète du terrain me permet d'aborder la fonction avec une vision stratégique et pragmatique."
            par2 = "Titulaire d'un Master 2 en Droit public, d'une Maîtrise en Sciences de Gestion et engagé dans un Master RSE à l'IAE de Paris, j'apporte à votre structure une expertise éprouvée des obligations légales, du pilotage de la masse salariale et du développement des compétences."
            par3 = "Totalement disponible et mobile, je me tiens à votre disposition pour vous détailler la valeur ajoutée et la rigueur que je peux apporter immédiatement à vos équipes."
        else:
            # AXE 3 : Conseil Social, Audit de Paie & Accompagnement Métiers du Chiffre
            accr = f"Formateur expert en droit social, gestion de la paie et ressources humaines, je souhaite mettre mes compétences techniques et mon sens du conseil au service du développement de {company} en qualité de {job_title}."
            par1 = "Intervenant auprès de chefs d'entreprise, d'experts-comptables et de gestionnaires en reconversion, j'ai développé une méthode rigoureuse d'audit de paie, de contrôle DSN et de veille juridique continue, garantissant une conformité sociale irréprochable."
            par2 = "Mon expérience auprès de publics diversifiés (Afpa, CMA, TPE-PME) et ma maîtrise avancée des outils du chiffre (Silae, Excel, Métis) constituent des atouts majeurs pour structurer vos missions et assurer un encadrement de haut niveau."
            par3 = "Je serais très honoré de convenir d'une rencontre pour vous exposer mon engagement durable et mon enthousiasme à rejoindre votre organisation."

        html = self.letter_template
        html = html.replace("{{COMPANY_NAME}}", company)
        html = html.replace("{{CONTACT_NAME}}", contact_name)
        html = html.replace("{{CONTACT_TITLE}}", contact_title)
        html = html.replace("{{ADDRESS_LINE1}}", address_1)
        html = html.replace("{{ADDRESS_LINE2}}", address_2)
        html = html.replace("{{POSTAL_CODE}}", postal_code)
        html = html.replace("{{CITY}}", city)
        html = html.replace("{{DATE_NOW}}", datetime.now().strftime("%d %B %Y").replace("August", "août").replace("September", "septembre"))
        html = html.replace("{{JOB_TITLE}}", job_title)
        html = html.replace("{{ACCROCHE}}", accr)
        html = html.replace("{{PARAGRAPH_1}}", par1)
        html = html.replace("{{PARAGRAPH_2}}", par2)
        html = html.replace("{{PARAGRAPH_3}}", par3)
        
        return html

    def generate_best_of_three_letter(self, job: Dict[str, Any]) -> Tuple[str, float, int]:
        """Génère 3 variantes, les évalue avec le QualityGuard et retient la meilleure."""
        scored_variants = []
        for i in range(1, 4):
            candidate_html = self.render_letter_variant(job, variant_index=i)
            score = self.guard.score_letter_candidate(candidate_html, job)
            scored_variants.append((candidate_html, score, i))
            
        scored_variants.sort(key=lambda x: x[1], reverse=True)
        best_html, best_score, best_idx = scored_variants[0]
        return best_html, best_score, best_idx

    def render_cv_html(self, job: Dict[str, Any]) -> str:
        raw_title = job.get("title", "Formateur Paie et RH")
        job_title = self.clean_job_title(raw_title).upper()
        
        html = self.cv_template
        html = html.replace("{{CV_TITLE}}", f"EXPERT PAIE, RESSOURCES HUMAINES & FORMATION — {job_title}")
        html = html.replace("{{TARGET_POSTE_KEY}}", job_title)
        return html

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        best_html, _, _ = self.generate_best_of_three_letter(job)
        return best_html
