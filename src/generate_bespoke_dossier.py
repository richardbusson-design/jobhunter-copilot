# -*- coding: utf-8 -*-
"""
Générateur chirurgical de candidatures sur-mesure (QualityGuard 3-Pass)
Produit les 6 fichiers réglementaires (HTML, PDF, PNG) calibrés pleine page A4 (794x1123px)
pour Richard BUSSON selon le standard hybride AltaCV x Awesome-CV et norme AFNOR.
"""

import os
import re
import asyncio
from playwright.async_api import async_playwright

SIGNATURE_PATH = r"C:\Users\richa\JobHunter\assets\signature_rb.png"

def build_cv_html(offer: dict) -> str:
    title = offer.get("title", "Enseignant en Économie-Gestion")
    academie = offer.get("academie", "Éducation Nationale")
    ref = offer.get("reference", "")
    location = offer.get("location", academie)

    # Détection de la spécialité
    spec = "Filière STMG & BTS"
    if "rh" in title.lower() or "grh" in title.lower():
        spec = "Spécialité Ressources Humaines & Organisation (L8011)"
    elif "marketing" in title.lower() or "vente" in title.lower() or "commerce" in title.lower():
        spec = "Spécialité Mercatique & Commerce (L8013)"
    elif "finance" in title.lower() or "comptab" in title.lower():
        spec = "Spécialité Gestion et Finance (L8012)"
    elif "sam" in title.lower():
        spec = "BTS Support à l'Action Managériale (SAM)"
    elif "sio" in title.lower():
        spec = "BTS Services Informatiques aux Organisations (SIO)"

    bottom_third_title = f"Affectation Immédiate & Priorité {academie}"
    bottom_third_desc = f"Mobilité totale acceptée sur l'ensemble de l'académie. Prise de service immédiate sans préavis sur les besoins d'enseignement en lycée."

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>CV Richard BUSSON - {title}</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  html, body {{
    width: 794px;
    height: 1123px;
    max-height: 1123px;
    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    overflow: hidden;
  }}

  /* 1. EN-TÊTE SUPÉRIEUR EXÉCUTIF */
  .header {{
    background: linear-gradient(135deg, #091e36 0%, #152e50 60%, #1c3d69 100%);
    color: #ffffff;
    padding: 13px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3.5px solid #d4af37;
    height: 104px;
  }}
  .header-left h1 {{
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #ffffff;
    margin-bottom: 3px;
    line-height: 1.1;
  }}
  .header-left .title-sub {{
    font-size: 13.5px;
    font-weight: 700;
    color: #f1c40f;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    margin-bottom: 3px;
  }}
  .header-left .title-tagline {{
    font-size: 11px;
    color: #cbd5e1;
    font-weight: 500;
  }}
  .header-right {{
    text-align: right;
    font-size: 10.5px;
    line-height: 1.45;
    color: #e2e8f0;
    border-left: 1.5px solid rgba(212, 175, 55, 0.45);
    padding-left: 14px;
  }}
  .header-right strong {{
    color: #ffffff;
  }}
  .header-right a {{
    color: #67e8f9;
    text-decoration: none;
  }}

  /* 2. CORPS EN 2 COLONNES ASYMÉTRIQUES */
  .main-container {{
    display: flex;
    width: 794px;
    height: 1019px;
    background-color: #ffffff;
  }}

  /* COLONNE GAUCHE (35%) */
  .sidebar {{
    width: 268px;
    background-color: #f8fafc;
    border-right: 1.5px solid #e2e8f0;
    padding: 12px 14px 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 9px;
  }}
  .side-section {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 8.5px 10px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }}
  .side-title {{
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    color: #0f2b48;
    border-bottom: 2px solid #d4af37;
    padding-bottom: 3.5px;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
  }}
  .badge-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 3.5px;
  }}
  .badge {{
    background-color: #f1f5f9;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    font-size: 9px;
    font-weight: 600;
    padding: 2.5px 5.5px;
    border-radius: 3px;
    line-height: 1.2;
  }}
  .badge-gold {{
    background-color: #fef9c3;
    color: #854d0e;
    border-color: #fde047;
    font-weight: 700;
  }}
  .side-item {{
    margin-bottom: 5.5px;
    font-size: 9.8px;
    line-height: 1.35;
    color: #334155;
  }}
  .side-item:last-child {{
    margin-bottom: 0;
  }}
  .side-item-title {{
    font-weight: 700;
    color: #0f2b48;
    font-size: 10px;
  }}
  .side-item-sub {{
    color: #64748b;
    font-size: 9px;
    font-style: italic;
  }}

  /* COLONNE DROITE (65%) */
  .content {{
    width: 526px;
    padding: 12px 18px 10px 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    background-color: #ffffff;
  }}
  .section-banner {{
    background: linear-gradient(90deg, #0f2b48 0%, #1e3a8a 100%);
    color: #ffffff;
    font-size: 11.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 4.5px 9px;
    border-radius: 4px;
    border-left: 3.5px solid #d4af37;
    margin-bottom: 2px;
  }}
  .exp-card {{
    border-left: 3px solid #cbd5e1;
    padding-left: 10px;
    margin-bottom: 2px;
    position: relative;
  }}
  .exp-card:hover {{
    border-left-color: #1e3a8a;
  }}
  .exp-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1.5px;
  }}
  .exp-role {{
    font-size: 11.2px;
    font-weight: 800;
    color: #0f2b48;
  }}
  .exp-date {{
    font-size: 9.8px;
    font-weight: 700;
    color: #b45309;
    background: #fef3c7;
    padding: 1px 5px;
    border-radius: 3px;
  }}
  .exp-org {{
    font-size: 10px;
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 2px;
  }}
  .exp-bullets {{
    list-style-type: none;
    padding-left: 0;
  }}
  .exp-bullets li {{
    font-size: 9.5px;
    line-height: 1.34;
    color: #334155;
    position: relative;
    padding-left: 11px;
    margin-bottom: 2px;
  }}
  .exp-bullets li::before {{
    content: "▪";
    color: #d4af37;
    font-size: 11px;
    position: absolute;
    left: 0;
    top: -1px;
  }}
  .exp-bullets li strong {{
    color: #0f172a;
    font-weight: 700;
  }}

  /* BAS DE PAGE COLONNE DROITE (CARTOUCHES COMPACTS) */
  .focus-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-top: 2.5px solid #1e3a8a;
    border-radius: 4px;
    padding: 6.5px 9px;
  }}
  .focus-title {{
    font-size: 10.2px;
    font-weight: 800;
    color: #0f2b48;
    text-transform: uppercase;
    margin-bottom: 2.5px;
  }}
  .focus-text {{
    font-size: 9.2px;
    line-height: 1.35;
    color: #334155;
  }}
