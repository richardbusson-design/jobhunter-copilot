# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime
from typing import Dict, Any

class ApplicationGenerator:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.profile = self.load_profile()
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
        """Nettoie les mentions (H/F), / Formatrice, etc. pour une intégration fluide en prose."""
        cleaned = re.sub(r'\(H/F\)|H/F|\(F/H\)|F/H', '', raw_title, flags=re.IGNORECASE)
        cleaned = cleaned.replace("/ Formatrice", "").replace("/ formatrice", "")
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def evaluate_match(self, job: Dict[str, Any]) -> int:
        text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
        score = 70
        
        # 1. Piliers Métiers Cibles
        if "paie" in text or "gestionnaire de paie" in text or "bulletin" in text:
            score += 8
        if "ressources humaines" in text or " rh " in text or "rh," in text or text.startswith("rh ") or text.endswith(" rh"):
            score += 8
        if "formation" in text or "formateur" in text or "pédagogique" in text or "coordinateur" in text or "tp-" in text:
            score += 8
        if "responsable rh" in text or "rrh" in text or "relations sociales" in text or "chargé rh" in text or "gestionnaire rh" in text:
            score += 8

        # 2. Compétences Techniques & Spécialisées
        tech_keywords = [
            "dsn", "silae", "titre professionnel", "qualiopi", "droit social", "droit du travail",
            "cse", "contrat", "contrats", "administration du personnel", "gestion du personnel",
            "masse salariale", "alternance", "cfa", "adea", "métis", "ecf"
        ]
        
        matched_tech = sum(1 for kw in tech_keywords if kw in text)
        score += min(matched_tech * 2, 16)
                
        return min(score, 98)

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        company = job.get("company", "Organisme")
        raw_title = job.get("title", "Formateur en gestion de paie et RH")
        title_clean = self.clean_job_title(raw_title)
        contact_name = job.get("contact_name", "")
        contact_title = job.get("contact_title", "Direction du Centre")
        city = job.get("city", "Creil")
        postal_code = str(job.get("postal_code", "60100"))
        address_1 = job.get("address_1", "")
        address_2 = job.get("address_2", "")
        
        contact_full = f"{contact_name}, {contact_title}".strip(", ") if contact_name else contact_title
        today_str = datetime.now().strftime("%d %B %Y").replace("August", "août").replace("September", "septembre").replace("October", "octobre")
        
        # Rédaction fluide et naturelle des paragraphes
        if "cma" in company.lower() or "artisanat" in company.lower():
            p1 = f"Votre recherche pour le poste de {title_clean.lower()} au sein de {company} retient toute mon attention. Acteur de référence dans la formation professionnelle et l’accompagnement des entreprises artisanales, votre organisme représente un environnement d’excellence dont je maîtrise parfaitement les exigences pédagogiques et réglementaires."
        elif "afpa" in company.lower():
            p1 = f"Votre recherche d’un {title_clean.lower()} au centre de formation Afpa retient toute mon attention. Intervenu entre 2016 et 2020 sur quatre centres Afpa (Vervins, Beauvais, Creil et Amiens), je connais parfaitement les exigences de vos dispositifs, l’outil Métis, les évaluations en cours de formation (ECF) et la gestion de groupes à entrées échelonnées et parcours individualisés."
        else:
            p1 = f"Votre recherche pour le poste de {title_clean.lower()} au sein de {company} retient toute mon attention. Structure reconnue dans le développement des compétences, votre établissement propose un cadre d'intervention en parfaite adéquation avec mon parcours de formateur expert et de responsable RH."

        p2 = "Le premier bloc de compétences de l’ADEA, assister à la gestion des ressources humaines et au management des collaborateurs d’une entreprise artisanale, représente 84 heures que je peux animer sans période d’adaptation. Le volet gestion du Brevet de Maîtrise et la formation continue des artisans employeurs relèvent de la même matière : embauche du premier salarié, contrat d’apprentissage, bulletin de paie, DSN et obligations de l’employeur. C’est ce que j’enseigne depuis 2014."
        p3 = "J’ai exercé ce métier avant de l’enseigner : de 2003 à 2010, j’ai dirigé les ressources humaines d’une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant aussi le plan de formation. Le cadre d’un centre de formation ne m’est pas étranger non plus : entre 2016 et 2020, je suis intervenu sur quatre centres Afpa, avec référentiel imposé, évaluations en cours de formation et parcours individualisés au sein d’un même groupe."
        p4 = "Si c’est une fonction de coordination que vous avez à pourvoir, elle me va tout autant. Je dirige un organisme certifié Qualiopi : le Référentiel National Qualité, la traçabilité des parcours et la préparation d’audit sont mes obligations quotidiennes. J’ai conçu de bout en bout un parcours certifiant de 758 heures préparant au Titre professionnel Gestionnaire de paie, et encadré quatre ans les équipes d’un site industriel en Nouvelle-Calédonie. Un Master 2 de droit public complète cette approche des cadres réglementaires."
        p5 = "Un mot de franchise pour finir. J’ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu’un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l’embauche au titre de ma situation de demandeur d’emploi senior, dont je vous communiquerai volontiers les modalités. Ma mobilité est nationale, sans réserve, sur l’ensemble du réseau, et ma disponibilité immédiate."

        # Nettoyage absolu de toute balise grasse dans le corps
        p1 = re.sub(r'</?[bi]>|</?strong>', '', p1)
        p2 = re.sub(r'</?[bi]>|</?strong>', '', p2)
        p3 = re.sub(r'</?[bi]>|</?strong>', '', p3)
        p4 = re.sub(r'</?[bi]>|</?strong>', '', p4)
        p5 = re.sub(r'</?[bi]>|</?strong>', '', p5)

        html = self.letter_template
        html = html.replace("{{ contact_full }}", contact_full)
        html = html.replace("{{ company_name }}", company)
        html = html.replace("{{ address_1 }}", address_1 if address_1 else "Direction des Ressources Humaines")
        html = html.replace("{{ postal_code }}", postal_code)
        html = html.replace("{{ city }}", city.upper())
        html = html.replace("{{ current_date }}", today_str)
        html = html.replace("{{ job_title_clean }}", title_clean)
        html = html.replace("{{ paragraph_1 }}", p1)
        html = html.replace("{{ paragraph_2 }}", p2)
        html = html.replace("{{ paragraph_3 }}", p3)
        html = html.replace("{{ paragraph_4 }}", p4)
        html = html.replace("{{ paragraph_5 }}", p5)
        
        return html

    def render_cv_html(self, job: Dict[str, Any]) -> str:
        raw_title = job.get("title", "Formateur en gestion de paie et RH")
        title_clean = self.clean_job_title(raw_title)
        
        summary = (
            "Dirigeant d’un organisme de formation certifié Qualiopi, formateur expert et ancien responsable des ressources humaines d’une structure de 580 collaborateurs. "
            "Ingénierie complète de parcours certifiants, conformité au Référentiel National Qualité, marchés publics de formation et gestion de site opérationnel. "
            "Master 2 de droit public. Mobilité nationale, disponibilité immédiate."
        )

        key_skills = [
            ("Formation d’adultes et d’alternants", "douze ans d’animation continue devant des publics adultes et alternants ; ingénierie de parcours certifiants, du référentiel d'activité à l’évaluation finale."),
            ("Gestion du personnel et paie en entreprise", "embauche, contrats d’apprentissage, administration de la paie, DSN, conventions collectives : la matière du bloc RH de l’ADEA et du Brevet de Maîtrise."),
            ("Qualité et conformité de la formation", "dirigeant d’un organisme certifié Qualiopi (ICPF, QUA007374) : maîtrise du Référentiel National Qualité, traçabilité, indicateurs et audits."),
            ("Coordination et pilotage", "direction de site opérationnel, pilotage RH de 580 collaborateurs, gestion de marchés publics et dialogue social.")
        ]
        key_skills_html = "".join([f'<div class="cv-bullet"><strong>{k} :</strong> {v}</div>' for k, v in key_skills])

        points_forts = [
            ("La qualité en formation, vécue de l’intérieur", "direction d’un organisme certifié Qualiopi : maîtrise du RNQ, traçabilité des parcours, indicateurs de performance, suivi d’audit et relations avec les financeurs."),
            ("Ingénierie complète, du référentiel au déroulé de séance", "parcours certifiant de 758 heures conçu de bout en bout (Titre pro Gestionnaire de paie), macro-planning, cadrage des évaluations et modules courts pour salariés."),
            ("Encadrement et gestion administrative maîtrisés", "direction d’un site opérationnel, pilotage RH de 580 collaborateurs, plan de développement des compétences et conduite de marchés publics.")
        ]
        points_forts_html = "".join([f'<div class="cv-bullet"><strong>{k} :</strong> {v}</div>' for k, v in points_forts])

        exp_data = [
            {
                "title": "Formateur et consultant en paie, ressources humaines et droit social",
                "org": "Kairos Formation, organisme certifié Qualiopi, président",
                "dates": "2014 – aujourd’hui",
                "bullets": [
                    "Conception et animation de parcours certifiants pour adultes, dont un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie (TP-01254, millésime 04) : référentiel, macro-planning, cadrage des évaluations, déroulés de séance.",
                    "Formation de dirigeants et de collaborateurs de TPE et PME à la gestion du personnel : embauche, contrats, apprentissage, paie, DSN, obligations de l’employeur, avec veille réglementaire continue.",
                    "Direction d’un organisme certifié Qualiopi : construction de l’offre, conformité au Référentiel National Qualité, indicateurs, relations avec les financeurs."
                ]
            },
            {
                "title": "Formateur en gestion de paie, en sous-traitance pédagogique pour l’Afpa",
                "org": "Centres Afpa de Vervins, Beauvais, Creil et Amiens",
                "dates": "2016 – 2020",
                "bullets": [
                    "Interventions sur quatre centres pour le compte d’organismes titulaires du marché : référentiel du donneur d’ordre, outil Métis, évaluations en cours de formation, traçabilité du suivi des stagiaires.",
                    "Formation en entrée permanente : groupes à entrées échelonnées et parcours individualisés, organisation proche de celle d’un centre de formation d’apprentis."
                ]
            },
            {
                "title": "Responsable des relations sociales et des ressources humaines",
                "org": "Secours Populaire, structure de 580 collaborateurs",
                "dates": "2003 – 2010",
                "bullets": [
                    "Paie et administration du personnel de 580 collaborateurs, salariés et bénévoles : contrats, avenants, absences, arrêts de travail, accidents du travail.",
                    "Pilotage du plan de formation, conduite de marchés publics RH et formation, animation du dialogue social."
                ]
            },
            {
                "title": "Responsable de site, management opérationnel",
                "org": "ETV, Nouvelle-Calédonie",
                "dates": "2010 – 2014",
                "bullets": [
                    "Montage et exploitation d’un site industriel : encadrement des équipes, organisation de la production, conformité réglementaire et prévention des risques."
                ]
            }
        ]

        exp_html = ""
        for exp in exp_data:
            bullets_str = "".join([f'<div class="cv-bullet">{b}</div>' for b in exp["bullets"]])
            exp_html += f"""
            <div class="exp-item">
              <div class="exp-header">
                <span class="exp-job">{exp['title']}</span>
                <span class="exp-date">{exp['dates']}</span>
              </div>
              <div class="exp-org">{exp['org']}</div>
              {bullets_str}
            </div>
            """

        html = self.cv_template
        html = html.replace("{{ target_title }}", title_clean)
        html = html.replace("{{ target_title_upper }}", title_clean.upper())
        html = html.replace("{{ summary }}", summary)
        html = html.replace("{{ key_skills_html }}", key_skills_html)
        html = html.replace("{{ points_forts_html }}", points_forts_html)
        html = html.replace("{{ experiences_html }}", exp_html)
        
        return html



