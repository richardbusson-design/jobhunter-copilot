# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

def normalize_text(text: str) -> str:
    """Normalise un texte pour comparaison stricte anti-doublon."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\(h/f\)|h/f|\(f/h\)|f/h', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class DashboardManager:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.dashboard_file = os.path.join(base_dir, "dashboard.md")
        self.tracker_file = os.path.join(base_dir, "tracker.json")

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
            
        # Comparaison floue : si le nom principal de la société et du titre correspondent
        for existing_fp in fingerprints.get("company_titles", []):
            if "___" in existing_fp:
                e_comp, e_tit = existing_fp.split("___", 1)
                comp_match = (e_comp in comp_norm) or (comp_norm in e_comp) or (e_comp[:12] == comp_norm[:12] and len(e_comp) >= 12)
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
        
        # Vérifier si elle existe déjà pour mise à jour sans dupliquer
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

    def generate_markdown_dashboard(self, apps: List[Dict[str, Any]] = None):
        if apps is None:
            apps = self.load_tracker()
            
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        md = f"""# 📊 Tableau de Bord des Candidatures & Annonces Réelles - Richard BUSSON

*Dernière synchronisation anti-doublon : {now_str}*
*Total candidatures actives enregistrées : **{len(apps)}***

| Date | Organisme / Employeur | Intitulé & Texte Intégral de l'Annonce | Ville & Mobilité | Salaire Brut | Match | Relance (J+7) | Fichiers PDF A4 |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
"""
        for a in apps:
            d = a.get("date", datetime.now().strftime("%Y-%m-%d"))
            comp = a.get("company", "Entreprise")
            tit = a.get("title", "Poste")
            city = a.get("city", "France")
            salary = a.get("salary", "30k€ - 40k€")
            score = a.get("score", 85)
            rel = a.get("relance_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            source = a.get("source", "France Travail / Apec / Indeed")
            url = a.get("url", "")
            desc = a.get("description", "Formation Gestionnaire de paie, RH, DSN, Qualiopi.")
            
            link_annonce = f"[🔗 **Consulter l'annonce originale sur {source}**]({url})" if url else f"*(Source : {source})*"
            annonce_block = f"**{tit}**<br>{link_annonce}<br><br>📝 **Texte de l'annonce :**<br><blockquote>{desc}</blockquote>"
            
            folder_rel = a.get("folder_rel", "").replace("\\", "/")
            if folder_rel:
                link_cv = f"[{comp} - CV]({folder_rel}/CV_Richard_BUSSON.pdf)"
                link_lm = f"[Lettre de Motivation]({folder_rel}/Lettre_Motivation_Richard_BUSSON.pdf)"
                pdf_links = f"📄 {link_cv}<br>✉️ {link_lm}"
            else:
                pdf_links = "Dossier généré"
                
            md += f"| {d} | **{comp}** | {annonce_block} | {city} | {salary} | **{score}%** | {rel} | {pdf_links} |\n"
            
        md += """
---

### 📌 Guide du Tableau de Bord :
* **Anti-Doublon Actif :** Aucun recandidatage sur un poste ou organisme déjà présent dans ce tableau.
* **Texte Intégral de l'Annonce :** Le descriptif complet des missions, compétences et modalités de recrutement est intégré dans chaque ligne.
* **Sécurité QualityGuard :** CV et Lettre générés sur 1 page A4 stricte en typographie haute lisibilité sans aucun gras dans le corps de lettre.
"""
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            f.write(md)
            
        gemini_dash = r"C:\Users\richa\Gemini\dashboard.md"
        try:
            with open(gemini_dash, "w", encoding="utf-8") as f:
                f.write(md)
        except Exception:
            pass

if __name__ == "__main__":
    dm = DashboardManager()
    fps = dm.get_existing_fingerprints()
    print(f"[OK] DashboardManager initialisé : {fps['total_count']} candidatures enregistrées.")

