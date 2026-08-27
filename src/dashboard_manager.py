# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DashboardManager:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.dashboard_file = os.path.join(base_dir, "dashboard.md")
        self.tracker_file = os.path.join(base_dir, "tracker.json")

    def load_tracker(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("applications", [])
            except Exception:
                pass
        return []

    def save_tracker(self, apps: List[Dict[str, Any]]):
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump({"applications": apps, "last_updated": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde tracker : {e}")

    def add_application(self, app_entry: Dict[str, Any]):
        apps = self.load_tracker()
        
        exists = False
        for a in apps:
            if a.get("company") == app_entry.get("company") and a.get("title") == app_entry.get("title"):
                a.update(app_entry)
                exists = True
                break
                
        if not exists:
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

*Dernière mise à jour automatique : {now_str}*

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
            stat = a.get("status", "Dossier PDF Prêt")
            rel = a.get("relance_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            source = a.get("source", "France Travail / Apec / Indeed")
            url = a.get("url", "")
            desc = a.get("description", "Formation Gestionnaire de paie, RH, DSN, Qualiopi.")
            
            link_annonce = f"[🔗 **Consulter l'annonce originale sur {source}**]({url})" if url else f"*(Source : {source})*"
            
            # Bloc texte complet de l'annonce
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
* **Texte Intégral de l'Annonce :** Le descriptif complet des missions, compétences et modalités de recrutement est intégré dans chaque ligne.
* **Score Match :** Évaluation automatique de l'adéquation avec votre profil (Paie, RH, Qualiopi, Afpa, 580 collaborateurs, Master 2).
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
    dm.generate_markdown_dashboard()
    print("dashboard.md régénéré avec le texte intégral des annonces.")
