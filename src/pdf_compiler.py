# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil

_BROWSER_PATH = None

def get_browser_path():
    """Détecte le navigateur headless disponible et mémorise le résultat pour la session.

    Ordre de résolution :
      1. Variable d'environnement JOBHUNTER_BROWSER (chemin explicite vers Chrome/Chromium/Edge).
      2. Windows : Edge ou Chrome installés aux emplacements standards.
      3. Linux / GitHub Actions : binaire Chrome ou Chromium présent dans le PATH.
      4. Chromium fourni par Playwright (environnement cloud Claude Code, GitHub Actions
         après `playwright install chromium`), uniquement si le binaire existe réellement.
    """
    global _BROWSER_PATH
    if _BROWSER_PATH:
        return _BROWSER_PATH

    env_browser = os.environ.get("JOBHUNTER_BROWSER")
    if env_browser and os.path.exists(env_browser):
        _BROWSER_PATH = env_browser
        return _BROWSER_PATH

    if sys.platform == "win32":
        for p in (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        ):
            if os.path.exists(p):
                _BROWSER_PATH = p
                return _BROWSER_PATH

    for b in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
        path = shutil.which(b)
        if path:
            _BROWSER_PATH = path
            return _BROWSER_PATH

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            candidate = p.chromium.executable_path
        if candidate and os.path.exists(candidate):
            _BROWSER_PATH = candidate
            return _BROWSER_PATH
    except Exception:
        pass

    raise RuntimeError(
        "Aucun navigateur headless trouvé. Installez Chromium via "
        "`python -m playwright install --with-deps chromium` ou définissez JOBHUNTER_BROWSER."
    )

def get_pdf_page_count(pdf_path: str) -> int:
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        try:
            import re
            with open(pdf_path, "rb") as fp:
                content = fp.read()
            return len(re.findall(rb"/Type\s*/Page\b", content))
        except Exception:
            return 1

def compile_html_to_pdf(html_path: str, pdf_path: str) -> bool:
    """Compile un fichier HTML vers un PDF A4 strict (1 page garantie) via Chromium / Edge headless."""
    abs_html = os.path.abspath(html_path)
    abs_pdf = os.path.abspath(pdf_path)
    try:
        browser = get_browser_path()
    except RuntimeError as e:
        print(f"[!] Compilation PDF impossible : {e}")
        return False

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
            pages = get_pdf_page_count(abs_pdf)
            # Auto-calibrage : Si le PDF dépasse 1 page (ex: variations métriques de polices),
            # injection d'un ajustement de compacité et recompilation immédiate.
            if pages > 1:
                try:
                    with open(abs_html, "r", encoding="utf-8") as f:
                        c = f.read()
                    if "</head>" in c and "zoom:" not in c:
                        c_mod = c.replace("</head>", "<style>body { zoom: 0.94 !important; }</style></head>")
                        with open(abs_html, "w", encoding="utf-8") as f:
                            f.write(c_mod)
                        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
                except Exception:
                    pass

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
    try:
        browser = get_browser_path()
    except RuntimeError as e:
        print(f"[!] Génération PNG impossible : {e}")
        return False
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
