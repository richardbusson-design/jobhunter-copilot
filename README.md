# 🚀 JOBHUNTER COPILOT - CANDIDATURES AUTOMATISÉES RICHARD BUSSON

Système automatisé de recherche d'emploi et de génération de candidatures sur-mesure (CV et Lettre de motivation) au format PDF A4 strict.

---

## 🔒 RÈGLES STRICTES DE GÉNÉRATION (NON NÉGOCIABLES)

### 1. Curriculum Vitae (1 Page A4 Stricte)
- **Dimensions :** Exactement 1 page A4 (210 × 297 mm / 794 × 1123 px).
- **Interdiction formelle :** Aucun dépassement sur une page 2 et aucun vide résiduel en bas.
- **Répartition :** 7 sections ordonnées (En-tête, Synthèse, Compétences clés, Points forts, Expériences professionnelles, Formations 2 colonnes, Outils & Langues).

### 2. Lettre de Motivation (Gabarit Officiel Validé)
- **Dimensions :** Exactement 1 page A4, répartie sur 100% de la hauteur de la feuille (height: 1123px, flexbox space-between).
- **Expéditeur (Gauche) :** 6 lignes en haut à gauche.
- **Destinataire (Droite) :** Démarre **très exactement à la hauteur de la 6ᵉ ligne de l'expéditeur (kairos-paye.fr)**.
- **Date :** Alignée sous le destinataire (*À Creil, le...*).
- **Règle stricte du GRAS :**
  - **AUCUN mot en gras dans le corps de la lettre.**
  - Le gras est **STRICTEMENT RÉSERVÉ** à deux éléments :
    1. **Objet : ...**
    2. **À l’attention de Prénom NOM [titre]**
- **Signature :** Signature manuscrite vectorielle (*RB*) positionnée en **bas à DROITE** au-dessus de *Richard Busson*.

---

## 🛠️ ARCHITECTURE DU PROJET

`
job_copilot/
├── config/
│   ├── profile.json            # Profil maître de Richard Busson
│   └── search_sources.json     # Configuration Indeed, France Travail, Apec
├── templates/
│   ├── template_cv.html        # Gabarit HTML CV 1 page A4 équilibrée
│   └── template_lettre.html    # Gabarit HTML Lettre officielle conforme
├── src/
│   ├── application_generator.py # Matcher & Rédacteur sur-mesure sans gras
│   ├── pdf_compiler.py          # Compilateur PDF Microsoft Edge Headless (300 DPI)
│   ├── job_searcher.py          # Recherche d'offres (France Travail, Apec, Indeed)
│   ├── dashboard_manager.py     # CRM & Suivi des relances J+7
│   └── run_jobhunter.py         # Script d'exécution principal
├── candidatures/               # Dossiers PDF générés prêts pour envoi
├── tests/
│   └── test_validation.py      # Tests de conformité et de non-régression
└── dashboard.md                # Tableau de bord de suivi des candidatures
`

---

## ⚡ COMMANDES RAPIDES

### 1. Lancer la génération des candidatures cibles :
`powershell
python src/run_jobhunter.py
`

### 2. Exécuter les tests de validation des règles :
`powershell
="src"; python tests/test_validation.py
`

---

## 🎯 SOURCES DE RECHERCHE D'EMPLOI
1. **France Travail** (API / Offres territoriales et régionales)
2. **Apec** (Postes cadres, formateurs experts, coordinateurs pédagogiques)
3. **Indeed** (Offres d'entreprises, CFA, cabinets comptables et organismes de formation)
