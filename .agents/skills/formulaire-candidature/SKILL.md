---
name: formulaire-candidature
description: >-
  Automatisation intégrale, intelligente et adaptative du remplissage et de la validation de tout formulaire de candidature d'emploi (ATS, Taleez, France Travail, Apec, Hellowork, sites carrières d'entreprises). Remplissage exhaustif des champs, téléversement du CV et de la lettre personnalisés, contournement anti-WAF/anti-bot, boucle de repli sans hallucination et auto-validation des e-mails de confirmation par IMAP.
---

# SKILL OFFICIELLE : COMPLÉTION ET VALIDATION AUTOMATISÉE DE FORMULAIRES DE CANDIDATURE

Ce skill confère à l'agent l'autonomie totale pour analyser, remplir, téléverser les documents requis et finaliser n'importe quel formulaire de candidature web pour **Richard BUSSON**, sans friction et sans hallucination.

---

## 👤 1. RÉFÉRENTIEL IDENTITÉ CANDIDAT (RICHARD BUSSON)

| Donnée | Valeur Officielle | Remarques d'injection |
| :--- | :--- | :--- |
| **Prénom** | `Richard` | Champ `fname`, `first_name`, `prenom` |
| **Nom** | `BUSSON` | Champ `lname`, `last_name`, `nom` |
| **Nom complet** | `Richard BUSSON` | Champ unique `name`, `full_name` |
| **E-mail de contact** | `richard.busson@kairos-paye.fr` | Toujours prioritaire pour les recruteurs |
| **E-mail de secours** | `richard.busson@gmail.com` | Utiliser uniquement si imposé (ex: France Travail) |
| **Téléphone mobile** | `0761961546` / `07 61 96 15 46` | Format standard ou avec espaces |
| **Téléphone international**| `+33761961546` | Sélecteurs `tel` avec indicatif pays |
| **Téléphone pro** | `09 39 20 08 70` | Si second numéro demandé |
| **Adresse** | `98, allée Paul Cézanne` | Voie |
| **Code Postal** | `60100` | Code postal |
| **Ville** | `Creil` | Ville |
| **Pays** | `France` | Dropdown pays (+33) |
| **Âge & Statut** | `59 ans` | Senior éligible aux aides à l'embauche |
| **Disponibilité** | `Immédiate` | Sans préavis |
| **Mobilité** | `Mobilité nationale (Hauts-de-France, Île-de-France, Littoral Atlantique & Méditerranée)` |
| **Fourchette salariale** | `40 000 € à 45 000 €` brut/an (ou 45 k€ - 50 k€) | Toujours >= 30 k€ |
| **LinkedIn** | `https://www.linkedin.com/in/richard-busson` | Profil certifié |
| **Site Web** | `https://kairos-paye.fr` | Organisme Kairos Formation |

---

## 🛑 2. RÈGLE D'OR : ZÉRO HALLUCINATION & BOUCLE D'ANALYSE D'ERREUR

1. **Interdiction de prétendre avoir postulé sans preuve matérielle :**
   - Chaque soumission doit être sanctionnée par une capture d'écran réelle horodatée du message de confirmation (`candidature_confirmee.png` ou URL de remerciement `thanks`, `confirmation`, `success`).
2. **Principe de résilience en boucle fermée (Fallback Loop) :**
   - Si un sélecteur échoue ou qu'un champ refuse l'injection : **ne pas abandonner ni demander à l'utilisateur de cliquer**.
   - Analyser le DOM et le type de blocage :
     * *Erreur WAF / anti-bot (Cloudflare, Datadome) :* Activer le mode furtif (`--disable-blink-features=AutomationControlled` et `navigator.webdriver = undefined`).
     * *Dropdown Angular / React bloquant :* Simuler un clic en coordonnées neutres (`page.mouse.click(10, 10)`) ou utiliser la recherche textuelle dans le composant.
     * *Bouton submit recouvert ou non cliquable :* Appliquer la cascade :
       1. Clic standard `button[type='submit'].click()`
       2. Clic forcé `button.click(force=True)`
       3. Soumission JS directe `page.evaluate("() => document.querySelector('form').submit()")`
       4. Pression clavier `page.keyboard.press("Enter")`
     * *Lien de confirmation e-mail obligatoire (ex: Taleez) :* Intercepter l'e-mail immédiatement via IMAP OVH et valider le lien en arrière-plan.

---

## 🔄 3. PROCÉDURE STANDARD D'EXÉCUTION EN 6 ÉTAPES

### Étape 1 : Appariement du Dossier de l'Offre
Identifier l'offre dans `tracker.json` ou dans le dossier `candidatures/` :
- Récupérer `CV_Richard_BUSSON.pdf` adapté au poste (Responsable RH, Formateur Qualiopi, Responsable Paie).
- Récupérer `Lettre_Motivation_Richard_BUSSON.pdf` et le texte de motivation correspondant.

### Étape 2 : Lancement du Navigateur Furtif
```python
browser = p.chromium.launch(
    executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    headless=True,
    args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
)
context = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### Étape 3 : Injection Intelligente des Coordonnées
- Parcourir tous les `input:visible` :
  - Détecter prénom (`fname`, `prenom`), nom (`lname`, `nom`), email, téléphone, adresse, code postal, ville.
- Injecter le texte dans `textarea` (lettre personnalisée).

### Étape 4 : Téléversement du CV et de la Lettre
- Localiser `input[type="file"]` :
  - Si 1 seul champ : injecter `CV_Richard_BUSSON.pdf`.
  - Si 2 champs distincts : attribuer CV et Lettre de motivation selon les labels (`cv`, `resume` vs `lettre`, `motivation`, `cover`).
- Attendre 3 à 5 secondes la fin du traitement réseau du serveur.

### Étape 5 : Sélection Salariale & Checkboxes
- Dérouler le sélecteur salarial et choisir `40.000 à 45.000 €` (ou option équivalente).
- Cocher les cases obligatoires de consentement RGPD (`terms`, `privacy`, `consent`).

### Étape 6 : Soumission et Validation
- Déclencher la soumission via la stratégie de repli.
- Si un écran "Confirmez votre e-mail" apparaît :
  - Se connecter en IMAP sur `ssl0.ovh.net:993` avec `richard.busson@kairos-paye.fr` / `mailK41R0sbTN001`.
  - Extraire le lien de validation reçu dans les 2 dernières minutes et le charger dans le navigateur.
- Prendre la capture d'écran finale de succès.
- Mettre à jour `tracker.json` avec le statut `OFFICIALLY_SUBMITTED_AND_CONFIRMED` et régénérer le tableau de bord.

---

## 🛠️ 4. OUTILS & SCRIPTS ASSOCIÉS

- **Moteur principal autonome :**  
  `C:\Users\richa\Gemini\Pipeline_JobHunter\src\form_auto_pilot.py`
- **Exécution d'un formulaire à la demande :**  
  ```bash
  python C:\Users\richa\Gemini\Pipeline_JobHunter\src\form_auto_pilot.py --url "<URL_DU_FORMULAIRE>"
  ```
- **Validation IMAP autonome :**  
  Intégrée dans la méthode `_auto_confirm_via_email()` de `FormAutoPilot`.
