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

def classify_sectors(title: str, desc: str) -> List[str]:
    """Catégorise l'offre selon les 3 piliers d'expertise de Richard Busson."""
    t = (title or "").lower()
    d = (desc or "").lower()
    sectors = set()
    
    # Formation / Ingénierie Pédagogique / Qualiopi
    if any(k in t for k in ["format", "enseign", "pédagog", "pedagog", "qualiopi", "métis", "metis", "afpa", "titre pro", "adea", "formateur", "formatrice", "professeur", "intervenant", "tuteur", "ingénieur pédagogique"]):
        sectors.add("formation")
    elif any(k in d[:400] for k in ["titre professionnel", "tp-01254", "qualiopi", "ingénierie pédagogique", "ingenierie pedagogique"]):
        sectors.add("formation")

    # Paie / Gestion Sociale / Silae
    if any(k in t for k in ["paie", "paye", "bulletin", "dsn", "salaire", "rémunération", "remuneration", "silae", "charges sociales"]):
        sectors.add("paie")
        
    # Ressources Humaines / Direction RH / Relations Sociales
    if any(k in t for k in ["rh", "ressources humaines", "drh", "rrh", "personnel", "social", "sociales", "talent", "recrutement", "adp"]):
        sectors.add("rh")

    if not sectors:
        if any(k in d for k in ["paie", "paye", "bulletin"]):
            sectors.add("paie")
        if any(k in d for k in ["ressources humaines", " rh "]):
            sectors.add("rh")
        if not sectors:
            sectors.add("rh")
            
    return list(sectors)

FRENCH_MONTHS = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
}