</style>
</head>
<body>

  <!-- EN-TÊTE -->
  <header class="header">
    <div class="header-left">
      <h1>Richard BUSSON</h1>
      <div class="title-sub">Enseignant Économie et Gestion · {spec}</div>
      <div class="title-tagline">Maîtrise Sciences de Gestion · Master 2 Droit Public · Dirigeant Qualiopi · 580 collab.</div>
    </div>
    <div class="header-right">
      <div>📍 <strong>Creil (60)</strong> — Mobilité Active & Permis B</div>
      <div>📞 <strong>09 39 20 08 70</strong> · 07 61 96 15 46</div>
      <div>✉️ <a href="mailto:richard.busson@kairos-paye.fr">richard.busson@kairos-paye.fr</a></div>
      <div>🌐 <a href="https://kairos-paye.fr">kairos-paye.fr</a> · linkedin.com/in/richard-busson</div>
      <div>⚡ Disponibilité : <strong>Immédiate sans préavis</strong></div>
    </div>
  </header>

  <!-- CORPS -->
  <main class="main-container">
    <!-- COLONNE GAUCHE (35%) -->
    <aside class="sidebar">
      <div class="side-section">
        <div class="side-title">Profil & Posture Civique</div>
        <div class="side-item">
          <strong>59 ans · Cadre Senior Expérimenté</strong><br>
          Grande loyauté, engagement républicain, pédagogie bienveillante et rigueur méthodologique.
        </div>
        <div class="side-item">
          <strong>Transmission & Pédagogie Active :</strong><br>
          Ancrage des notions académiques dans des cas concrets d'entreprise et d'actualité économique.
        </div>
      </div>

      <div class="side-section">
        <div class="side-title">Compétences Éco-Gestion</div>
        <div class="badge-grid">
          <span class="badge badge-gold">Management STMG</span>
          <span class="badge badge-gold">Économie & Droit</span>
          <span class="badge badge-gold">Ressources Humaines</span>
          <span class="badge">Gestion & Finance</span>
          <span class="badge">Sciences de Gestion</span>
          <span class="badge">Droit du Travail & Public</span>
          <span class="badge">Organisation & Stratégie</span>
          <span class="badge">Communication Managériale</span>
          <span class="badge">Logiciels Métiers & Silae</span>
          <span class="badge">Contrôle de Gestion</span>
          <span class="badge">Audit Social</span>
          <span class="badge">Démarche RSE / IAE</span>
        </div>
      </div>

      <div class="side-section">
        <div class="side-title">Ingénierie & Outils Éducatifs</div>
        <div class="side-item">
          <strong>Conformité Pédagogique Qualiopi :</strong><br>
          Conception intégrale de référentiels (758h), animation de groupes et évaluations formatives ECF.
        </div>
        <div class="side-item">
          <strong>Systèmes & Didactique :</strong><br>
          Outil Métis (Afpa), ENT, pédagogie par projet, études de cas numériques, différenciation pédagogique.
        </div>
      </div>

      <div class="side-section">
        <div class="side-title">Formation Supérieure</div>
        <div class="side-item">
          <div class="side-item-title">Master RSE (En cours)</div>
          <div class="side-item-sub">IAE Paris - Sorbonne Business School</div>
        </div>
        <div class="side-item">
          <div class="side-item-title">Master 2 Droit Public</div>
          <div class="side-item-sub">Univ. Picardie Jules Verne · Mention Droit</div>
        </div>
        <div class="side-item">
          <div class="side-item-title">Maîtrise Sciences de Gestion</div>
          <div class="side-item-sub">Univ. Paris XIII · Option Finance & RH</div>
        </div>
        <div class="side-item">
          <div class="side-item-title">DUT GEA option RH</div>
          <div class="side-item-sub">Univ. Paris XIII · Gestion des Entreprises</div>
        </div>
      </div>
    </aside>

    <!-- COLONNE DROITE (65%) -->
    <section class="content">
      <div class="section-banner">Expériences Professionnelles & Réalisations Terrain</div>

      <!-- Expérience 1 -->
      <div class="exp-card">
        <div class="exp-header">
          <span class="exp-role">Dirigeant & Formateur Référent Éco-Gestion / RH</span>
          <span class="exp-date">Depuis 2014</span>
        </div>
        <div class="exp-org">Kairos Formation · Organisme Certifié Qualiopi (Paris & Creil)</div>
        <ul class="exp-bullets">
          <li><strong>Ingénierie de formation complète :</strong> Conception et animation d'un parcours certifiant de 758 heures (Titre pro TP-01254 millésime 04) combinant économie, gestion, droit social et paie.</li>
          <li><strong>Pédagogie active & insertion :</strong> Encadrement d'apprenants adultes et jeunes, préparation intensive aux jurys d'examen officiels, 100% de conformité aux référentiels d'État.</li>
          <li><strong>Animation consulaire (CMA) :</strong> Enseignement des modules d'organisation, gestion d'entreprise et relations professionnelles (ADEA et Brevet de Maîtrise).</li>
        </ul>
      </div>

      <!-- Expérience 2 -->
      <div class="exp-card">
        <div class="exp-header">
          <span class="exp-role">Formateur Vacataire & Sous-traitant Enseignement Tertiaire</span>
          <span class="exp-date">2016 – 2020</span>
        </div>
        <div class="exp-org">Centres Afpa (Creil, Beauvais, Amiens, Vervins)</div>
        <ul class="exp-bullets">
          <li><strong>Animation en filière tertiaire administrative :</strong> Gestion de promotions individualisées à entrées permanentes sur les matières de gestion, droit et administration.</li>
          <li><strong>Digitalisation & suivi individualisé :</strong> Déploiement actif de l'outil Métis, conception de livrets d'Évaluation en Cours de Formation (ECF), remédiation personnalisée.</li>
        </ul>
      </div>

      <!-- Expérience 3 -->
      <div class="exp-card">
        <div class="exp-header">
          <span class="exp-role">Responsable des Ressources Humaines & Gestion Sociale</span>
          <span class="exp-date">2003 – 2010</span>
        </div>
        <div class="exp-org">Secours Populaire Français · Pilotage RH de 580 Collaborateurs</div>
        <ul class="exp-bullets">
          <li><strong>Direction opérationnelle des RH :</strong> Pilotage intégral des contrats de travail, dialogue social soutenu avec les instances représentatives (CSE, CE, DP), gestion de crise.</li>
          <li><strong>Gestion prévisionnelle & Masse salariale :</strong> Élaboration du plan de formation, animation de séminaires internes, supervision budgétaire et juridique stricte.</li>
        </ul>
      </div>

      <!-- Expérience 4 -->
      <div class="exp-card">
        <div class="exp-header">
          <span class="exp-role">Responsable de Site Opérationnel & Gestion d'Exploitation</span>
          <span class="exp-date">2010 – 2014</span>
        </div>
        <div class="exp-org">ETV Nouvelle-Calédonie · Exploitation Industrielle & Environnement</div>
        <ul class="exp-bullets">
          <li><strong>Gestion d'un centre de profit :</strong> Pilotage budgétaire, management d'équipes pluridisciplinaires, négociation avec les autorités publiques locales et partenaires.</li>
        </ul>
      </div>

      <!-- 3 CARTES DE BAS DE PAGE -->
      <div class="focus-box">
        <div class="focus-title">Valeur Ajoutée pour les Élèves de STMG & BTS</div>
        <div class="focus-text">Capacité prouvée à vulgariser la réalité concrète de l'entreprise moderne (organigrammes, flux économiques, dialogue social, obligations fiscales et comptables). Préparation rigoureuse des lycéens aux épreuves du baccalauréat et à la poursuite d'études supérieures.</div>
      </div>

      <div class="focus-box">
        <div class="focus-title">Pédagogie Républicaine & Cadre Éducatif</div>
        <div class="focus-text">Autorité naturelle bienveillante, sens élevé du service public, transmission des principes de laïcité et de civisme, accompagnement bienveillant pour la réussite de chaque jeune.</div>
      </div>

      <div class="focus-box">
        <div class="focus-title">{bottom_third_title}</div>
        <div class="focus-text">{bottom_third_desc}</div>
      </div>
    </section>
  </main>

