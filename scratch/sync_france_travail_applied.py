import sys
import os
import re
import json
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO_DIR = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\richa\JobHunter\browser_profile"

env_path = os.path.join(REPO_DIR, ".env")
username = ""
password = ""
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("FRANCE_TRAVAIL_USER="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("FRANCE_TRAVAIL_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")

print("=" * 75)
print("  [🔄 SYNCHRONISATION ESPACE PERSONNEL FRANCE TRAVAIL - ÉTAPE 0]")
print("=" * 75)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        executable_path=CHROME_PATH,
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.pages[0] if context.pages else context.new_page()
    
    cand_url = "https://candidat.francetravail.fr/candidature/mescandidatures"
    print(f"[*] Accès à l'espace candidatures : {cand_url}...")
    page.goto(cand_url, wait_until='networkidle')
    time.sleep(3)
    
    # Authentification si besoin
    if "authentification" in page.url or page.locator("#identifiant").is_visible():
        print("[*] Reconnexion requise, saisie des identifiants...")
        page.locator("#identifiant").fill(username)
        page.locator("#password").fill(password)
        page.locator("#submit").click()
        page.wait_for_load_state("networkidle")
        time.sleep(4)
        
    print(f"[✓] Connecté sur : {page.url} - {page.title()}")
    
    # Déroulement complet de la liste ("Afficher plus de candidatures")
    click_count = 0
    while True:
        more_btn = page.locator("p.list-candidatures-more button, button:has-text('Afficher plus de candidatures')").first
        if more_btn.is_visible():
            click_count += 1
            print(f"  [+] Chargement de la page suivante ({click_count})...")
            more_btn.click()
            time.sleep(2)
        else:
            print("[✓] Toutes les candidatures ont été chargées avec succès !")
            break
            
    # Extraction de toutes les cartes de candidatures
    candidature_cards = page.locator("li.candidature").all()
    print(f"\n[✓] Total candidatures trouvées dans l'espace personnel : {len(candidature_cards)}")
    
    extracted_candidatures = []
    
    for c in candidature_cards:
        try:
            # Titre & ID
            title_a = c.locator("h3.media-heading a").first
            title = title_a.inner_text().strip() if title_a.is_visible() else "Poste inconnu"
            cand_ref = title_a.get_attribute("id") or ""
            href = title_a.get_attribute("href") or ""
            
            # Entreprise & Localisation
            sub = c.locator("p.subtext").first
            company_el = sub.locator(".emphasis").first
            company = company_el.inner_text().strip() if company_el.is_visible() else "Entreprise confidentielle"
            sub_full = sub.inner_text().strip() if sub.is_visible() else ""
            
            # Localisation
            city = ""
            m_city = re.search(r'([0-9]{2}\s*-\s*[^,\n\r]+)', sub_full)
            if m_city:
                city = m_city.group(1).strip()
                
            # Date d'envoi
            desc = c.locator("p.description").first
            desc_text = desc.inner_text().strip() if desc.is_visible() else ""
            
            # Statut
            state = c.locator("p.state .state-text").first
            state_text = state.inner_text().strip() if state.is_visible() else "Statut inconnu"
            
            # Contrat
            contrat = c.locator(".contrat").first
            contrat_text = contrat.inner_text().strip().replace('\n', ' ') if contrat.is_visible() else ""
            
            item = {
                "candidature_id": cand_ref,
                "title": title,
                "company": company,
                "city": city,
                "raw_subtext": sub_full,
                "details_link": f"https://candidat.francetravail.fr/candidature/{href}" if href else "",
                "send_date": desc_text,
                "contract": contrat_text,
                "status": state_text
            }
            extracted_candidatures.append(item)
            
        except Exception as e:
            print(f"  [!] Erreur extraction carte : {e}")
            
    print("\n--- Échantillon des 5 dernières candidatures détectées ---")
    for it in extracted_candidatures[:5]:
        print(f"  • [{it['send_date']}] {it['company']} - {it['title']} ({it['status']})")
        
    # Sauvegarde dans data/
    out_dir = os.path.join(REPO_DIR, "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "france_travail_espace_candidatures.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(extracted_candidatures, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Données enregistrées dans : {out_file}")
    
    # Capture d'écran finale de preuve
    page.screenshot(path=os.path.join(REPO_DIR, "scratch", "preuve_espace_candidatures_complet.png"))
    
    # Synchronisation avec tracker.json
    tracker_path = os.path.join(REPO_DIR, "tracker.json")
    with open(tracker_path, "r", encoding="utf-8") as f:
        tracker = json.load(f)
        
    existing_companies_titles = {
        f"{re.sub(r'[^\w\s]', ' ', x.get('company', '').lower()).strip()}|{re.sub(r'[^\w\s]', ' ', x.get('title', '').lower()).strip()}"
        for x in tracker
    }
    
    added_count = 0
    for cand in extracted_candidatures:
        c_norm = re.sub(r'[^\w\s]', ' ', cand['company'].lower()).strip()
        t_norm = re.sub(r'[^\w\s]', ' ', cand['title'].lower()).strip()
        pair = f"{c_norm}|{t_norm}"
        
        if pair not in existing_companies_titles:
            # Add to tracker so it is permanently guarded
            tracker_item = {
                "id": f"FT-ESPACE-{cand['candidature_id']}",
                "date": cand['send_date'],
                "company": cand['company'],
                "title": cand['title'],
                "city": cand['city'],
                "salary": "Non précisé (Espace France Travail)",
                "score": 85,
                "url": cand['details_link'],
                "status": cand['status'],
                "source": "Espace Candidat France Travail (Historique officiel)"
            }
            tracker.append(tracker_item)
            existing_companies_titles.add(pair)
            added_count += 1
            
    if added_count > 0:
        with open(tracker_path, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2, ensure_ascii=False)
        print(f"[✓] {added_count} candidatures historiques synchronisées et verrouillées dans tracker.json !")
    else:
        print("[✓] Toutes les candidatures de l'espace personnel étaient déjà répertoriées dans tracker.json.")
        
    context.close()
