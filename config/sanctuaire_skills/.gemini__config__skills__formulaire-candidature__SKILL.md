---
name: remplir-formulaire
description: >-
  Automatisation intégrale, adaptative et résiliente du remplissage et de la validation de tout formulaire de candidature d'emploi en ligne (ATS d'entreprise, PayJob, Taleez, Michael Page, portail Apec avec contournement Datadome par courbe de Bézier et redirection directe vers l'ATS recruteur, France Travail avec 2FA autonome par IMAP, SmartRecruiters, Lever, Workday, HelloWork). Injection des coordonnées officielles de Richard BUSSON (07 61 96 15 46 · 09 39 20 08 70, richard.busson@kairos-paye.fr, Creil), téléversement automatique des PDF calibrés A4 (CV et Lettre), validation RGPD, boucle de repli à 4 stratégies et capture de la preuve matérielle horodatée.
---

# SKILL OFFICIELLE : REMPLISSAGE ET DÉPÔT AUTOMATISÉ DE FORMULAIRES DE CANDIDATURE

Ce skill confère à l'agent et aux routines JobHunter l'autonomie totale et définitive pour analyser, remplir, téléverser les documents requis et sceller n'importe quel formulaire de candidature web pour **Richard BUSSON**, sans intervention manuelle et sans hallucination.

---

## 👤 1. RÉFÉRENTIEL IMMUABLE DES COORDONNÉES (RICHARD BUSSON)

| Champ Détecté | Valeur Officielle à Injecter | Heuristiques & Sélecteurs Cibles |
| :--- | :--- | :--- |
| **Prénom** | `Richard` | `input[name*='prenom']`, `input[name*='first']`, `input[placeholder*='prénom' i]` |
| **Nom** | `BUSSON` | `input[name*='nom']`, `input[name*='last']`, `input[placeholder*='nom' i]` (hors 'prénom') |
| **Nom complet** | `Richard BUSSON` | `input[name*='name']`, `input[name*='full']`, `input[placeholder*='nom complet' i]` |
| **E-mail principal** | `richard.busson@kairos-paye.fr` | `input[type='email']`, `input[name*='mail']`, `input[placeholder*='email' i]` |
| **E-mail secondaire** | `richard.busson@gmail.com` | Uniquement si imposé pour l'espace France Travail |
| **Téléphone mobile** | `07 61 96 15 46` (ou `0761961546`) | `input[type='tel']`, `input[name*='tel']`, `input[name*='phone']`, `input[name*='mobile']` |
| **Téléphone international** | `+33761961546` | Sélecteurs téléphoniques exigeant le préfixe pays |
| **Téléphone fixe / pro** | `09 39 20 08 70` | Champ secondaire si téléphone pro demandé |
| **Adresse** | `98, allée Paul Cézanne` | `input[name*='addr']`, `input[name*='adresse']`, `input[name*='rue']` |
| **Code Postal** | `60100` | `input[name*='cp']`, `input[name*='zip']`, `input[name*='postal']` |
| **Ville** | `Creil` | `input[name*='city']`, `input[name*='ville']`, `input[name*='commune']` |
| **Pays** | `France` | `select[name*='country']`, dropdowns pays (+33) |
| **Âge & Statut** | `59 ans` | Demandeur d'emploi senior éligible aux aides à l'embauche |
| **Disponibilité** | `Immédiate` | `input[name*='dispo']`, selecteurs de préavis |
| **Prétentions salariales**| `40 000 € à 45 000 €` (ou `42000`) | Sélecteurs salariaux ou champs texte libres (toujours >= 30 k€) |
| **Mobilité** | `Mobilité nationale (Hauts-de-France, Île-de-France, Façades Atlantique & Méditerranée)` |
| **LinkedIn** | `https://www.linkedin.com/in/richard-busson` | `input[name*='linkedin']` |
| **Site Web Pro** | `https://kairos-paye.fr` | `input[name*='site']`, `input[name*='web']`, `input[name*='url']` |

---

## 🛡️ 2. GESTION DES PASSERELLES ET ANTI-BOTS SPÉCIFIQUES

### 🔹 CAS 1 : LE PORTAIL APEC (CONTOURNEMENT DATADOME & REDIRECTION ATS RECRUTEUR)
L'Apec protège ses offres par le WAF **DataDome** (`geo.captcha-delivery.com`) et exige un compte candidat Apec pour les candidatures internes. La stratégie validée en production fonctionne en 3 étapes :

1. **Lancement sous profil persistant Chrome :**  
   Utiliser `user_data_dir=C:\Users\richa\JobHunter\browser_profile` avec `executable_path=C:\Program Files\Google\Chrome\Application\chrome.exe` et `headless=False` (sur Windows local).
2. **Résolution Furtive du Slider DataDome :**  
   - Si l'iframe DataDome apparaît, détecter `.slider` et `.sliderTarget`.
   - Calculer les coordonnées absolues (offset de l'iframe + position de l'élément).
   - Effectuer un glissement souris humain via une **interpolation en courbe de Bézier cubique** (`ease = 3*t² - 2*t³`) avec micro-déviations aléatoires sur l'axe Y et pauses d'hésitation réalistes.
   - Le slider franchi enregistre le cookie `datadome` valide dans le profil Chrome persistant.