</body>
</html>"""
    return html

def build_lettre_html(offer: dict) -> str:
    title = offer.get("title", "Enseignant en Économie-Gestion")
    academie = offer.get("academie", "Académie compétente")
    ref = offer.get("reference", "")
    location = offer.get("location", academie)

    # Titre du destinataire
    recipient_title = f"Monsieur le Recteur / Madame la Rectrice<br>Rectorat de l'{academie}<br>Direction des Personnels Enseignants"
    if "DPE" in offer.get("raw_card", ""):
        recipient_title = f"Monsieur le Recteur / Madame la Rectrice<br>Rectorat de l'{academie}<br>Service DPE - Gestion des contractuels"

    ref_mention = f" (Réf. {ref})" if ref else ""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Lettre de Motivation - Richard Busson</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: Calibri, "Segoe UI", Arial, Helvetica, sans-serif;
      font-size: 11pt;
      line-height: 1.52;
      color: #000000;
      background: #ffffff;
      width: 794px;
      height: 1123px;
      margin: 0 auto;
      padding: 34px 48px 24px 48px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }}
    .header-container {{
      width: 100%;
      margin-bottom: 8px;
    }}
    .sender-box {{
      width: 48%;
      text-align: left;
      font-size: 10.5pt;
      line-height: 1.38;
      color: #111111;
    }}
    .sender-name {{
      color: #000000;
      font-size: 11.5pt;
      font-weight: bold;
      letter-spacing: 0.02em;
      text-align: left;
    }}
    .recipient-box {{
      width: 50%;
      margin-left: auto;
      margin-top: 12px;
      text-align: left;
      font-size: 10.5pt;
      line-height: 1.38;
      color: #111111;
      padding-left: 10px;
    }}
    .recipient-name {{
      color: #000000;
      font-size: 11.5pt;
      font-weight: bold;
      letter-spacing: 0.02em;
      text-align: left;
    }}
    .date-box {{
      width: 100%;
      text-align: right;
      font-size: 10.5pt;
      color: #222222;
      margin-top: 10px;
      margin-bottom: 12px;
    }}
    .subject-box {{
      width: 100%;
      font-size: 11pt;
      font-weight: bold;
      color: #000000;
      background-color: #f4f6f9;
      padding: 8px 12px;
      border-left: 3.5px solid #1a365d;
      margin-bottom: 14px;
      line-height: 1.35;
    }}
    .body-content {{
      width: 100%;
      text-align: justify;
      hyphens: auto;
      margin-bottom: 8px;
    }}
    .body-content p {{
      margin-bottom: 10px;
      font-size: 10.8pt;
      line-height: 1.5;
      color: #1a1a1a;
    }}
    .footer-container {{
      width: 100%;
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .attachments {{
      font-size: 9.5pt;
      color: #444444;
      line-height: 1.4;
      text-align: left;
    }}
    .signature-block {{
      text-align: right;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }}
    .signature-name {{
      font-size: 11pt;
      font-weight: bold;
      color: #000000;
      margin-bottom: 4px;
    }}
    .signature-img {{
      height: 48px;
      width: auto;
      object-fit: contain;
    }}
  </style>
</head>
<body>

  <!-- EXPÉDITEUR ET DESTINATAIRE -->
  <div class="header-container">
    <div class="sender-box">
      <div class="sender-name">Richard BUSSON</div>
      <div>98, allée Paul Cézanne</div>
      <div>60100 Creil</div>
      <div>Tél. : 09 39 20 08 70 · 07 61 96 15 46</div>
      <div>Courriel : richard.busson@kairos-paye.fr</div>
      <div>Site : kairos-paye.fr</div>
    </div>
    <div class="recipient-box">
      <div class="recipient-name">{recipient_title}</div>
      <div>{location}</div>
    </div>
  </div>

  <!-- DATE -->
  <div class="date-box">
    Creil, le 15 septembre 2026
  </div>

  <!-- OBJET -->
  <div class="subject-box">
    Objet : Candidature au poste d'{title}{ref_mention}
  </div>

  <!-- CORPS STRICTEMENT SANS AUCUN CARACTÈRE GRAS -->
  <div class="body-content">
    <p>Monsieur le Recteur, Madame la Rectrice,</p>

    <p>Le développement des compétences économiques, juridiques et managériales au sein de la filière technologique constitue un enjeu déterminant pour la réussite et l'orientation des lycéens. Pleinement conscient des exigences académiques portées par votre rectorat pour assurer la continuité pédagogique au sein des établissements scolaires, je vous soumets avec un grand engagement ma candidature en qualité de professeur contractuel d'économie et gestion.</p>

    <p>Titulaire d'une Maîtrise en Sciences de Gestion complétée par un Master 2 en Droit public et une formation continue en Responsabilité Sociétale des Entreprises à l'IAE de Paris, je dispose d'une solide assise théorique couvrant l'ensemble du programme de la filière STMG et des cursus tertiaires : économie générale, droit du travail et des contrats, management des organisations, sciences de gestion, gestion des ressources humaines et comptabilité. Ce socle pluridisciplinaire me permet d'aborder chaque notion avec rigueur tout en reliant les concepts aux réalités contemporaines du tissu économique.</p>

    <p>Mon parcours professionnel conjugue plus de dix ans de direction opérationnelle, notamment à la tête des ressources humaines d'une structure de 580 collaborateurs et la direction d'un site d'exploitation, avec une pratique pédagogique confirmée depuis 2014. Dirigeant d'un organisme de formation certifié Qualiopi préparant aux diplômes d'État et formateur sous-traitant pour l'Afpa, j'ai développé une solide maîtrise de la didactique professionnelle, des évaluations certificatives et des outils numériques éducatifs. Cette double culture de l'entreprise et de la pédagogie me confère une capacité démontrée à capter l'intérêt des élèves, à contextualiser les enseignements par des cas vivants et à maintenir un climat de classe propice au travail et à la bienveillance républicaine.</p>

    <p>Rigoureux, loyal, disponible immédiatement sans préavis et titulaire du permis de conduire, je serais honoré de mettre mon énergie, mon sens aigu du service public et mon expérience au service de la réussite scolaire et civique des lycéens de votre académie. Dans l'attente d'un échange lors d'un entretien à votre convenance, je vous prie d'agréer, Monsieur le Recteur, Madame la Rectrice, l'expression de ma haute considération.</p>
  </div>

  <!-- BAS DE PAGE -->
  <div class="footer-container">
    <div class="attachments">
      P.J. : Curriculum Vitae complet, Diplômes nationaux, Passeport
    </div>
    <div class="signature-block">
      <div class="signature-name">Richard BUSSON</div>
      <img src="{SIGNATURE_PATH}" alt="Signature" class="signature-img">
    </div>
  </div>

</body>
</html>"""
    return html

