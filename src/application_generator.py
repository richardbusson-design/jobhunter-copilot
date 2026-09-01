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
        if "formateur" in text or "formatrice" in text or "pédagogique" in text or "coordinateur de formation" in text or "cfa" in text:
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
        score = 75
        cat = self.detect_category(job)
        if cat == "RRH_PAIE":
            score += 15
        elif cat == "FORMATEUR_PAIE_RH":
            score += 15
        elif cat == "GESTIONNAIRE_PAIE":
            score += 14
        elif cat == "GESTIONNAIRE_RH":
            score += 12
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
        score += min(matched_tech * 2, 6)
                
        return min(score, 98)

    def render_letter_variant(self, job: Dict[str, Any], variant_index: int) -> str:
        company = job.get("company", "votre entreprise").replace('"', '')
        raw_title = job.get("title", "Poste RH & Paie")
        job_title = self.clean_job_title(raw_title)
        
        contact_name = job.get("contact_name", "Monsieur le Responsable du Recrutement")
        contact_title = job.get("contact_title", "Direction des Ressources Humaines")
        contact_full = f"{contact_name}"
        
        recipient_body_lines = []
        if contact_title:
            recipient_body_lines.append(f"<div>{contact_title}</div>")
        recipient_body_lines.append(f"<div>{company}</div>")
        
        address_1 = job.get("address_1", "")
        if address_1 and address_1 != "Service Recrutement & RH":
            recipient_body_lines.append(f"<div>{address_1}</div>")
            
        postal_code = job.get("postal_code", "60000")
        city = job.get("city", "CREIL").upper()
        recipient_body_lines.append(f"<div>{postal_code} {city}</div>")
        
        recipient_body_html = "\n".join(recipient_body_lines)
        current_date = datetime.now().strftime("%d %B %Y").replace("August", "août").replace("September", "septembre")

        cat = self.detect_category(job)

        # Formule d'appel et de politesse
        if "directeur" in contact_name.lower() or "directeur" in contact_title.lower():
            call_formula = "Monsieur le Directeur,"
            politesse_formula = "Je vous prie d’agréer, Monsieur le Directeur, l’expression de ma considération distinguée."
        elif "directrice" in contact_name.lower() or "directrice" in contact_title.lower():
            call_formula = "Madame la Directrice,"
            politesse_formula = "Je vous prie d’agréer, Madame la Directrice, l’expression de ma considération distinguée."
        else:
            call_formula = "Madame, Monsieur,"
            politesse_formula = "Je vous prie d’agréer, Madame, Monsieur, l’expression de ma considération distinguée."

        # 5 paragraphes denses et calibrés basés scrupuleusement sur le modèle PDF officiel
        if cat == "FORMATEUR_PAIE_RH":
            job_object_clean = f"Candidature : {job_title}"
            p1 = f"Votre recherche pour le poste de {job_title} au sein de {company} a retenu toute mon attention. Acteur reconnu dans le développement des compétences professionnelles, votre organisme représente un environnement d’excellence dont je connais parfaitement les enjeux pédagogiques et techniques."
            p2 = "Le premier bloc de compétences de l’ADEA, assister à la gestion des ressources humaines et au management des collaborateurs d’une entreprise artisanale, représente 84 heures que je peux animer sans période d’adaptation. Le volet gestion du Brevet de Maîtrise et la formation continue des artisans employeurs relèvent de la même matière : embauche du premier salarié, contrat d’apprentissage, bulletin de paie, DSN et obligations de l’employeur. C’est ce que j’enseigne depuis 2014."
            p3 = "J’ai exercé ce métier avant de l’enseigner : de 2003 à 2010, j’ai dirigé les ressources humaines d’une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant aussi le plan de formation. Le cadre d’un centre de formation ne m’est pas étranger non plus : entre 2016 et 2020, je suis intervenu sur quatre centres Afpa, à Vervins, Beauvais, Creil et Amiens, avec référentiel imposé, évaluations en cours de formation et parcours individualisés au sein d’un même groupe."
            p4 = "Si c’est une fonction de coordination que vous avez à pourvoir, elle me va tout autant. Je dirige un organisme certifié Qualiopi : le Référentiel National Qualité, la traçabilité des parcours et la préparation d’audit sont mes obligations quotidiennes. J’ai conçu de bout en bout un parcours certifiant de 758 heures préparant au Titre professionnel Gestionnaire de paie, et encadré quatre ans les équipes d’un site industriel en Nouvelle-Calédonie. Un Master 2 de droit public complète cette approche des cadres réglementaires."
            p5 = "Un mot de franchise pour finir. J’ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu’un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l’embauche au titre de ma situation de demandeur d’emploi senior, dont je vous communiquerai volontiers les modalités. Ma mobilité est nationale, sans réserve, sur l’ensemble du réseau, et ma disponibilité immédiate."
        elif cat == "RRH_PAIE":
            job_object_clean = f"Candidature : {job_title}"
            p1 = f"Votre recherche pour le poste de {job_title} au sein de {company} a retenu toute mon attention. Structure dynamique aux enjeux humains et organisationnels exigeants, votre entreprise représente un cadre de travail de référence au sein duquel je souhaite mettre à profit mon expertise globale de la fonction RH et du pilotage de la paie."
            p2 = "De la collecte des éléments variables jusqu'au contrôle approfondi de la DSN et à la maîtrise de la masse salariale, je supervise l'ensemble des cycles de paie et de l'administration du personnel. Ma pratique éprouvée du logiciel Silae et des plateformes déclaratives dématérialisées me permet de garantir une totale conformité sociale, une gestion rigoureuse des cotisations et un traitement irréprochable des procédures d'entrée et de sortie."
            p3 = "J'ai exercé ce métier avec une responsabilité d'envergure : de 2003 à 2010, j'ai dirigé les ressources humaines d'une organisation de 580 collaborateurs, salariés et bénévoles, en y pilotant le plan de développement des compétences, les procédures contractuelles et le dialogue social avec les instances représentatives (CSE, CE, DP). Cette expérience m'a appris à concilier le strict respect de la réglementation avec l'instauration d'un climat social serein et constructif."
            p4 = "Je dirige par ailleurs un organisme de formation certifié Qualiopi où j'ai conçu de bout en bout un parcours certifiant de 758 heures pour le Titre professionnel Gestionnaire de paie, et encadré quatre ans les équipes d'un site industriel en Nouvelle-Calédonie. Titulaire d'un Master 2 en Droit public, d'une Maîtrise en Sciences de Gestion et engagé dans un Master RSE à l'IAE de Paris, j'apporte une vision stratégique, éthique et sécurisée de vos relations de travail."
            p5 = "Un mot de franchise pour finir. J'ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu'un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l'embauche au titre de ma situation de demandeur d'emploi senior, dont je vous communiquerai volontiers les modalités. Ma mobilité est totale sur l'ensemble de votre secteur, et ma disponibilité immédiate."
        elif cat == "COMPTABILITE_SOCIALE":
            job_object_clean = f"Candidature : {job_title}"
            p1 = f"Votre recherche pour le poste de {job_title} au sein de {company} a retenu toute mon attention. Expert autonome de la paie, du droit social et de la gestion comptable du personnel, je souhaite mettre ma rigueur technique, mon sens de la relation client et ma polyvalence au service de votre structure et de vos portefeuilles clients."
            p2 = "Habitué à la gestion de dossiers multi-conventions collectives aux spécificités techniques exigeantes, j'assure en toute autonomie l'intégralité du cycle de paie : collecte des variables, traitement des absences et congés, calcul des cotisations sociales, établissement des soldes de tout compte et télédéclarations DSN mensuelles et événementielles avec contrôle de cohérence rigoureux et régularisations annuelles."
            p3 = "J'ai exercé ce métier avec une grande exigence opérationnelle : de 2003 à 2010, j'ai dirigé les ressources humaines et la paie d'une structure de 580 collaborateurs, salariés et bénévoles. J'ai également dispensé la pratique du bulletin et du droit social sur quatre centres Afpa (Vervins, Beauvais, Creil, Amiens) et auprès d'artisans employeurs dans le cadre des blocs RH/Paie de l'ADEA et du Brevet de Maîtrise."
            p4 = "Je dirige par ailleurs un organisme de formation certifié Qualiopi où j'ai conçu un parcours certifiant de 758 heures pour le Titre professionnel Gestionnaire de paie. Titulaire d'un Master 2 en Droit public et d'une Maîtrise en Sciences de Gestion, je maîtrise parfaitement l'environnement logiciel Silae et l'exploitation experte d'Excel, garantissant une sécurité juridique absolue et un conseil fiable face aux contrôles Urssaf."
            p5 = "Un mot de franchise pour finir. J'ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu'un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l'embauche au titre de ma situation de demandeur d'emploi senior, dont je vous communiquerai volontiers les modalités. Titulaire du permis B, je dispose d'une disponibilité immédiate."
        elif cat == "GESTIONNAIRE_RH":
            job_object_clean = f"Candidature : {job_title}"
            p1 = f"Votre offre d'emploi pour le poste de {job_title} au sein de {company} correspond parfaitement à mes compétences et à mon projet professionnel. Spécialiste confirmé de l'administration du personnel, du suivi contractuel et de la gestion sociale avec plus de 15 ans de pratique, je vous propose mon autonomie opérationnelle et ma réactivité pour renforcer votre service RH."
            p2 = "Au fil de mon parcours, j'ai supervisé l'ensemble du cycle de vie des collaborateurs : formalités d'embauche (DPAE, contrats, avenants), suivi des périodes d'essai, gestion des temps et activités, suivi disciplinaire, ruptures conventionnelles et relations avec la médecine du travail et les organismes de prévoyance. J'accorde une importance primordiale à la qualité du service rendu aux managers opérationnels et aux salariés."
            p3 = "J'ai exercé ce métier avec une responsabilité directe : de 2003 à 2010, j'ai dirigé les ressources humaines d'une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant l'administration, le plan de formation et le dialogue social avec les représentants du personnel (CSE, DP, CE). Cette pratique m'a conféré une solide aisance relationnelle et une capacité reconnue à instaurer un climat de confiance au sein des équipes."
            p4 = "Dirigeant d'un organisme de formation certifié Qualiopi où j'ai conçu un parcours certifiant de 758 heures pour le Titre professionnel Gestionnaire de paie, je possède une parfaite maîtrise de l'environnement légal et conventionnel. Titulaire d'un Master 2 en Droit public et d'une Maîtrise en Sciences de Gestion, je garantis une veille juridique permanente et une rigueur irréprochable dans le traitement de vos dossiers administratifs."
            p5 = "Un mot de franchise pour finir. J'ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu'un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l'embauche au titre de ma situation de demandeur d'emploi senior, dont je vous communiquerai volontiers les modalités. Titulaire du permis B, je dispose d'une mobilité complète et d'une disponibilité immédiate."
        else: # GESTIONNAIRE_PAIE
            job_object_clean = f"Candidature : {job_title}"
            p1 = f"Votre offre d'emploi pour le poste de {job_title} au sein de {company} retient toute mon attention. Gestionnaire de paie confirmé et expert du droit social, je vous propose mon autonomie complète pour assurer la production irréprochable de vos bulletins de paie, sécuriser vos déclarations sociales et optimiser vos procédures administratives."
            p2 = "De la collecte méthodique des variables jusqu'au virement des salaires et au contrôle minutieux des déclarations DSN (mensuelles, arrêts de travail, fins de contrat), je prends en charge l'intégralité du cycle de paie. Mon expertise technique couvre le paramétrage approfondi sur logiciel Silae, le traitement des cotisations spécifiques, la régularisation des plafonds et la relation suivie avec l'Urssaf, les caisses de retraite et les organismes de prévoyance."
            p3 = "J'ai exercé ce métier avec une responsabilité concrète avant de l'enseigner : de 2003 à 2010, j'ai piloté les ressources humaines et la paie d'une structure de 580 collaborateurs, salariés et bénévoles. J'ai également dispensé la pratique du bulletin et du droit social sur quatre centres Afpa (Vervins, Beauvais, Creil, Amiens) et auprès d'artisans employeurs dans le cadre des blocs RH/Paie de l'ADEA et du Brevet de Maîtrise."
            p4 = "Je dirige par ailleurs un organisme certifié Qualiopi où j'ai conçu de bout en bout un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie. Titulaire d'un Master 2 en Droit public et d'une Maîtrise en Sciences de Gestion, j'apporte une double maîtrise du chiffre et de la règle juridique, garantissant des réponses documentées aux collaborateurs et une sécurité sans faille face aux audits de paie."
            p5 = "Un mot de franchise pour finir. J'ai 59 ans : je suis loin de la retraite et je cherche un engagement durable plutôt qu'un passage. Mon recrutement peut par ailleurs ouvrir droit à une aide à l'embauche au titre de ma situation de demandeur d'emploi senior, dont je vous communiquerai volontiers les modalités. Titulaire du permis B, immédiatement disponible et mobile, je me tiens à votre entière disposition pour un entretien."

        paragraphs_html = f"<p>{p1}</p>\n<p>{p2}</p>\n<p>{p3}</p>\n<p>{p4}</p>\n<p>{p5}</p>"

        html = self.letter_template
        html = html.replace("{{CONTACT_FULL}}", contact_full)
        html = html.replace("{{RECIPIENT_BODY_HTML}}", recipient_body_html)
        html = html.replace("{{CURRENT_DATE}}", current_date)
        html = html.replace("{{JOB_OBJECT_CLEAN}}", job_object_clean)
        html = html.replace("{{CALL_FORMULA}}", call_formula)
        html = html.replace("{{POLITESSE_FORMULA}}", politesse_formula)
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
            cv_subtitle = "Formateur en gestion de paie, ressources humaines et droit social"
            target_title = "FORMATEUR EN GESTION DE PAIE, RESSOURCES HUMAINES ET DROIT SOCIAL"
            summary = "Formateur en paie et en droit social depuis douze ans, après vingt ans de pratique du métier enseigné, dont sept années à la tête des ressources humaines d'une structure de 580 collaborateurs. Intervenant sur quatre centres Afpa entre 2016 et 2020. La gestion du personnel en TPE et PME est la matière exacte du bloc RH de l'ADEA et du volet gestion du Brevet de Maîtrise. Mobilité nationale, disponibilité immédiate."
            skills = """
      <div class="cv-bullet"><strong>Formation d'adultes et d'alternants :</strong> douze ans d'animation devant des publics en reconversion ; ingénierie de parcours certifiants, du référentiel à l'évaluation.</div>
      <div class="cv-bullet"><strong>Gestion du personnel en TPE et PME :</strong> embauche, contrat d'apprentissage, paie, DSN, conventions collectives : la matière du bloc RH de l'ADEA et du Brevet de Maîtrise.</div>
      <div class="cv-bullet"><strong>Qualité et conformité de la formation :</strong> dirigeant d'un organisme certifié Qualiopi (ICPF, QUA007374) : Référentiel National Qualité, traçabilité, indicateurs, suivi d'audit.</div>
      <div class="cv-bullet"><strong>Coordination et pilotage :</strong> direction d'un site opérationnel, pilotage RH de 580 collaborateurs, marchés publics du champ formation.</div>
            """.strip()
            points_forts = """
      <div class="cv-bullet"><strong>Le bloc de gestion des ressources humaines, sans période d'adaptation :</strong> embauche, contrat d'apprentissage, paie, DSN et obligations de l'employeur sont mon cœur de métier depuis 2014, auprès de dirigeants de TPE.</div>
      <div class="cv-bullet"><strong>Un formateur qui a exercé le métier avant de l'enseigner :</strong> paie et administration du personnel de 580 collaborateurs, puis conseil auprès d'entreprises multi-conventionnelles : des séquences bâties sur des cas réels.</div>
      <div class="cv-bullet"><strong>L'alternance et l'entrée permanente déjà pratiquées :</strong> quatre centres Afpa entre 2016 et 2020, en parcours individualisés et groupes à entrées échelonnées, dans un cadre imposé.</div>
            """.strip()
        elif cat == "RRH_PAIE":
            cv_subtitle = "Responsable Ressources Humaines & Paie | Relations Sociales"
            target_title = f"RESPONSABLE RESSOURCES HUMAINES ET PAIE — {job_title.upper()}"
            summary = "Professionnel senior des Ressources Humaines et du pilotage de la Paie (+15 ans d'expérience) ayant dirigé les RH d'une organisation de 580 collaborateurs (salariés et bénévoles). Maîtrise globale du cycle de paie, des déclarations DSN, du dialogue social (CSE/DP/CE), de la masse salariale et du plan de développement des compétences. Double formation juridique et managériale (Master 2 Droit public, Master RSE en cours)."
            skills = """
      <div class="cv-bullet"><strong>Direction RH & Administration du personnel :</strong> Gestion contractuelle complète, procédures disciplinaires, gestion des temps et des carrières pour 580 collaborateurs.</div>
      <div class="cv-bullet"><strong>Supervision de la Paie & Déclarations DSN :</strong> Sécurisation des cycles de paie, déclarations sociales dématérialisées, audit de paie et contrôle Urssaf.</div>
      <div class="cv-bullet"><strong>Dialogue Social & Relations Collectives :</strong> Animation des réunions CSE/CE/DP, négociations d'accords d'entreprise, gestion des conflits et veille en droit du travail.</div>
      <div class="cv-bullet"><strong>Ingénierie de Formation & Qualité :</strong> Dirigeant d'organisme certifié Qualiopi (ICPF QUA007374), élaboration et pilotage du plan de développement des compétences.</div>
            """.strip()
            points_forts = """
      <div class="cv-bullet"><strong>Un cadre RH ayant exercé des responsabilités d'envergure :</strong> Direction opérationnelle et stratégique des RH et de la paie pour 580 collaborateurs avec pilotage de la masse salariale.</div>
      <div class="cv-bullet"><strong>Double compétence juridique et opérationnelle :</strong> Titulaire d'un Master 2 en Droit public, maîtrise éprouvée du logiciel Silae, de la DSN et d'Excel avancé.</div>
      <div class="cv-bullet"><strong>Stabilité exemplaire & atout senior :</strong> Âgé de 59 ans, engagement durable et loyal, éligible aux aides à l'embauche pour demandeurs d'emploi seniors.</div>
            """.strip()
        elif cat == "GESTIONNAIRE_RH":
            cv_subtitle = "Chargé des Ressources Humaines & ADP Senior | Droit Social"
            target_title = f"CHARGÉ DES RESSOURCES HUMAINES ET ADP — {job_title.upper()}"
            summary = "Spécialiste confirmé de l'administration du personnel et du droit social opérationnel avec plus de 15 ans d'expérience. Pilotage complet des formalités d'embauche, des contrats de travail, du suivi des temps et des procédures disciplinaires. Ex-responsable RH de 580 collaborateurs, alliant rigueur juridique, réactivité et posture d'écoute."
            skills = """
      <div class="cv-bullet"><strong>Administration du Personnel & Contrats :</strong> Gestion intégrale des dossiers salariés, DPAE, rédaction des contrats et avenants, suivi des temps et absences.</div>
      <div class="cv-bullet"><strong>Sécurisation Juridique & Veille Sociale :</strong> Application du Code du travail et des conventions collectives, procédures disciplinaires et ruptures conventionnelles.</div>
      <div class="cv-bullet"><strong>Relations Sociales & Climat Social :</strong> Préparation des réunions CSE, dialogue avec les représentants du personnel et maintien du dialogue interne.</div>
      <div class="cv-bullet"><strong>Gestion des Compétences & Outils :</strong> Suivi des entretiens professionnels, intégration des embauchés, maîtrise de Silae, SIRH et Excel.</div>
            """.strip()
            points_forts = """
      <div class="cv-bullet"><strong>Pratique éprouvée du terrain RH :</strong> Gestion administrative et contractuelle pour 580 collaborateurs en environnement multi-sites.</div>
      <div class="cv-bullet"><strong>Rigueur réglementaire :</strong> Diplômé d'un Master 2 en Droit public et d'une Maîtrise en Gestion, garantissant une conformité juridique sans faille.</div>
      <div class="cv-bullet"><strong>Fidélité & Disponibilité :</strong> 59 ans, recherche d'un engagement pérenne, éligible aux aides à l'embauche senior, disponible immédiatement.</div>
            """.strip()
        else: # GESTIONNAIRE_PAIE & COMPTABILITE_SOCIALE
            cv_subtitle = "Gestionnaire de Paie et Droit Social Confirmé"
            target_title = f"GESTIONNAIRE DE PAIE ET DROIT SOCIAL — {job_title.upper()}"
            summary = "Spécialiste autonome de la gestion de la paie et de l'administration du personnel avec plus de 15 ans d'expérience. Maîtrise de bout en bout du cycle de paie, du paramétrage logiciel Silae, du contrôle de cohérence DSN et de la législation sociale. Concepteur d'un parcours certifiant de 758 heures pour le Titre pro Gestionnaire de paie et ex-responsable RH de 580 collaborateurs."
            skills = """
      <div class="cv-bullet"><strong>Production Autonome des Bulletins de Paie :</strong> Collecte des variables, traitement des absences, congés, heures supplémentaires, primes et soldes de tout compte.</div>
      <div class="cv-bullet"><strong>Déclarations Sociales Nominatives (DSN) :</strong> Déclarations mensuelles et événementielles, contrôle des cotisations Urssaf, caisses de retraite et prévoyance.</div>
      <div class="cv-bullet"><strong>Administration du Personnel & Contrats :</strong> DPAE, rédaction des contrats et avenants, attestations France Travail et gestion des dossiers salariés.</div>
      <div class="cv-bullet"><strong>Outils Informatiques & Audit :</strong> Maîtrise opérationnelle du logiciel Silae, expert Excel (tableaux croisés, formules avancées), veille conventionnelle.</div>
            """.strip()
            points_forts = """
      <div class="cv-bullet"><strong>Une expertise paie complète et immédiatement opérationnelle :</strong> Pratique éprouvée du bulletin complexe, de la DSN et du logiciel Silae sans période d'adaptation.</div>
      <div class="cv-bullet"><strong>Un professionnel qui enseigne la matière :</strong> Concepteur du parcours 758h TP Gestionnaire de paie (Qualiopi) et formateur Afpa / Chambres de Métiers.</div>
      <div class="cv-bullet"><strong>Stabilité, engagement & aides senior :</strong> Demandeur d'emploi senior de 59 ans, disponible immédiatement, ouvrant droit aux aides à l'embauche.</div>
            """.strip()

        experiences = """
    <div class="exp-item">
      <div class="exp-header"><span class="exp-job">Formateur et consultant en paie, ressources humaines et droit social</span> | <span class="exp-org">Kairos Formation, organisme certifié Qualiopi, président (2014 - aujourd'hui)</span></div>
      <div class="cv-bullet">Conception et animation de parcours certifiants pour adultes, dont un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie (TP-01254, millésime 04) : référentiel, macro-planning, cadrage des évaluations, déroulés de séance.</div>
      <div class="cv-bullet">Formation de dirigeants et de collaborateurs de TPE et PME à la gestion du personnel : embauche, contrats, apprentissage, paie, DSN, obligations de l'employeur, avec veille réglementaire continue.</div>
      <div class="cv-bullet">Direction d'un organisme certifié Qualiopi : construction de l'offre, conformité au Référentiel National Qualité (ICPF QUA007374), indicateurs, relations avec les financeurs.</div>
    </div>
    <div class="exp-item">
      <div class="exp-header"><span class="exp-job">Formateur en gestion de paie, en sous-traitance pédagogique pour l'Afpa</span> | <span class="exp-org">Centres Afpa de Vervins, Beauvais, Creil et Amiens (2016 - 2020)</span></div>
      <div class="cv-bullet">Interventions sur quatre centres pour le compte d'organismes titulaires du marché : référentiel du donneur d'ordre, outil Métis, évaluations en cours de formation, traçabilité du suivi des stagiaires.</div>
      <div class="cv-bullet">Formation en entrée permanente : groupes à entrées échelonnées et parcours individualisés, organisation proche de celle d'un centre de formation d'apprentis.</div>
    </div>
    <div class="exp-item">
      <div class="exp-header"><span class="exp-job">Responsable des relations sociales et des ressources humaines</span> | <span class="exp-org">Secours Populaire, structure de 580 collaborateurs (2003 - 2010)</span></div>
      <div class="cv-bullet">Paie et administration du personnel de 580 collaborateurs, salariés et bénévoles : contrats, avenants, absences, arrêts de travail, accidents du travail.</div>
      <div class="cv-bullet">Pilotage du plan de formation, conduite de marchés publics RH et formation, animation du dialogue social (CSE/DP/CE).</div>
    </div>
    <div class="exp-item">
      <div class="exp-header"><span class="exp-job">Responsable de site, management opérationnel</span> | <span class="exp-org">ETV, Nouvelle-Calédonie (2010 - 2014)</span></div>
      <div class="cv-bullet">Montage et exploitation d'un site industriel : encadrement des équipes, organisation de la production, conformité réglementaire et prévention des risques.</div>
    </div>
        """.strip()

        html = self.cv_template
        html = html.replace("{{CV_SUBTITLE}}", cv_subtitle)
        html = html.replace("{{TARGET_TITLE}}", target_title)
        html = html.replace("{{SUMMARY}}", summary)
        html = html.replace("{{KEY_SKILLS_HTML}}", skills)
        html = html.replace("{{POINTS_FORTS_HTML}}", points_forts)
        html = html.replace("{{EXPERIENCES_HTML}}", experiences)
        
        return html

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        best_html, _, _ = self.generate_best_of_three_letter(job)
        return best_html
