import sys, os
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
# -*- coding: utf-8 -*-
"""
WIDGET FLOTTANT "BOUTON VERT GO CANDIDATURES"
Bouton interactif Always-On-Top, déplaçable, avec relief 3D.
Ouvre instantanément le Tableau de Bord officiel JobHunter (640 candidatures).
"""
import os
import sys
import subprocess
import webbrowser
import threading
import tkinter as tk

REPO_DIR = r"C:\Users\richa\Gemini\Pipeline_JobHunter"
DASH_FILE = r"C:\Users\richa\JobHunter\dashboard.html"
LAUNCH_SCRIPT = r"C:\Users\richa\JobHunter\launch.py"

class FloatingGoButton:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GO Candidatures")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Dimensions du bouton
        self.width = 130
        self.height = 80
        
        # Positionnement par défaut bien visible (haut-droite, visible sur le ciel du bureau)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = max(100, screen_w - 220)
        start_y = 120
        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")
        
        # Transparence du fond
        self.trans_color = "#f000f0"
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.trans_color,
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Variables pour le déplacement (drag & drop)
        self.drag_x = 0
        self.drag_y = 0
        self.is_dragging = False
        self.press_start_pos = (0, 0)
        
        # Dessiner le bouton initial
        self.is_hovered = False
        self.is_pressed = False
        self.draw_button()
        
        # Événements souris
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def draw_button(self):
        self.canvas.delete("all")
        w, h = self.width, self.height
        offset_y = 3 if self.is_pressed else 0
        
        # Palette de couleurs 3D
        if self.is_hovered:
            c_top = "#7aff9e"
            c_main = "#38e07b"
            c_bot = "#1a9c4a"
            c_shadow = "#0d5c2a"
        else:
            c_top = "#60ea8b"
            c_main = "#2ec86a"
            c_bot = "#168a3f"
            c_shadow = "#0c4f24"

        # Ombre portée 3D (fixe en bas)
        if not self.is_pressed:
            self.canvas.create_oval(14, 18, 54, 68, fill="#000000", outline="", stipple="gray50")
            self.canvas.create_oval(38, 8, 92, 68, fill="#000000", outline="", stipple="gray50")
            self.canvas.create_oval(68, 16, 116, 68, fill="#000000", outline="", stipple="gray50")
            self.canvas.create_rectangle(24, 30, 106, 68, fill="#000000", outline="", stipple="gray50")

        # Base 3D sombre (tranche du bouton)
        by = offset_y
        self.canvas.create_oval(12, 16 + by + 6, 52, 66 + by + 6, fill=c_shadow, outline="")
        self.canvas.create_oval(36, 6 + by + 6, 90, 66 + by + 6, fill=c_shadow, outline="")
        self.canvas.create_oval(66, 14 + by + 6, 114, 66 + by + 6, fill=c_shadow, outline="")
        self.canvas.create_rectangle(22, 28 + by + 6, 104, 66 + by + 6, fill=c_shadow, outline="")

        # Corps principal vert relief
        self.canvas.create_oval(12, 16 + by, 52, 66 + by, fill=c_main, outline=c_bot, width=1)
        self.canvas.create_oval(36, 6 + by, 90, 66 + by, fill=c_main, outline=c_bot, width=1)
        self.canvas.create_oval(66, 14 + by, 114, 66 + by, fill=c_main, outline=c_bot, width=1)
        self.canvas.create_rectangle(22, 26 + by, 104, 66 + by, fill=c_main, outline="")

        # Reflet lumineux supérieur (effet brillant)
        self.canvas.create_oval(42, 10 + by, 84, 34 + by, fill=c_top, outline="")
        self.canvas.create_oval(20, 20 + by, 46, 40 + by, fill=c_top, outline="")

        # Texte principal "GO" en relief
        text_y = 34 + by
        # Ombre du texte
        self.canvas.create_text(64, text_y + 2, text="GO", font=("Segoe UI", 20, "bold"), fill="#0c4f24")
        # Texte blanc éclatant
        self.canvas.create_text(63, text_y, text="GO", font=("Segoe UI", 20, "bold"), fill="#ffffff")

        # Sous-texte "Candidatures"
        sub_y = 52 + by
        self.canvas.create_text(64, sub_y + 1, text="CANDIDATURES", font=("Segoe UI", 7, "bold"), fill="#0c4f24")
        self.canvas.create_text(63, sub_y, text="CANDIDATURES", font=("Segoe UI", 7, "bold"), fill="#ffffff")

    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()

    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.draw_button()

    def on_press(self, event):
        self.is_pressed = True
        self.press_start_pos = (event.x_root, event.y_root)
        self.drag_x = event.x
        self.drag_y = event.y
        self.draw_button()

    def on_drag(self, event):
        dx = abs(event.x_root - self.press_start_pos[0])
        dy = abs(event.y_root - self.press_start_pos[1])
        if dx > 4 or dy > 4:
            self.is_dragging = True
            new_x = self.root.winfo_x() + (event.x - self.drag_x)
            new_y = self.root.winfo_y() + (event.y - self.drag_y)
            self.root.geometry(f"+{new_x}+{new_y}")

    def on_release(self, event):
        self.is_pressed = False
        self.draw_button()
        if not self.is_dragging:
            # C'est un clic !
            self.open_dashboard()
        self.is_dragging = False

    def open_dashboard(self):
        try:
            if os.path.exists(LAUNCH_SCRIPT):
                subprocess.Popen(["pythonw.exe", LAUNCH_SCRIPT], cwd=os.path.dirname(LAUNCH_SCRIPT))
            elif os.path.exists(DASH_FILE):
                webbrowser.open(f"file:///{DASH_FILE.replace(os.sep, '/')}")
        except Exception as e:
            if os.path.exists(DASH_FILE):
                webbrowser.open(f"file:///{DASH_FILE.replace(os.sep, '/')}")

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📊 Ouvrir le Tableau de Bord (640 candidatures)", command=self.open_dashboard)
        menu.add_command(label="📁 Ouvrir le dossier Candidatures", command=lambda: os.startfile(r"C:\Users\richa\JobHunter\candidatures"))
        menu.add_separator()
        menu.add_command(label="❌ Masquer le bouton", command=self.root.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FloatingGoButton()
    app.run()