async def generate_dossier_files(offer: dict, output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    
    cv_html_path = os.path.join(output_dir, "CV_Richard_BUSSON.html")
    cv_pdf_path = os.path.join(output_dir, "CV_Richard_BUSSON.pdf")
    cv_png_path = os.path.join(output_dir, "CV_Richard_BUSSON.png")

    lm_html_path = os.path.join(output_dir, "Lettre_Motivation_Richard_BUSSON.html")
    lm_pdf_path = os.path.join(output_dir, "Lettre_Motivation_Richard_BUSSON.pdf")
    lm_png_path = os.path.join(output_dir, "Lettre_Motivation_Richard_BUSSON.png")

    # Écriture HTML
    cv_html = build_cv_html(offer)
    with open(cv_html_path, "w", encoding="utf-8") as f:
        f.write(cv_html)

    lm_html = build_lettre_html(offer)
    with open(lm_html_path, "w", encoding="utf-8") as f:
        f.write(lm_html)

    # Compilation PDF et captures PNG avec Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page(viewport={"width": 794, "height": 1123})

        # 1. Compilation CV
        await page.goto(f"file:///{os.path.abspath(cv_html_path).replace(os.sep, '/')}", wait_until="networkidle")
        await page.pdf(
            path=cv_pdf_path,
            width="794px",
            height="1123px",
            print_background=True,
            page_ranges="1",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        await page.screenshot(path=cv_png_path, full_page=True)

        # 2. Compilation Lettre
        await page.goto(f"file:///{os.path.abspath(lm_html_path).replace(os.sep, '/')}", wait_until="networkidle")
        await page.pdf(
            path=lm_pdf_path,
            width="794px",
            height="1123px",
            print_background=True,
            page_ranges="1",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        await page.screenshot(path=lm_png_path, full_page=True)

        await browser.close()

    # Vérification de non-vacuité
    for f in [cv_pdf_path, cv_png_path, lm_pdf_path, lm_png_path]:
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            raise RuntimeError(f"Erreur QualityGuard : fichier vide ou manquant : {f}")

    print(f"[OK] Dossier 6 fichiers généré avec succès dans : {output_dir}")
    return {
        "cv_pdf": cv_pdf_path,
        "cv_png": cv_png_path,
        "lm_pdf": lm_pdf_path,
        "lm_png": lm_png_path
    }

if __name__ == "__main__":
    # Test rapide unitaire
    test_offer = {
        "title": "Enseignant(e) d'économie-gestion",
        "academie": "Académie d'AMIENS",
        "reference": "MENJ-25-TEST-01",
        "location": "Amiens / Creil (60)",
        "raw_card": "Académie d'AMIENS DPE4"
    }
    test_dir = r"C:\Users\richa\Gemini\Pipeline_JobHunter\candidatures\test_amiens"
    asyncio.run(generate_dossier_files(test_offer, test_dir))
