# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil

def get_browser_path():
    """Détecte automatiquement le navigateur headless disponible (Windows Edge ou Linux Chromium)."""
    # 1. Sous Windows (Edge ou Chrome)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    ]
    for p in edge_paths:
        if os.path.exists(p):
            return p
            
    # 2. Sous Linux / GitHub Actions (Chromium ou Chrome)
    linux_bins = ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]
    for b in linux_bins:
        path = shutil.which(b)
        if path:
            return path
            
    return "chromium"

def compile_html_to_pdf(html_path: str, pdf_path: str) -> bool:
    """Compile un fichier HTML vers un PDF A4 strict via Chromium / Edge headless."""
    abs_html = os.path.abspath(html_path)
    abs_pdf = os.path.abspath(pdf_path)
    browser = get_browser_path()
    
    file_url = f"file:///{abs_html.replace(os.sep, '/')}"
    
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--print-to-pdf={abs_pdf}",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        file_url
    ]
    
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
        if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
            # Génération automatique et simultanée de l'image visuelle haute fidélité (PNG)
            png_path = abs_pdf.replace(".pdf", ".png")
            render_html_to_png(html_path, png_path)
            return True
        return False
    except Exception as e:
        print(f"[!] Erreur de compilation PDF : {e}")
        return False

def render_html_to_png(html_path: str, png_path: str) -> bool:
    """Génère une capture visuelle PNG haute résolution (794x1123) pour contrôle visuel immédiat."""
    abs_html = os.path.abspath(html_path)
    abs_png = os.path.abspath(png_path)
    browser = get_browser_path()
    file_url = f"file:///{abs_html.replace(os.sep, '/')}"
    
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=794,1123",
        f"--screenshot={abs_png}",
        file_url
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return os.path.exists(abs_png) and os.path.getsize(abs_png) > 0
    except Exception as e:
        print(f"[!] Erreur de génération PNG : {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        compile_html_to_pdf(sys.argv[1], sys.argv[2])
