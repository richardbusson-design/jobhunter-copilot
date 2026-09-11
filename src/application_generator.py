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
        # Si un titre contient 'Collaborateur Comptable' ou 'Comptable', on le recadre strictement sur son volet Paie / Social
        if "comptab" in cleaned.lower() and "paie" not in cleaned.lower():
            cleaned = "Gestionnaire de Paie et Droit Social"
        return cleaned

    def detect_category(self, job: Dict[str, Any]) -> str:
        text = (job.get("title", "") + " " + job.get("description", "")).lower()
        if "formateur" in text or "formatrice" in text or "pédagogique" in text or "coordinateur de formation" in text or "cfa" in text:
            return "FORMATEUR_PAIE_RH"
        elif "responsable rh" in text or "responsable des ressources" in text or "rrh" in text or "responsable du développement rh" in text or "responsable paie" in text:
            return "RRH_PAIE"
        elif "chargé rh" in text or "chargé des ressources" in text or "gestionnaire rh" in text or "gestionnaire adp" in text:
            return "GESTIONNAIRE_RH"
        else:
            # 100% Gestionnaire de Paie et Droit Social (ZÉRO comptabilité pure)
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
        company = job.get("company", "votre entreprise").replace('"', '').strip()
        raw_title = job.get("title", "Poste RH & Paie")
        job_title = self.clean_job_title(raw_title)
        city = job.get("city", "").strip()
        postal_code = str(job.get("postal_code", "")).strip()
        desc = (job.get("description", "") + " " + job.get("title", "") + " " + job.get("company", "")).lower()
        
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
            
        if city:
            loc_line = f"{postal_code} {city}".strip() if postal_code else city
            recipient_body_lines.append(f"<div>{loc_line}</div>")
        
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
            politesse_formula = "Je vous prie d’agréer, Madame, Monsieur, l’expression de mes salutations distinguées."

        # Détection sémantique fine de l'offre
        overseas_terms = [r"\bmayotte\b", r"\bouangani\b", r"\bmamoudzou\b", r"\bcalédonie\b", r"\bguadeloupe\b", r"\bmartinique\b", r"\bguyane\b", r"\bdom-tom\b", r"\boutre-mer\b"]
        is_mayotte_or_dom = (
            any(re.search(term, desc) for term in overseas_terms)
            or "la réunion" in desc or "île de la réunion" in desc
            or any(c in city.lower() for c in ["ouangani", "mamoudzou", "nouméa", "cayenne", "fort-de-france", "pointe-à-pitre"])
            or any(postal_code.startswith(d) for d in ["971", "972", "973", "974", "976", "988"])
        )
        is_industry = any(k in desc for k in ["industr", "agro", "avicole", "production", "usine", "fabrication", "métallurg", "technique", "chantier", "btp", "logistique", "transport"])
        is_medico_social = any(k in desc for k in ["santé", "médico-social", "hospital", "ehpad", "clinique", "associat", "ccas", "enfance", "handicap", "sociale"])
        is_formation = (cat == "FORMATEUR_PAIE_RH") or any(k in desc for k in ["formateur", "formatrice", "formation", "pédagogique", "cfa", "apprenant", "alternant", "enseignement"])
        is_cse_social = any(k in desc for k in ["cse", "relations sociales", "dialogue social", "accords", "nao", "conflit", "climat social", "délégué", "représentant", "syndic"])
        is_silae = "silae" in desc
        is_gta = any(k in desc for k in ["gta", "temps de travail", "gestion des temps", "absences", "congés", "pointage", "planning"])
        is_externalized = any(k in desc for k in ["externalis", "prestataire", "cabinet"])
        is_excel = any(k in desc for k in ["excel", "tableaux de bord", "reporting", "indicateur", "indicateurs"])

        loc_mention = f" à {city}" if city and city.lower() not in ["france", "inconnu", "none"] else ""
        job_object_clean = f"Candidature au poste de {job_title}"

        # ----------------- PARAGRAPHE 1 : Accroche & Résonance -----------------
        if is_formation:
            p1 = f"Votre recherche d'un {job_title}{loc_mention} au sein de {company} a retenu toute mon attention. Acteur reconnu dans le développement des compétences et la formation professionnelle, votre organisme représente un cadre d'excellence dont je mesure pleinement les exigences pédagogiques, la rigueur méthodologique et la volonté d'accompagner des apprenants vers une qualification certifiante reconnue."
        elif is_mayotte_or_dom:
            p1 = f"Votre recherche d'un {job_title}{loc_mention} au sein de {company} a retenu toute mon attention. Acteur de référence dans son domaine d'activité{loc_mention}, votre structure combine des enjeux d'organisation opérationnelle, de dialogue de proximité et de conformité sociale rigoureuse. C'est avec un vif intérêt que je vous propose mon expertise RH généraliste, ma pratique de la paie et mon sens de l'accompagnement pour soutenir durablement vos équipes."
        elif is_industry:
            p1 = f"Votre recherche d'un {job_title}{loc_mention} au sein de {company} correspond exactement à mes compétences et à mon projet professionnel. Entreprise industrielle dynamique aux exigences de production soutenues, votre structure requiert un pilotage RH réactif, une présence active auprès des équipes opérationnelles et une sécurisation rigoureuse de la gestion sociale dans le strict respect des cadences et du cadre conventionnel."
        elif is_medico_social:
            p1 = f"Votre recherche d'un {job_title}{loc_mention} au sein de {company} a retenu toute mon attention. Structure engagée aux missions humaines essentielles, votre établissement requiert une gestion des ressources humaines attentive et rigoureuse, capable de concilier la fidélisation des collaborateurs, l'accompagnement des encadrants et le strict respect des conventions collectives du secteur médico-social."
        elif cat == "RRH_PAIE":
            p1 = f"Votre offre d'emploi pour le poste de {job_title}{loc_mention} au sein de {company} retient toute mon attention. Organisation exigeante aux enjeux humains et organisationnels majeurs, votre structure recherche un professionnel chevronné capable de prendre en charge le pilotage global des ressources humaines tout en garantissant une maîtrise sans faille des cycles de paie et de la conformité réglementaire."
        else:
            p1 = f"Votre recherche d'un {job_title}{loc_mention} au sein de {company} correspond parfaitement à mes compétences et à mon projet professionnel. Entreprise reconnue dans son domaine, votre structure requiert une autonomie complète, une rigueur irréprochable dans le traitement des données du personnel et une capacité d'adaptation immédiate à vos processus de gestion sociale."

        # ----------------- PARAGRAPHE 2 : Cœur de métier technique -----------------
        if is_formation:
            if variant_index == 2:
                p2 = "Formateur spécialisé en paie et ressources humaines, j'anime sans période d'adaptation les cursus certifiants (Titre professionnel Gestionnaire de paie, blocs RH de l'ADEA et du Brevet de Maîtrise). Mon enseignement s'appuie sur des cas d'entreprise réels : analyse des conventions collectives, paramétrage sur logiciel Silae, télédéclarations DSN et gestion contractuelle. Je veille scrupuleusement à l'acquisition des bons réflexes professionnels et au respect des critères d'évaluation des compétences."
            else:
                p2 = "Mon parcours allie une longue expérience de terrain à une pratique éprouvée de l'enseignement. Je maîtrise de bout en bout l'animation des blocs RH et Paie, depuis l'embauche du premier salarié jusqu'à la production du bulletin, le contrôle approfondi de la DSN et le suivi des obligations de l'employeur. Rompu à la pédagogie active auprès d'adultes en reconversion et d'alternants, je sais contextualiser chaque règle juridique et chaque calcul pour garantir une assimilation rapide et pérenne des compétences du référentiel."
        elif is_mayotte_or_dom:
            p2 = "Au fil de mon parcours professionnel, j'ai développé une pratique approfondie de l'administration du personnel et de la sécurisation contractuelle. De la rédaction des contrats et des avenants au suivi des temps et activités (GTA), jusqu'à la collecte rigoureuse des variables de paie et la coordination avec les prestataires sociaux, je garantis un traitement fiable et réactif des dossiers individuels. Mon niveau avancé sur Excel représente également un appui direct pour modéliser vos tableaux de bord, piloter les indicateurs sociaux et fiabiliser le reporting opérationnel."
        elif cat == "GESTIONNAIRE_PAIE":
            tool_mention = "du logiciel Silae et des plateformes déclaratives" if is_silae else "des principaux logiciels de paie (notamment Silae) et des outils SIRH"
            p2 = f"De la collecte méthodique des éléments variables jusqu'au virement des salaires et au contrôle approfondi des déclarations DSN (mensuelles, arrêts de travail, fins de contrat), je supervise l'intégralité du cycle de paie en parfaite autonomie. Ma pratique approfondie {tool_mention} me permet de gérer les régularisations complexes, d'anticiper les évolutions de plafonds et d'assurer des relations fluides avec l'Urssaf et les organismes de prévoyance. Sur le volet administratif, j'assure le suivi des entrées/sorties, les déclarations d'embauche et les soldes de tout compte."
        elif cat == "GESTIONNAIRE_RH":
            p2 = "Au fil de mon parcours, j'ai pris en charge l'ensemble des formalités d'administration du personnel et du suivi contractuel : préparation des contrats de travail et avenants, déclarations préalables à l'embauche, suivi des périodes d'essai, gestion des temps et des absences (GTA) et organisation des visites médicales. En interface permanente avec la paie, je fiabilise la transmission des variables et le suivi des dossiers individuels, tout en assurant un rôle d'écoute et d'information auprès des collaborateurs et des managers opérationnels."
        else: # RRH_PAIE
            p2 = "Généraliste confirmé des ressources humaines, je supervise l'ensemble des volets administratifs, juridiques et financiers de la fonction. De la sécurisation des contrats de travail et du suivi des procédures disciplinaires jusqu'au contrôle méthodique des cycles de paie et des déclarations DSN, je veille à la conformité absolue de chaque dossier. Ma maîtrise du logiciel Silae et des outils de reporting Excel me permet de piloter la masse salariale avec précision et d'éclairer les arbitrages de la direction par des indicateurs sociaux pertinents."

        # ----------------- PARAGRAPHE 3 : Envergure & Terrain -----------------
        if is_mayotte_or_dom:
            p3 = "J'ai exercé ces missions avec un haut niveau de responsabilité : de 2003 à 2010, j'ai dirigé les relations sociales et les ressources humaines d'une structure de 580 collaborateurs, salariés et bénévoles. J'y ai piloté les instances représentatives du personnel (CSE, DP, CE) et instauré un dialogue social serein fondé sur l'écoute et l'équité. De 2010 à 2014, j'ai en outre dirigé un site industriel ETV en Nouvelle-Calédonie, encadrant jusqu'à 50 personnes en environnement d'usine. Cette expérience réussie outre-mer me confère une parfaite compréhension des impératifs logistiques, humains et culturels d'une exploitation insulaire."
        elif is_formation:
            p3 = "J'ai exercé ce métier avec une responsabilité directe avant de l'enseigner : de 2003 à 2010, j'ai dirigé les ressources humaines et la paie d'une structure de 580 collaborateurs, salariés et bénévoles, en y pilotant l'administration, le plan de formation et le dialogue social. Par ailleurs, entre 2016 et 2020, je suis intervenu sur quatre centres Afpa (Vervins, Beauvais, Creil et Amiens), avec référentiel imposé, outil Métis, parcours individualisés et passage régulier des évaluations en cours de formation (ECF). Ce double ancrage professionnel donne à mes interventions un réalisme immédiatement apprécié."
        elif is_cse_social or cat == "RRH_PAIE":
            p3 = "J'ai exercé ces missions avec un haut niveau d'exigence : de 2003 à 2010, j'ai dirigé les ressources humaines d'une structure de 580 collaborateurs, salariés et bénévoles. J'y ai piloté les instances représentatives du personnel (CSE, DP, CE), conduit les négociations d'accords collectifs et animé le dialogue social quotidien dans un climat d'écoute et de respect mutuel. Cette pratique éprouvée du terrain m'a conféré une grande aisance relationnelle, une forte capacité de médiation et le réflexe d'accompagner les managers opérationnels dans la gestion quotidienne de leurs équipes."
        else:
            p3 = "J'ai exercé ce métier avec une responsabilité d'envergure : de 2003 à 2010, j'ai piloté l'administration du personnel, la paie et les relations sociales d'une structure de 580 collaborateurs, salariés et bénévoles. Cette expérience m'a appris à gérer des volumes importants avec méthode, à traiter les situations sensibles avec diplomatie et à instaurer une relation de confiance durable avec les salariés comme avec les représentants du personnel. De 2010 à 2014, j'ai également dirigé un site opérationnel de 50 collaborateurs en environnement industriel, renforçant mon sens de la réactivité et du résultat."

        # ----------------- PARAGRAPHE 4 : Qualiopi, Droit public, Atout Senior & Disponibilité -----------------
        loc_disp = f"pour une installation sur place" if is_mayotte_or_dom else "sur l'ensemble de votre secteur géographique"
        if is_formation:
            p4 = f"Dirigeant d'un organisme certifié Qualiopi (ICPF QUA007374), j'ai conçu de bout en bout un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie (TP-01254). Titulaire d'un Master 2 en Droit public et d'une Maîtrise en Sciences de Gestion, j'apporte une double expertise juridique et managériale garantissant des contenus rigoureusement actualisés et conformes aux dernières réformes du droit du travail. À 59 ans, j'inscris ma candidature dans un engagement loyal, pérenne et constructif, tout en ouvrant droit aux aides à l'embauche pour demandeur d'emploi senior. Titulaire du permis B, immédiatement disponible et parfaitement mobile {loc_disp}, je serais honoré d'échanger avec vous lors d'un entretien pour étudier les modalités concrètes de notre future collaboration."
        else:
            p4 = f"Dirigeant d'un organisme certifié Qualiopi où j'ai conçu et déployé un parcours de 758 heures préparant au Titre professionnel Gestionnaire de paie, je possède une solide expertise dans la formalisation des procédures et l'accompagnement des compétences. Titulaire d'un Master 2 en Droit public et d'une Maîtrise en Sciences de Gestion, j'assure une veille sociale rigoureuse pour sécuriser vos pratiques au quotidien : rédaction des accords, gestion des procédures disciplinaires, sécurisation des départs et conformité face aux audits et contrôles administratifs. À 59 ans, je privilégie un engagement loyal et durable, ouvrant droit aux aides à l'embauche senior. Titulaire du permis B, immédiatement disponible et parfaitement mobile {loc_disp}, je serais honoré de vous rencontrer lors d'un entretien approfondi."

        paragraphs_html = f"<p>{p1}</p>\n<p>{p2}</p>\n<p>{p3}</p>\n<p>{p4}</p>"

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

    def render_letter_html(self, job: Dict[str, Any]) -> str:
        best_html, _, _ = self.generate_best_of_three_letter(job)
        return best_html

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
        else: # GESTIONNAIRE_PAIE (100% Paie & Droit Social)
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

    def render_motivation_text(self, job: Dict[str, Any]) -> str:
        """Génère le texte court de motivation pour les formulaires web (France Travail / Apec)."""
        raw_title = job.get("title", "Responsable RH et Paie")
        job_title = self.clean_job_title(raw_title)
        company = job.get("company", "votre organisme")
        city = job.get("city", "votre secteur")
        contact_title = job.get("contact_title", "")
        contact_name = job.get("contact_name", "")
        
        formula = "Madame, Monsieur,"
        if "directeur" in contact_title.lower() or "directeur" in contact_name.lower():
            formula = "Monsieur le Directeur,"
        elif "directrice" in contact_title.lower() or "directrice" in contact_name.lower():
            formula = "Madame la Directrice,"
            
        return f"""{formula}

Titulaire d'un Master 2 en Droit public et fort d'une expérience probante de direction des Ressources Humaines et de la paie (580 collaborateurs), j'ai l'honneur de vous soumettre ma candidature au poste de {job_title} au sein de {company}.

Familier des enjeux opérationnels, juridiques et conventionnels de la fonction, je maîtrise l'ensemble des missions attendues : la sécurisation des processus RH, le dialogue social constructif et serein avec les instances représentatives (CSE), l'administration du personnel et la supervision irréprochable de la paie et de la DSN. Dirigeant par ailleurs un organisme de formation certifié Qualiopi, j'allie rigueur juridique, sens de l'humain et vision stratégique.

À 59 ans, en recherche d'un engagement durable et loyal, et éligible aux aides à l'embauche pour demandeur d'emploi senior, je suis immédiatement disponible pour échanger à {city}.

Dans l'attente de votre retour, je vous prie d'agréer l'expression de ma considération distinguée.

Richard BUSSON
09 39 20 08 70 • richard.busson@kairos-paye.fr"""