def parse_date_str(date_str: str) -> Tuple[str, str, str]:
    """Parse une date brute (YYYY-MM-DD ou texte France Travail DD/MM/YYYY) et retourne (clean_date, month_key, month_label)."""
    if not date_str:
        return "2026-08-01", "2026-08", "Août 2026"
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        month_name = FRENCH_MONTHS.get(mo, mo)
        return f"{y}-{mo}-{d}", f"{y}-{mo}", f"{month_name} {y}"
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        month_name = FRENCH_MONTHS.get(mo, mo)
        return f"{y}-{mo}-{d}", f"{y}-{mo}", f"{month_name} {y}"
    return "2026-08-01", "2026-08", "Août 2026"

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
        """Extrait les empreintes uniques pour blocage strict des doublons (inclut l'historique archivé)."""
        apps = self.load_tracker()
        all_tracked_apps = list(apps)
        
        # Charger également l'historique archivé dans data/ pour un blocage anti-doublon absolu
        backup_dir = os.path.join(self.base_dir, "data")
        if os.path.exists(backup_dir):
            for fname in os.listdir(backup_dir):
                if fname.endswith(".json") and "backup" in fname:
                    try:
                        with open(os.path.join(backup_dir, fname), "r", encoding="utf-8") as f:
                            b_data = json.load(f)
                            if isinstance(b_data, list):
                                all_tracked_apps.extend(b_data)
                    except Exception:
                        pass
                        
        ids = set()
        urls = set()
        company_titles = set()
        
        for a in all_tracked_apps:
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
            "count": len(all_tracked_apps),
            "total_count": len(all_tracked_apps)
        }

    def is_duplicate(self, job: Dict[str, Any], fps: Dict[str, Any]) -> Tuple[bool, str]:
        """Vérifie si une offre est un doublon par ID, URL ou couple Entreprise/Titre."""
        job_id = str(job.get("id", "")).strip()
        job_url = str(job.get("url", "")).strip()
        c_norm = normalize_text(job.get("company", ""))
        t_norm = normalize_text(job.get("title", ""))
        ct_pair = f"{c_norm}|{t_norm}" if c_norm and t_norm else ""
        
        # Test direct sur les sets ou avec remplacement de underscores pour robustesse
        ids = fps.get("ids", set())
        urls = fps.get("urls", set())
        cts = fps.get("company_titles", set())
        
        if job_id and job_id in ids:
            return True, f"Identifiant unique déjà existant ({job_id})"
        if job_url and job_url in urls:
            return True, f"URL déjà traitée ({job_url})"
        if ct_pair:
            # Vérifie correspondance directe ou partielle
            for ct in cts:
                ct_clean = ct.replace("___", "|")
                if ct_pair == ct_clean or ct_pair == ct:
                    return True, f"Couple Entreprise / Titre déjà traité ({ct_pair})"
                if "|" in ct_clean:
                    e_part, t_part = ct_clean.split("|", 1)
                    if e_part in c_norm or c_norm in e_part:
                        words_t = set(t_part.split()) - {"de", "et", "le", "la", "en", "du", "des", "pour"}
                        words_norm = set(t_norm.split())
                        if words_t and (words_t.issubset(words_norm) or len(words_t & words_norm) >= 2):
                            return True, f"Poste similaire détecté pour la même entreprise ({c_norm})"
        return False, ""

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
        
        for a in apps:
            clean_d, month_key, month_label = parse_date_str(a.get("date"))
            a["_clean_date"] = clean_d
            apps_by_month[(month_key, month_label)].append(a)
            
        # Compteurs statistiques dynamiques
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")
        week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        count_today = sum(1 for a in apps if a.get("_clean_date") == today_str)
        count_week = sum(1 for a in apps if a.get("_clean_date", "") >= week_ago_str and a.get("_clean_date", "") <= today_str)
        count_month = sum(1 for a in apps if a.get("_clean_date", "").startswith(current_month_str))
        count_total = len(apps)

        def get_delivery_state(a):
            rec_delivery = a.get("recruiter_delivery", {})
            if isinstance(rec_delivery, dict):
                is_sent = rec_delivery.get("sent", False)
                is_portal = rec_delivery.get("mode") == "WEB_PORTAL_REQUIRED"
            elif isinstance(rec_delivery, str):
                is_sent = "SUBMITTED" in rec_delivery or "CONFIRMED" in rec_delivery
                is_portal = "WEB_PORTAL" in rec_delivery
            else:
                is_sent = False
                is_portal = False
            proof_p = os.path.join(self.base_dir, a.get("folder_rel", ""), "preuve_soumission_officielle.png") if a.get("folder_rel") else ""
            has_p = bool(proof_p and os.path.exists(proof_p))
            if is_sent or has_p:
                return "confirmed"
            elif is_portal:
                return "portal"
            else:
                return "ready"

        count_proofs = sum(1 for a in apps if a.get("folder_rel") and os.path.exists(os.path.join(self.base_dir, a["folder_rel"], "preuve_soumission_officielle.png")))
        count_confirmed = sum(1 for a in apps if get_delivery_state(a) == "confirmed")
        count_portal = sum(1 for a in apps if get_delivery_state(a) == "portal")
        count_ready = sum(1 for a in apps if get_delivery_state(a) == "ready")

        count_formation = sum(1 for a in apps if "formation" in classify_sectors(a.get("title", ""), a.get("description", "")))
        count_paie = sum(1 for a in apps if "paie" in classify_sectors(a.get("title", ""), a.get("description", "")))
        count_rh = sum(1 for a in apps if "rh" in classify_sectors(a.get("title", ""), a.get("description", "")))
        
        sorted_months = sorted(apps_by_month.keys(), key=lambda x: x[0], reverse=True)
        
        sections_html = ""
        for month_key, month_label in sorted_months:
            month_apps = apps_by_month[(month_key, month_label)]
            
            rows_html = ""
            for idx, a in enumerate(month_apps):
                d = a.get("_clean_date") or a.get("date", datetime.now().strftime("%Y-%m-%d"))
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
                if isinstance(rec_delivery, dict):
                    rec_mail = a.get("contact_email") or rec_delivery.get("recruiter_email")
                    is_sent = rec_delivery.get("sent")
                    is_portal = rec_delivery.get("mode") == "WEB_PORTAL_REQUIRED"
                elif isinstance(rec_delivery, str):
                    rec_mail = a.get("contact_email")
                    is_sent = "SUBMITTED" in rec_delivery or "CONFIRMED" in rec_delivery
                    is_portal = "WEB_PORTAL" in rec_delivery
                else:
                    rec_mail = a.get("contact_email")
                    is_sent = False
                    is_portal = False

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
                if is_sent:
                    mode_label = "Portail Web" if (isinstance(rec_delivery, dict) and "PORTAL" in str(rec_delivery.get("mode", ""))) else (rec_delivery.get("mode") if isinstance(rec_delivery, dict) else "Validé")
                    delivery_badge = f'<div style="margin-top:4px;"><span style="background: #065f46; color: #34d399; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">✓ Transmise &amp; Validée ({mode_label})</span></div>'
                elif is_portal:
                    delivery_badge = '<div style="margin-top:4px;"><span style="background: #854d0e; color: #fde047; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🌐 Postulation Web requise</span></div>'
                else:
                    delivery_badge = '<div style="margin-top:4px;"><span style="background: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 6px; border-radius: 4px;">📁 Dossier Prêt</span></div>'
                
                link_ref = f'<a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">🔗 {ref_id} ({source})</a>' if url else f'<span style="color: #94a3b8;">Réf. {ref_id}</span>'
                
                proof_path = os.path.join(self.base_dir, folder_rel, "preuve_soumission_officielle.png") if folder_rel else ""
                has_proof = bool(proof_path and os.path.exists(proof_path))
                safe_proof = f"{safe_url_path(folder_rel)}/preuve_soumission_officielle.png" if (folder_rel and has_proof) else ""

                if is_sent or has_proof:
                    status_attr = "confirmed"
                elif is_portal:
                    status_attr = "portal"
                else:
                    status_attr = "ready"

                secs = classify_sectors(tit, desc)
                sectors_attr = " ".join(secs)

                raw_search = f"{d} {comp} {tit} {city} {pcode} {ref_id} {source} {contact_name} {contact_title} {salary}"
                clean_search = normalize_text(raw_search)

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

                    proof_btn = ""
                    if has_proof:
                        proof_btn = f'<button class="btn-action" style="background: #059669; color: #fff; margin-top: 4px;" onclick="openProofModal(\'{js_comp}\', \'{js_tit}\', \'{pdf_letter}\', \'{pdf_cv}\', \'{png_letter}\', \'{png_cv}\', \'{html_letter}\', \'{html_cv}\', \'{safe_proof}\')" title="Visualiser la preuve officielle certifiée">📸 Preuve Officielle</button>'
                    
                    action_col = f"""
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      <button class="btn-action btn-view" onclick="openViewerModal('{js_comp}', '{js_tit}', '{pdf_letter}', '{pdf_cv}', '{png_letter}', '{png_cv}', '{html_letter}', '{html_cv}', '{safe_proof}')">
                        👁️ Consulter Dossier
                      </button>
                      <div style="display: flex; gap: 4px;">
                        <a class="btn-action btn-pdf" href="{pdf_letter}" target="_blank" title="Ouvrir la Lettre PDF">✉️ Lettre</a>
                        <a class="btn-action btn-pdf" href="{pdf_cv}" target="_blank" title="Ouvrir le CV PDF">📄 CV</a>
                      </div>
                      {proof_btn}
                    </div>
                    """
                else:
                    action_col = '<span style="color: #94a3b8;">Dossier Prêt</span>'
                    
                rows_html += f"""
                <tr class="job-row" data-status="{status_attr}" data-sectors="{sectors_attr}" data-has-proof="{1 if has_proof else 0}" data-search="{clean_search}">
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
    
    /* BARRE DE RECHERCHE ET FILTRES */
    .filters-panel {{
      background: rgba(30, 41, 59, 0.95);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 18px 24px;
      margin-bottom: 24px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .search-row {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }}
    .search-input-wrap {{
      position: relative;
      flex: 1;
      display: flex;
      align-items: center;
    }}
    .search-icon {{
      position: absolute;
      left: 14px;
      font-size: 16px;
      color: var(--text-muted);
      pointer-events: none;
    }}
    #dashboardSearch {{
      width: 100%;
      background: #0f172a;
      border: 1px solid #475569;
      border-radius: 8px;
      padding: 10px 38px 10px 42px;
      color: #f8fafc;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }}
    #dashboardSearch:focus {{
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }}
    .btn-clear {{
      position: absolute;
      right: 12px;
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 14px;
      display: none;
      padding: 4px;
    }}
    .btn-clear:hover {{ color: #f8fafc; }}
    .results-badge {{
      background: #0f172a;
      border: 1px solid var(--border-color);
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 700;
      color: var(--accent-blue);
      white-space: nowrap;
    }}
    .btn-reset-filters {{
      background: #334155;
      border: 1px solid #475569;
      color: #f8fafc;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s;
    }}
    .btn-reset-filters:hover {{
      background: #475569;
    }}
    .filter-groups {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .filter-group {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .filter-group-label {{
      font-size: 11px;
      font-weight: 800;
      color: var(--text-muted);
      width: 75px;
      letter-spacing: 0.5px;
    }}
    .filter-pill {{
      background: #0f172a;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-pill:hover {{
      background: #1e293b;
      color: #f8fafc;
      border-color: #475569;
    }}
    .filter-pill.active {{
      background: #2563eb;
      color: #ffffff;
      border-color: #38bdf8;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }}
    .filter-pill.pill-confirmed.active {{
      background: #065f46;
      border-color: #34d399;
      color: #ecfdf5;
      box-shadow: 0 0 10px rgba(52, 211, 153, 0.3);
    }}
    .filter-pill.pill-proof.active {{
      background: #059669;
      border-color: #10b981;
      color: #ecfdf5;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }}
    .filter-pill.pill-portal.active {{
      background: #854d0e;
      border-color: #fde047;
      color: #fef9c3;
      box-shadow: 0 0 10px rgba(253, 224, 71, 0.3);
    }}
    .filter-pill.pill-ready.active {{
      background: #475569;
      border-color: #94a3b8;
      color: #f8fafc;
    }}
    .filter-pill.pill-rh.active {{
      background: #1e40af;
      border-color: #60a5fa;
      color: #eff6ff;
      box-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
    }}
    .filter-pill.pill-paie.active {{
      background: #0e7490;
      border-color: #22d3ee;
      color: #ecfeff;
      box-shadow: 0 0 10px rgba(34, 211, 238, 0.3);
    }}
    .filter-pill.pill-formation.active {{
      background: #6d28d9;
      border-color: #c084fc;
      color: #faf5ff;
      box-shadow: 0 0 10px rgba(192, 132, 252, 0.3);
    }}

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
        <p>Expert Paie &amp; Ressources Humaines • Suivi en temps réel des candidatures certifiées</p>
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
          <div class="lbl">Total Traitées</div>
        </div>
      </div>
    </div>

    <!-- BARRE DE RECHERCHE ET FILTRES MULTI-CRITÈRES -->
    <div class="filters-panel">
      <div class="search-row">
        <div class="search-input-wrap">
          <span class="search-icon">🔍</span>
          <input type="text" id="dashboardSearch" placeholder="Rechercher une entreprise, poste, ville, département, code postal, mot-clé..." oninput="applyFilters()" autocomplete="off" />
          <button id="btnClearSearch" class="btn-clear" onclick="clearSearch()" title="Effacer la recherche">✕</button>
        </div>
        <div id="resultsCount" class="results-badge">
          {count_total} dossiers
        </div>
        <button class="btn-reset-filters" onclick="resetAllFilters()" title="Réinitialiser tous les filtres">↺ Réinitialiser</button>
      </div>
      
      <div class="filter-groups">
        <div class="filter-group">
          <span class="filter-group-label">STATUT :</span>
          <button class="filter-pill active" data-filter-type="status" data-filter-val="all" onclick="setStatusFilter('all')">
            Tous ({count_total})
          </button>
          <button class="filter-pill pill-confirmed" data-filter-type="status" data-filter-val="confirmed" onclick="setStatusFilter('confirmed')">
            🟢 Transmises &amp; Certifiées ({count_confirmed})
          </button>
          <button class="filter-pill pill-proof" data-filter-type="status" data-filter-val="proof_only" onclick="setStatusFilter('proof_only')">
            📸 Avec Preuve ({count_proofs})
          </button>
          <button class="filter-pill pill-portal" data-filter-type="status" data-filter-val="portal" onclick="setStatusFilter('portal')">
            🌐 Postulation Web ({count_portal})
          </button>
          <button class="filter-pill pill-ready" data-filter-type="status" data-filter-val="ready" onclick="setStatusFilter('ready')">
            📁 Prêtes ({count_ready})
          </button>
        </div>
        
        <div class="filter-group">
          <span class="filter-group-label">MÉTIER :</span>
          <button class="filter-pill active" data-filter-type="sector" data-filter-val="all" onclick="setSectorFilter('all')">
            Tous Métiers ({count_total})
          </button>
          <button class="filter-pill pill-rh" data-filter-type="sector" data-filter-val="rh" onclick="setSectorFilter('rh')">
            👔 Direction RH ({count_rh})
          </button>
          <button class="filter-pill pill-paie" data-filter-type="sector" data-filter-val="paie" onclick="setSectorFilter('paie')">
            📊 Paie &amp; Silae ({count_paie})
          </button>
          <button class="filter-pill pill-formation" data-filter-type="sector" data-filter-val="formation" onclick="setSectorFilter('formation')">
            🎓 Formation Qualiopi ({count_formation})
          </button>
        </div>
      </div>
    </div>

    <!-- MESSAGE AUCUN RÉSULTAT -->
    <div id="noResultsMsg" style="display: none; background: #1e293b; border: 1px dashed #475569; border-radius: 12px; padding: 48px 24px; text-align: center; margin-bottom: 24px;">
      <div style="font-size: 36px; margin-bottom: 12px;">🔍</div>
      <div style="font-size: 18px; font-weight: bold; color: #f8fafc; margin-bottom: 6px;">Aucun dossier ne correspond à vos critères de recherche</div>
      <p style="color: #94a3b8; font-size: 14px; margin-bottom: 16px;">Essayez d'ajuster vos mots-clés ou réinitialisez les filtres.</p>
      <button class="btn-action" style="background: #2563eb; color: #fff; padding: 8px 18px; font-size: 13px;" onclick="resetAllFilters()">↺ Réinitialiser tous les filtres</button>
    </div>

    {sections_html}
  </div>

  <!-- MODAL VISIONNEUSE MULTI-MODE AVEC ONGLET PREUVE -->
  <div id="viewerModal" class="modal-overlay" onclick="closeViewerModal(event)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div>
          <h3 id="modalTitle" style="color: #f8fafc; font-size: 16px; font-weight: 700;">Dossier de Candidature</h3>
          <div id="modalSub" style="color: #94a3b8; font-size: 13px;"></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <div style="background: #0f172a; border-radius: 8px; padding: 4px; display: flex; gap: 4px; border: 1px solid #334155;">
            <button id="tabBtnLettre" class="btn-action" style="background: #2563eb; color: #fff;" onclick="switchDocTab('lettre')">✉️ Lettre de Motivation</button>
            <button id="tabBtnCv" class="btn-action" style="background: #334155; color: #cbd5e1;" onclick="switchDocTab('cv')">📄 Curriculum Vitae</button>
            <button id="tabBtnPreuve" class="btn-action" style="background: #334155; color: #cbd5e1;" onclick="switchDocTab('preuve')">📸 Preuve de Dépôt</button>
          </div>
          <a id="btnDownloadPdf" href="#" target="_blank" class="btn-action" style="background: #059669; color: #fff;">⬇️ Ouvrir Document</a>
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
          <div id="viewContainerPreuve" style="display: none; justify-content: center; width: 100%; flex-direction: column; align-items: center; gap: 14px;">
            <div id="preuveBanner" style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #34d399; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 10px; max-width: 900px; width: 100%;">
              <span style="font-size: 18px;">✅</span>
              <div>
                <div>Récépissé officiel de télécandidature certifié conforme</div>
                <div style="font-size: 11px; color: #a7f3d0; font-weight: normal;">Horodatage, contrôle anti-faux positif et preuve de dépôt vérifiée par QualityGuard.</div>
              </div>
            </div>
            <img id="imgPreuve" class="doc-page" src="" alt="Preuve Officielle de Dépôt" style="max-width: 95%; max-height: 80vh; object-fit: contain; border: 1px solid #334155; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.6);" />
            <div id="noPreuveMsg" style="display: none; color: #94a3b8; font-size: 15px; padding: 60px 20px; text-align: center;">
              <div style="font-size: 40px; margin-bottom: 12px;">📁</div>
              <div style="font-weight: 700; color: #f1f5f9; margin-bottom: 6px;">Aucune capture d'écran de télécandidature pour ce dossier</div>
              <div style="font-size: 13px; color: #64748b;">Le dossier (CV et Lettre) est préparé et prêt pour soumission sur le portail recruteur.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentDossier = {{}};
    let currentStatusFilter = 'all';
    let currentSectorFilter = 'all';

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

    function openViewerModal(comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC, proofUrl) {{
      currentDossier = {{ comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC, proofUrl }};
      document.getElementById('modalTitle').innerText = comp;
      document.getElementById('modalSub').innerText = tit;
      
      const tabP = document.getElementById('tabBtnPreuve');
      if (proofUrl && proofUrl.trim() !== '') {{
        tabP.innerHTML = '📸 Preuve de Dépôt <span style="background:#10b981; color:#fff; font-size:10px; border-radius:8px; padding:1px 5px; margin-left:4px;">Certifiée</span>';
        tabP.title = 'Preuve de dépôt certifiée disponible';
      }} else {{
        tabP.innerHTML = '📸 Preuve de Dépôt';
        tabP.title = 'Aucune preuve capturée';
      }}
      
      switchDocTab('lettre');
      document.getElementById('viewerModal').style.display = 'flex';
    }}

    function openProofModal(comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC, proofUrl) {{
      openViewerModal(comp, tit, pdfL, pdfC, pngL, pngC, htmlL, htmlC, proofUrl);
      switchDocTab('preuve');
    }}

    function closeViewerModal(event) {{
      if (event && event.target && event.target.id !== 'viewerModal') {{
        return;
      }}
      document.getElementById('viewerModal').style.display = 'none';
    }}

    function switchDocTab(tab) {{
      const bL = document.getElementById('tabBtnLettre');
      const bC = document.getElementById('tabBtnCv');
      const bP = document.getElementById('tabBtnPreuve');
      const vL = document.getElementById('viewContainerLettre');
      const vC = document.getElementById('viewContainerCv');
      const vP = document.getElementById('viewContainerPreuve');
      const dPdf = document.getElementById('btnDownloadPdf');

      [bL, bC, bP].forEach(b => {{
        b.style.background = '#334155';
        b.style.color = '#cbd5e1';
      }});
      vL.style.display = 'none';
      vC.style.display = 'none';
      vP.style.display = 'none';

      if (tab === 'lettre') {{
        bL.style.background = '#2563eb';
        bL.style.color = '#fff';
        vL.style.display = 'flex';
        dPdf.href = currentDossier.pdfL;
        dPdf.innerText = '⬇️ Ouvrir PDF Lettre';
        dPdf.style.background = '#059669';
        document.getElementById('imgLettre').src = currentDossier.pngL;
        document.getElementById('frameLettre').src = currentDossier.htmlL;
      }} else if (tab === 'cv') {{
        bC.style.background = '#2563eb';
        bC.style.color = '#fff';
        vC.style.display = 'flex';
        dPdf.href = currentDossier.pdfC;
        dPdf.innerText = '⬇️ Ouvrir PDF CV';
        dPdf.style.background = '#059669';
        document.getElementById('imgCv').src = currentDossier.pngC;
        document.getElementById('frameCv').src = currentDossier.htmlC;
      }} else if (tab === 'preuve') {{
        bP.style.background = '#059669';
        bP.style.color = '#fff';
        vP.style.display = 'flex';
        const hasP = currentDossier.proofUrl && currentDossier.proofUrl.trim() !== '';
        const imgP = document.getElementById('imgPreuve');
        const banP = document.getElementById('preuveBanner');
        const noP = document.getElementById('noPreuveMsg');
        if (hasP) {{
          imgP.src = currentDossier.proofUrl;
          imgP.style.display = 'block';
          banP.style.display = 'flex';
          noP.style.display = 'none';
          dPdf.href = currentDossier.proofUrl;
          dPdf.innerText = '🔍 Plein Écran Preuve (HD)';
          dPdf.style.background = '#059669';
        }} else {{
          imgP.style.display = 'none';
          banP.style.display = 'none';
          noP.style.display = 'block';
          dPdf.href = '#';
          dPdf.innerText = '📸 Aucune preuve';
          dPdf.style.background = '#475569';
        }}
      }}
    }}

    function handleImageError(imgEl, type) {{
      imgEl.style.display = 'none';
      if (type === 'lettre') {{
        document.getElementById('frameLettre').style.display = 'block';
      }} else if (type === 'cv') {{
        document.getElementById('frameCv').style.display = 'block';
      }}
    }}

    function normalizeSearch(str) {{
      return (str || '')
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\\s]/g, ' ')
        .replace(/\\s+/g, ' ')
        .trim();
    }}

    function setStatusFilter(val) {{
      currentStatusFilter = val;
      document.querySelectorAll('[data-filter-type="status"]').forEach(el => {{
        el.classList.toggle('active', el.getAttribute('data-filter-val') === val);
      }});
      applyFilters();
    }}

    function setSectorFilter(val) {{
      currentSectorFilter = val;
      document.querySelectorAll('[data-filter-type="sector"]').forEach(el => {{
        el.classList.toggle('active', el.getAttribute('data-filter-val') === val);
      }});
      applyFilters();
    }}

    function clearSearch() {{
      const inp = document.getElementById('dashboardSearch');
      if (inp) {{
        inp.value = '';
        inp.focus();
      }}
      applyFilters();
    }}

    function resetAllFilters() {{
      const inp = document.getElementById('dashboardSearch');
      if (inp) inp.value = '';
      currentStatusFilter = 'all';
      currentSectorFilter = 'all';
      document.querySelectorAll('[data-filter-type="status"]').forEach(el => {{
        el.classList.toggle('active', el.getAttribute('data-filter-val') === 'all');
      }});
      document.querySelectorAll('[data-filter-type="sector"]').forEach(el => {{
        el.classList.toggle('active', el.getAttribute('data-filter-val') === 'all');
      }});
      applyFilters();
    }}

    function applyFilters() {{
      const rawQ = document.getElementById('dashboardSearch') ? document.getElementById('dashboardSearch').value : '';
      const q = normalizeSearch(rawQ);
      const words = q.split(' ').filter(w => w.length > 0);

      const clearBtn = document.getElementById('btnClearSearch');
      if (clearBtn) clearBtn.style.display = rawQ.trim().length > 0 ? 'inline-flex' : 'none';

      let totalVisible = 0;
      const monthCards = document.querySelectorAll('.month-card');

      monthCards.forEach(card => {{
        const rows = card.querySelectorAll('.job-row');
        let monthVisible = 0;

        rows.forEach(row => {{
          const rowStatus = row.getAttribute('data-status');
          const rowSectors = row.getAttribute('data-sectors') || '';
          const hasProof = row.getAttribute('data-has-proof') === '1';
          const searchText = row.getAttribute('data-search') || '';

          let matchStatus = false;
          if (currentStatusFilter === 'all') matchStatus = true;
          else if (currentStatusFilter === 'confirmed') matchStatus = (rowStatus === 'confirmed');
          else if (currentStatusFilter === 'proof_only') matchStatus = hasProof;
          else if (currentStatusFilter === 'portal') matchStatus = (rowStatus === 'portal');
          else if (currentStatusFilter === 'ready') matchStatus = (rowStatus === 'ready');

          let matchSector = false;
          if (currentSectorFilter === 'all') matchSector = true;
          else if (rowSectors.indexOf(currentSectorFilter) !== -1) matchSector = true;

          let matchSearch = true;
          if (words.length > 0) {{
            for (let i = 0; i < words.length; i++) {{
              if (searchText.indexOf(words[i]) === -1) {{
                matchSearch = false;
                break;
              }}
            }}
          }}

          if (matchStatus && matchSector && matchSearch) {{
            row.style.display = '';
            monthVisible++;
            totalVisible++;
          }} else {{
            row.style.display = 'none';
          }}
        }});

        const badge = card.querySelector('.badge-count');
        const totalInMonth = rows.length;
        if (monthVisible === 0) {{
          card.style.display = 'none';
        }} else {{
          card.style.display = 'block';
          if (badge) {{
            if (monthVisible === totalInMonth) {{
              badge.innerText = totalInMonth;
            }} else {{
              badge.innerText = monthVisible + ' / ' + totalInMonth;
            }}
          }}
          if (words.length > 0 || currentStatusFilter !== 'all' || currentSectorFilter !== 'all') {{
            const content = card.querySelector('.month-content');
            const icon = card.querySelector('.toggle-icon');
            if (content) content.style.display = 'block';
            if (icon) icon.innerText = '▼';
          }}
        }}
      }});

      const resBadge = document.getElementById('resultsCount');
      if (resBadge) {{
        if (words.length > 0 || currentStatusFilter !== 'all' || currentSectorFilter !== 'all') {{
          resBadge.innerText = totalVisible + ' dossier' + (totalVisible > 1 ? 's' : '') + ' filtré' + (totalVisible > 1 ? 's' : '');
          resBadge.style.color = '#38bdf8';
        }} else {{
          resBadge.innerText = totalVisible + ' dossiers';
          resBadge.style.color = '#94a3b8';
        }}
      }}

      const noRes = document.getElementById('noResultsMsg');
      if (noRes) {{
        noRes.style.display = (totalVisible === 0) ? 'block' : 'none';
      }}
    }}

    document.addEventListener('keydown', function(e) {{
      const modal = document.getElementById('viewerModal');
      if (modal && modal.style.display === 'flex') {{
        if (e.key === 'Escape') {{
          closeViewerModal();
        }} else if (e.key === '1') {{
          switchDocTab('lettre');
        }} else if (e.key === '2') {{
          switchDocTab('cv');
        }} else if (e.key === '3') {{
          switchDocTab('preuve');
        }}
      }} else if (e.key === 'Escape') {{
        clearSearch();
      }}
    }});
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
            clean_d, month_key, month_label = parse_date_str(a.get("date"))
            a["_clean_date"] = clean_d
            apps_by_month[(month_key, month_label)].append(a)
            
        sorted_months = sorted(apps_by_month.keys(), key=lambda x: x[0], reverse=True)
        
        # Compteurs statistiques dynamiques
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")
        week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        count_today = sum(1 for a in apps if a.get("_clean_date") == today_str)
        count_week = sum(1 for a in apps if a.get("_clean_date", "") >= week_ago_str and a.get("_clean_date", "") <= today_str)
        count_month = sum(1 for a in apps if a.get("_clean_date", "").startswith(current_month_str))
        count_total = len(apps)
        
        count_proofs = sum(1 for a in apps if a.get("folder_rel") and os.path.exists(os.path.join(self.base_dir, a["folder_rel"], "preuve_soumission_officielle.png")))
        
        md_content = f"# 📋 TABLEAU DE BORD DES CANDIDATURES — RICHARD BUSSON\n\n"
        md_content += f"> ### 📊 Compteurs d'Envoi et Suivi d'Activité\n"
        md_content += f"> | 📅 Aujourd'hui | 📆 Cette Semaine | 🗓️ Ce Mois-ci | 📸 Preuves Certifiées | 🏆 Total Traitées |\n"
        md_content += f"> | :---: | :---: | :---: | :---: | :---: |\n"
        md_content += f"> | **{count_today}** | **{count_week}** | **{count_month}** | **{count_proofs}** | **{count_total}** |\n"
        md_content += f">\n"
        md_content += f"> *Dernière mise à jour et synchronisation : {now.strftime('%d/%m/%Y %H:%M')}*\n\n"
        
        for month_key, month_label in sorted_months:
            month_apps = apps_by_month[(month_key, month_label)]
            md_content += f"## 🗓️ {month_label} ({len(month_apps)} candidatures)\n\n"
            md_content += "| Date | Entreprise | Contact / Destinataire | Localisation | Téléphone | E-mail | Poste & Annonce Source | Statut Envoi | Dossier PDF |\n"
            md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            
            for a in month_apps:
                d = a.get("_clean_date") or a.get("date", "")
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
                if isinstance(rec_delivery, dict):
                    rec_mail = a.get("contact_email") or rec_delivery.get("recruiter_email")
                    is_sent = rec_delivery.get("sent")
                    is_portal = rec_delivery.get("mode") == "WEB_PORTAL_REQUIRED"
                elif isinstance(rec_delivery, str):
                    rec_mail = a.get("contact_email")
                    is_sent = "SUBMITTED" in rec_delivery or "CONFIRMED" in rec_delivery
                    is_portal = "WEB_PORTAL" in rec_delivery
                else:
                    rec_mail = a.get("contact_email")
                    is_sent = False
                    is_portal = False

                if not rec_mail:
                    m_em = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
                    for em in m_em:
                        if not em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and 'example.com' not in em.lower():
                            rec_mail = em.strip()
                            break
                email_md = f"[{rec_mail}](mailto:{rec_mail})" if rec_mail else "🌐 Portail Web"
                
                if is_sent:
                    send_status = f"🟢 Transmis & Validé ({rec_mail or 'Web ATS'})"
                elif is_portal:
                    send_status = "🌐 Portail Web"
                else:
                    send_status = "📁 Prêt"
                    
                tit_link = f"[{tit}]({url})" if url else tit
                pdf_letter_link = f"[Lettre]({safe_url_path(folder_rel)}/Lettre_Motivation_Richard_BUSSON.pdf)" if folder_rel else "-"
                pdf_cv_link = f"[CV]({safe_url_path(folder_rel)}/CV_Richard_BUSSON.pdf)" if folder_rel else "-"
                
                # Preuve dans Markdown
                proof_path = os.path.join(self.base_dir, folder_rel, "preuve_soumission_officielle.png")
                dossier_col = f"{pdf_letter_link} / {pdf_cv_link}"
                if os.path.exists(proof_path):
                    dossier_col += f" / [📸 Preuve]({safe_url_path(folder_rel)}/preuve_soumission_officielle.png)"
                
                md_content += f"| {d} | **{comp}** | {contact_name} ({contact_title}) | {loc_str} | {phone} | {email_md} | {tit_link} ({salary} - {score}%) | {send_status} | {dossier_col} |\n"
                
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
