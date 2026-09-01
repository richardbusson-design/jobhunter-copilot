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

    def detect_category(self, job: Dict[str, Any]) -> str:
        text = (job.get("title", "") + " " + job.get("description", "")).lower()
        if "formateur" in text or "formatrice" in text or "pédagogique" in text or "coordinateur de formation" in text:
            return "FORMATEUR_PAIE_RH"
        elif "responsable rh" in text or "responsable des ressources" in text or "rrh" in text or "responsable du développement rh" in text or "responsable paie" in text:
            return "RRH_PAIE"
        elif "chargé rh" in text or "chargé des ressources" in text or "gestionnaire rh" in text or "gestionnaire adp" in text:
            return "GESTIONNAIRE_RH"
        elif "collaborateur comptable" in text or "comptable" in text or "cabinet" in text:
            return "COMPTABILITE_SOCIALE"
        else:
            return "GESTIONNAIRE_PAIE"

    def evaluate_match(self, job: Dict[str, Any]) -> int:
        text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
        score = 72
        
        cat = self.detect_category(job)
        if cat == "RRH_PAIE":
            score += 18
        elif cat == "FORMATEUR_PAIE_RH":
            score += 18
        elif cat == "GESTIONNAIRE_PAIE":
            score += 15
        elif cat == "GESTIONNAIRE_RH":
            score += 14
        elif cat == "COMPTABILITE_SOCIALE":
            score += 10
            
        if "paie" in text or "bulletin" in text or "dsn" in text or "silae" in text:
            score += 4
        if "ressources humaines" in text or "relations sociales" in text or "droit social" in text or "cse" in text:
            score += 4

        tech_keywords = [
            "dsn", "silae", "titre professionnel", "qualiopi", "droit social", "droit du travail",
            "cse", "contrat", "contrats", "administration du personnel", "gestion du personnel",
            "masse salariale", "alternance", "cfa", "adea", "métis", "ecf"
        ]
        matched_tech = sum(1 for kw in tech_keywords if kw in text)
        score += min(matched_tech * 2, 8)
                
        return min(score, 98)

    def render_letter_variant(self, job: Dict[str, Any], variant_index: int) -> str:
        company = job.get("company", "Organisme").replace('"', '')
        raw_title = job.get("title", "Poste RH & Paie")
        job_title = self.clean_job_title(raw_title)
        
        contact_name = job.get("contact_name", "Monsieur le Responsable du Recrutement")
        contact_title = job.get("contact_title", "Direction des Ressources Humaines")
        contact_full = f"{contact_name}, {contact_title}" if contact_title else contact_name
        address_1 = job.get("address_1", "Service Recrutement & RH")
        postal_code = job.get("postal_code", "60000")
        city = job.get("city", "CREIL").upper()
        current_date = datetime.now().strftime("%d %B %Y").replace("August", "août").replace("September", "septembre")

        cat = self.detect_category(job)

        # Génération des 3 variantes dynamiques selon la catégorie réelle du poste
        if cat == "FORMATEUR_PAIE_RH":
            p1 = f"Votre recherche pour le poste de {job_title} au sein de {company} retient toute mon attention. Dirigeant d'un organisme de formation certifié Qualiopi et formateur référent sur la filière Paie et Ressources Humaines, je vous propose mon expertise pédagogique et technique pour accompagner vos apprenants vers une employabilité immédiate."
            p2 = "Fort de la conception d'un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie (TP-01254 millésime 04) et de vacations régulières au sein des centres Afpa des Hauts-de-France (groupes individualisés, outil Métis, évaluations ECF), je transmets la pratique du bulletin de paie, la DSN, le paramétrage sur Silae et la rigueur du droit social avec une méthodologie structurée."
            p3 = "Mon parcours conjugue l'animation certifiante (blocs RH/Paie de l'ADEA, Brevet de Maîtrise) et la direction opérationnelle des ressources humaines de 580 collaborateurs. Cette double compétence me permet d'apporter aux apprenants des cas pratiques concrets issus du monde de l'entreprise, dans le respect rigoureux des exigences Qualiopi."
            p4 = "J'ai 59 ans : je recherche un engagement professionnel durable et stable. Disponible immédiatement et titulaire du permis B avec mobilité nationale, je serais ravi d'échanger avec vous lors d'un entretien pour vous détailler mon implication au service de vos promotions."
        elif cat == "RRH_PAIE":
            p1 = f"Votre offre pour le poste de {job_title} au sein de {company} correspond parfaitement à mon parcours et à mes compétences. Fort d'une solide expérience de Responsable des Ressources Humaines et de la Paie, j'ai piloté l'ensemble des dimensions sociales, administratives et juridiques au service de la performance de l'organisation."
            p2 = "De 2003 à 2010, j'ai dirigé les ressources humaines d'une structure de 580 collaborateurs (salariés et bénévoles), supervisant l'administration du personnel, la sécurisation des paies complexes, les déclarations dématérialisées (DSN) et le dialogue social avec les instances représentatives (CSE, CE, DP) dans des contextes à forts enjeux."
            p3 = "Titulaire d'un Master 2 en Droit public, d'une Maîtrise en Sciences de Gestion et engagé dans un Master RSE à l'IAE de Paris, j'apporte à votre entreprise une maîtrise rigoureuse de la réglementation du travail, de l'audit de paie et du pilotage de la masse salariale. Ma double casquette de dirigeant d'organisme de formation garantit également un accompagnement de haut niveau sur le développement des compétences."
            p4 = "À 59 ans, j'offre une stabilité professionnelle exemplaire et je m'inscris dans un engagement durable. Mon recrutement est par ailleurs éligible aux aides à l'embauche pour demandeur d'emploi senior. Totalement disponible et mobile, je me tiens à votre disposition pour convenir d'une rencontre."
        elif cat == "COMPTABILITE_SOCIALE":
            p1 = f"C'est avec un grand intérêt que je vous soumets ma candidature au poste de {job_title} chez {company}. Spécialiste de la paie, du droit social et de la gestion comptable sociale, je souhaite mettre ma rigueur et mon autonomie au service de votre structure et de vos clients."
            p2 = "Habitué à gérer des portefeuilles multi-conventions et des problématiques sociales variées, j'assure la production complète des bulletins de paie, les déclarations sociales nominatives (DSN), les soldes de tout compte et le suivi des contrats de travail dans le strict respect de la législation en vigueur."
            p3 = "Ma pratique approfondie des logiciels spécialisés (Silae, Excel avancé) et ma formation supérieure en gestion (Maîtrise Sciences de Gestion, Master 2 Droit public) me permettent de réaliser des audits de paie fiables et d'apporter un conseil éclairé aux chefs d'entreprise et managers opérationnels."
            p4 = "Rigoureux, loyal et disponible sans délai, je recherche un engagement professionnel pérenne. Je serais honoré de convenir d'un rendez-vous pour vous exposer la valeur ajoutée que je peux apporter immédiatement à votre équipe."
        else: # GESTIONNAIRE_PAIE & GESTIONNAIRE_RH
            p1 = f"Votre recherche pour le poste de {job_title} au sein de {company} retient toute mon attention. Expert de la gestion de la paie et de l'administration du personnel, je vous propose mon autonomie opérationnelle pour sécuriser l'ensemble de vos cycles de paie et vos déclarations sociales."
            p2 = "De la collecte des éléments variables jusqu'au contrôle DSN et aux relations avec les organismes sociaux (Urssaf, caisses de retraite, prévoyance), je maîtrise chaque étape du processus de paie. Mon expertise couvre le paramétrage sur logiciel Silae, le traitement des entrées/sorties et l'application stricte des conventions collectives."
            p3 = "Mon parcours allie une pratique confirmée de la paie en entreprise (direction RH de 580 collaborateurs) et une expertise d'ingénierie reconnue (conception d'un parcours de 758 heures pour le Titre professionnel Gestionnaire de paie). Cette rigueur technique garantit une conformité sociale irréprochable et un climat social apaisé."
            p4 = "Disponible immédiatement et titulaire du permis B, je recherche une collaboration durable au sein de laquelle mettre à profit mon sérieux et mon expertise. Je me tiens à votre entière disposition pour un entretien."

        # Rendu des paragraphes HTML (ZÉRO GRAS)
        paragraphs_html = f"<p>{p1}</p>\n<p>{p2}</p>\n<p>{p3}</p>\n<p>{p4}</p>"

        html = self.letter_template
        html = html.replace("{{CONTACT_FULL}}", contact_full)
        html = html.replace("{{COMPANY_NAME}}", company)
        html = html.replace("{{ADDRESS_1}}", address_1)
        html = html.replace("{{POSTAL_CODE}}", postal_code)
        html = html.replace("{{CITY}}", city)
        html = html.replace("{{CURRENT_DATE}}", current_date)
        html = html.replace("{{JOB_TITLE_CLEAN}}", job_title)
        html = html.replace("{{PARAGRAPHS_HTML}}", paragraphs_html)
        
        return html

    def generate_best_of_three_letter(self, job: Dict[str, Any]) -> Tuple[str, float, int]:
        scored_variants = []
        for i in range(1, 4):
            candidate_html = self.render_letter_variant(job, variant_index=i)
            score = self.guard.score_letter_candidate(candidate_html, job)
            scored_variants.append((candidate_html, score, i))
            
        scored_variants.sort(key=lambda x: x[1], reverse=True)
        best_html, best_score, best_idx = scored_variants[0]
        return best_html, best_score, best_idx

    def render_cv_html(self, job: Dict[str, Any]) -> str:
        raw_title = job.get("title", "Poste RH & Paie")
        job_title = self.clean_job_title(raw_title)
        cat = self.detect_category(job)

        if cat == "FORMATEUR_PAIE_RH":
            target_title = f"FORMATEUR EXPERT PAIE & RH — {job_title.upper()}"
            summary = "Dirigeant d'organisme de formation certifié Qualiopi et formateur référent Titre professionnel Gestionnaire de paie (TP-01254). Plus de 15 ans d'expertise combinant direction des ressources humaines (580 collaborateurs), ingénierie pédagogique (758h de formation) et vacations certifiantes Afpa / Chambres de Métiers. Maîtrise éprouvée de Silae, de la DSN, de l'outil Métis et des évaluations ECF."
            skills = """
      <div class="cv-bullet"><strong>Ingénierie Pédagogique & Qualiopi :</strong> Conception intégrale du parcours TP Gestionnaire de paie (758h), animation ADEA, Brevet de Maîtrise, conformité RNQ / ICPF.</div>
      <div class="cv-bullet"><strong>Pratique Métier Paie & Droit Social :</strong> Bulletin de paie complexe, contrôle et déclarations DSN, veille juridique, paramétrage avancé sur logiciel Silae.</div>
      <div class="cv-bullet"><strong>Pédagogie Active & Individualisée :</strong> Vacations Afpa (4 centres), suivi des parcours individualisés, outil Métis, encadrement des jurys et évaluations ECF.</div>
      <div class="cv-bullet"><strong>Management & Gestion de Projet :</strong> Pilotage d'équipes et de structures, dialogue social, rigueur administrative et respect des référentiels RNCP.</div>
            """.strip()
        elif cat == "RRH_PAIE":
            target_title = f"RESPONSABLE RESSOURCES HUMAINES & PAIE — {job_title.upper()}"
            summary = "Cadre RH et Paie senior (+15 ans d'expérience) ayant dirigé les ressources humaines d'une structure de 580 collaborateurs (salariés et bénévoles). Maîtrise globale du pilotage de la paie, des déclarations DSN, du dialogue social (CSE, DP, CE), du plan de développement des compétences et de la masse salariale. Solide formation juridique (Master 2 Droit public, Master RSE en cours)."
            skills = """
      <div class="cv-bullet"><strong>Direction RH & Administration du Personnel :</strong> Gestion contractuelle complète, procédures disciplinaires, gestion des temps et des carrières pour 580 collaborateurs.</div>
      <div class="cv-bullet"><strong>Supervision de la Paie & Déclarations DSN :</strong> Sécurisation des cycles de paie, déclarations sociales dématérialisées, audit de paie et contrôle Urssaf.</div>
      <div class="cv-bullet"><strong>Dialogue Social & Relations Collectives :</strong> Animation des réunions CSE/CE/DP, négociations d'accords d'entreprise, gestion des conflits et veille en droit du travail.</div>
      <div class="cv-bullet"><strong>Développement des Compétences :</strong> Élaboration et pilotage du plan de formation, ingénierie certifiante Qualiopi, accompagnement managérial.</div>
            """.strip()
        else: # GESTIONNAIRE_PAIE & COMPTA
            target_title = f"GESTIONNAIRE DE PAIE & DROIT SOCIAL CONFIRMÉ — {job_title.upper()}"
            summary = "Spécialiste autonome de la gestion de la paie et de l'administration du personnel avec plus de 15 ans d'expérience. Maîtrise de bout en bout du cycle de paie, du paramétrage logiciel Silae, du contrôle de cohérence DSN et de la législation sociale. Concepteur d'un parcours de 758 heures pour le Titre pro Gestionnaire de paie et ex-responsable RH de 580 collaborateurs."
            skills = """
      <div class="cv-bullet"><strong>Production Autonome des Bulletins de Paie :</strong> Collecte des variables, traitement des absences, congés, heures supplémentaires, primes et indemnités de rupture.</div>
      <div class="cv-bullet"><strong>Déclarations Sociales Nominatives (DSN) :</strong> Déclarations mensuelles et événementielles, contrôle des cotisations Urssaf, caisses de retraite et prévoyance.</div>
      <div class="cv-bullet"><strong>Administration du Personnel & Contrats :</strong> DPAE, rédaction des contrats et avenants, soldes de tout compte, attestations France Travail et gestion des dossiers salariés.</div>
      <div class="cv-bullet"><strong>Outils Informatiques & Audit :</strong> Maîtrise opérationnelle du logiciel Silae, expert Excel (tableaux croisés, formules avancées), audit et veille conventionnelle.</div>
            """.strip()

        points_forts = """
      <div class="cv-bullet"><strong>Double Expertise Terrain & Formation :</strong> Pratique concrète de la direction RH (580 collaborateurs) et ingénierie pédagogique certifiante Qualiopi (Titre Pro TP-01254).</div>
      <div class="cv-bullet"><strong>Stabilité, Engagement & Disponibilité :</strong> Demandeur d'emploi senior de 59 ans, loyal et disponible immédiatement. Éligible aux aides à l'embauche pour seniors.</div>
      <div class="cv-bullet"><strong>Rigueur Juridique & Maîtrise Logicielle :</strong> Titulaire d'un Master 2 en Droit public, maîtrise avancée de Silae, DSN, Excel et de l'environnement Métis.</div>
        """.strip()

        experiences = """
      <div class="exp-item">
        <div class="exp-header"><span class="exp-job">Dirigeant d'Organisme & Formateur Référent Titre Pro Paie (TP-01254)</span><span class="exp-date">Depuis 2014</span></div>
        <div class="exp-org">Kairos Formation (Organisme certifié Qualiopi RNQ / ICPF QUA007374)</div>
        <div class="cv-bullet">Conception et animation d'un parcours certifiant de 758h préparant au Titre professionnel Gestionnaire de paie (millésime 04).</div>
        <div class="cv-bullet">Formation à la pratique du bulletin, DSN, paramétrage Silae, blocs RH/Paie de l'ADEA et du Brevet de Maîtrise pour les Chambres de Métiers.</div>
      </div>
      <div class="exp-item">
        <div class="exp-header"><span class="exp-job">Formateur Sous-Traitant Paie & Ressources Humaines</span><span class="exp-date">2016 – 2020</span></div>
        <div class="exp-org">Afpa Hauts-de-France (Centres de Vervins, Beauvais, Creil et Amiens)</div>
        <div class="cv-bullet">Animation de sessions pour Gestionnaires de paie, gestion de groupes individualisés à entrées permanentes, outil Métis et évaluations ECF.</div>
      </div>
      <div class="exp-item">
        <div class="exp-header"><span class="exp-job">Responsable des Ressources Humaines & de la Paie</span><span class="exp-date">2003 – 2010</span></div>
        <div class="exp-org">Fédération du Secours Populaire Français</div>
        <div class="cv-bullet">Pilotage intégral des RH et de la paie pour 580 collaborateurs (salariés et bénévoles), administration du personnel, plan de formation et dialogue social (CSE/DP/CE).</div>
      </div>
      <div class="exp-item">
        <div class="exp-header"><span class="exp-job">Responsable de Site Opérationnel Industriel</span><span class="exp-date">2010 – 2014</span></div>
        <div class="exp-org">ETV – Nouvelle-Calédonie</div>
        <div class="cv-bullet">Montage technique, exploitation de site industriel, encadrement d'équipes opérationnelles et gestion administrative.</div>
      </div>
        """.strip()

        html = self.cv_template
        html = html.replace("{{TARGET_TITLE}}", target_title)
        html = html.replace("{{SUMMARY}}", summary)
        html = html.replace("{{KEY_SKILLS_HTML}}", skills)
        html = html.replace("{{POINTS_FORTS_HTML}}", points_forts)
        html = html.replace("{{EXPERIENCES_HTML}}", experiences)
        
        return html

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        best_html, _, _ = self.generate_best_of_three_letter(job)
        return best_html
