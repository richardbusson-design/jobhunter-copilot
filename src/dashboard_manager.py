import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class DashboardManager:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.tracker_file = os.path.join(base_dir, "tracker.json")
        self.dashboard_file = os.path.join(base_dir, "dashboard.md")
        self.applications = self.load_tracker()

    def load_tracker(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_tracker(self):
        with open(self.tracker_file, "w", encoding="utf-8") as f:
            json.dump(self.applications, f, indent=2, ensure_ascii=False)
        self.generate_dashboard_md()

    def add_application(self, app_data: Dict[str, Any]):
        # Éviter les doublons
        for a in self.applications:
            if a.get("company") == app_data.get("company") and a.get("title") == app_data.get("title"):
                return
        
        now = datetime.now()
        app_data["date"] = now.strftime("%Y-%m-%d")
        app_data["follow_up_date"] = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        app_data["status"] = "Dossier PDF Prêt"
        self.applications.insert(0, app_data)
        self.save_tracker()

    def generate_dashboard_md(self):
        md = "# 📊 Tableau de Bord des Candidatures - Richard BUSSON\n\n"
        md += f"*Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n\n"
        md += "| Date | Entreprise / Organisme | Poste | Ville | Score Match | Statut | Relance (J+7) | Dossier PDF |\n"
        md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        
        if not self.applications:
            md += "| - | *Aucune candidature générée pour le moment* | - | - | - | - | - | - |\n"
        else:
            for app in self.applications:
                date = app.get("date", "-")
                company = app.get("company", "-")
                title = app.get("title", "-")
                city = app.get("city", "-")
                score = f"**{app.get('score', 85)}%**"
                status = app.get("status", "Prêt")
                relance = app.get("follow_up_date", "-")
                folder = app.get("folder_rel", "")
                link = f"[📂 Ouvrir Dossier]({folder})" if folder else "-"
                
                md += f"| {date} | **{company}** | {title} | {city} | {score} | {status} | {relance} | {link} |\n"
                
        md += "\n---\n\n### 📌 Légende des statuts :\n"
        md += "- Dossier PDF Prêt : CV et Lettre de motivation générés au format A4 conforme et prêts à l'envoi.\n"
        md += "- Postulé : Candidature envoyée.\n"
        md += "- Relance à faire : 7 jours écoulés sans retour.\n"
        
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            f.write(md)

if __name__ == "__main__":
    dm = DashboardManager()
    dm.generate_dashboard_md()
    print("DashboardManager initialisé avec succès.")
