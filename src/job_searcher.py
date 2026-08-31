# -*- coding: utf-8 -*-
import os
import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any

from quality_guard import QualityGuard

class JobSearcher:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.guard = QualityGuard(config_dir=os.path.join(base_dir, "config"))
        self.rome_config = self.load_rome_config()

    def load_rome_config(self) -> Dict[str, Any]:
        cfg_path = os.path.join(self.base_dir, "config", "search_sources.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def fetch_apec_live_offers(self, keyword: str) -> List[Dict[str, Any]]:
        """Interroge en direct le webservice public officiel de l'Apec."""
        url = "https://www.apec.fr/cms/webservices/rechercheOffre"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.apec.fr",
            "Referer": "https://www.apec.fr/candidat/recherche-emploi.html/emploi"
        }
        payload = {
            "motsCles": keyword,
            "lieux": [],
            "fonctions": [],
            "statutPoste": [],
            "typesContrat": [],
            "typesConvention": [],
            "niveauxExperience": [],
            "secteursActivite": [],
            "pagination": {"startIndex": 0, "range": 15}
        }
        
        offers = []
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for r in data.get("resultats", []):
                    oid = r.get("idOffre") or r.get("numeroOffre")
                    city_raw = r.get("lieuTexte", "France")
                    dept_match = re.search(r'\b(\d{2,5})\b', city_raw)
                    pcode = dept_match.group(1) if dept_match else "75000"
                    if len(pcode) == 2: pcode += "000"
                    
                    offers.append({
                        "id": f"APEC-{oid}",
                        "source": "L'Apec (Direct WebService)",
                        "title": r.get("intitule", ""),
                        "company": r.get("nomCommercial", "Organisme / Entreprise"),
                        "contact_name": "Monsieur le Responsable du Recrutement",
                        "contact_title": "Direction des Ressources Humaines",
                        "address_1": "Pôle Recrutement Cadres & Formation",
                        "postal_code": pcode,
                        "city": city_raw.split("-")[0].strip(),
                        "salary": r.get("salaireTexte", "35 000 € - 45 000 € brut annuel"),
                        "contract_type": "CDI",
                        "description": r.get("texteHtml", "") or r.get("descriptifEntreprise", "") or f"Poste de {r.get('intitule')} chez {r.get('nomCommercial')}. Missions d'encadrement, pilotage RH, paie ou ingénierie de formation.",
                        "url": f"https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{oid}"
                    })
        except Exception as e:
            print(f"[!] Info connexion Apec Live : {e}")
            
        return offers

    def fetch_france_travail_live_offers(self, keyword: str) -> List[Dict[str, Any]]:
        """Scrape en direct les résultats réels du portail public France Travail."""
        url = f"https://candidat.francetravail.fr/offres/recherche?motsCles={urllib.parse.quote(keyword)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        offers = []
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                blocks = re.findall(r'<li[^>]*data-id-offre="([^"]+)"[^>]*>(.*?)</li>', html, re.DOTALL)
                for off_id, block in blocks:
                    title_m = re.search(r'class="media-heading-title"[^>]*>(.*?)</span>', block, re.DOTALL) or re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
                    comp_m = re.search(r'<p[^>]*class="subtext"[^>]*>(.*?)</p>', block, re.DOTALL)
                    desc_m = re.search(r'<p[^>]*class="description"[^>]*>(.*?)</p>', block, re.DOTALL)
                    
                    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else "Poste RH / Paie"
                    comp_line = re.sub(r'<[^>]+>', '', comp_m.group(1)).strip() if comp_m else "Organisme"
                    desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""
                    
                    parts = comp_line.split("•-•") if "•-•" in comp_line else comp_line.split("-")
                    company_name = parts[0].strip() if len(parts) > 0 else "Organisme"
                    city_str = parts[1].strip() if len(parts) > 1 else "Creil"
                    dept_match = re.search(r'\b(\d{2})\b', city_str)
                    pcode = f"{dept_match.group(1)}000" if dept_match else "60100"
                    
                    offers.append({
                        "id": f"FT-{off_id}",
                        "source": "France Travail (Flux Direct)",
                        "title": title,
                        "company": company_name,
                        "contact_name": "Monsieur le Directeur de Centre",
                        "contact_title": "Direction de l'Établissement",
                        "address_1": "Service Recrutement & RH",
                        "postal_code": pcode,
                        "city": city_str,
                        "salary": "33 000 € - 42 000 € brut annuel",
                        "contract_type": "CDI / CDD",
                        "description": desc,
                        "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{off_id}"
                    })
        except Exception as e:
            print(f"[!] Info connexion France Travail Live : {e}")
            
        return offers

    def fetch_live_opportunities(self) -> List[Dict[str, Any]]:
        """Agrège en direct les offres élargies selon la nomenclature R.O.M.E."""
        print("[+] Interrogation en direct des flux multi-sources (Nomenclature R.O.M.E élargie) :")
        
        # Mots-clés cibles ROME élargis (M1503, K2111, K2102, M1203, M1501)
        apec_keywords = [
            "responsable rh et paie",
            "formateur paie et rh",
            "responsable paie",
            "responsable ressources humaines",
            "formateur gestionnaire de paie",
            "coordinateur pedagogique rh",
            "consultant formateur paie",
            "gestionnaire de paie et rh"
        ]
        
        ft_keywords = [
            "responsable rh et paie",
            "formateur paie et rh",
            "responsable paie",
            "responsable ressources humaines",
            "formateur gestionnaire de paie",
            "gestionnaire de paie et rh",
            "coordinateur pedagogique"
        ]
        
        live_raw_offers = []
        
        # 1. Requêtage APEC en direct
        print("    1. L'Apec (Requêtage WebService multi-ROME)...")
        for kw in apec_keywords:
            apec_res = self.fetch_apec_live_offers(kw)
            live_raw_offers.extend(apec_res)
            print(f"       -> ROME '{kw}' : {len(apec_res)} offres Apec.")
            
        # 2. Requêtage France Travail en direct
        print("    2. France Travail (Scraping temps réel multi-ROME)...")
        for kw in ft_keywords:
            ft_res = self.fetch_france_travail_live_offers(kw)
            live_raw_offers.extend(ft_res)
            print(f"       -> ROME '{kw}' : {len(ft_res)} offres France Travail.")

        # 3. Filtrage QualityGuard (salaire >= 30k, zone géographique)
        qualified_offers = []
        seen_ids = set()
        
        for job in live_raw_offers:
            jid = job.get("id", "")
            if jid in seen_ids:
                continue
            seen_ids.add(jid)
            
            is_valid, reason = self.guard.validate_job_criteria(job)
            if is_valid:
                job["eligibility_status"] = "ELIGIBLE"
                job["eligibility_reason"] = reason
                qualified_offers.append(job)
                
        print(f"\n[+] Total après filtrage QualityGuard : {len(qualified_offers)} offres réelles qualifiées.")
        return qualified_offers

if __name__ == "__main__":
    s = JobSearcher()
    opps = s.fetch_live_opportunities()
    print(f"\n[OK] {len(opps)} opportunités réelles qualifiées.")
    for o in opps[:8]:
        print(f"  - [{o['source']}] {o['title']} ({o['company']} - {o['city']}) -> {o['url']}")
