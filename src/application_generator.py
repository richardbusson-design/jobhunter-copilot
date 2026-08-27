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

    def evaluate_match(self, job: Dict[str, Any]) -> int:
        text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
        score = 65
        keywords_high = ["paie", "gestionnaire de paie", "ressources humaines", "rh", "formation", "formateur", "coordinateur"]
        keywords_mid = ["dsn", "silae", "titre professionnel", "qualiopi", "comptabilité", "social", "droit social", "alternance", "cfa", "adea"]
        
        for kw in keywords_high:
            if kw in text:
                score += 6
        for kw in keywords_mid:
            if kw in text:
                score += 4
                
        return min(score, 98)

    def generate_letter_content(self, job: Dict[str, Any]) -> Dict[str, str]:
        company = job.get("company", "CMA Nouvelle-Aquitaine")
        title = job.get("title", "formateur en paie et ressources humaines, ou coordinateur de formation")
        contact_name = job.get("contact_name", "Monsieur Stéphane BON")
        contact_title = job.get("contact_title", "Directeur régional de la Formation")
        city = job.get("city", "BORDEAUX")
        postal_code = job.get("postal_code", "33000")
        address_1 = job.get("address_1", "46, rue Général de Larminat")
        address_2 = job.get("address_2", "CS 81423")
        custom_p1 = job.get("custom_p1")
        custom_p2 = job.get("custom_p2")
        custom_p3 = job.get("custom_p3")
        custom_p4 = job.get("custom_p4")
        custom_p5 = job.get("custom_p5")
        
        salutation = "Monsieur le Directeur" if "directeur" in contact_title.lower() else "Madame, Monsieur"
        today_str = job.get("date_str", datetime.now().strftime("%d %B %Y").replace("August", "août").replace("September", "septembre").replace("October", "octobre"))
        
        # Paragraphes impeccables : accents rigoureux et ponctuation française soignée
        if not custom_p1:
            if "cma" in company.lower():
                custom_p1 = f"Votre appel à votre réseau a retenu mon attention. Le poste que vous publiiez relevait d’un autre métier que le mien, aussi est-ce une candidature spontanée que je me permets de vous adresser. {company} accompagne près de 13 000 apprenants par an sur quinze sites et forme environ 18 % des apprentis de Nouvelle-Aquitaine : c’est un opérateur dont je connais la matière, sans en connaître encore la maison."
            elif "afpa" in company.lower():
                custom_p1 = f"Votre recherche d’un {title} au centre de formation Afpa retient toute mon attention. Intervenu entre 2016 et 2020 sur quatre centres Afpa (Vervins, Beauvais, Creil et Amiens), je connais parfaitement les exigences de vos dispositifs, l’outil Métis, les évaluations en cours de formation (ECF) et la gestion de groupes à entrées échelonnées et parcours individualisés."
            else:
                custom_p1 = f"Votre recherche d’un {title} au sein de {company} a retenu toute mon attention. Acteur reconnu sur notre territoire dans le développement des compétences professionnelles, votre structure représente un environnement dont je maîtrise parfaitement les enjeux techniques, opérationnels et réglementaires."

        custom_p1 = re.sub(r'</?[bi]>|</?strong>', '', custom_p1)

        if not custom_p2:
            custom_p2 = "Le premier bloc de compétences de l’ADEA, assister à la gestion des ressources humaines et au management des collaborateurs d’une entreprise artisanale, représente 84 heures que je peux animer sans période d’adaptation. Le volet gestion du Brevet de Maîtrise et la formation continue des artisans employeurs relèvent de la même matière : embauche du premier salarié, contrat d’apprentissage, bulletin de paie, DSN et obligations de l’employeur. C’est ce que j’enseigne depuis 2014."

        if not custom_p3:
            custom_p3 = "J’ai exercé ce métier avant de l’enseigner : de 2003 à 2010, j’ai dirigé les ressources humaines d’une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant aussi le plan de formation. Le cadre d’un centre de formation ne m’est pas étranger non plus : entre 2016 et 2020, je suis intervenu sur quatre centres Afpa, avec référentiel imposé, évaluations en cours de formation et parcours individualisés au sein d’un même groupe."

        if not custom_p4:
            custom_p4 = "Si c’est une fonction de coordination que vous avez à pourvoir, elle me va tout autant. Je dirige un organisme certifié Qualiopi : le Référentiel National Qualité, la traçabilité des parcours et la préparation d’audit sont mes obligations quotidiennes. J’ai conçu de bout en bout un parcours certifiant de 758 heures préparant au Titre professionnel Gestionnaire de paie, et encadré quatre ans les équipes d’un site industriel en Nouvelle-Calédonie. Un Master 2 de droit public complète cette approche des cadres réglementaires."

        if not custom_p5:
            custom_p5 = "Un mot de franchise pour finir. J’ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu’un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l’embauche au titre de ma situation de demandeur d’emploi senior, dont je vous communiquerai volontiers les modalités. Ma mobilité est nationale, sans réserve, sur l’ensemble du réseau, et ma disponibilité immédiate."

        return {
            "recipient_contact": f"À l’attention de {contact_name}" if contact_name else f"À l’attention de la Direction",
            "recipient_title": contact_title,
            "recipient_company": company,
            "recipient_address_1": address_1,
            "recipient_address_2": address_2 if address_2 else "",
            "recipient_city": f"{postal_code} {city.upper()}".strip(),
            "date_line": f"À Creil, le {today_str}",
            "objet": f"Candidature spontanée : {title}" if "spontanée" in title.lower() or "candidature" in title.lower() else f"Candidature : {title}",
            "salutation": salutation,
            "paragraph_1": custom_p1,
            "paragraph_2": custom_p2,
            "paragraph_3": custom_p3,
            "paragraph_4": custom_p4,
            "paragraph_5": custom_p5,
            "closing_politeness": f"Je vous prie d’agréer, {salutation}, l’expression de ma considération distinguée."
        }

    def generate_cv_content(self, job: Dict[str, Any]) -> Dict[str, str]:
        title = job.get("title", "Coordinateur de formation / Formateur Paie & RH")
        
        pf1 = "<strong>La qualité en formation, vécue de l'intérieur :</strong> direction d'un organisme certifié Qualiopi : Référentiel National Qualité, traçabilité des parcours, indicateurs, suivi d'audit, relations avec les financeurs."
        pf2 = "<strong>Ingénierie complète, du référentiel au déroulé de séance :</strong> parcours certifiant de 758 heures construit de bout en bout, macro-planning, cadrage des évaluations, et modules courts pour publics en poste."
        pf3 = "<strong>Encadrement et gestion administrative maîtrisés :</strong> direction d'un site opérationnel, pilotage RH de 580 collaborateurs, plan de formation et marchés publics du champ formation."
        
        points_forts_html = f"""
        <div class="cv-bullet text-justify">{pf1}</div>
        <div class="cv-bullet text-justify">{pf2}</div>
        <div class="cv-bullet text-justify">{pf3}</div>
        """
        
        key_skills_html = """
        <div class="cv-bullet text-justify"><strong>Formation d'adultes et d'alternants :</strong> douze ans d'animation devant des publics en reconversion ; ingénierie de parcours certifiants, du référentiel à l'évaluation.</div>
        <div class="cv-bullet text-justify"><strong>Gestion du personnel en TPE et PME :</strong> embauche, contrat d'apprentissage, paie, DSN, conventions collectives : la matière du bloc RH de l'ADEA et du Brevet de Maîtrise.</div>
        <div class="cv-bullet text-justify"><strong>Qualité et conformité de la formation :</strong> dirigeant d'un organisme certifié Qualiopi (ICPF, QUA007374) : Référentiel National Qualité, traçabilité, indicateurs, suivi d'audit.</div>
        <div class="cv-bullet text-justify"><strong>Coordination et pilotage :</strong> direction d'un site opérationnel, pilotage RH de 580 collaborateurs, marchés publics du champ formation.</div>
        """
        
        exp_html = """
        <div>
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-weight: bold; color: #000000;">Formateur et consultant en paie, ressources humaines et droit social</span>
            <span style="font-size: 10.5px; color: #333333; font-style: italic;">2014 - aujourd'hui</span>
          </div>
          <div style="font-size: 10.8px; color: #222222; font-style: italic;">Kairos Formation, organisme certifié Qualiopi, président</div>
          <div style="margin-top: 2px;">
            <div class="cv-bullet text-justify">Conception et animation de parcours certifiants pour adultes, dont un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie (TP-01254, millésime 04) : référentiel, macro-planning, cadrage des évaluations, déroulés de séance.</div>
            <div class="cv-bullet text-justify">Formation de dirigeants et de collaborateurs de TPE et PME à la gestion du personnel : embauche, contrats, apprentissage, paie, DSN, obligations de l'employeur, avec veille réglementaire continue.</div>
            <div class="cv-bullet text-justify">Direction d'un organisme certifié Qualiopi : construction de l'offre, conformité au Référentiel National Qualité, indicateurs, relations avec les financeurs.</div>
          </div>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-weight: bold; color: #000000;">Formateur en gestion de paie, en sous-traitance pédagogique pour l'Afpa</span>
            <span style="font-size: 10.5px; color: #333333; font-style: italic;">2016 - 2020</span>
          </div>
          <div style="font-size: 10.8px; color: #222222; font-style: italic;">Centres Afpa de Vervins, Beauvais, Creil et Amiens</div>
          <div style="margin-top: 2px;">
            <div class="cv-bullet text-justify">Interventions sur quatre centres pour le compte d'organismes titulaires du marché : référentiel du donneur d'ordre, outil Métis, évaluations en cours de formation, traçabilité du suivi des stagiaires.</div>
            <div class="cv-bullet text-justify">Formation en entrée permanente : groupes à entrées échelonnées et parcours individualisés, organisation proche de celle d'un centre de formation d'apprentis.</div>
          </div>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-weight: bold; color: #000000;">Responsable des relations sociales et des ressources humaines</span>
            <span style="font-size: 10.5px; color: #333333; font-style: italic;">2003 - 2010</span>
          </div>
          <div style="font-size: 10.8px; color: #222222; font-style: italic;">Secours Populaire, structure de 580 collaborateurs</div>
          <div style="margin-top: 2px;">
            <div class="cv-bullet text-justify">Paie et administration du personnel de 580 collaborateurs, salariés et bénévoles : contrats, avenants, absences, arrêts de travail, accidents du travail.</div>
            <div class="cv-bullet text-justify">Pilotage du plan de formation, conduite de marchés publics RH et formation, animation du dialogue social.</div>
          </div>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-weight: bold; color: #000000;">Responsable de site, management opérationnel</span>
            <span style="font-size: 10.5px; color: #333333; font-style: italic;">2010 - 2014</span>
          </div>
          <div style="font-size: 10.8px; color: #222222; font-style: italic;">ETV, Nouvelle-Calédonie</div>
          <div class="cv-bullet text-justify" style="margin-top: 2px;">
            Montage et exploitation d'un site industriel : encadrement des équipes, organisation de la production, conformité réglementaire et prévention des risques.
          </div>
        </div>
        """
        
        return {
            "target_title": title,
            "target_title_upper": title.upper(),
            "summary": self.profile["summary"],
            "key_skills_html": key_skills_html.strip(),
            "points_forts_html": points_forts_html.strip(),
            "experiences_html": exp_html.strip(),
            "tools": self.profile["tools"]
        }

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        data = self.generate_letter_content(job)
        html = self.letter_template
        for k, v in data.items():
            html = html.replace(f"{{{{ {k} }}}}", v)
        return html

    def render_cv_html(self, job: Dict[str, Any]) -> str:
        data = self.generate_cv_content(job)
        html = self.cv_template
        for k, v in data.items():
            html = html.replace(f"{{{{ {k} }}}}", v)
        return html
