---
name: candidature-france-travail
description: >-
  Automatisation 100% autonome, certifiée et sans hallucination des candidatures directes sur France Travail (espace candidat officiel Richard Louis Busson). Sélection intelligente du CV ciblé dans la bibliothèque, sélection de la carte de compétences expert droit social/paie/RH, injection de la lettre sur-mesure (<1450 car.), validation des coordonnées, soumission officielle et capture de la preuve avec macaron vert de transmission.
---

# SKILL OFFICIEL : CANDIDATURE DIRECTE AUTOMATISÉE SUR FRANCE TRAVAIL

Ce skill standardise la procédure éprouvée et certifiée pour postuler de manière 100% autonome aux offres d'emploi directes sur la plateforme officielle **France Travail** pour le compte de **Richard BUSSON**.

---

## 👤 1. RÉFÉRENTIEL DU CANDIDAT (ESPACE PERSONNEL FRANCE TRAVAIL)
- **Titulaire du compte :** Richard Louis BUSSON
- **Profil connecté :** Espace Candidat officiel France Travail (session active et certifiée)
- **Email de contact :** `richard.busson@kairos-paye.fr` (secours compte : `richard.busson@gmail.com`)
- **Téléphone :** `09 39 20 08 70` / `07 61 96 15 46`
- **Adresse :** 98, allée Paul Cézanne, 60100 Creil
- **Statut :** 59 ans, senior/expert (+15 ans d'expérience), éligible aux aides à l'embauche pour demandeur d'emploi senior, permis B, mobilité nationale (Creil, Île-de-France, Littoraux Atlantique & Méditerranée).
- **Rémunération plancher :** Strictement >= 30 000 € brut/an.

---

## 🔍 2. DÉTECTION ET SÉLECTION DES OFFRES DIRECTES (FLUX DIRECT)
Seules les offres comportant le formulaire de postulation interne France Travail (non externalisées) sont ciblées par ce protocole :
- **Paramètres d'URL obligatoires :** `natureOffre=E1&offresPartenaires=false`
- **Contrôle anti-doublon préalable :**
  - Vérification de l'ID offre et du couple `Entreprise | Titre` contre `tracker.json` et `data/tracker_backup_*.json`.
  - Vérification visuelle sur l'espace France Travail : élimination immédiate si la bannière *« Vous avez déjà postulé sur cette offre ! »* est présente.

---

## ⚙️ 3. PROCÉDURE D'EXÉCUTION EN 8 ÉTAPES SUR LE FORMULAIRE OFFICIEL

### Étape 1 : Accès à l'offre et ouverture du formulaire
1. Navigation vers `https://candidat.francetravail.fr/offres/recherche/detail/{raw_id}`.
2. Clic sur le bouton `Postuler`.
3. Clic sur `Envoyer ma candidature` dans la fenêtre modale (s'ouvre dans un nouvel onglet `candidat.francetravail.fr/candidature/postulerenligne/{raw_id}`).
4. Attente de la stabilisation DOM / Angular (`domcontentloaded` + attente de disparition du spinner de chargement).

### Étape 2 : Sélection ciblée du CV dans la bibliothèque
Sélectionner automatiquement le CV correspondant à la typologie de l'offre parmi les documents pré-enregistrés sur l'espace France Travail :
- **Postes RH / Management :** `CV_Bibliotheque_ResponsableRH.pdf` (`input#cv-83557459` ou `label[for='cv-83557459']`)
- **Postes Formateur :** `CV_Bibliotheque_FormateurPaieRH.pdf` (`input#cv-83522766` ou `label[for='cv-83522766']`)
- **Postes Consultant :** `CV_Bibliotheque_ConsultantPaieRH.pdf` (`input#cv-83557493` ou `label[for='cv-83557493']`)
- **Postes Paie / Gestionnaire de Paie :** `CV_Bibliotheque_GestionnaireDePaie.pdf` (`input#cv-83522771` ou `label[for='cv-83522771']`)
- *Repli :* Cocher le premier CV disponible si les libellés diffèrent.

### Étape 3 : Sélection du profil de compétences expert
- Cocher le profil de compétences valorisant :
  `input#choix-carte-visite-16674788` ou `label[for='choix-carte-visite-16674788']` (*« expert en droit social, paie, RH »*).

### Étape 4 : Injection du texte de motivation calibré
- Champ cible : `textarea#lettre-motivation` (ou `textarea[name='textMessage']`).
- **Règle stricte de longueur :** Extraire les paragraphes centraux de la lettre de motivation sur-mesure (générée lors du passage 2 QualityGuard) et tronquer à **1 450 caractères maximum** pour respecter la limite technique de France Travail sans coupure abrupte.

### Étape 5 : Confirmation des coordonnées
- Cocher la case obligatoire confirmant l'exactitude des coordonnées :
  `label[for='confirmcoordonnees']` ou `input#confirmcoordonnees`.

### Étape 6 : Capture de l'état prêt à soumettre
- Enregistrer la capture plein écran `form_ready_to_submit.png` dans le dossier de la candidature pour audit et traçabilité.

### Étape 7 : Clic officiel sur « Envoyer »
- Localiser et cliquer sur `button:has-text('Envoyer')`.
- Attendre 6 à 8 secondes la réponse du serveur France Travail.

### Étape 8 : Capture de la preuve matérielle de soumission (Macaron Vert)
- Enregistrer la capture plein écran `preuve_soumission_officielle.png`.
- **Validation matérielle obligatoire :** Vérifier que la page affiche le macaron vert et la mention officielle :
  *« Candidature transmise - Votre candidature pour l'offre a bien été envoyée au recruteur ou à l'agence France Travail qui gère l'offre d'emploi. »*
- Fermer l'onglet du formulaire.

---

## 📊 4. TRAÇABILITÉ & SYNCHRONISATION
1. Enregistrer la candidature dans `tracker.json` avec l'empreinte complète et le mode :
   `recruiter_delivery.mode = "FRANCE_TRAVAIL_OFFICIAL_DIRECT_SUBMISSION"`
2. Régénérer les tableaux de bord Markdown et HTML (`dashboard.md` et `dashboard.html`).
3. Notifier Richard BUSSON par e-mail récapitulatif sur `richard.busson@kairos-paye.fr`.
4. Effectuer le `git commit` et `git push` automatique vers le dépôt GitHub distant.
