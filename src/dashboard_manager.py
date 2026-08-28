# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict

def normalize_text(text: str) -> str:
    """Normalise un texte pour comparaison stricte anti-doublon."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\(h/f\)|h/f|\(f/h\)|f/h', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

FRENCH_MONTHS = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
}

class DashboardManager:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.dashboard_file = os.path.join(base_dir, "dashboard.md")
        self.readme_file = os.path.join(base_dir, "README.md")
        self.html_file = os.path.join(base_dir, "dashboard.html")
        self.tracker_file = os.path.join(base_dir, "tracker.json")
        self.gemini_html_file = r"C:\Users\richa\Gemini\dashboard.html"

    def load_tracker(self) -> List[Dict[str, Any]]:
        """Charge l'ensemble des candidatures historiques depuis le tracker JSON."""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("applications", [])
            except Exception as e:
                print(f"[!] Avertissement lecture tracker : {e}")
        return []

    def get_existing_fingerprints(self) -> Dict[str, Any]:
        """Extrait les empreintes uniques (ID, URL, Société+Titre) pour blocage strict des doublons."""
        apps = self.load_tracker()
        ids = set()
        urls = set()
        company_titles = set()
        
        for a in apps:
            if a.get("id"):
                ids.add(str(a.get("id")).strip())
            if a.get("url"):
                urls.add(str(a.get("url")).strip())
            
            comp_norm = normalize_text(a.get("company", ""))
            tit_norm = normalize_text(a.get("title", ""))
            if comp_norm and tit_norm:
                company_titles.add(f"{comp_norm}___{tit_norm}")
                
        return {
            "ids": ids,
            "urls": urls,
            "company_titles": company_titles,
            "total_count": len(apps)
        }

    def is_duplicate(self, job: Dict[str, Any], fingerprints: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Vérifie si une offre d'emploi a déjà été traitée ou candidate."""
        if fingerprints is None:
            fingerprints = self.get_existing_fingerprints()
            
        jid = str(job.get("id", "")).strip()
        if jid and jid in fingerprints["ids"]:
            return True, f"ID déjà candidaté ({jid})"
            
        jurl = str(job.get("url", "")).strip()
        if jurl and jurl in fingerprints["urls"]:
            return True, f"URL déjà traitée ({jurl})"
            
        comp_norm = normalize_text(job.get("company", ""))
        tit_norm = normalize_text(job.get("title", ""))
        fp = f"{comp_norm}___{tit_norm}"
        if fp in fingerprints["company_titles"]:
            return True, f"Société et Intitulé identiques ({job.get('company')} - {job.get('title')})"
            
        # Comparaison floue : société et métier
        for existing_fp in fingerprints.get("company_titles", []):
            if "___" in existing_fp:
                e_comp, e_tit = existing_fp.split("___", 1)
                comp_match = (e_comp in comp_norm) or (comp_norm in e_comp) or (e_comp[:10] == comp_norm[:10] and len(e_comp) >= 10)
                tit_match = (e_tit in tit_norm) or (tit_norm in e_tit) or ("formateur" in e_tit and "formateur" in tit_norm and "paie" in e_tit and "paie" in tit_norm)
                if comp_match and tit_match:
                    return True, f"Société et Titre très similaires ({existing_fp})"
            
        return False, ""

    def save_tracker(self, apps: List[Dict[str, Any]]):
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump({"applications": apps, "last_updated": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] Erreur sauvegarde tracker : {e}")

    def add_application(self, app_entry: Dict[str, Any]):
        apps = self.load_tracker()
        
        exists_idx = -1
        for i, a in enumerate(apps):
            if (a.get("id") and a.get("id") == app_entry.get("id")) or \
               (normalize_text(a.get("company", "")) == normalize_text(app_entry.get("company", "")) and \
                normalize_text(a.get("title", "")) == normalize_text(app_entry.get("title", ""))):
                exists_idx = i
                break
                
        if exists_idx >= 0:
            apps[exists_idx].update(app_entry)
        else:
            app_entry["date"] = app_entry.get("date", datetime.now().strftime("%Y-%m-%d"))
            relance_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            app_entry["relance_date"] = app_entry.get("relance_date", relance_date)
            app_entry["status"] = app_entry.get("status", "Dossier PDF Prêt")
            apps.insert(0, app_entry)
            
        self.save_tracker(apps)
        self.generate_markdown_dashboard(apps)
        self.generate_html_dashboard(apps)

    def generate_html_dashboard(self, apps: List[Dict[str, Any]] = None):
        """Génère un tableau de bord HTML complet, groupé par mois, pour le bouton Bureau Windows."""
        if apps is None:
            apps = self.load_tracker()
            
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        # Grouper les candidatures par mois (ex: "2026-08" -> "Août 2026")
        apps_by_month = defaultdict(list)
        for a in apps:
            d_str = a.get("date", datetime.now().strftime("%Y-%m-%d"))
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")
                month_label = f"{FRENCH_MONTHS.get(dt.strftime('%m'), dt.strftime('%B'))} {dt.year}"
            except Exception:
                month_key = "2026-08"
                month_label = "Août 2026"
            apps_by_month[(month_key, month_label)].append(a)
            
        # Tri des mois par ordre antéchronologique
        sorted_months = sorted(apps_by_month.keys(), key=lambda x: x[0], reverse=True)
        
        sections_html = ""
        for month_key, month_label in sorted_months:
            month_apps = apps_by_month[(month_key, month_label)]
            
            rows_html = ""
            for a in month_apps:
                d = a.get("date", datetime.now().strftime("%Y-%m-%d"))
                comp = a.get("company", "Entreprise")
                tit = a.get("title", "Poste")
                ref_id = a.get("id", "REF-AUTO")
                city = a.get("city", "France")
                salary = a.get("salary", ">= 30 000 €")
                score = a.get("score", 85)
                rel = a.get("relance_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
                source = a.get("source", "France Travail / Apec / Indeed / LinkedIn")
                url = a.get("url", "")
                desc = a.get("description", "Détail de l'offre...")
                folder_rel = a.get("folder_rel", "").replace("\\", "/")
                
                link_ref = f'<a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">🔗 {ref_id} ({source})</a>' if url else f'<span style="color: #94a3b8;">Réf. {ref_id}</span>'
                
                # Liens PDF & Aperçu
                pdf_col = ""
                if folder_rel:
                    pdf_letter = f"{folder_rel}/Lettre_Motivation_Richard_BUSSON.pdf"
                    pdf_cv = f"{folder_rel}/CV_Richard_BUSSON.pdf"
                    png_cv = f"{folder_rel}/CV_Richard_BUSSON.png"
                    pdf_col = f"""
                    <a class="btn-pdf" href="{pdf_letter}" target="_blank">✉️ Lettre PDF</a><br>
                    <a class="btn-pdf" href="{pdf_cv}" target="_blank">📄 CV A4</a><br>
                    <a class="btn-preview" href="{png_cv}" target="_blank">🔍 Aperçu Image</a>
                    """
                else:
                    pdf_col = '<span style="color: #94a3b8;">Dossier Prêt</span>'
                    
                rows_html += f"""
                <tr>
                  <td style="white-space: nowrap; font-weight: bold; color: #cbd5e1;">{d}</td>
                  <td><strong style="color: #f1f5f9; font-size: 15px;">{comp}</strong></td>
                  <td>
                    <div style="font-weight: 600; color: #38bdf8; font-size: 14px;">{tit}</div>
                    <div style="margin-top: 4px; font-size: 12px;">{link_ref}</div>
                    <details style="margin-top: 8px; background: #0f172a; padding: 8px 12px; border-radius: 6px; border: 1px solid #334155;">
                      <summary style="cursor: pointer; color: #94a3b8; font-size: 12px; font-weight: 600;">📝 Voir le texte intégral de l'annonce</summary>
                      <div style="margin-top: 8px; color: #cbd5e1; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">{desc}</div>
                    </details>
                  </td>
                  <td style="color: #cbd5e1;">{city}</td>
                  <td style="color: #34d399; font-weight: bold; white-space: nowrap;">{salary}</td>
                  <td><span class="score-badge">{score}%</span></td>
                  <td style="color: #f59e0b; font-weight: 600; white-space: nowrap;">{rel}</td>
                  <td style="white-space: nowrap;">{pdf_col}</td>
                </tr>
                """
                
            sections_html += f"""
            <div class="month-card">
              <div class="month-header">
                <h2>📅 {month_label}</h2>
                <span class="month-count">{len(month_apps)} candidature(s) envoyée(s)</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th style="width: 100px;">Date</th>
                    <th style="width: 220px;">Entreprise / Organisme</th>
                    <th>Intitulé du Poste & Détails Annonce</th>
                    <th style="width: 140px;">Lieu</th>
                    <th style="width: 140px;">Salaire Brut</th>
                    <th style="width: 70px;">Match</th>
                    <th style="width: 110px;">Relance (J+7)</th>
                    <th style="width: 160px;">Documents A4</th>
                  </tr>
                </thead>
                <tbody>
                  {rows_html}
                </tbody>
              </table>
            </div>
            """
            
        html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tableau de Bord des Candidatures - Richard BUSSON</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #090d16;
      color: #f8fafc;
      margin: 0;
      padding: 24px;
    }}
    .container {{
      max-width: 1700px;
      margin: 0 auto;
    }}
    .header-bar {{
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 24px 32px;
      margin-bottom: 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }}
    .header-bar h1 {{
      margin: 0;
      font-size: 24px;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .candidate-info {{
      color: #94a3b8;
      font-size: 14px;
      margin-top: 6px;
    }}
    .badge-pill {{
      background: #0284c7;
      color: white;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .badge-green {{
      background: #059669;
    }}
    .month-card {{
      background: #131c2e;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 28px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    .month-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 16px;
      margin-bottom: 16px;
      border-bottom: 2px solid #1e293b;
    }}
    .month-header h2 {{
      margin: 0;
      font-size: 20px;
      color: #f1f5f9;
    }}
    .month-count {{
      background: #334155;
      color: #f8fafc;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 600;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }}
    th {{
      background: #0b1120;
      color: #94a3b8;
      padding: 12px 14px;
      text-align: left;
      border-bottom: 2px solid #334155;
      font-weight: 600;
    }}
    td {{
      padding: 14px;
      border-bottom: 1px solid #1e293b;
      vertical-align: top;
    }}
    tr:hover {{
      background: #182235;
    }}
    .score-badge {{
      background: #0284c7;
      color: white;
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 12px;
    }}
    .btn-pdf {{
      display: inline-block;
      background: #2563eb;
      color: white;
      text-decoration: none;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 12px;
      margin: 2px 0;
      font-weight: 500;
      transition: background 0.2s;
    }}
    .btn-pdf:hover {{
      background: #1d4ed8;
    }}
    .btn-preview {{
      display: inline-block;
      background: #475569;
      color: white;
      text-decoration: none;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 11px;
      margin: 2px 0;
      transition: background 0.2s;
    }}
    .btn-preview:hover {{
      background: #64748b;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-bar">
      <div>
        <h1>📊 Tableau de Bord des Candidatures par Mois</h1>
        <div class="candidate-info">
          Candidat : <strong>Richard BUSSON</strong> (Creil, 60100) &bull; Téléphone : 09 39 20 08 70 &bull; richard.busson@kairos-paye.fr
        </div>
      </div>
      <div style="display: flex; gap: 10px;">
        <div class="badge-pill badge-green">🛡️ Anti-Doublon Actif ({len(apps)} dossiers)</div>
        <div class="badge-pill">⏰ Synchro : {now_str}</div>
      </div>
    </div>

    {sections_html}

    <div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 40px;">
      JobHunter Copilot &bull; Système automatisé de candidatures sur-mesure conforme Qualiopi & Direction RH &bull; Richard Busson
    </div>
  </div>
</body>
</html>"""

        # Sauvegarder dans le répertoire de travail
        with open(self.html_file, "w", encoding="utf-8") as f:
            f.write(html_doc)
            
        # Sauvegarder dans le miroir local ouvert par le bouton Bureau
        try:
            with open(self.gemini_html_file, "w", encoding="utf-8") as f:
                f.write(html_doc)
        except Exception as e:
            print(f"[!] Erreur écriture miroir HTML : {e}")

    def generate_markdown_dashboard(self, apps: List[Dict[str, Any]] = None):
        """Génère la page d'accueil GitHub (README.md) et dashboard.md avec le tableau précis en tête de page."""
        if apps is None:
            apps = self.load_tracker()
            
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        content = f"""# 📊 TABLEAU DE BORD OFFICIEL DES CANDIDATURES — RICHARD BUSSON

> **🛡️ SYSTÈME ANTI-DOUBLON ACTIF :** Avant toute nouvelle recherche, l'historique complet ci-dessous est analysé pour garantir que seules des **opportunités 100% fraîches et inédites** sont traitées.
> **⏰ Horaires d'exécution Cloud autonome :** 08h00, 13h00, 18h00 UTC *(09h, 14h, 19h Paris)*
> **Dernière actualisation :** {now_str} | **Total candidatures qualifiées :** {len(apps)}

---

## 📋 SUIVI PRÉCIS DES CANDIDATURES EXPÉDIÉES & EN COURS (PAR ORDRE ANTÉCHRONOLOGIQUE)

| Date | Nom de l'Entreprise / Organisme | Intitulé & Réf. Annonce | Lieu / Département | Salaire Brut Annuel | Match | Relance (J+7) | Fichiers PDF Officiels (A4) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
"""

        for a in apps:
            d = a.get("date", datetime.now().strftime("%Y-%m-%d"))
            comp = a.get("company", "Entreprise")
            tit = a.get("title", "Poste")
            ref_id = a.get("id", "REF-AUTO")
            city = a.get("city", "France")
            salary = a.get("salary", ">= 30 000 €")
            score = a.get("score", 85)
            rel = a.get("relance_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            source = a.get("source", "France Travail / Apec / Indeed / LinkedIn")
            url = a.get("url", "")
            desc = a.get("description", "Détail de l'offre...")
            
            link_ref = f"[🔗 **Réf. {ref_id} ({source})**]({url})" if url else f"*(Réf : {ref_id})*"
            
            titre_et_texte = f"""**{tit}**<br>{link_ref}<br>
<details>
<summary>📝 <b>Lire le texte intégral de l'annonce</b></summary>
<br>
<blockquote>{desc}</blockquote>
</details>"""

            folder_rel = a.get("folder_rel", "").replace("\\", "/")
            if folder_rel:
                link_cv = f"[📄 CV A4 Officiel]({folder_rel}/CV_Richard_BUSSON.pdf)"
                link_lm = f"[✉️ Lettre Motivation A4]({folder_rel}/Lettre_Motivation_Richard_BUSSON.pdf)"
                pdf_links = f"{link_cv}<br>{link_lm}"
            else:
                pdf_links = "Dossier PDF Prêt"
                
            content += f"| **{d}** | **{comp}** | {titre_et_texte} | {city} | {salary} | **{score}%** | {rel} | {pdf_links} |\n"

        content += """
---

## 🎯 LES 4 CATÉGORIES DE POSTES CIBLES
1. **Gestionnaire de Paie** *(Production, DSN, Déclarations sociales dématérialisées, Silae, Contrôle et audit)*
2. **Responsable RH** *(Relations sociales, CSE, Droit du travail, Masse salariale, Plan de développement)*
3. **Formateur Gestionnaire de Paie** *(Ingénierie pédagogique, Titre pro TP-01254, Qualiopi, Afpa Métis, ECF)*
4. **Gestionnaire Ressources Humaines** *(Administration du personnel senior, Contrats, Procédures disciplinaires)*

---

## 🛡️ RÈGLES QUALITYGUARD APPLIQUÉES À CHAQUE CANDIDATURE
- **Contrôle Anti-Doublon :** Lecture préalable du tableau. Zéro régénération et zéro réexpédition pour une offre déjà enregistrée.
- **Seuil Salarial :** Minimum `>= 30 000 € brut / an` (ou `>= 2 500 € brut / mois`).
- **Périmètre Géographique :** Creil (60100) `<= 2h` de trajet ou **Façades Océan Atlantique / Mer Méditerranée** ou **Télétravail**.
- **Format CV :** Strictement **1 page A4**, aucun vide en bas, typographie Arial nette.
- **Format Lettre :** Strictement **1 page A4**, destinataire aligné sur la 6ᵉ ligne (`kairos-paye.fr`), **ZÉRO mot en gras dans le corps**, signature vectorielle manuscrite lisible.
- **Aperçu Visuel :** Chaque dossier génère le PDF et une capture PNG haute résolution pour vérification directe sans code brut.
"""

        with open(self.readme_file, "w", encoding="utf-8") as f:
            f.write(content)

        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        gemini_dash = r"C:\Users\richa\Gemini\dashboard.md"
        try:
            with open(gemini_dash, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

if __name__ == "__main__":
    dm = DashboardManager()
    dm.generate_markdown_dashboard()
    dm.generate_html_dashboard()
    print("[OK] Dashboard HTML et Markdown régénérés avec regroupement par mois.")
