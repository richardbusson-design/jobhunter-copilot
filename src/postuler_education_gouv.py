# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from playwright.async_api import async_playwright

async def postuler():
    print("=== POSTULATION AUTOMATISÉE SUR RECRUTEMENT.EDUCATION.GOUV.FR ===")
    offer_url = "https://recrutement.education.gouv.fr/recrutement/offreemploi/a1DIV00000D7OXa2AN/enseignante-en-%C3%A9conomie-gestion-fili%C3%A8re-stmg"
    dossier_dir = r"C:\Users\richa\Gemini\Pipeline_JobHunter\candidatures\2026-09-14_Academie_de_Versailles_Enseignant_en_economie_gestion_filiere_stmg"
    cv_pdf = os.path.join(dossier_dir, "CV_Richard_BUSSON.pdf")
    lettre_pdf = os.path.join(dossier_dir, "Lettre_Motivation_Richard_BUSSON.pdf")

    user_data_dir = r"C:\Users\richa\JobHunter\browser_profile"
    os.makedirs(user_data_dir, exist_ok=True)

    async with async_playwright() as p:
        print("[+] Lancement du navigateur avec le profil persistant...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"[+] Navigation vers l'offre : {offer_url}")
        await page.goto(offer_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(5)

        postuler_btn = page.locator("button:has-text('Je postule'), a:has-text('Je postule')").first
        if await postuler_btn.count() > 0:
            print("[+] Bouton 'Je postule' détecté, ouverture du parcours de candidature...")
            await postuler_btn.click()
            await asyncio.sleep(5)
        else:
            conn_btn = page.locator("button:has-text('Je me connecte pour postuler'), a:has-text('Je me connecte pour postuler')").first
            if await conn_btn.count() > 0:
                print("[!] Connexion requise sur le portail dans la fenêtre Chrome ouverte...")
                await conn_btn.click()
                await asyncio.sleep(8)

        # Remplissage automatique des champs de saisie
        print("[+] Remplissage automatique des coordonnées officielles...")
        inputs = await page.locator("input").all()
        for inp in inputs:
            name = (await inp.get_attribute("name") or "").lower()
            ph = (await inp.get_attribute("placeholder") or "").lower()
            type_attr = (await inp.get_attribute("type") or "").lower()
            
            if "prenom" in name or "first" in name or "prénom" in ph:
                await inp.fill("Richard")
            elif "nom" in name or "last" in name:
                await inp.fill("BUSSON")
            elif type_attr == "email" or "mail" in name:
                await inp.fill("richard.busson@kairos-paye.fr")
            elif type_attr == "tel" or "phone" in name or "mobile" in name:
                await inp.fill("07 61 96 15 46")
            elif "ville" in name or "city" in name:
                await inp.fill("Creil")
            elif "cp" in name or "postal" in name or "zip" in name:
                await inp.fill("60100")

        # Téléversement des fichiers
        file_inputs = await page.locator("input[type='file']").all()
        if len(file_inputs) >= 2:
            print("[+] Téléversement CV et Lettre de motivation...")
            await file_inputs[0].set_input_files(cv_pdf)
            await file_inputs[1].set_input_files(lettre_pdf)
        elif len(file_inputs) == 1:
            print("[+] Téléversement du CV...")
            await file_inputs[0].set_input_files(cv_pdf)

        proof_path = os.path.join(dossier_dir, "preuve_candidature_ecran.png")
        await page.screenshot(path=proof_path, full_page=True)
        print(f"[✓] Preuve visuelle enregistrée : {proof_path}")

        print("[*] Écran de contrôle prêt pour validation.")
        await asyncio.sleep(15)
        await context.close()

if __name__ == "__main__":
    asyncio.run(postuler())
