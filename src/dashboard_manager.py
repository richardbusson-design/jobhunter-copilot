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
        
        # Vérifier si l'application existe déjà
        exists = False
        for a in apps:
            if a.get("company") == app_entry.get("company") and a.get("title") == app_entry.get("title"):
                # Mettre à jour les champs si nécessaire
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
        
        md = f"""# 📊 Tableau de Bord des Candidatures - Richard BUSSON

*Dernière mise à jour automatique : {now_str}*

| Date | Organisme / Entreprise | Intitulé du Poste & Détails Annonce | Ville & Zone | Rémunération | Score Match | Statut | Relance (J+7) | Fichiers PDF A4 |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
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
            
            # Bloc Annonce avec lien cliquable
            link_annonce = f"[🔗 Voir l'annonce ({source})]({url})" if url else f"*(Source : {source})*"
            poste_details = f"**{tit}**<br>{link_annonce}<br><small style='color:#666;'>{desc[:120]}...</small>" if len(desc) > 120 else f"**{tit}**<br>{link_annonce}<br><small style='color:#666;'>{desc}</small>"
            
            # Liens web propres avec slashs normaux pour GitHub
            folder_rel = a.get("folder_rel", "").replace("\\", "/")
            if folder_rel:
                link_cv = f"[{comp} - CV]({folder_rel}/CV_Richard_BUSSON.pdf)"
                link_lm = f"[Lettre de Motivation]({folder_rel}/Lettre_Motivation_Richard_BUSSON.pdf)"
                pdf_links = f"📄 {link_cv}<br>✉️ {link_lm}"
            else:
                pdf_links = "Dossier généré"
                
            md += f"| {d} | **{comp}** | {poste_details} | {city} | {salary} | **{score}%** | `{stat}` | {rel} | {pdf_links} |\n"
            
        md += """
---

### 📌 Guide du Tableau de Bord :
* **Détails Annonce :** Chaque ligne intègre l'intitulé exact, le lien direct vers l'annonce d'origine et le résumé des exigences.
* **Score Match :** Évaluation automatique de l'adéquation avec vos compétences (Paie, RH, Qualiopi, Afpa, 580 pers., Master 2).
* **Statut `Dossier PDF Prêt` :** CV et Lettre de motivation générés et 100% validés par le **QualityGuard** (strictement 1 page A4, zéro gras dans le corps).
* **Relance (J+7) :** Date conseillée pour relancer le recruteur si aucun retour n'a été reçu.
"""
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            f.write(md)
            
        # Synchroniser vers Gemini root
        gemini_dash = r"C:\Users\richa\Gemini\dashboard.md"
        try:
            with open(gemini_dash, "w", encoding="utf-8") as f:
                f.write(md)
        except Exception:
            pass

if __name__ == "__main__":
    dm = DashboardManager()
    dm.generate_markdown_dashboard()
    print("dashboard.md régénéré avec la colonne Annonce et descriptif.")
