# -*- coding: utf-8 -*-
import os
import subprocess
import time
import shutil
import sys

def find_browser_path():
    possible_paths = [
        # Windows
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        # Linux / Ubuntu (GitHub Actions)
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        # PATH
        shutil.which("msedge"),
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chrome")
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError("Navigateur Chromium / Chrome / Edge introuvable pour la compilation PDF.")

def compile_html_to_pdf(html_path: str, output_pdf_path: str, timeout: int = 20) -> bool:
    browser_path = find_browser_path()
    abs_html = os.path.abspath(html_path)
    abs_pdf = os.path.abspath(output_pdf_path)
    
    os.makedirs(os.path.dirname(abs_pdf), exist_ok=True)
    
    if os.path.exists(abs_pdf):
        try:
            os.remove(abs_pdf)
        except Exception:
            pass

    cmd = [
        browser_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={abs_pdf}",
        abs_html
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        for _ in range(12):
            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                return True
            time.sleep(0.3)
    except Exception as e:
        print(f"Exception lors de la compilation PDF : {e}")

    return os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        success = compile_html_to_pdf(sys.argv[1], sys.argv[2])
        print("Succès:" if success else "Échec", sys.argv[2])
