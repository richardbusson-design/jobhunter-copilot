---
name: dashboard-autopilot
description: Automatisation complète et autonome du traitement des candidatures du tableau de bord (résolution des canaux recruteurs, complétion ATS Taleez/Flatchr/HelloWork, validation OTP/liens IMAP, archivage des preuves et synchronisation Git).
---

# SKILL OFFICIEL : DASHBOARD AUTOPILOT (RICHARD BUSSON)

## 🎯 OBJECTIF DE LA SKILL
Cette compétence permet à l'agent d'automatiser **à 100% de bout en bout** le traitement de l'ensemble des offres présentes sur le tableau de bord (`tracker.json` / `dashboard.html`).
L'agent n'a plus besoin d'interrompre l'utilisateur pour cliquer, glisser-déposer un CV, ou saisir un code de vérification : **tout est géré de manière autonome, réactive et certifiée sans hallucination.**

---

## 👤 DONNÉES CANDIDAT CERTIFIÉES (RICHARD BUSSON)
- **Nom & Prénom :** Richard BUSSON
- **Email officiel :** `richard.busson@kairos-paye.fr` (et compte FT : `richard.busson@gmail.com`)
- **Téléphone portable :** `07 61 96 15 46` | Fixe : `09 39 20 08 70`
- **Adresse :** 98, allée Paul Cézanne, 60100 Creil
- **Statut & Atouts :** 59 ans, senior expert (+15 ans d'expérience), éligible aux aides à l'embauche pour demandeur d'emploi senior, permis B, mobilité nationale (Façades Atlantique / Méditerranée / Creil & IDF), disponibilité immédiate.
- **Rémunération cible :** 40 000 € à 50 000 € brut annuel (ou tranche 40k-45k€ / 45k-50k€).
- **Messagerie OVH IMAP/SMTP :** `ssl0.ovh.net` (IMAP: 993, SMTP: 587) / `richard.busson@kairos-paye.fr` / `mailK41R0sbTN001`.

---

## 🔄 WORKFLOW OFFICIEL EN 5 PHASES (ZERO-HALLUCINATION)

### 1. AUDIT DU TRACKER & DÉTECTION DES DOSSIERS
1. Lire `tracker.json`. Filtrer toutes les candidatures n'ayant pas le statut `CONFIRMED` ou `sent: true`.
2. Localiser dans `/candidatures` le dossier officiel (`CV_Richard_BUSSON.pdf` et `Lettre_Motivation_Richard_BUSSON.pdf`).
3. Vérifier que la taille de chaque PDF est strictement supérieure à 0 octet.

### 2. DÉTERMINATION & RÉSOLUTION DU CANAL D'ENVOI
- **Canal A : Email Recruteur Direct (SMTP TLS)**
  - Si un email de contact recruteur est disponible ou découvert (`contact@`, `recrutement@`, email de l'offre).
  - Générer le corps personnalisé (expérience 580 collab / Titre Pro 758h / Silae / atout senior).
  - Joindre la lettre et le CV PDF.
  - Envoyer via `ssl0.ovh.net:587` avec BCC `richard.busson@kairos-paye.fr`.
  - Mettre à jour `tracker.json` avec `mode: DIRECT_RECRUITER_EMAIL`.
- **Canal B : Portails ATS Dédiés (Taleez, Flatchr, SmartRecruiters, Lever)**
  - Lancer Playwright furtif (`--disable-blink-features=AutomationControlled`, `navigator.webdriver = undefined`).
  - Remplir coordonnées (Prénom, Nom, Email, Téléphone `0761961546`).
  - Téléverser sélectivement le CV dans la dropzone CV et la Lettre dans la dropzone Lettre.
  - Sélectionner les tranches de salaires ou d'expérience requises.
  - Cliquer sur « Postuler » ou « Envoyer ma candidature ».
- **Canal C : Jobboards / HelloWork**
  - Cliquer sur « Continuer sans accepter » ou accepter les cookies.
  - Remplir Prénom, Nom, Email, téléverser le CV et cocher les CGU.
  - Cliquer sur « Continuer ma candidature ».

### 3. BOUCLE D'AUTO-VALIDATION IMAP OVH (2FA / OTP / LIENS)
- Si le système affiche « Veuillez confirmer votre adresse email » (Taleez) :
  - Se connecter à `ssl0.ovh.net:993`.
  - Extraire le lien `/apply/confirm/...`.
  - Naviguer sur l'URL dans le navigateur pour finaliser la validation.
- Si le système affiche « Saisissez le code reçu par email » (HelloWork OTP) :
  - Se connecter à `ssl0.ovh.net:993`.
  - Extraire le code à 6 chiffres (`re.findall(r'\b\d{6}\b', subject)`).
  - Taper le code dans les 6 cases et cliquer sur « Valider ».

### 4. CAPTURE & ARCHIVAGE DE LA PREUVE OFFICIELLE
- Attendre l'écran de succès (« Merci, votre candidature a bien été prise en compte », « Candidature bien reçue », etc.).
- Capturer l'écran en haute définition et l'enregistrer obligatoirement sous :
  `candidatures/<dossier>/preuve_soumission_officielle.png`.

### 5. SYNCHRONISATION DASHBOARD & DÉPÔT GIT
- Enregistrer le statut dans `tracker.json` :
  `recruiter_delivery: "OFFICIALLY_SUBMITTED_AND_CONFIRMED"`
- Régénérer les dashboards :
  `DashboardManager('.').generate_html_dashboard()`
  `DashboardManager('.').generate_markdown_dashboard()`
- Synchroniser immédiatement sur GitHub :
  `git add -A ; git commit -m "feat: Candidature officiellement validée pour <Entreprise>" ; git push origin main`.
- Le tableau de bord local et en ligne affiche instantanément le badge vert **✓ Candidature Transmise et Validée**.

---

## ⚡ COMMANDES D'EXÉCUTION RAPIDE DU MOTEUR
- Traiter l'offre suivante du tableau de bord :
  ```bash
  python src/dashboard_autopilot.py
  ```
- Traiter automatiquement toutes les offres en attente :
  ```bash
  python src/dashboard_autopilot.py --all
  ```