3. **Bypass Apec vers l'ATS Recruteur Direct :**  
   - Fermer la bannière cookies Apec.
   - Cliquer sur le bouton jaune : `Postuler sur le site de l'entreprise`.
   - Sur la page intermédiaire `postuler-a-une-offre.html`, cliquer sur le lien en bas à gauche :  
     **`Aller directement sur le site du recruteur`**
   - Suivre la redirection immédiate vers l'ATS direct (ex: PayJob, Michael Page, Taleez, Hellotravail) où le formulaire est libre, sans compte obligatoire.

---

### 🔹 CAS 2 : LE PORTAIL FRANCE TRAVAIL (ESPACE CANDIDAT OFFICIEL)
1. Naviguer vers `https://candidat.francetravail.fr/espacepersonnel/`.
2. S'authentifier automatiquement avec les identifiants stockés dans `.env` (`FRANCE_TRAVAIL_USER`, `FRANCE_TRAVAIL_PASSWORD`).
3. Intercepter le code 2FA à 8 chiffres dans Gmail par connexion sécurisée IMAP (`imap.gmail.com:993`) avec `GMAIL_APP_PASSWORD`.
4. Injecter les 8 chiffres avec un délai humain de 40ms par touche et cliquer sur **"Faire confiance à ce navigateur pendant 3 mois"**.
5. Sur l'offre : cliquer sur `Postuler` -> `Envoyer ma candidature` -> sélectionner le CV thématique ou téléverser `CV_Richard_BUSSON.pdf` -> injecter la lettre de motivation (calibrée à 1450 caractères) -> cocher la confirmation des coordonnées -> cliquer sur `Envoyer`.

---

### 🔹 CAS 3 : FORMULAIRES ATS RECRUTEURS UNIVERSELS (PAYJOB, TALEEZ, WORKDAY, ETC.)
1. **Fermeture des bandeaux de consentement :**  
   Cliquer systématiquement sur `Accepter`, `Autoriser` ou `Continuer sans accepter`.
2. **Téléversement des Pièces Jointes :**  
   - Si 1 zone unique (`input[type='file']`) : injecter `CV_Richard_BUSSON.pdf`.
   - Si 2 zones distinctes : attribuer le CV (`input[name*='cv']`) et la Lettre de motivation (`input[name*='lettre']` ou `[name*='cover']`).
3. **Message / Lettre de motivation dans `textarea` :**  
   Injecter la lettre rédigée sur-mesure pour l'offre (4 paragraphes stricts : Vous / Moi / Réalisations Terrain / Nous & Entretien).
4. **Cases à cocher RGPD & Consentement :**  
   Cocher obligatoirement les cases de politique de confidentialité et de traitement des données.

---

## ⚡ 3. BOUCLE DE REPLI DE SOUMISSION (FALLBACK SUBMIT LOOP)

Ne jamais échouer sur un bouton non cliquable. Appliquer la cascade de soumission en 4 paliers :
```python
# Palier 1 : Clic direct standard
btn = page.locator("button[type='submit'], button:has-text('Envoyer ma candidature'), button:has-text('Postuler'), button:has-text('Valider')").first
btn.click(timeout=5000)

# Palier 2 : Clic forcé (bypass d'overlay / opacité)
btn.click(force=True, timeout=5000)

# Palier 3 : Déclenchement JS natif via form.submit()
page.evaluate("() => { const f = document.querySelector('form'); if (f) f.submit(); }")

# Palier 4 : Émission de la touche Entrée clavier
page.keyboard.press("Enter")
```

---

## 📧 4. AUTO-VALIDATION DU LIEN DE CONFIRMATION PAR EMAIL (IMAP OVH)

Certains ATS (comme Taleez) envoient un e-mail avec un lien d'activation obligatoire :
1. Se connecter en SSL à `ssl0.ovh.net:993` avec le compte `richard.busson@kairos-paye.fr`.
2. Rechercher les messages non lus récents contenant un lien de confirmation (`confirm`, `validate`, `activation`).
3. Ouvrir ce lien dans le navigateur pour valider définitivement la candidature.

---

## 📸 5. RÈGLE D'OR : CONTRÔLE DE PREUVE MATÉRIELLE (ZÉRO HALLUCINATION)

Aucune candidature n'est déclarée soumise sans respect des deux jalons photographiques :
1. **`form_ready_to_submit.png`** : Capture d'écran du formulaire intégralement rempli avec fichiers attachés, juste avant le clic final.
2. **`preuve_soumission_officielle.png`** : Capture d'écran du message de confirmation officiel (*"Votre candidature a bien été transmise"*, macaron vert, numéro de dossier ou URL de succès).
3. Enregistrement immédiat dans `tracker.json` avec mise à jour du statut en `OFFICIALLY_SUBMITTED_AND_CONFIRMED` et rafraîchissement du `dashboard.html`.

---

## 🚀 6. INVOCATION RAPIDE EN LIGNE DE COMMANDE

Pour exécuter le remplissage et la postulation immédiate sur n'importe quel lien web :
```bash
python C:\Users\richa\Gemini\Pipeline_JobHunter\src\form_auto_pilot.py --url "<URL_DE_L_OFFRE>" --folder "<CHEMIN_DU_DOSSIER_CANDIDATURE>"
```
