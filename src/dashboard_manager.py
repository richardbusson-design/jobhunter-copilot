# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def normalize_text(text: str) -> str:
    """Normalise un texte pour comparaison stricte anti-doublon."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\(h/f\)|h/f|\(f/h\)|f/h', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def safe_url_path(path_str: str) -> str:
    """Encode proprement les chemins de fichiers pour les liens HTML/navigateurs."""
    if not path_str:
        return ""
    clean = path_str.replace("\\", "/")
    parts = clean.split("/")
    encoded_parts = [urllib.parse.quote(p) for p in parts]
    return "/".join(encoded_parts)

FRENCH_MONTHS = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
}

class DashboardManager:
    def __init__(self, base_dir="."):
        self.base_dir = os.path.abspath(base_dir)
        self.dashboard_file = os.path.join(self.base_dir, "dashboard.md")
        self.readme_file = os.path.join(self.base_dir, "README.md")
        self.html_file = os.path.join(self.base_dir, "dashboard.html")
        self.tracker_file = os.path.join(self.base_dir, "tracker.json")
        self.gemini_html_file = r"C:\Users\richa\Gemini\dashboard.html"
        self.jobhunter_dir = r"C:\Users\richa\JobHunter"
        self.jobhunter_html_file = os.path.join(self.jobhunter_dir, "dashboard.html")

    def ensure_local_junction(self):
        """Garantit l'existence de la jonction candidatures dans le dossier JobHunter."""
        try:
            target_cand = os.path.join(self.base_dir, "candidatures")
            link_cand = os.path.join(self.jobhunter_dir, "candidatures")
            if os.path.exists(target_cand) and not os.path.exists(link_cand):
                import subprocess
                subprocess.run(f'cmd /c mklink /J "{link_cand}" "{target_cand}"', shell=True, capture_output=True)
        except Exception:
            pass

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
        """Extrait les empreintes uniques pour blocage strict des doublons."""
        apps = self.load_tracker()
        ids = set()
        urls = set()
        company_titles = set()
        
        for a in apps:
            if a.get("id"):
                ids.add(str(a.get("id")).strip())
            if a.get("url"):
                urls.add(str(a.get("url")).strip())
            
            c_norm = normalize_text(a.get("company", ""))
            t_norm = normalize_text(a.get("title", ""))
            if c_norm and t_norm:
                company_titles.add(f"{c_norm}|{t_norm}")
                
        return {
            "ids": ids,
            "urls": urls,
            "company_titles": company_titles,
            "count": len(apps)
        }

    def add_application(self, application_data: Dict[str, Any]):
        """Ajoute une nouvelle candidature dans le tracker JSON après vérification anti-doublon."""
        apps = self.load_tracker()
        fingerprints = self.get_existing_fingerprints()
        
        app_id = str(application_data.get("id", "")).strip()
        app_url = str(application_data.get("url", "")).strip()
        c_norm = normalize_text(application_data.get("company", ""))
        t_norm = normalize_text(application_data.get("title", ""))
        ct_pair = f"{c_norm}|{t_norm}"
        
        if app_id and app_id in fingerprints["ids"]:
            print(f"[!] BLOCAGE DOUBLON : ID {app_id} déjà existant dans le tableau.")
            return
        if app_url and app_url in fingerprints["urls"]:
            print(f"[!] BLOCAGE DOUBLON : URL {app_url} déjà existante dans le tableau.")
            return
        if ct_pair in fingerprints["company_titles"]:
            print(f"[!] BLOCAGE DOUBLON : Couple '{application_data.get('company')}' / '{application_data.get('title')}' déjà existant.")
            return
            
        if "date" not in application_data:
            application_data["date"] = datetime.now().strftime("%Y-%m-%d")
        if "relance_date" not in application_data:
            application_data["relance_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            
        apps.append(application_data)
        
        with open(self.tracker_file, "w", encoding="utf-8") as f:
            json.dump(apps, f, ensure_ascii=False, indent=2)
            
        self.generate_markdown_dashboard()
        self.generate_html_dashboard()

    def generate_html_dashboard(self):
        """Génère un tableau de bord HTML complet avec visionneuse multi-mode et statut recruteur."""
        apps = self.load_tracker()
        apps_by_month = defaultdict(list)
        
        # Compteurs statistiques dynamiques
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")
        week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        count_today = sum(1 for a in apps if a.get("date") == today_str)
        count_week = sum(1 for a in apps if a.get("date", "") >= week_ago_str and a.get("date", "") <= today_str)
        count_month = sum(1 for a in apps if a.get("date", "").startswith(current_month_str))
        count_total = len(apps)
        
        for a in apps:
            date_str = a.get("date", "2026-08-01")
            try:
                parts = date_str.split("-")
                year, month = parts[0], parts[1]
                month_name = FRENCH_MONTHS.get(month, month)
                month_key = f"{year}-{month}"
                month_label = f"{month_name} {year}"
            except Exception:
                month_key = "2026-08"
                month_label = "Août 2026"
            apps_by_month[(month_key, month_label)].append(a)
            
        sorted_months = sorted(apps_by_month.keys(), key=lambda x: x[0], reverse=True)
        
        sections_html = ""
        for month_key, month_label in sorted_months:
            month_apps = apps_by_month[(month_key, month_label)]
            
            rows_html = ""
            for idx, a in enumerate(month_apps):
                d = a.get("date", datetime.now().strftime("%Y-%m-%d"))
                comp = a.get("company", "Entreprise").replace('"', '&quot;')
                tit = a.get("title", "Poste").replace('"', '&quot;')
                ref_id = a.get("id", "REF-AUTO")
                city = a.get("city", "France")
                pcode = a.get("postal_code", "")
                salary = a.get("salary", ">= 30 000 €")
                score = a.get("score", 85)
                rel = a.get("relance_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
                source = a.get("source", "France Travail / Apec")
                url = a.get("url", "")
                desc = a.get("description", "Détail de l'offre...")
                folder_rel = a.get("folder_rel", "").replace("\\", "/")
                
                # Personne ou organisme contacté
                contact_name = a.get("contact_name") or "Monsieur le Responsable du Recrutement"
                contact_title = a.get("contact_title") or "Direction des Ressources Humaines"
                contact_cell = f'<div style="font-weight: 600; color: #f1f5f9; font-size: 13px;">{contact_name}</div><div style="font-size: 11px; color: #94a3b8;">{contact_title}</div>'
                
                # Localisation
                loc_cell = f'<div style="color: #cbd5e1; font-weight: 500;">{city}</div>'
                if pcode:
                    loc_cell += f'<div style="font-size: 11px; color: #94a3b8;">CP: {pcode}</div>'
                    
                # Téléphone
                phone = a.get("phone")
                if not phone or phone == "Non communiqué":
                    m_ph = re.search(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', desc)
                    if m_ph:
                        phone = m_ph.group(0).strip()
                if phone and phone != "Non communiqué":
                    phone_cell = f'<a href="tel:{phone.replace(" ", "")}" style="color: #38bdf8; text-decoration: none; font-weight: 600; white-space: nowrap;">📞 {phone}</a>'
                else:
                    phone_cell = '<span style="color: #64748b; font-size: 12px;">Non communiqué</span>'
                    
                # E-mail
                rec_delivery = a.get("recruiter_delivery", {})
                rec_mail = a.get("contact_email") or rec_delivery.get("recruiter_email")
                if not rec_mail:
                    m_em = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                    for em in m_em:
                        if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and 'example.com' not in em.lower():
                            rec_mail = em.strip()
                            break
                if rec_mail:
                    email_cell = f'<a href="mailto:{rec_mail}" style="color: #34d399; text-decoration: none; font-weight: 600; word-break: break-all;">✉️ {rec_mail}</a>'
                else:
                    email_cell = '<span style="background: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 6px; border-radius: 4px; border: 1px solid #334155; white-space: nowrap;">🌐 Portail Web</span>'

                # Statut d'expédition au recruteur
                if rec_delivery.get("sent"):
                    delivery_badge = f'<div style="margin-top:4px;"><span style="background: #065f46; color: #34d399; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">✉️ Transmis Recruteur ({rec_mail})</span></div>'
                elif rec_delivery.get("mode") == "WEB_PORTAL_REQUIRED":
                    delivery_badge = '<div style="margin-top:4px;"><span style="background: #854d0e; color: #fde047; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🌐 Postulation Web requise</span></div>'
                else:
                    delivery_badge = '<div style="margin-top:4px;"><span style="background: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 6px; border-radius: 4px;">📁 Dossier Prêt</span></div>'
                
                link_ref = f'<a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">🔗 {ref_id} ({source})</a>' if url else f'<span style="color: #94a3b8;">Réf. {ref_id}</span>'
                
                if folder_rel:
                    safe_folder = safe_url_path(folder_rel)
                    pdf_letter = f"{safe_folder}/Lettre_Motivation_Richard_BUSSON.pdf"
                    pdf_cv = f"{safe_folder}/CV_Richard_BUSSON.pdf"
                    png_letter = f"{safe_folder}/Lettre_Motivation_Richard_BUSSON.png"
                    png_cv = f"{safe_folder}/CV_Richard_BUSSON.png"
                    html_letter = f"{safe_folder}/Lettre_Motivation_Richard_BUSSON.html"
                    html_cv = f"{safe_folder}/CV_Richard_BUSSON.html"
                    
                    js_comp = comp.replace("'", "\\'").replace('"', '&quot;')
                    js_tit = tit.replace("'", "\\'").replace('"', '&quot;')
                    
                    action_col = f"""
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      <button class="btn-action btn-view" onclick="openViewerModal('{js_comp}', '{js_tit}', '{pdf_letter}', '{pdf_cv}', '{png_letter}', '{png_cv}', '{html_letter}', '{html_cv}')">
                        👁️ Consulter Dossier
                      </button>
                      <div style="display: flex; gap: 4px;">
                        <a class="btn-action btn-pdf" href="{pdf_letter}" target="_blank" title="Ouvrir la Lettre PDF">✉️ Lettre</a>
                        <a class="btn-action btn-pdf" href="{pdf_cv}" target="_blank" title="Ouvrir le CV PDF">📄 CV</a>
                      </div>
                    </div>
                    """
                else:
                    action_col = '<span style="color: #94a3b8;">Dossier Prêt</span>'
                    
                rows_html += f"""
                <tr>
                  <td style="white-space: nowrap; font-weight: bold; color: #cbd5e1;">{d}</td>
                  <td><strong style="color: #f1f5f9; font-size: 15px;">{comp}</strong></td>
                  <td>{contact_cell}</td>
                  <td>{loc_cell}</td>
                  <td style="white-space: nowrap;">{phone_cell}</td>
                  <td>{email_cell}</td>
                  <td>
                    <div style="font-weight: 600; color: #38bdf8; font-size: 14px;">{tit}</div>
                    <div style="margin-top: 4px; font-size: 12px;">{link_ref}</div>
                    <div style="margin-top: 4px; font-size: 12px; color: #34d399;">💰 {salary} • <span class="score-badge">{score}%</span></div>
                    <details style="margin-top: 8px; background: #0b1120; padding: 8px 12px; border-radius: 6px; border: 1px solid #334155;">
                      <summary style="cursor: pointer; color: #94a3b8; font-size: 12px; font-weight: 600;">📝 Voir le texte intégral de l'annonce</summary>
                      <div style="margin-top: 8px; color: #cbd5e1; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">{desc}</div>
                    </details>
                  </td>
                  <td style="white-space: nowrap;">{delivery_badge}</td>
                  <td style="white-space: nowrap;">{action_col}</td>
                </tr>
                """
                
            sections_html += f"""
            <div class="month-card">
              <div class="month-header" onclick="toggleMonth('{month_key}')">
                <div class="month-title">
                  <span class="badge-count">{len(month_apps)}</span>
                  <span>🗓️ {month_label}</span>
                </div>
                <span id="icon-{month_key}" class="toggle-icon">▼</span>
              </div>
              <div id="content-{month_key}" class="month-content">
                <div class="table-responsive">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Entreprise</th>
                        <th>Contact / Destinataire</th>
                        <th>Localisation</th>
                        <th>Téléphone</th>
                        <th>E-mail</th>
                        <th>Poste & Annonce Source</th>
                        <th>Statut Envoi</th>
                        <th>Dossier Officiel</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows_html}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            """

        full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Tableau de Bord - Candidatures Richard BUSSON</title>
  <style>
    :root {{
      --bg-dark: #0f172a;
      --card-bg: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-green: #34d399;
      --border-color: #334155;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      padding: 24px;
      line-height: 1.5;
    }}
    .container {{ max-width: 1500px; margin: 0 auto; }}
    .header {{
      background: linear-gradient(135deg, #1e293b, #0f172a);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px 32px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .header h1 {{ font-size: 26px; color: #ffffff; margin-bottom: 6px; }}
    .header p {{ color: var(--text-muted); font-size: 14px; }}
    .stats-bar {{ display: flex; gap: 16px; }}
    .stat-badge {{
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 10px 18px;
      border-radius: 8px;
      text-align: center;
    }}
    .stat-badge .val {{ font-size: 22px; font-weight: bold; color: var(--accent-blue); }}
    .stat-badge .lbl {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; }}
    .month-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      margin-bottom: 20px;
      overflow: hidden;
    }}
    .month-header {{
      background: #1e293b;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      border-bottom: 1px solid var(--border-color);
      user-select: none;
    }}
    .month-title {{ display: flex; align-items: center; gap: 12px; font-size: 18px; font-weight: bold; }}
    .badge-count {{
      background: var(--accent-blue);
      color: #0f172a;
      font-size: 13px;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 20px;
    }}
    .table-responsive {{ overflow-x: auto; }}
    .data-table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
    .data-table th {{
      background: #0f172a;
      padding: 12px 16px;
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 2px solid var(--border-color);
    }}
    .data-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-color);
      vertical-align: top;
    }}
    .score-badge {{
      background: rgba(52, 211, 153, 0.15);
      color: var(--accent-green);
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: bold;
      display: inline-block;
    }}
    .btn-action {{
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: bold;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
    }}
    .btn-view {{ background: #2563eb; color: #ffffff; width: 100%; margin-bottom: 4px; }}
    .btn-view:hover {{ background: #1d4ed8; }}
    .btn-pdf {{ background: #334155; color: #f8fafc; flex: 1; }}
    .btn-pdf:hover {{ background: #475569; }}
    
    /* MODAL DE VISIONNEUSE HD AUTO-SECOURS */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.85);
      z-index: 9999;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }}
    .modal-box {{
      background: #1e293b;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      width: 95%;
      max-width: 1200px;
      height: 92vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }}
    .modal-header {{
      background: #0f172a;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-color);
    }}
    .modal-body {{
      display: flex;
      flex: 1;
      overflow: hidden;
      background: #0f172a;
    }}
    .viewer-tab-content {{
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      overflow-y: auto;
      padding: 20px;
    }}
    .doc-page {{
      background: #ffffff;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      border-radius: 4px;
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>📋 Tableau de Bord - Candidatures Richard BUSSON</h1>
        <p>Expert Paie & Ressources Humaines • Suivi en temps réel des candidatures certifiées</p>
      </div>
      <div class="stats-bar">
        <div class="stat-badge" style="border-color: rgba(56, 189, 248, 0.4);">
          <div class="val" style="color: #38bdf8;">{count_today}</div>
          <div class="lbl">Aujourd'hui</div>
        </div>
        <div class="stat-badge" style="border-color: rgba(129, 140, 248, 0.4);">
          <div class="val" style="color: #818cf8;">{count_week}</div>
          <div class="lbl">Cette Semaine</div>
        </div>
        <div class="stat-badge" style="border-color: rgba(245, 158, 11, 0.4);">
          <div class="val" style="color: #f59e0b;">{count_month}</div>
          <div class="lbl">Ce Mois-ci</div>
        </div>
        <div class="stat-badge" style="border-color: rgba(52, 211, 153, 0.4);">
          <div class="val" style="color: #34d399;">{count_total}</div>
          <div class="lbl">Total Envoyées</div>
        </div>
      </div>
    </div>

    {sections_html}
  </div>

  <!-- MODAL VISIONNEUSE MULTI-MODE -->
  <div id="viewerModal" class="modal-overlay" onclick="closeViewerModal(event)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div>
          <h3 id="modalTitle" style="color: #f8fafc; font-size: 16px;">Dossier de Candidature</h3>
          <div id="modalSub" style="color: #94a3b8; font-size: 13px;"></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <div style="background: #0f172a; border-radius: 8px; padding: 4px; display: flex; gap: 4px;">
            <button id="tabBtnLettre" class="btn-action" style="background: #2563eb; color: #fff;" onclick="switchDocTab('lettre')">✉️ Lettre de Motivation</button>
            <button id="tabBtnCv" class="btn-action" style="background: #334155; color: #fff;" onclick="switchDocTab('cv')">📄 Curriculum Vitae</button>
          </div>
          <a id="btnDownloadPdf" href="#" target="_blank" class="btn-action" style="background: #059669; color: #fff;">⬇️ Ouvrir PDF</a>
          <button class="btn-action" style="background: #ef4444; color: #fff;" onclick="closeViewerModal()">✕ Fermer</button>
        </div>
      </div>
      <div class="modal-body">
        <div class="viewer-tab-content">
          <div id="viewContainerLettre" style="display: flex; justify-content: center; width: 100%;">
            <img id="imgLettre" class="doc-page" src="" alt="Lettre de Motivation" onerror="handleImageError(this, 'lettre')" />
            <iframe id="frameLettre" style="display: none; width: 794px; height: 1123px; border: none; background: #fff;" src=""></iframe>
          </div>
          <div id="viewContainerCv" style="display: none; justify-content: center; width: 100%;">
            <img id="imgCv" class="doc-page" src="" alt="Curriculum Vitae" onerror="handleImageError(this, 'cv')" />
            <iframe id="frameCv" style="display: none; width: 794px; height: 1123px; border: none; background: #fff;" src=""></iframe>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentDossier = {{}};
    function toggleMonth(k) {{
      const c = document.getElementById('content-' + k);
      const ic = document.getElementById('icon-' + k);
      if (c.style.display === 'none') {{
        c.style.display = 'block';
        ic.innerText = '▼';
      }} else {{
        c.style.display = 'none';
        ic.innerText = '▶';
      }}
    }}
    function openViewerModal(comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC) {{
      currentDossier = {{ comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC }};
      document.getElementById('modalTitle').innerText = comp;
      document.getElementById('modalSub').innerText = tit;
      switchDocTab('lettre');
      document.getElementById('viewerModal').style.display = 'flex';
    }}
    function closeViewerModal() {{
      document.getElementById('viewerModal').style.display = 'none';
    }}
    function switchDocTab(tab) {{
      const bL = document.getElementById('tabBtnLettre');
      const bC = document.getElementById('tabBtnCv');
      const vL = document.getElementById('viewContainerLettre');
      const vC = document.getElementById('viewContainerCv');
      const dPdf = document.getElementById('btnDownloadPdf');

      if (tab === 'lettre') {{
        bL.style.background = '#2563eb';
        bC.style.background = '#334155';
        vL.style.display = 'flex';
        vC.style.display = 'none';
        dPdf.href = currentDossier.pdfL;
        document.getElementById('imgLettre').src = currentDossier.pngL;
        document.getElementById('frameLettre').src = currentDossier.htmlL;
      }} else {{
        bL.style.background = '#334155';
        bC.style.background = '#2563eb';
        vL.style.display = 'none';
        vC.style.display = 'flex';
        dPdf.href = currentDossier.pdfC;
        document.getElementById('imgCv').src = currentDossier.pngC;
        document.getElementById('frameCv').src = currentDossier.htmlC;
      }}
    }}
    function handleImageError(imgEl, type) {{
      imgEl.style.display = 'none';
      if (type === 'lettre') {{
        document.getElementById('frameLettre').style.display = 'block';
      }} else {{
        document.getElementById('frameCv').style.display = 'block';
      }}
    }}
  </script>
</body>
</html>"""

        with open(self.html_file, "w", encoding="utf-8") as f:
            f.write(full_html)
            
        try:
            with open(self.gemini_html_file, "w", encoding="utf-8") as f:
                f.write(full_html)
        except Exception:
            pass
            
        try:
            os.makedirs(self.jobhunter_dir, exist_ok=True)
            with open(self.jobhunter_html_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            self.ensure_local_junction()
        except Exception:
            pass

    def generate_markdown_dashboard(self):
        """Génère le dashboard Markdown et le README.md."""
        apps = self.load_tracker()
        apps_by_month = defaultdict(list)
        
        for a in apps:
            date_str = a.get("date", "2026-08-01")
            try:
                parts = date_str.split("-")
                year, month = parts[0], parts[1]
                month_name = FRENCH_MONTHS.get(month, month)
                month_key = f"{year}-{month}"
                month_label = f"{month_name} {year}"
            except Exception:
                month_key = "2026-08"
                month_label = "Août 2026"
            apps_by_month[(month_key, month_label)].append(a)
            
        sorted_months = sorted(apps_by_month.keys(), key=lambda x: x[0], reverse=True)
        
        # Compteurs statistiques dynamiques
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")
        week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        count_today = sum(1 for a in apps if a.get("date") == today_str)
        count_week = sum(1 for a in apps if a.get("date", "") >= week_ago_str and a.get("date", "") <= today_str)
        count_month = sum(1 for a in apps if a.get("date", "").startswith(current_month_str))
        count_total = len(apps)
        
        md_content = f"# 📋 TABLEAU DE BORD DES CANDIDATURES — RICHARD BUSSON\n\n"
        md_content += f"> ### 📊 Compteurs d'Envoi et Suivi d'Activité\n"
        md_content += f"> | 📅 Aujourd'hui | 📆 Cette Semaine | 🗓️ Ce Mois-ci | 🏆 Total Envoyées |\n"
        md_content += f"> | :---: | :---: | :---: | :---: |\n"
        md_content += f"> | **{count_today}** | **{count_week}** | **{count_month}** | **{count_total}** |\n"
        md_content += f">\n"
        md_content += f"> *Dernière mise à jour et synchronisation : {now.strftime('%d/%m/%Y %H:%M')}*\n\n"
        
        for month_key, month_label in sorted_months:
            month_apps = apps_by_month[(month_key, month_label)]
            md_content += f"## 🗓️ {month_label} ({len(month_apps)} candidatures)\n\n"
            md_content += "| Date | Entreprise | Contact / Destinataire | Localisation | Téléphone | E-mail | Poste & Annonce Source | Statut Envoi | Dossier PDF |\n"
            md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            
            for a in month_apps:
                d = a.get("date", "")
                comp = a.get("company", "Entreprise").replace("|", "-")
                contact_name = a.get("contact_name") or "Monsieur le Responsable du Recrutement"
                contact_title = a.get("contact_title") or "Direction des Ressources Humaines"
                tit = a.get("title", "Poste").replace("|", "-")
                city = a.get("city", "France")
                pcode = a.get("postal_code", "")
                loc_str = f"{city} ({pcode})" if pcode else city
                salary = a.get("salary", ">= 30k€")
                score = a.get("score", 85)
                url = a.get("url", "")
                desc = a.get("description", "")
                folder_rel = a.get("folder_rel", "").replace("\\", "/")
                
                # Téléphone
                phone = a.get("phone")
                if not phone or phone == "Non communiqué":
                    m_ph = re.search(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', desc)
                    phone = m_ph.group(0).strip() if m_ph else "Non communiqué"
                    
                # E-mail
                rec_delivery = a.get("recruiter_delivery", {})
                rec_mail = a.get("contact_email") or rec_delivery.get("recruiter_email")
                if not rec_mail:
                    m_em = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                    for em in m_em:
                        if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and 'example.com' not in em.lower():
                            rec_mail = em.strip()
                            break
                email_md = f"[{rec_mail}](mailto:{rec_mail})" if rec_mail else "🌐 Portail Web"
                
                if rec_delivery.get("sent"):
                    send_status = f"🟢 Transmis ({rec_delivery.get('recruiter_email', '')})"
                elif rec_delivery.get("mode") == "WEB_PORTAL_REQUIRED":
                    send_status = "🌐 Portail Web"
                else:
                    send_status = "📁 Prêt"
                    
                tit_link = f"[{tit}]({url})" if url else tit
                pdf_letter_link = f"[Lettre]({safe_url_path(folder_rel)}/Lettre_Motivation_Richard_BUSSON.pdf)" if folder_rel else "-"
                pdf_cv_link = f"[CV]({safe_url_path(folder_rel)}/CV_Richard_BUSSON.pdf)" if folder_rel else "-"
                
                md_content += f"| {d} | **{comp}** | {contact_name} ({contact_title}) | {loc_str} | {phone} | {email_md} | {tit_link} ({salary} - {score}%) | {send_status} | {pdf_letter_link} / {pdf_cv_link} |\n"
                
            md_content += "\n"
            
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        with open(self.readme_file, "w", encoding="utf-8") as f:
            f.write(md_content)

if __name__ == "__main__":
    dm = DashboardManager()
    dm.generate_html_dashboard()
    dm.generate_markdown_dashboard()
    print("[✓] Tableaux de bord HTML et Markdown régénérés avec succès.")
