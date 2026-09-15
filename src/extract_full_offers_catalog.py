# -*- coding: utf-8 -*-
"""
Extraction automatisée du catalogue complet des offres Éco-Gestion & STMG
depuis recrutement.education.gouv.fr
"""

import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

BASE_DIR = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
SESSION_FILE = r"C:\Users\richa\JobHunter\browser_profile\education_storage_state.json"
CATALOG_FILE = os.path.join(BASE_DIR, "data", "catalogue_offres_stmg_national.json")
QUALIFIED_JSON = os.path.join(BASE_DIR, "data", "offres_stmg_nationales_qualifiees.json")

async def extract_catalog():
    os.makedirs(os.path.dirname(CATALOG_FILE), exist_ok=True)
    
    if not os.path.exists(QUALIFIED_JSON):
        print(f"[!] Fichier {QUALIFIED_JSON} introuvable.")
        return

    with open(QUALIFIED_JSON, "r", encoding="utf-8") as f:
        target_offers = json.load(f)

    print(f"[*] Chargement de {len(target_offers)} annonces cibles à enrichir...")

    catalog = []
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                catalog = json.load(f)
            print(f"[*] {len(catalog)} offres déjà extraites dans le catalogue existant.")
        except Exception:
            catalog = []

    already_done_titles = {c.get("title") for c in catalog if c.get("url")}

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()

        for idx, item in enumerate(target_offers, 1):
            title = item["title"]
            if title in already_done_titles:
                print(f"[{idx}/{len(target_offers)}] Déjà extrait : {title[:50]}")
                continue

            # Exclure Versailles qui est déjà traitée
            if "Versailles" in title or "VERSAILLES" in item.get("card_text", ""):
                if "filière stmg" in title.lower():
                    print(f"[{idx}/{len(target_offers)}] Ignorer offre Versailles déjà postulée : {title[:50]}")
                    continue

            print(f"\n[{idx}/{len(target_offers)}] Recherche directe : {title[:60]}...")
            try:
                await page.goto("https://recrutement.education.gouv.fr/recrutement/offres", wait_until="domcontentloaded", timeout=45000)
                await asyncio.sleep(3)

                search_input = page.locator("input[name='search']").first
                await search_input.fill("")
                clean_kw = re.sub(r'\(.*?\)', '', title).strip()
                clean_kw = clean_kw[:35].strip()
                await search_input.type(clean_kw, delay=30)
                await page.locator("button:has-text('Rechercher')").first.click()
                await asyncio.sleep(5)

                cards = page.locator(".fr-card")
                n_cards = await cards.count()
                matched_card = None

                for ci in range(min(n_cards, 10)):
                    c = cards.nth(ci)
                    ctxt = await c.inner_text()
                    if any(word.lower() in ctxt.lower() for word in clean_kw.split() if len(word) > 4):
                        matched_card = c
                        break

                if matched_card:
                    link = matched_card.locator("a").first
                    await link.click()
                    await asyncio.sleep(5)

                    offer_url = page.url
                    content = await page.eval_on_selector("main", "el => el ? el.innerText : ''")
                    if not content:
                        content = await page.eval_on_selector("body", "el => el.innerText")

                    ref_match = re.search(r'(MENJ-[A-Z0-9-]+)', content)
                    ref = ref_match.group(1) if ref_match else ""

                    acad_match = re.search(r'Académie de\s+([A-ZÉÈÊÀÂÔÛÎÇ\-]+)', content, re.I)
                    acad = acad_match.group(0) if acad_match else ""

                    loc_match = re.search(r'Lieu de travail\s*:\s*([^\n]+)', content)
                    loc = loc_match.group(1).strip() if loc_match else ""

                    entry = {
                        "title": title,
                        "url": offer_url,
                        "reference": ref,
                        "academie": acad,
                        "location": loc,
                        "raw_card": item.get("card_text", ""),
                        "full_content": content
                    }
                    catalog.append(entry)
                    already_done_titles.add(title)
                    print(f"    [OK] URL: {offer_url} | Ref: {ref} | {acad}")

                    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
                        json.dump(catalog, f, indent=2, ensure_ascii=False)
                else:
                    print(f"    [!] Carte non trouvée pour : {clean_kw}")

            except Exception as e:
                print(f"    [ERREUR] {e}")

        await browser.close()

    print(f"\n[+] Catalogue finalisé avec {len(catalog)} offres détaillées : {CATALOG_FILE}")

if __name__ == "__main__":
    asyncio.run(extract_catalog())
