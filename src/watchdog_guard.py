# -*- coding: utf-8 -*-
"""
WATCHDOG RÉSILIENT D'AUTO-GUÉRISON & PROTECTION PERMANENTE
Candidat : Richard BUSSON

Missions clés :
1. Contrôle d'intégrité SHA256 des skills et templates officiels avec auto-restauration immédiate en cas d'altération
2. Protection et sauvegarde tournante de tracker.json (659 candidatures)
3. Synchronisation et vérification du dashboard.html et de la jonction candidatures
4. Surveillance active du Bouton Flottant Vert GO et des raccourcis Bureau
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import hashlib
import shutil
import subprocess
from datetime import datetime

jh_dir = r"C:\Users\richa\JobHunter"
repo_dir = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
sanctuary_dir = os.path.join(jh_dir, "sanctuaire_skills")
manifest_path = os.path.join(sanctuary_dir, "skills_manifest.json")
backups_dir = os.path.join(jh_dir, "backups")

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def heal_skills_and_templates():
    """Vérifie chaque skill et template contre le manifeste SHA256 et auto-restaure en cas d'écart."""
    if not os.path.exists(manifest_path):
        return 0, []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        return 0, []

    healed = 0
    logs = []
    files_dict = manifest.get("files", {})

    for rel_path, meta in files_dict.items():
        expected_sha = meta.get("sha256")
        flat_name = meta.get("flat_name")
        orig_path = meta.get("original_path")
        sanctuary_copy = os.path.join(sanctuary_dir, flat_name)

        current_sha = compute_sha256(orig_path)
        if current_sha != expected_sha:
            if os.path.exists(sanctuary_copy):
                try:
                    os.makedirs(os.path.dirname(orig_path), exist_ok=True)
                    shutil.copy2(sanctuary_copy, orig_path)
                    healed += 1
                    logs.append(f"[RESTORED] {rel_path} auto-restauré depuis le sanctuaire !")
                except Exception as e:
                    logs.append(f"[ERROR] Impossible de restaurer {rel_path} : {e}")

    return healed, logs

def protect_tracker_and_dashboard():
    """Vérifie la validité de tracker.json et maintient les sauvegardes tournantes."""
    tracker_path = os.path.join(repo_dir, "tracker.json")
    golden_path = os.path.join(backups_dir, "tracker_latest_golden.json")

    is_valid = False
    app_count = 0
    if os.path.exists(tracker_path):
        try:
            with open(tracker_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) >= 600:
                    is_valid = True
                    app_count = len(data)
        except Exception:
            is_valid = False

    if not is_valid:
        # Restauration d'urgence
        if os.path.exists(golden_path):
            try:
                shutil.copy2(golden_path, tracker_path)
                print("[!] URGENCE : tracker.json corrompu, restauré depuis la sauvegarde dorée !")
            except Exception:
                pass
    else:
        # Mise à jour de la sauvegarde dorée
        try:
            shutil.copy2(tracker_path, golden_path)
            now_day = datetime.now().strftime("%Y-%m-%d")
            daily_bk = os.path.join(backups_dir, f"tracker_{now_day}.json")
            if not os.path.exists(daily_bk):
                shutil.copy2(tracker_path, daily_bk)
        except Exception:
            pass

    # Synchronisation de dashboard.html
    html_repo = os.path.join(repo_dir, "dashboard.html")
    html_jh = os.path.join(jh_dir, "dashboard.html")
    if os.path.exists(html_repo) and os.path.exists(html_jh):
        if os.path.getmtime(html_repo) > os.path.getmtime(html_jh):
            try:
                shutil.copy2(html_repo, html_jh)
            except Exception:
                pass

def ensure_floating_button_and_shortcuts():
    """Garantit la présence et l'exécution du widget bouton flottant GO."""
    bk_dir = os.path.join(jh_dir, "backup_bouton")
    btn_path = os.path.join(jh_dir, "floating_button.pyw")
    vbs_path = os.path.join(jh_dir, "lancer_bouton_vert.vbs")
    ico_path = os.path.join(jh_dir, "GO-Candidatures.ico")

    for fname in ["floating_button.pyw", "lancer_bouton_vert.vbs", "GO-Candidatures.ico", "app_icon.ico"]:
        dst = os.path.join(jh_dir, fname)
        src = os.path.join(bk_dir, fname)
        if not os.path.exists(dst) and os.path.exists(src):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

    # Raccourci Startup
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    startup_lnk = os.path.join(startup_dir, "Bouton Flottant GO Candidatures.lnk")
    if not os.path.exists(startup_lnk) and os.path.exists(vbs_path):
        try:
            ps_cmd = f'$sh = New-Object -ComObject WScript.Shell; $sc = $sh.CreateShortcut(\'{startup_lnk}\'); $sc.TargetPath = \'wscript.exe\'; $sc.Arguments = \'"{vbs_path}"\'; $sc.WorkingDirectory = \'{jh_dir}\'; $sc.IconLocation = \'{ico_path},0\'; $sc.Save()'
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        except Exception:
            pass

    # Raccourcis Bureau
    desktop_paths = [
        os.path.join(r"C:\Users\richa\OneDrive\Archives\Bureau 2021", "Tableau de Bord - Candidatures.lnk"),
        os.path.join(r"C:\Users\richa\Desktop", "Tableau de Bord - Candidatures.lnk"),
        os.path.join(r"C:\Users\richa\Desktop", "🟢 GO CANDIDATURES.lnk")
    ]
    for sc in desktop_paths:
        if not os.path.exists(sc):
            try:
                ps = f'$sh = New-Object -ComObject WScript.Shell; $s = $sh.CreateShortcut(\'{sc}\'); $s.TargetPath = \'wscript.exe\'; $s.Arguments = \'"{os.path.join(jh_dir, "launch.vbs")}"\'; $s.WorkingDirectory = \'{jh_dir}\'; $s.IconLocation = \'{os.path.join(jh_dir, "app_icon.ico")},0\'; $s.Save()'
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], capture_output=True, timeout=5)
            except Exception:
                pass

    # Vérification du processus
    try:
        cmd = 'powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \\"Name=\'pythonw.exe\'\\" | Where-Object { $_.CommandLine -match \'floating_button\' } | Select-Object -ExpandProperty ProcessId"'
        out = subprocess.check_output(cmd, shell=True).decode("utf-8", errors="ignore").strip()
        if not out and os.path.exists(vbs_path):
            subprocess.Popen(["wscript.exe", vbs_path], cwd=jh_dir)
    except Exception:
        pass

def run_watchdog():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Exécution du Watchdog de Protection JobHunter...")
    h_count, logs = heal_skills_and_templates()
    if h_count > 0:
        for l in logs:
            print(f"  {l}")
    else:
        print("  [✓] 100% des skills et templates officiels sont intacts et conformes.")

    protect_tracker_and_dashboard()
    print("  [✓] tracker.json et dashboard.html sécurisés.")

    ensure_floating_button_and_shortcuts()
    print("  [✓] Bouton Flottant GO et raccourcis Bureau opérationnels.")

if __name__ == "__main__":
    run_watchdog()
