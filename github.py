#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import hashlib
import time
import json
import threading
import ctypes
import git
from git import Repo
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog, font
from datetime import datetime

# Configuration
CONFIG_FILE = "github_py_config.json"
TEMP_DIR = "temp_git"
CACHE_DIR = "git_cache"
BACKUP_DIR = "git_backups"
HISTORY_FILE = "git_history.json"

# Thème de couleurs plus douce et moderne
COLORS = {
    'primary': '#3F88C5',         # Bleu principal plus doux
    'primary_dark': '#1565C0',    # Bleu foncé
    'primary_light': '#BBDEFB',   # Bleu clair
    'accent': '#FF9E80',          # Orange corail adouci
    'success': '#66BB6A',         # Vert succès plus doux
    'warning': '#FFCA28',         # Jaune avertissement
    'error': '#EF5350',           # Rouge erreur plus doux
    'bg_light': '#F8F9FA',        # Fond clair plus doux
    'bg_dark': '#2C3E50',         # Fond sombre plus doux
    'text_light': '#FFFFFF',      # Texte clair
    'text_dark': '#37474F',       # Texte sombre plus doux
    'text_secondary': '#78909C',  # Texte secondaire plus doux
    'divider': '#ECEFF1',         # Diviseur très léger
    'card': '#FFFFFF',            # Carte
    'card_border': '#E1E7EC',     # Bordure de carte très légère
    'shadow': 'rgba(0, 0, 0, 0.1)',# Ombre
    'header_bg': '#6FB1E4',       # Fond d'en-tête dégradé
    'button_hover': '#64B5F6',    # Couleur de survol des boutons
    'secondary': '#90A4AE',        # Couleur secondaire
}

# Fonction pour désactiver la mise à l'échelle automatique de Windows (DPI Awareness)
def disable_dpi_scaling():
    if sys.platform.startswith('win'):
        try:
            # Désactiver la mise à l'échelle automatique pour plus de netteté
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

# Pour ajouter des coins arrondis aux Canvas
tk.Canvas.create_rounded_rectangle = lambda self, x1, y1, x2, y2, r, **kwargs: self.create_polygon(
    int(x1+r), int(y1), int(x2-r), int(y1), int(x2), int(y1), int(x2), int(y1+r), 
    int(x2), int(y2-r), int(x2), int(y2), int(x2-r), int(y2), int(x1+r), int(y2), 
    int(x1), int(y2), int(x1), int(y2-r), int(x1), int(y1+r), int(x1), int(y1), 
    smooth=True, **kwargs)

# Initialisation des polices à utiliser de manière uniforme
class Fonts:
    DEFAULT = "TkDefaultFont"
    HEADING = "TkHeadingFont"
    TEXT = "TkTextFont"
    FIXED = "TkFixedFont"
    
    @staticmethod
    def init_fonts():
        font.nametofont(Fonts.DEFAULT).configure(family="Segoe UI", size=10)
        font.nametofont(Fonts.TEXT).configure(family="Segoe UI", size=10)
        font.nametofont(Fonts.FIXED).configure(family="Consolas", size=10)
        
        # Créer des polices personnalisées si nécessaire
        try:
            font.Font(name="TkHeadingFont", family="Segoe UI", size=11, weight="bold")
            font.Font(name="TkTitleFont", family="Segoe UI", size=16, weight="bold")
            font.Font(name="TkButtonFont", family="Segoe UI", size=10, weight="bold")
        except:
            # Si les polices existent déjà, les reconfigurer
            try:
                font.nametofont("TkHeadingFont").configure(family="Segoe UI", size=11, weight="bold")
                font.nametofont("TkTitleFont").configure(family="Segoe UI", size=16, weight="bold")
                font.nametofont("TkButtonFont").configure(family="Segoe UI", size=10, weight="bold")
            except:
                pass 

class RepoConfig:
    def __init__(self):
        self.repos = []
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.repos = config.get("repos", [])
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
                self.repos = []
        else:
            # Créer le fichier de configuration s'il n'existe pas
            self.repos = []
            self.save_config()
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"repos": self.repos}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def add_repo(self, name, local_path, remote_url, branch, excluded_files):
        """Ajoute un nouveau dépôt à la configuration"""
        repo = {
            "name": name,
            "local_path": local_path,
            "remote_url": remote_url,
            "branch": branch,
            "excluded_files": excluded_files
        }
        self.repos.append(repo)
        self.save_config()
        return repo
    
    def update_repo(self, index, **kwargs):
        """Met à jour un dépôt existant"""
        if 0 <= index < len(self.repos):
            for key, value in kwargs.items():
                self.repos[index][key] = value
            self.save_config()
    
    def delete_repo(self, index):
        """Supprime un dépôt"""
        if 0 <= index < len(self.repos):
            del self.repos[index]
            self.save_config()
    
    def get_repos(self):
        """Renvoie la liste des dépôts"""
        return self.repos 

# Widget personnalisé pour un bouton moderne avec coins arrondis et ombre
class ModernButton(tk.Frame):
    def __init__(self, parent, text, command=None, width=120, height=36, bg_color=COLORS['primary'], 
                 hover_color=COLORS['button_hover'], text_color=COLORS['text_light'], state=tk.NORMAL):
        # Correction pour éviter l'erreur
        super().__init__(parent, width=width, height=height)
        self.configure(background=COLORS['bg_light'])
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.state_normal = state == tk.NORMAL
        self.command = command
        
        # Créer le canvas pour le bouton
        self.canvas = tk.Canvas(self, width=width, height=height, 
                              highlightthickness=0, bd=0, bg=COLORS['bg_light'])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Créer l'ombre
        self.shadow_id = self.canvas.create_rounded_rectangle(4, 4, width-1, height-1, 12, 
                                                      fill='#DDDDDD', outline='')
        
        # Créer le rectangle du bouton
        self.rect_id = self.canvas.create_rounded_rectangle(0, 0, width-4, height-4, 12, 
                                                        fill=bg_color if self.state_normal else COLORS['divider'],
                                                        outline='')
        
        # Ajouter le texte - Utiliser une configuration de police sûre
        try:
            # Utiliser directement une police système pour plus de sécurité
            self.text_id = self.canvas.create_text(int(width/2) - 2, int(height/2) - 2, text=text, 
                                           fill=text_color if self.state_normal else COLORS['text_secondary'],
                                           font=("System", 10))
        except:
            # Fallback sûr
            self.text_id = self.canvas.create_text(int(width/2) - 2, int(height/2) - 2, text=text, 
                                           fill=text_color if self.state_normal else COLORS['text_secondary'])
        
        # Lier les événements
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
    def on_enter(self, event):
        if self.state_normal:
            # Effet de transition douce lors du survol
            self.canvas.itemconfig(self.rect_id, fill=self.hover_color)
            self.canvas.itemconfig(self.shadow_id, fill='#D0D0D0')
    
    def on_leave(self, event):
        if self.state_normal:
            self.canvas.itemconfig(self.rect_id, fill=self.bg_color)
            self.canvas.itemconfig(self.shadow_id, fill='#DDDDDD')
    
    def on_press(self, event):
        if self.state_normal:
            # Effet d'enfoncement
            self.canvas.move(self.text_id, 1, 1)
            self.canvas.move(self.rect_id, 1, 1)
            self.canvas.itemconfig(self.shadow_id, fill='#EEEEEE')
    
    def on_release(self, event):
        if self.state_normal:
            # Restaurer la position
            self.canvas.move(self.text_id, -1, -1)
            self.canvas.move(self.rect_id, -1, -1)
            self.canvas.itemconfig(self.shadow_id, fill='#DDDDDD')
            if self.command:
                self.command()
    
    def configure(self, **kwargs):
        if 'state' in kwargs:
            self.state_normal = kwargs['state'] == tk.NORMAL
            self.canvas.itemconfig(self.rect_id, 
                               fill=self.bg_color if self.state_normal else COLORS['divider'])
            self.canvas.itemconfig(self.text_id, 
                               fill=self.text_color if self.state_normal else COLORS['text_secondary'])
        
        if 'text' in kwargs:
            self.canvas.itemconfig(self.text_id, text=kwargs['text'])
            
    # Alias pour compatibilité
    config = configure 

# Frame avec effet d'ombre
class ShadowFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        style_name = kwargs.pop('style', 'TFrame')
        super().__init__(parent, style=style_name, **kwargs)
        
        # Créer un cadre d'ombre sous le frame principal
        self.shadow = ttk.Frame(parent, style='Shadow.TFrame')
        
        # Configurer le positionnement
        self.bind("<Map>", self._on_map)
        self.bind("<Configure>", self._on_configure)
    
    def _on_map(self, event):
        self.shadow.lift(self)
    
    def _on_configure(self, event):
        x, y = self.winfo_x(), self.winfo_y()
        width, height = self.winfo_width(), self.winfo_height()
        # Utiliser des coordonnées entières pour l'ombre
        self.shadow.place(x=int(x+4), y=int(y+4), width=int(width), height=int(height)) 

class GitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Github.py - Gestion de dépôts Git")
        self.root.geometry("1070x700")
        self.root.minsize(900, 650)
        
        # Désactiver la mise à l'échelle pour un rendu net
        disable_dpi_scaling()
        
        # Configurer l'anticrénelage pour les polices
        Fonts.init_fonts()
        
        # Variables
        self.repo_config = RepoConfig()
        self.current_repo = None
        self.git_repo = None
        self.operation_running = False
        
        # Configurer le thème de l'application
        self.setup_theme()
        
        # Create widgets
        self.create_widgets()
        
        # Center the window
        self.center_window()
    
    def setup_theme(self):
        """Configure le thème global de l'application"""
        self.root.configure(bg=COLORS['bg_light'])
        
        # Configurer le style global
        style = ttk.Style()
        
        # Configurer les styles de base avec des polices sûres
        style.configure(".", font=Fonts.DEFAULT, background=COLORS['bg_light'])
        
        # Boutons avec coins arrondis et effet de relief
        style.configure("TButton", font=Fonts.DEFAULT, foreground=COLORS['text_dark'], 
                      background=COLORS['primary'], borderwidth=0, focuscolor=COLORS['primary'], 
                      relief=tk.RAISED, padding=(10, 5))
        style.map("TButton", 
                background=[('active', COLORS['button_hover']), ('disabled', COLORS['divider'])],
                foreground=[('disabled', COLORS['text_secondary'])])
        
        # Étiquettes et cadres
        style.configure("TLabel", font=Fonts.DEFAULT, background=COLORS['bg_light'], foreground=COLORS['text_dark'])
        style.configure("TFrame", background=COLORS['bg_light'])
        style.configure("Shadow.TFrame", background='#DDDDDD')  # Style pour l'ombre
        
        # Cadres avec étiquette
        style.configure("TLabelframe", background=COLORS['bg_light'], foreground=COLORS['text_dark'], borderwidth=1)
        style.configure("TLabelframe.Label", font=Fonts.HEADING, background=COLORS['bg_light'], foreground=COLORS['primary'])
        
        # Configurer les styles personnalisés
        style.configure("Title.TLabel", font=Fonts.HEADING, background=COLORS['bg_light'], foreground=COLORS['primary'])
        style.configure("Card.TFrame", background=COLORS['card'])
        
        # En-tête avec dégradé
        style.configure("Header.TFrame", background=COLORS['header_bg'], padx=15, pady=8)
        style.configure("Header.TLabel", font=Fonts.DEFAULT, foreground=COLORS['text_light'], background=COLORS['header_bg'])
        
        # Style pour la liste des dépôts
        style.configure("Treeview", 
                     font=Fonts.DEFAULT, 
                     rowheight=30, 
                     background=COLORS['card'], 
                     fieldbackground=COLORS['card'],
                     borderwidth=0)
        style.configure("Treeview.Heading", 
                      font=Fonts.HEADING, 
                      background=COLORS['primary_light'], 
                      foreground=COLORS['text_dark'],
                      relief=tk.FLAT)
        style.map("Treeview", 
                background=[('selected', COLORS['primary'])],
                foreground=[('selected', COLORS['text_light'])])
        
        # Style pour les entrées
        style.configure("TEntry", font=Fonts.DEFAULT, padding=8, relief=tk.FLAT)
        style.configure("TCombobox", font=Fonts.DEFAULT, padding=8)
        
        # Style pour le texte
        self.root.option_add("*TScrolledText*Font", Fonts.FIXED)
        
        # Style pour la barre de progression avec contours nets
        style.configure("Horizontal.TProgressbar", 
                      foreground=COLORS['primary'], 
                      background=COLORS['primary'],
                      troughcolor=COLORS['bg_light'],
                      thickness=8,
                      borderwidth=0)
    
    def create_widgets(self):
        """Crée les widgets de l'interface"""
        # Frame principal avec marge et padding
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # En-tête de l'application avec effet d'ombre
        header_frame = ttk.Frame(main_container, style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo/Icône (représenté par un texte stylisé)
        title_label = ttk.Label(header_frame, text="Github.py", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        # Sous-titre
        subtitle_label = ttk.Label(header_frame, text="Gestion de dépôts Git", 
                                foreground=COLORS['text_light'], background=COLORS['header_bg'],
                                font=("Segoe UI", 10))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Container pour les dépôts et les actions avec espacement
        top_container = ttk.Frame(main_container, style="TFrame")
        top_container.pack(fill=tk.X, pady=(0, 20))
        
        # Frame pour les dépôts avec style "carte" et ombre
        repo_frame = ttk.LabelFrame(top_container, text="Dépôts", padding=15)
        repo_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Liste des dépôts avec style moderne
        self.repo_list = ttk.Treeview(repo_frame, columns=("name"), show="headings", height=3)
        self.repo_list.heading("name", text="Nom du dépôt")
        self.repo_list.column("name", width=200)
        self.repo_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(repo_frame, orient="vertical", command=self.repo_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.repo_list.configure(yscrollcommand=scrollbar.set)
        
        self.repo_list.bind("<<TreeviewSelect>>", self.on_repo_select)
        
        # Frame pour les boutons de gestion des dépôts
        repo_buttons_frame = ttk.Frame(top_container)
        repo_buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))
        
        # Utilisation de boutons modernes personnalisés avec espacements
        add_btn = ModernButton(repo_buttons_frame, text="Ajouter un dépôt", command=self.add_repo_dialog, 
                            width=150, height=40, bg_color=COLORS['primary'], 
                            text_color=COLORS['text_light'])
        add_btn.pack(fill=tk.X, pady=5)
        
        edit_btn = ModernButton(repo_buttons_frame, text="Modifier", command=self.edit_repo_dialog,
                             width=150, height=40, bg_color=COLORS['primary'],
                             text_color=COLORS['text_light'])
        edit_btn.pack(fill=tk.X, pady=5)
        
        delete_btn = ModernButton(repo_buttons_frame, text="Supprimer", command=self.delete_repo,
                               width=150, height=40, bg_color=COLORS['primary'],
                               text_color=COLORS['text_light'])
        delete_btn.pack(fill=tk.X, pady=5)
        
        # Frame pour les actions avec plus d'espace
        action_frame = ttk.LabelFrame(main_container, text="Actions", padding=15)
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Conteneur d'actions avec espacement équitable
        action_container = ttk.Frame(action_frame)
        action_container.pack(fill=tk.X, pady=5)
        
        # Utiliser des boutons ModernButton pour les actions
        btn_width = 150
        btn_height = 40
        
        self.clone_btn = ModernButton(action_container, text="Cloner le dépôt", command=self.clone_repo,
                                    width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                    state=tk.DISABLED)  # Désactivé par défaut
        self.clone_btn.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        
        self.commit_btn = ModernButton(action_container, text="Créer un commit", command=self.create_commit,
                                    width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                    state=tk.DISABLED)
        self.commit_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.branch_btn = ModernButton(action_container, text="Nouvelle branche", command=self.create_branch,
                                   width=btn_width, height=btn_height, bg_color=COLORS['success'],
                                   state=tk.DISABLED)
        self.branch_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.merge_btn = ModernButton(action_container, text="Fusionner", command=self.merge_branches,
                                     width=btn_width, height=btn_height, bg_color=COLORS['warning'],
                                     text_color=COLORS['text_dark'], state=tk.DISABLED)
        self.merge_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.pull_btn = ModernButton(action_container, text="Pull", command=self.pull_changes,
                                    width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                    state=tk.DISABLED)
        self.pull_btn.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
        
        # Ajout du bouton Push
        self.push_btn = ModernButton(action_container, text="Push", command=self.push_changes,
                                    width=btn_width, height=btn_height, bg_color=COLORS['success'],
                                    state=tk.DISABLED)
        self.push_btn.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
        
        # Deuxième rangée d'actions
        action_container2 = ttk.Frame(action_frame)
        action_container2.pack(fill=tk.X, pady=5)
        
        self.switch_btn = ModernButton(action_container2, text="Changer de branche", command=self.switch_branch,
                                     width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                     state=tk.DISABLED)
        self.switch_btn.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        
        self.delete_branch_btn = ModernButton(action_container2, text="Supprimer branche", command=self.delete_branch,
                                           width=btn_width, height=btn_height, bg_color=COLORS['error'],
                                           state=tk.DISABLED)
        self.delete_branch_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.resolve_btn = ModernButton(action_container2, text="Résoudre conflits", command=self.resolve_conflicts,
                                     width=btn_width, height=btn_height, bg_color=COLORS['warning'],
                                     text_color=COLORS['text_dark'], state=tk.DISABLED)
        self.resolve_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.history_btn = ModernButton(action_container2, text="Historique", command=self.show_commit_history,
                                      width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                      state=tk.DISABLED)
        self.history_btn.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        
        self.tag_btn = ModernButton(action_container2, text="Taguer version", command=self.create_tag,
                                  width=btn_width, height=btn_height, bg_color=COLORS['primary'],
                                  state=tk.DISABLED)
        self.tag_btn.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
        
        # Frame pour les logs avec style carte et plus d'espacement
        log_frame = ttk.LabelFrame(main_container, text="Journal", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Journal avec coloration syntaxique et une police moderne
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg=COLORS['card'], 
                                         relief=tk.FLAT, borderwidth=0, highlightthickness=0,
                                         padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Configurer les tags pour la coloration du texte
        self.log_text.tag_configure("info", foreground=COLORS['text_dark'])
        self.log_text.tag_configure("error", foreground=COLORS['error'])
        self.log_text.tag_configure("success", foreground=COLORS['success'])
        self.log_text.tag_configure("warning", foreground=COLORS['warning'])
        self.log_text.tag_configure("highlight", foreground=COLORS['primary'])
        
        # Barre de statut moderne avec plus d'espacement
        status_frame = ttk.Frame(main_container, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Ajouter un subtil effet de séparateur au-dessus
        separator = ttk.Separator(main_container, orient='horizontal')
        separator.pack(fill=tk.X, pady=(15, 0))
        
        status_container = ttk.Frame(status_frame)
        status_container.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(status_container, text="Prêt")
        self.status_label.pack(side=tk.LEFT)
        
        # Barre de progression moderne avec coins arrondis
        self.progress_bar = ttk.Progressbar(status_container, mode="determinate", length=200, 
                                      style="Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.RIGHT)
        
        # Charger la liste des dépôts
        self.load_repo_list()
    
    def load_repo_list(self):
        """Charge la liste des dépôts"""
        # Effacer la liste actuelle
        for item in self.repo_list.get_children():
            self.repo_list.delete(item)
        
        # Ajouter les dépôts
        repos = self.repo_config.get_repos()
        for i, repo in enumerate(repos):
            self.repo_list.insert("", "end", values=(repo["name"]), iid=str(i))
    
    def on_repo_select(self, event):
        """Gère la sélection d'un dépôt dans la liste"""
        selection = self.repo_list.selection()
        if selection:
            index = int(selection[0])
            repos = self.repo_config.get_repos()
            if 0 <= index < len(repos):
                self.current_repo = repos[index]
                self.log(f"Dépôt sélectionné: {self.current_repo['name']}")
                
                # Activer le bouton de clonage puisqu'un dépôt est sélectionné
                self.clone_btn.config(state=tk.NORMAL)
                
                # Activer les boutons appropriés
                if os.path.exists(os.path.join(self.current_repo['local_path'], '.git')):
                    try:
                        self.git_repo = Repo(self.current_repo['local_path'])
                        self.commit_btn.config(state=tk.NORMAL)
                        self.branch_btn.config(state=tk.NORMAL)
                        self.merge_btn.config(state=tk.NORMAL)
                        self.pull_btn.config(state=tk.NORMAL)
                        self.push_btn.config(state=tk.NORMAL)
                        self.switch_btn.config(state=tk.NORMAL)
                        self.delete_branch_btn.config(state=tk.NORMAL)
                        self.resolve_btn.config(state=tk.NORMAL)
                        self.history_btn.config(state=tk.NORMAL)
                        self.tag_btn.config(state=tk.NORMAL)
                        
                        # Afficher la branche actuelle
                        current_branch = self.git_repo.active_branch.name
                        self.log(f"Branche actuelle: {current_branch}", "info")
                    except Exception as e:
                        self.log(f"Erreur lors de l'ouverture du dépôt Git: {e}", "error")
                else:
                    self.git_repo = None
                    self.commit_btn.config(state=tk.DISABLED)
                    self.branch_btn.config(state=tk.DISABLED)
                    self.merge_btn.config(state=tk.DISABLED)
                    self.pull_btn.config(state=tk.DISABLED)
                    self.push_btn.config(state=tk.DISABLED)
                    self.switch_btn.config(state=tk.DISABLED)
                    self.delete_branch_btn.config(state=tk.DISABLED)
                    self.resolve_btn.config(state=tk.DISABLED)
                    self.history_btn.config(state=tk.DISABLED)
                    self.tag_btn.config(state=tk.DISABLED)
        else:
            # Aucun dépôt n'est sélectionné, désactiver tous les boutons
            self.current_repo = None
            self.git_repo = None
            self.clone_btn.config(state=tk.DISABLED)
            self.commit_btn.config(state=tk.DISABLED)
            self.branch_btn.config(state=tk.DISABLED)
            self.merge_btn.config(state=tk.DISABLED)
            self.pull_btn.config(state=tk.DISABLED)
            self.push_btn.config(state=tk.DISABLED)
            self.switch_btn.config(state=tk.DISABLED)
            self.delete_branch_btn.config(state=tk.DISABLED)
            self.resolve_btn.config(state=tk.DISABLED)
            self.history_btn.config(state=tk.DISABLED)
            self.tag_btn.config(state=tk.DISABLED)
    
    def add_repo_dialog(self):
        """Affiche la boîte de dialogue pour ajouter un dépôt"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter un dépôt")
        dialog.geometry("750x750")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal avec marge
        main_frame = ttk.Frame(dialog, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre plus visible sans icône
        title_label = ttk.Label(main_frame, text="Ajouter un nouveau dépôt Git", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 25))
        
        # Conteneur pour les formulaires
        form_container = ttk.Frame(main_frame)
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Style pour les labels de formulaire - plus d'espace
        form_label_style = {"anchor": tk.W, "padding": (0, 12, 0, 6)}
        
        # Champs de formulaire avec plus d'espace et meilleure présentation
        ttk.Label(form_container, text="Nom du dépôt:", **form_label_style).grid(row=0, column=0, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(form_container, textvariable=name_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=6)
        
        ttk.Label(form_container, text="Dossier local:", **form_label_style).grid(row=1, column=0, sticky=tk.W)
        local_path_var = tk.StringVar(value=os.getcwd())
        local_path_entry = ttk.Entry(form_container, textvariable=local_path_var, width=50)
        local_path_entry.grid(row=1, column=1, sticky=tk.W, pady=6)
        
        browse_btn = ModernButton(form_container, text="Parcourir...", 
                                command=lambda: local_path_var.set(filedialog.askdirectory()),
                                width=120, height=36)
        browse_btn.grid(row=1, column=2, sticky=tk.W, pady=6, padx=(12, 0))
        
        ttk.Label(form_container, text="URL du dépôt distant:", **form_label_style).grid(row=2, column=0, sticky=tk.W)
        remote_url_var = tk.StringVar()
        ttk.Entry(form_container, textvariable=remote_url_var, width=50).grid(row=2, column=1, sticky=tk.W, pady=6)
        
        ttk.Label(form_container, text="Branche par défaut:", **form_label_style).grid(row=3, column=0, sticky=tk.W)
        branch_var = tk.StringVar(value="main")
        ttk.Entry(form_container, textvariable=branch_var, width=50).grid(row=3, column=1, sticky=tk.W, pady=6)
        
        ttk.Label(form_container, text="Fichiers/dossiers à exclure:", **form_label_style).grid(row=4, column=0, sticky=tk.W)
        
        # Cadre avec ombre pour la zone de texte
        excluded_frame = ttk.Frame(form_container)
        excluded_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=6)
        
        # Zone de texte avec bordure et fond blanc plus élégante
        excluded_text = scrolledtext.ScrolledText(excluded_frame, wrap=tk.WORD, width=55, height=15,
                                              bg=COLORS['card'], relief=tk.FLAT, 
                                              borderwidth=1, highlightthickness=1,
                                              highlightbackground=COLORS['divider'],
                                              padx=10, pady=10)
        excluded_text.pack(fill=tk.BOTH, expand=True)
        excluded_text.insert(tk.END, "__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n.idea/\n.vscode/")
        
        # Boutons pour parcourir les fichiers/dossiers à exclure
        exclude_btn_frame = ttk.Frame(form_container)
        exclude_btn_frame.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(8, 18))
        
        def add_exclude_files():
            fichiers = filedialog.askopenfilenames(title="Sélectionner des fichiers à exclure")
            if fichiers:
                # Extraire les noms des fichiers du chemin complet
                for fichier in fichiers:
                    nom_fichier = os.path.basename(fichier)
                    excluded_text.insert(tk.END, f"\n{nom_fichier}")
        
        def add_exclude_dir():
            dossier = filedialog.askdirectory(title="Sélectionner un dossier à exclure")
            if dossier:
                # Extraire le nom du dossier du chemin complet
                nom_dossier = os.path.basename(dossier)
                excluded_text.insert(tk.END, f"\n{nom_dossier}/")
        
        # Boutons avec meilleur espacement
        add_files_btn = ModernButton(exclude_btn_frame, text="Ajouter fichiers...", 
                                   command=add_exclude_files, width=150, height=36)
        add_files_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        add_dir_btn = ModernButton(exclude_btn_frame, text="Ajouter dossier...", 
                                 command=add_exclude_dir, width=150, height=36)
        add_dir_btn.pack(side=tk.LEFT)
        
        # Séparateur plus visible
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=18)
        
        # Boutons d'action plus élégants avec style ModernButton
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        # Option pour initialiser ou pas un nouveau dépôt
        init_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text="Initialiser un nouveau dépôt Git", variable=init_var).pack(side=tk.LEFT)
        
        cancel_btn = ModernButton(btn_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'],
                               hover_color='#455A64')
        cancel_btn.pack(side=tk.RIGHT)
        
        save_btn = ModernButton(btn_frame, text="Enregistrer", 
                             command=lambda: self.save_new_repo(
                                 name_var.get(), local_path_var.get(), remote_url_var.get(), 
                                 branch_var.get(), excluded_text.get("1.0", tk.END).splitlines(),
                                 init_var.get(), dialog
                             ),
                             width=150, height=40, bg_color=COLORS['primary'])
        save_btn.pack(side=tk.RIGHT, padx=(0, 12))
    
    def save_new_repo(self, name, local_path, remote_url, branch, excluded_files, init_repo, dialog):
        """Sauvegarde un nouveau dépôt"""
        if not name or not local_path:
            messagebox.showerror("Erreur", "Le nom du dépôt et le dossier local sont obligatoires", parent=dialog)
            return
        
        # Nettoyer la liste des fichiers exclus (enlever les lignes vides)
        excluded_files = [f.strip() for f in excluded_files if f.strip()]
        
        try:
            # Créer le dossier local s'il n'existe pas
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            
            # Initialiser un nouveau dépôt si demandé
            if init_repo:
                if not os.path.exists(os.path.join(local_path, '.git')):
                    self.log(f"Initialisation d'un nouveau dépôt Git dans {local_path}", "info")
                    repo = Repo.init(local_path)
                    
                    # Créer un fichier .gitignore avec les exclusions
                    if excluded_files:
                        with open(os.path.join(local_path, '.gitignore'), 'w') as f:
                            f.write('\n'.join(excluded_files))
                        
                        # Ajouter le .gitignore au dépôt
                        repo.git.add('.gitignore')
                        repo.git.commit('-m', 'Initial commit: Add .gitignore')
                    
                    # Configurer l'URL distante si fournie
                    if remote_url:
                        repo.create_remote('origin', remote_url)
                else:
                    self.log(f"Un dépôt Git existe déjà dans {local_path}", "warning")
            
            # Ajouter le dépôt à la configuration
            self.repo_config.add_repo(name, local_path, remote_url, branch, excluded_files)
            
            # Recharger la liste
            self.load_repo_list()
            
            # Fermer la boîte de dialogue
            dialog.destroy()
            
            self.log(f"Dépôt ajouté: {name} ({local_path})", "success")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du dépôt: {str(e)}", parent=dialog)
            self.log(f"Erreur lors de la création du dépôt: {str(e)}", "error")
    
    def edit_repo_dialog(self):
        """Ouvre la boîte de dialogue pour modifier un dépôt"""
        # Implémentation de la boîte de dialogue pour modifier un dépôt
        pass
    
    def delete_repo(self):
        """Supprime le dépôt sélectionné"""
        # Implémentation de la suppression du dépôt
        pass
    
    def clone_repo(self):
        """Clone le dépôt sélectionné"""
        if not self.current_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt à cloner")
            return
            
        # Vérifier si le dépôt a une URL distante configurée
        if not self.current_repo.get("remote_url"):
            messagebox.showerror("Erreur", "Ce dépôt n'a pas d'URL distante configurée")
            return
            
        # Créer la boîte de dialogue pour choisir le dossier cible
        dialog = tk.Toplevel(self.root)
        dialog.title("Cloner le dépôt")
        dialog.geometry("700x400")  # Dimensions augmentées
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal avec marge
        main_frame = ttk.Frame(dialog, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text=f"Cloner le dépôt: {self.current_repo['name']}", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 25))
        
        # Conteneur pour le formulaire
        form_container = ttk.Frame(main_frame)
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Style pour les labels de formulaire
        form_label_style = {"anchor": tk.W, "padding": (0, 12, 0, 6)}
        
        # Afficher l'URL du dépôt
        url_frame = ttk.Frame(form_container)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="URL du dépôt:", **form_label_style).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(url_frame, text=self.current_repo['remote_url']).pack(side=tk.LEFT)
        
        # Champ pour le dossier local
        local_frame = ttk.Frame(form_container)
        local_frame.pack(fill=tk.X, pady=5)
        ttk.Label(local_frame, text="Dossier local:", **form_label_style).pack(side=tk.LEFT, padx=(0, 5))
        local_path_var = tk.StringVar(value=os.path.join(os.getcwd(), self.current_repo["name"] + "_clone"))
        local_path_entry = ttk.Entry(local_frame, textvariable=local_path_var, width=50)
        local_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ModernButton(local_frame, text="Parcourir...", 
                                command=lambda: local_path_var.set(filedialog.askdirectory()),
                                width=120, height=36)
        browse_btn.pack(side=tk.LEFT, padx=(12, 0))
        
        # Champ pour la branche
        branch_frame = ttk.Frame(form_container)
        branch_frame.pack(fill=tk.X, pady=5)
        ttk.Label(branch_frame, text="Branche:", **form_label_style).pack(side=tk.LEFT, padx=(0, 5))
        branch_var = tk.StringVar(value=self.current_repo["branch"])
        branch_entry = ttk.Entry(branch_frame, textvariable=branch_var, width=50)
        branch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Séparateur
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=18)
        
        # Boutons d'action
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        cancel_btn = ModernButton(btn_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'],
                               hover_color='#455A64')
        cancel_btn.pack(side=tk.RIGHT)
        
        clone_btn = ModernButton(btn_frame, text="Cloner", 
                              command=lambda: self.do_clone_repo(
                                  self.current_repo["name"] + "_clone", 
                                  self.current_repo["remote_url"], 
                                  local_path_var.get(), 
                                  branch_var.get(), 
                                  dialog
                              ),
                              width=150, height=40, bg_color=COLORS['primary'])
        clone_btn.pack(side=tk.RIGHT, padx=(0, 12))
    
    def do_clone_repo(self, name, remote_url, local_path, branch, dialog):
        """Clone un dépôt distant"""
        if not name or not remote_url or not local_path:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires", parent=dialog)
            return
        
        # Désactiver les boutons de clonage pendant l'opération
        # Au lieu de désactiver tous les widgets, on désactive seulement les boutons
        for widget in dialog.winfo_children():
            self._disable_widget_safely(widget)
        
        # Lancer le clonage dans un thread séparé
        threading.Thread(target=lambda: self._clone_thread(name, remote_url, local_path, branch, dialog)).start()
    
    def _clone_thread(self, name, remote_url, local_path, branch, dialog):
        """Thread pour cloner un dépôt"""
        try:
            self.log(f"Clonage de {remote_url} dans {local_path}...", "info")
            
            # Créer le dossier parent si nécessaire
            if not os.path.exists(os.path.dirname(local_path)):
                os.makedirs(os.path.dirname(local_path))
            
            # Tenter de cloner le dépôt avec la branche spécifiée
            try:
                self.log(f"Tentative de clonage avec la branche {branch}...", "info")
                repo = Repo.clone_from(remote_url, local_path, branch=branch)
            except Exception as branch_error:
                # Si la première tentative échoue (probablement à cause d'une branche non trouvée)
                error_str = str(branch_error)
                if "Remote branch" in error_str and "not found in upstream" in error_str:
                    self.log(f"Branche '{branch}' non trouvée. Tentative de clonage sans spécifier de branche...", "warning")
                    
                    # Supprimer le dossier local partiellement créé s'il existe
                    if os.path.exists(local_path):
                        shutil.rmtree(local_path, ignore_errors=True)
                    
                    # Réessayer sans spécifier de branche
                    repo = Repo.clone_from(remote_url, local_path)
                    actual_branch = repo.active_branch.name
                    self.log(f"Clonage réussi. La branche actuelle est '{actual_branch}'", "info")
                    
                    # Mettre à jour la branche dans la configuration
                    branch = actual_branch
                else:
                    # Si l'erreur est différente, la relancer
                    raise branch_error
            
            # Extraire les fichiers exclus du .gitignore
            excluded_files = []
            gitignore_path = os.path.join(local_path, '.gitignore')
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    excluded_files = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
            
            # Ajouter le dépôt à la configuration
            self.repo_config.add_repo(name, local_path, remote_url, branch, excluded_files)
            
            # Mettre à jour l'interface dans le thread principal
            self.root.after(0, lambda: self._clone_completed(dialog))
            
        except Exception as e:
            # Nettoyer le dossier partiellement créé en cas d'erreur
            if os.path.exists(local_path):
                try:
                    shutil.rmtree(local_path, ignore_errors=True)
                except:
                    pass
                
            # Stocker l'erreur dans une variable locale pour éviter les problèmes de portée
            error_message = str(e)
            # Gérer les erreurs dans le thread principal
            self.root.after(0, lambda: self._clone_error(dialog, error_message))
    
    def _clone_completed(self, dialog):
        """Gère la fin d'un clonage réussi"""
        self.log("Clonage terminé avec succès", "success")
        self.load_repo_list()
        dialog.destroy()
        
        # Afficher un message de succès
        messagebox.showinfo("Succès", "Le dépôt a été cloné avec succès")
    
    def _clone_error(self, dialog, error_msg):
        """Gère une erreur de clonage"""
        self.log(f"Erreur lors du clonage: {error_msg}", "error")
        
        # Réactiver les widgets du dialogue
        for widget in dialog.winfo_children():
            try:
                widget.configure(state=tk.NORMAL)
            except:
                pass  # Certains widgets n'ont pas d'état
        
        # Afficher l'erreur
        messagebox.showerror("Erreur de clonage", error_msg, parent=dialog)
    
    def create_commit(self):
        """Crée un commit pour le dépôt sélectionné"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Vérifier s'il y a des modifications à commiter
        os.chdir(self.current_repo["local_path"])
        
        # Obtenir le statut des fichiers
        diffs = self.git_repo.git.status(porcelain=True)
        if not diffs:
            messagebox.showinfo("Information", "Aucune modification à commiter")
            return
        
        # Créer la boîte de dialogue pour le commit
        dialog = tk.Toplevel(self.root)
        dialog.title("Créer un commit")
        dialog.geometry("800x700")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Créer un nouveau commit", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Liste des fichiers modifiés
        files_frame = ttk.LabelFrame(main_frame, text="Fichiers modifiés", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tableau des fichiers avec cases à cocher
        columns = ("status", "path")
        files_tree = ttk.Treeview(files_list_frame, columns=columns, show="headings", height=10)
        files_tree.heading("status", text="État")
        files_tree.heading("path", text="Fichier")
        files_tree.column("status", width=100)
        files_tree.column("path", width=400)
        
        files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient="vertical", command=files_tree.yview)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        # Variables pour les cases à cocher
        file_vars = {}
        
        # Parser les fichiers modifiés et les ajouter à la liste
        status_codes = {
            "M ": "Modifié",
            " M": "Modifié",
            "MM": "Modifié",
            "A ": "Ajouté",
            "D ": "Supprimé",
            "R ": "Renommé",
            "C ": "Copié",
            "U ": "Conflit",
            "??": "Non suivi"
        }
        
        # Ajouter les fichiers à la liste
        for line in diffs.splitlines():
            if not line:
                continue
                
            status_code = line[:2]
            file_path = line[3:].strip()
            
            # Si le fichier a un espace dans le nom, il sera entouré de guillemets
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
                
            status = status_codes.get(status_code, status_code)
            
            item_id = files_tree.insert("", "end", values=(status, file_path))
            # Par défaut, tous les fichiers sont sélectionnés
            files_tree.selection_add(item_id)
        
        # Boutons pour sélectionner/désélectionner tous les fichiers
        select_frame = ttk.Frame(files_frame)
        select_frame.pack(fill=tk.X, pady=(0, 5))
        
        select_all_btn = ModernButton(select_frame, text="Tout sélectionner", 
                                   command=lambda: files_tree.selection_set(files_tree.get_children()),
                                   width=150, height=32, bg_color=COLORS['primary'])
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        deselect_all_btn = ModernButton(select_frame, text="Tout désélectionner", 
                                      command=lambda: files_tree.selection_remove(files_tree.get_children()),
                                      width=150, height=32, bg_color=COLORS['secondary'])
        deselect_all_btn.pack(side=tk.LEFT)
        
        # Message de commit
        message_frame = ttk.LabelFrame(main_frame, text="Message du commit", padding="10")
        message_frame.pack(fill=tk.X, pady=(0, 15))
        
        message_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, width=70, height=5)
        message_text.pack(fill=tk.X, expand=True)
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = ModernButton(button_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'])
        cancel_btn.pack(side=tk.RIGHT)
        
        commit_btn = ModernButton(button_frame, text="Créer le commit", 
                               command=lambda: self.do_create_commit(
                                   [files_tree.item(item, "values")[1] for item in files_tree.selection()],
                                   message_text.get("1.0", tk.END).strip(),
                                   dialog
                               ),
                               width=150, height=40, bg_color=COLORS['primary'])
        commit_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def do_create_commit(self, selected_files, message, dialog):
        """Exécute la création du commit"""
        if not selected_files:
            messagebox.showerror("Erreur", "Veuillez sélectionner au moins un fichier", parent=dialog)
            return
        
        if not message:
            messagebox.showerror("Erreur", "Veuillez saisir un message de commit", parent=dialog)
            return
        
        dialog.destroy()
        self.operation_running = True
        self.status_label.config(text="Création du commit...")
        self.progress_bar["value"] = 20
        
        # Lancer la création du commit dans un thread
        threading.Thread(target=lambda: self._create_commit_thread(selected_files, message)).start()
    
    def _create_commit_thread(self, selected_files, message):
        """Thread pour créer un commit"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Ajouter les fichiers sélectionnés
            self.log("Ajout des fichiers au commit...", "info")
            for file_path in selected_files:
                self.git_repo.git.add(file_path)
            
            self.progress_bar["value"] = 60
            
            # Créer le commit
            self.log(f"Création du commit avec le message: {message}", "info")
            self.git_repo.git.commit('-m', message)
            
            self.progress_bar["value"] = 100
            self.log("Commit créé avec succès", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._commit_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._commit_error(str(e)))
    
    def _commit_completed(self):
        """Gère la fin d'un commit réussi"""
        self.operation_running = False
        self.status_label.config(text="Prêt")
        self.progress_bar["value"] = 0
        messagebox.showinfo("Succès", "Le commit a été créé avec succès")
    
    def _commit_error(self, error_msg):
        """Gère une erreur lors d'un commit"""
        self.operation_running = False
        self.status_label.config(text="Erreur")
        self.progress_bar["value"] = 0
        self.log(f"Erreur lors de la création du commit: {error_msg}", "error")
        messagebox.showerror("Erreur", f"Erreur lors de la création du commit: {error_msg}")
    
    def create_branch(self):
        """Crée une nouvelle branche"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Demander le nom de la branche
        branch_name = simpledialog.askstring("Nouvelle branche", "Nom de la nouvelle branche:", parent=self.root)
        if not branch_name:
            return
        
        # Vérifier si la branche existe déjà
        existing_branches = [b.name for b in self.git_repo.branches]
        if branch_name in existing_branches:
            messagebox.showerror("Erreur", f"La branche '{branch_name}' existe déjà")
            return
        
        # Demander si l'utilisateur veut basculer sur la nouvelle branche
        switch_to = messagebox.askyesno("Basculer", f"Basculer sur la nouvelle branche '{branch_name}' après sa création?")
        
        # Créer la branche dans un thread
        self.operation_running = True
        self.status_label.config(text="Création de la branche...")
        self.progress_bar["value"] = 20
        
        threading.Thread(target=lambda: self._create_branch_thread(branch_name, switch_to)).start()
    
    def _create_branch_thread(self, branch_name, switch_to):
        """Thread pour créer une nouvelle branche"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Créer la branche
            self.log(f"Création de la branche '{branch_name}'...", "info")
            current_branch = self.git_repo.active_branch.name
            
            # Créer à partir de la branche courante
            self.git_repo.git.branch(branch_name)
            
            self.progress_bar["value"] = 70
            
            # Basculer sur la nouvelle branche si demandé
            if switch_to:
                self.log(f"Basculement sur la branche '{branch_name}'...", "info")
                self.git_repo.git.checkout(branch_name)
            
            self.progress_bar["value"] = 100
            self.log(f"Branche '{branch_name}' créée avec succès", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._branch_operation_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._branch_operation_error(str(e)))
    
    def switch_branch(self):
        """Change de branche"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Récupérer la liste des branches
        branches = [b.name for b in self.git_repo.branches]
        
        if not branches:
            messagebox.showinfo("Information", "Aucune branche disponible")
            return
        
        # Créer la boîte de dialogue pour sélectionner une branche
        dialog = tk.Toplevel(self.root)
        dialog.title("Changer de branche")
        dialog.geometry("600x500")  # Dimensions augmentées
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Sélectionner une branche", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Liste des branches
        branch_frame = ttk.Frame(main_frame)
        branch_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Listbox avec scrollbar
        branch_list = tk.Listbox(branch_frame, height=15, width=50, font=Fonts.DEFAULT)
        branch_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(branch_frame, orient="vertical", command=branch_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        branch_list.configure(yscrollcommand=scrollbar.set)
        
        # Remplir la liste des branches
        current_branch = self.git_repo.active_branch.name
        for i, branch in enumerate(branches):
            branch_list.insert(tk.END, branch)
            if branch == current_branch:
                branch_list.selection_set(i)
                branch_list.see(i)
                branch_list.itemconfig(i, bg=COLORS['primary_light'], fg=COLORS['primary_dark'])
        
        # Label pour afficher la branche actuelle
        current_label = ttk.Label(main_frame, text=f"Branche actuelle: {current_branch}", font=Fonts.DEFAULT)
        current_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        stash_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Mettre de côté les modifications non commitées", variable=stash_var).pack(anchor=tk.W)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = ModernButton(button_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'])
        cancel_btn.pack(side=tk.RIGHT)
        
        switch_btn = ModernButton(button_frame, text="Changer", 
                               command=lambda: self.do_switch_branch(
                                   branches[branch_list.curselection()[0]] if branch_list.curselection() else None,
                                   stash_var.get(), dialog
                               ),
                               width=150, height=40, bg_color=COLORS['primary'])
        switch_btn.pack(side=tk.RIGHT, padx=(0, 12))
        
        # Double-clic pour changer de branche
        branch_list.bind("<Double-Button-1>", lambda e: self.do_switch_branch(
            branches[branch_list.curselection()[0]] if branch_list.curselection() else None,
            stash_var.get(), dialog
        ))
    
    def do_switch_branch(self, branch_name, stash, dialog):
        """Effectue le changement de branche"""
        if not branch_name:
            messagebox.showerror("Erreur", "Veuillez sélectionner une branche", parent=dialog)
            return
        
        # Vérifier si c'est la branche actuelle
        current_branch = self.git_repo.active_branch.name
        if branch_name == current_branch:
            messagebox.showinfo("Information", f"Vous êtes déjà sur la branche '{branch_name}'", parent=dialog)
            dialog.destroy()
            return
        
        dialog.destroy()
        self.operation_running = True
        self.status_label.config(text="Changement de branche...")
        self.progress_bar["value"] = 20
        
        # Lancer l'opération dans un thread
        threading.Thread(target=lambda: self._switch_branch_thread(branch_name, stash)).start()
    
    def _switch_branch_thread(self, branch_name, stash):
        """Thread pour changer de branche"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Vérifier s'il y a des modifications non commitées
            if self.git_repo.is_dirty():
                if stash:
                    self.log("Mise de côté des modifications non commitées...", "info")
                    self.git_repo.git.stash('save', f'Auto-stash avant de basculer sur {branch_name}')
                else:
                    raise Exception("Il y a des modifications non commitées. Veuillez les commiter ou utiliser l'option de mise de côté.")
            
            self.progress_bar["value"] = 50
            
            # Changer de branche
            self.log(f"Basculement sur la branche '{branch_name}'...", "info")
            self.git_repo.git.checkout(branch_name)
            
            self.progress_bar["value"] = 100
            self.log(f"Changement de branche réussi. Branche actuelle: {branch_name}", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._branch_operation_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._branch_operation_error(str(e)))
    
    def delete_branch(self):
        """Supprime une branche"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Récupérer la liste des branches
        branches = [b.name for b in self.git_repo.branches]
        current_branch = self.git_repo.active_branch.name
        
        # Exclure la branche courante
        branches = [b for b in branches if b != current_branch]
        
        if not branches:
            messagebox.showinfo("Information", "Aucune branche disponible à supprimer")
            return
        
        # Créer la boîte de dialogue pour sélectionner une branche
        dialog = tk.Toplevel(self.root)
        dialog.title("Supprimer une branche")
        dialog.geometry("600x500")  # Dimensions augmentées
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Sélectionner une branche à supprimer", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Liste des branches
        branch_frame = ttk.Frame(main_frame)
        branch_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Listbox avec scrollbar
        branch_list = tk.Listbox(branch_frame, height=15, width=50, font=Fonts.DEFAULT)
        branch_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(branch_frame, orient="vertical", command=branch_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        branch_list.configure(yscrollcommand=scrollbar.set)
        
        # Remplir la liste des branches
        for branch in branches:
            branch_list.insert(tk.END, branch)
        
        # Label pour afficher la branche actuelle
        current_label = ttk.Label(main_frame, text=f"Branche actuelle: {current_branch} (non supprimable)", font=Fonts.DEFAULT)
        current_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Forcer la suppression (même si non fusionnée)", variable=force_var).pack(anchor=tk.W)
        
        remote_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Supprimer également la branche distante", variable=remote_var).pack(anchor=tk.W)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = ModernButton(button_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'])
        cancel_btn.pack(side=tk.RIGHT)
        
        delete_btn = ModernButton(button_frame, text="Supprimer", 
                               command=lambda: self.do_delete_branch(
                                   branches[branch_list.curselection()[0]] if branch_list.curselection() else None,
                                   force_var.get(), remote_var.get(), dialog
                               ),
                               width=150, height=40, bg_color=COLORS['error'])
        delete_btn.pack(side=tk.RIGHT, padx=(0, 12))
    
    def do_delete_branch(self, branch_name, force, remote, dialog):
        """Effectue la suppression de la branche"""
        if not branch_name:
            messagebox.showerror("Erreur", "Veuillez sélectionner une branche", parent=dialog)
            return
        
        # Demander confirmation
        if not messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la branche '{branch_name}'?", parent=dialog):
            return
        
        dialog.destroy()
        self.operation_running = True
        self.status_label.config(text="Suppression de la branche...")
        self.progress_bar["value"] = 20
        
        # Lancer l'opération dans un thread
        threading.Thread(target=lambda: self._delete_branch_thread(branch_name, force, remote)).start()
    
    def _delete_branch_thread(self, branch_name, force, remote):
        """Thread pour supprimer une branche"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Supprimer la branche locale
            self.log(f"Suppression de la branche locale '{branch_name}'...", "info")
            
            if force:
                self.git_repo.git.branch('-D', branch_name)
            else:
                self.git_repo.git.branch('-d', branch_name)
            
            self.progress_bar["value"] = 60
            
            # Supprimer la branche distante si demandé
            if remote:
                self.log(f"Suppression de la branche distante '{branch_name}'...", "info")
                self.git_repo.git.push('origin', '--delete', branch_name)
            
            self.progress_bar["value"] = 100
            self.log(f"Branche '{branch_name}' supprimée avec succès", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._branch_operation_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._branch_operation_error(str(e)))
    
    def _branch_operation_completed(self):
        """Gère la fin d'une opération sur les branches réussie"""
        self.operation_running = False
        self.status_label.config(text="Prêt")
    
    def _branch_operation_error(self, error_msg):
        """Gère une erreur lors d'une opération sur les branches"""
        self.operation_running = False
        self.status_label.config(text="Erreur")
        self.progress_bar["value"] = 0
        self.log(f"Erreur: {error_msg}", "error")
        messagebox.showerror("Erreur", error_msg)
    
    def merge_branches(self):
        """Fusionne les branches pour le dépôt sélectionné"""
        # Implémentation de la fusion des branches
        pass
    
    def pull_changes(self):
        """Pull les changements pour le dépôt sélectionné"""
        # Implémentation de la mise à jour du dépôt
        pass
    
    def show_commit_history(self):
        """Affiche l'historique des commits"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Créer la fenêtre d'historique
        history_window = tk.Toplevel(self.root)
        history_window.title("Historique des commits")
        history_window.geometry("1100x820")  # Hauteur encore augmentée
        history_window.transient(self.root)
        history_window.grab_set()
        history_window.configure(bg=COLORS['bg_light'])
        
        # Centrer la fenêtre
        self.center_window(history_window)
        
        # Frame principal avec moins de padding pour maximiser l'espace
        main_frame = ttk.Frame(history_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre avec moins d'espace vertical
        title_label = ttk.Label(main_frame, text="Historique des commits", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Informations sur le dépôt - plus compact
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        branch_label = ttk.Label(info_frame, text=f"Branche: {self.git_repo.active_branch.name}", font=Fonts.DEFAULT)
        branch_label.pack(side=tk.LEFT)
        
        # Options de filtrage plus compactes
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Layout horizontal pour économiser de l'espace vertical
        filters_container = ttk.Frame(filter_frame)
        filters_container.pack(fill=tk.X, pady=2)
        
        # Premier conteneur pour auteur et message
        filters_row1 = ttk.Frame(filters_container)
        filters_row1.pack(fill=tk.X, pady=2)
        
        author_frame = ttk.Frame(filters_row1)
        author_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(author_frame, text="Auteur:").pack(side=tk.LEFT, padx=(0, 5))
        author_var = tk.StringVar()
        author_entry = ttk.Entry(author_frame, textvariable=author_var, width=20)
        author_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        message_frame = ttk.Frame(filters_row1)
        message_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(message_frame, text="Message:").pack(side=tk.LEFT, padx=(0, 5))
        message_var = tk.StringVar()
        message_entry = ttk.Entry(message_frame, textvariable=message_var, width=20)
        message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Deuxième ligne avec nombre de commits et bouton
        filters_row2 = ttk.Frame(filters_container)
        filters_row2.pack(fill=tk.X, pady=2)
        
        limit_frame = ttk.Frame(filters_row2)
        limit_frame.pack(side=tk.LEFT, fill=tk.X)
        ttk.Label(limit_frame, text="Nombre de commits:").pack(side=tk.LEFT, padx=(0, 5))
        limit_var = tk.StringVar(value="50")
        limit_entry = ttk.Entry(limit_frame, textvariable=limit_var, width=8)
        limit_entry.pack(side=tk.LEFT)
        
        # Bouton d'application des filtres
        filter_btn = ModernButton(filters_row2, text="Appliquer les filtres", 
                               command=lambda: self.load_commit_history(
                                   history_list, author_var.get(), message_var.get(), limit_var.get()
                               ),
                               width=150, height=30, bg_color=COLORS['primary'])
        filter_btn.pack(side=tk.RIGHT, pady=(2, 0))
        
        # Conteneur principal en deux parties
        main_container = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        main_container.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Liste des commits - hauteur réduite significativement
        list_frame = ttk.Frame(main_container)
        main_container.add(list_frame, weight=1)
        
        columns = ("hash", "author", "date", "message")
        history_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)  # Hauteur réduite
        
        # En-têtes
        history_list.heading("hash", text="Hash")
        history_list.heading("author", text="Auteur")
        history_list.heading("date", text="Date")
        history_list.heading("message", text="Message")
        
        # Largeur des colonnes
        history_list.column("hash", width=80)
        history_list.column("author", width=150)
        history_list.column("date", width=150)
        history_list.column("message", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=history_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_list.configure(yscrollcommand=scrollbar.set)
        history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Zone de détails du commit
        details_frame = ttk.LabelFrame(main_frame, text="Détails du commit", padding="5")
        details_frame.pack(fill=tk.X, pady=(0, 5))
        
        details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=7)  # Hauteur réduite
        details_text.pack(fill=tk.BOTH)
        details_text.config(state=tk.DISABLED)
        
        # Fonction pour afficher les détails d'un commit
        def show_commit_details(event):
            selection = history_list.selection()
            if not selection:
                return
            
            item = selection[0]
            commit_hash = history_list.item(item, "values")[0]
            
            try:
                commit = self.git_repo.commit(commit_hash)
                
                details = f"Commit: {commit.hexsha}\n"
                details += f"Auteur: {commit.author.name} <{commit.author.email}>\n"
                details += f"Date: {datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')}\n"
                details += f"Message:\n{commit.message}\n\n"
                
                details += "Fichiers modifiés:\n"
                for parent in commit.parents:
                    for diff in parent.diff(commit):
                        details += f"- {diff.a_path}\n"
                
                details_text.config(state=tk.NORMAL)
                details_text.delete(1.0, tk.END)
                details_text.insert(tk.END, details)
                details_text.config(state=tk.DISABLED)
            except Exception as e:
                details_text.config(state=tk.NORMAL)
                details_text.delete(1.0, tk.END)
                details_text.insert(tk.END, f"Erreur lors de la récupération des détails: {str(e)}")
                details_text.config(state=tk.DISABLED)
        
        # Lier l'événement de sélection
        history_list.bind("<<TreeviewSelect>>", show_commit_details)
        
        # Boutons d'action plus petits et compacts
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10))  # Padding vertical augmenté
        
        close_btn = ModernButton(button_frame, text="Fermer", command=history_window.destroy,
                              width=110, height=36, bg_color=COLORS['bg_dark'])  # Boutons un peu plus grands
        close_btn.pack(side=tk.RIGHT)
        
        tag_btn = ModernButton(button_frame, text="Créer un tag", 
                            command=lambda: self.create_tag_from_commit(
                                history_list.item(history_list.selection()[0], "values")[0] if history_list.selection() else None
                            ),
                            width=110, height=36, bg_color=COLORS['primary'])  # Boutons un peu plus grands
        tag_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Charger l'historique
        self.load_commit_history(history_list, "", "", "50")
    
    def load_commit_history(self, history_list, author, message, limit):
        """Charge l'historique des commits avec les filtres spécifiés"""
        # Vider la liste
        for item in history_list.get_children():
            history_list.delete(item)
        
        try:
            # Convertir la limite en entier
            try:
                limit_int = int(limit)
            except ValueError:
                limit_int = 50
                
            # Utiliser l'API GitPython directement au lieu de la commande git externe
            commits = []
            try:
                # Obtenir les commits à partir de l'API GitPython
                commit_iterator = self.git_repo.iter_commits(max_count=limit_int)
                
                # Appliquer les filtres si nécessaire
                if author or message:
                    filtered_commits = []
                    for commit in commit_iterator:
                        # Filtrer par auteur si spécifié
                        if author and author.lower() not in commit.author.name.lower():
                            continue
                            
                        # Filtrer par message si spécifié
                        if message and message.lower() not in commit.message.lower():
                            continue
                            
                        filtered_commits.append(commit)
                        if len(filtered_commits) >= limit_int:
                            break
                    commits = filtered_commits
                else:
                    # Pas de filtre, prendre tous les commits
                    commits = list(commit_iterator)
                    
                # Ajouter les commits à la liste
                for commit in commits:
                    # Formater la date
                    commit_date = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
                    # Ajouter à la liste
                    history_list.insert("", "end", values=(
                        commit.hexsha[:8],
                        commit.author.name,
                        commit_date,
                        commit.message.split('\n')[0]  # Prendre seulement la première ligne du message
                    ))
                
                if not commits:
                    messagebox.showinfo("Information", "Aucun commit trouvé avec ces critères")
                    
            except Exception as api_error:
                # Si l'API GitPython échoue, afficher un message d'erreur plus informatif
                error_msg = f"Erreur lors de l'accès à l'historique Git: {str(api_error)}"
                self.log(error_msg, "error")
                messagebox.showerror("Erreur", error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement de l'historique: {str(e)}"
            self.log(error_msg, "error")
            messagebox.showerror("Erreur", error_msg)
    
    def create_tag_from_commit(self, commit_hash):
        """Crée un tag à partir d'un commit spécifique"""
        if not commit_hash:
            messagebox.showerror("Erreur", "Veuillez sélectionner un commit")
            return
        
        # Demander le nom du tag
        tag_name = simpledialog.askstring("Nouveau tag", "Nom du tag:", parent=self.root)
        if not tag_name:
            return
        
        # Demander un message pour le tag
        tag_message = simpledialog.askstring("Message du tag", "Message (optionnel):", parent=self.root)
        
        # Demander si on veut pousser le tag
        push_tag = messagebox.askyesno("Pousser le tag", "Voulez-vous pousser ce tag vers le dépôt distant?")
        
        try:
            os.chdir(self.current_repo["local_path"])
            
            # Créer le tag
            if tag_message:
                self.git_repo.git.tag('-a', tag_name, commit_hash, '-m', tag_message)
            else:
                self.git_repo.git.tag(tag_name, commit_hash)
            
            self.log(f"Tag '{tag_name}' créé sur le commit {commit_hash}", "success")
            
            # Pousser le tag si demandé
            if push_tag:
                self.git_repo.git.push('origin', tag_name)
                self.log(f"Tag '{tag_name}' poussé vers le dépôt distant", "success")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du tag: {str(e)}")
    
    def create_tag(self):
        """Crée un tag sur le commit actuel (HEAD)"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Afficher la boîte de dialogue pour créer un tag
        dialog = tk.Toplevel(self.root)
        dialog.title("Créer un tag")
        dialog.geometry("600x400")  # Dimensions augmentées
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Créer un nouveau tag", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Formulaire
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Nom du tag
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Nom du tag:").pack(side=tk.LEFT, padx=(0, 5))
        name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=name_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Message du tag
        message_frame = ttk.Frame(form_frame)
        message_frame.pack(fill=tk.X, pady=5)
        ttk.Label(message_frame, text="Message:").pack(anchor=tk.W)
        message_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, width=50, height=5)
        message_text.pack(fill=tk.X, pady=(5, 0))
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        push_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Pousser le tag vers le dépôt distant", variable=push_var).pack(anchor=tk.W)
        
        lightweight_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Tag léger (sans message)", variable=lightweight_var).pack(anchor=tk.W)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        cancel_btn = ModernButton(button_frame, text="Annuler", command=dialog.destroy,
                               width=150, height=40, bg_color=COLORS['bg_dark'])
        cancel_btn.pack(side=tk.RIGHT)
        
        create_btn = ModernButton(button_frame, text="Créer", 
                               command=lambda: self.do_create_tag(
                                   name_var.get(), message_text.get("1.0", tk.END).strip(),
                                   lightweight_var.get(), push_var.get(), dialog
                               ),
                               width=150, height=40, bg_color=COLORS['primary'])
        create_btn.pack(side=tk.RIGHT, padx=(0, 12))
    
    def do_create_tag(self, name, message, lightweight, push, dialog):
        """Crée effectivement le tag"""
        if not name:
            messagebox.showerror("Erreur", "Le nom du tag est obligatoire", parent=dialog)
            return
        
        if not lightweight and not message:
            messagebox.showerror("Erreur", "Le message est obligatoire pour un tag annoté", parent=dialog)
            return
        
        dialog.destroy()
        self.operation_running = True
        self.status_label.config(text="Création du tag...")
        self.progress_bar["value"] = 20
        
        # Lancer l'opération dans un thread
        threading.Thread(target=lambda: self._create_tag_thread(name, message, lightweight, push)).start()
    
    def _create_tag_thread(self, name, message, lightweight, push):
        """Thread pour créer un tag"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Créer le tag
            if lightweight:
                self.log(f"Création d'un tag léger '{name}'...", "info")
                self.git_repo.git.tag(name)
            else:
                self.log(f"Création d'un tag annoté '{name}'...", "info")
                self.git_repo.git.tag('-a', name, '-m', message)
            
            self.progress_bar["value"] = 60
            
            # Pousser le tag si demandé
            if push:
                self.log(f"Push du tag '{name}' vers le dépôt distant...", "info")
                self.git_repo.git.push('origin', name)
            
            self.progress_bar["value"] = 100
            self.log(f"Tag '{name}' créé avec succès", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._tag_operation_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._tag_operation_error(str(e)))
    
    def _tag_operation_completed(self):
        """Gère la fin d'une opération de tag réussie"""
        self.operation_running = False
        self.status_label.config(text="Prêt")
    
    def _tag_operation_error(self, error_msg):
        """Gère une erreur lors d'une opération de tag"""
        self.operation_running = False
        self.status_label.config(text="Erreur")
        self.progress_bar["value"] = 0
        self.log(f"Erreur lors de la création du tag: {error_msg}", "error")
        messagebox.showerror("Erreur", f"Erreur lors de la création du tag: {error_msg}")
    
    def _disable_widget_safely(self, widget):
        """Désactive un widget de manière sécurisée en vérifiant son type"""
        try:
            # Pour les ModernButton personnalisés
            if isinstance(widget, ModernButton):
                widget.configure(state=tk.DISABLED)
            # Pour les widgets standard de tkinter qui supportent l'état
            elif hasattr(widget, 'configure') and isinstance(widget, (tk.Button, ttk.Button, tk.Entry, ttk.Entry)):
                widget.configure(state=tk.DISABLED)
            # Pour les conteneurs, on parcourt récursivement leurs enfants
            elif hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    self._disable_widget_safely(child)
        except Exception as e:
            # Ignorer silencieusement les erreurs liées aux widgets qui ne supportent pas cette configuration
            pass

    def center_window(self, window=None):
        """Centre une fenêtre sur l'écran"""
        if window is None:
            window = self.root
        
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def log(self, message, message_type="info"):
        """Ajoute un message au journal avec style amélioré"""
        now = datetime.now().strftime("%H:%M:%S")
        
        # Déterminer le style du message
        if message_type == "info":
            tag = "info"
            prefix = "INFO"
        elif message_type == "error":
            tag = "error"
            prefix = "ERREUR"
        elif message_type == "success":
            tag = "success"
            prefix = "SUCCÈS"
        elif message_type == "warning":
            tag = "warning"
            prefix = "ATTENTION"
        else:
            tag = "info"
            prefix = "INFO"
        
        # Ajouter le message au journal avec un format plus moderne et plus doux
        self.log_text.config(state=tk.NORMAL)
        
        # Ajouter l'horodatage avec style
        self.log_text.insert(tk.END, f"{now} ", "highlight")
        
        # Ajouter le préfixe avec le bon tag
        self.log_text.insert(tk.END, f"[{prefix}] ", tag)
        
        # Ajouter le message avec le bon tag
        self.log_text.insert(tk.END, f"{message}\n", tag)
        
        # Défiler vers le bas
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def resolve_conflicts(self):
        """Affiche les fichiers en conflit et propose des options pour les résoudre"""
        # Renomme cette fonction pour éviter un conflit de nommage
        return self._resolve_conflicts()
        
    def _resolve_conflicts(self):
        """Affiche les fichiers en conflit et propose des options pour les résoudre"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
        
        # Vérifier s'il y a des conflits
        unmerged_files = []
        try:
            unmerged_output = self.git_repo.git.execute(['ls-files', '--unmerged'])
            if not unmerged_output:
                messagebox.showinfo("Information", "Aucun conflit détecté")
                return
            
            # Parser la sortie pour extraire les fichiers uniques
            for line in unmerged_output.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    unmerged_files.append(' '.join(parts[3:]))
            
            unmerged_files = list(set(unmerged_files))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la détection des conflits: {str(e)}")
            return
        
        # Créer la boîte de dialogue pour résoudre les conflits
        dialog = tk.Toplevel(self.root)
        dialog.title("Résoudre les conflits")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS['bg_light'])
        
        # Centrer la boîte de dialogue
        self.center_window(dialog)
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Résoudre les conflits de fusion", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Liste des fichiers en conflit
        files_frame = ttk.LabelFrame(main_frame, text="Fichiers en conflit", padding="10")
        files_frame.pack(fill=tk.X, pady=(0, 15))
        
        files_list = tk.Listbox(files_frame, height=6, width=80, font=Fonts.DEFAULT)
        files_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=files_list.yview)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        files_list.configure(yscrollcommand=files_scrollbar.set)
        
        # Remplir la liste des fichiers en conflit
        for file in unmerged_files:
            files_list.insert(tk.END, file)
        
        # Informations
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        info_text = ttk.Label(info_frame, text="Sélectionnez un fichier puis choisissez une action pour résoudre le conflit.", 
                           wraplength=760, justify="left")
        info_text.pack(anchor=tk.W)
        
        # Actions
        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Boutons d'action pour résoudre les conflits
        open_btn = ModernButton(actions_frame, text="Ouvrir dans l'éditeur", 
                             command=lambda: self.open_conflict_file(files_list.get(files_list.curselection()[0]) if files_list.curselection() else None),
                             width=200, height=36, bg_color=COLORS['primary'])
        open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        keep_ours_btn = ModernButton(actions_frame, text="Garder notre version", 
                                  command=lambda: self.resolve_conflict_with(
                                      files_list.get(files_list.curselection()[0]) if files_list.curselection() else None, 
                                      "--ours", files_list, dialog
                                  ),
                                  width=200, height=36, bg_color=COLORS['success'])
        keep_ours_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        keep_theirs_btn = ModernButton(actions_frame, text="Garder leur version", 
                                    command=lambda: self.resolve_conflict_with(
                                        files_list.get(files_list.curselection()[0]) if files_list.curselection() else None, 
                                        "--theirs", files_list, dialog
                                    ),
                                    width=200, height=36, bg_color=COLORS['warning'])
        keep_theirs_btn.pack(side=tk.LEFT)
        
        # Boutons pour finaliser
        finish_frame = ttk.Frame(main_frame)
        finish_frame.pack(fill=tk.X, pady=(15, 0))
        
        cancel_btn = ModernButton(finish_frame, text="Annuler", 
                               command=lambda: self.abort_merge(dialog),
                               width=150, height=40, bg_color=COLORS['error'])
        cancel_btn.pack(side=tk.LEFT)
        
        continue_btn = ModernButton(finish_frame, text="Fermer", 
                                 command=dialog.destroy,
                                 width=150, height=40, bg_color=COLORS['bg_dark'])
        continue_btn.pack(side=tk.RIGHT)
        
        commit_btn = ModernButton(finish_frame, text="Finaliser la fusion", 
                               command=lambda: self.complete_merge(dialog),
                               width=200, height=40, bg_color=COLORS['primary'])
        commit_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def push_changes(self):
        """Push les changements vers le dépôt distant"""
        if not self.current_repo or not self.git_repo:
            messagebox.showinfo("Information", "Veuillez sélectionner un dépôt Git valide")
            return
            
        # Vérifier si un remote est configuré
        try:
            remotes = list(self.git_repo.remotes)
            if not remotes:
                messagebox.showerror("Erreur", "Aucun dépôt distant n'est configuré pour ce projet")
                return
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vérification des dépôts distants: {str(e)}")
            return
            
        # Demander confirmation
        current_branch = self.git_repo.active_branch.name
        if not messagebox.askyesno("Confirmation", f"Voulez-vous pousser la branche '{current_branch}' vers le dépôt distant?"):
            return
            
        # Démarrer l'opération
        self.operation_running = True
        self.status_label.config(text="Push en cours...")
        self.progress_bar["value"] = 20
        
        # Lancer dans un thread séparé
        threading.Thread(target=self._push_thread).start()
    
    def _push_thread(self):
        """Thread pour pousser les modifications"""
        try:
            # Aller dans le répertoire du dépôt
            os.chdir(self.current_repo["local_path"])
            
            # Obtenir la branche actuelle
            current_branch = self.git_repo.active_branch.name
            
            # Push vers le dépôt distant
            self.log(f"Push de la branche '{current_branch}' vers le dépôt distant...", "info")
            remote_name = self.git_repo.remotes[0].name
            
            # Exécuter le push
            output = self.git_repo.git.push(remote_name, current_branch)
            
            self.progress_bar["value"] = 100
            self.log("Push terminé avec succès", "success")
            
            # Mettre à jour l'interface
            self.root.after(0, self._push_completed)
            
        except Exception as e:
            self.root.after(0, lambda: self._push_error(str(e)))
    
    def _push_completed(self):
        """Gère la fin d'un push réussi"""
        self.operation_running = False
        self.status_label.config(text="Prêt")
    
    def _push_error(self, error_msg):
        """Gère une erreur lors d'un push"""
        self.operation_running = False
        self.status_label.config(text="Erreur")
        self.progress_bar["value"] = 0
        self.log(f"Erreur lors du push: {error_msg}", "error")
        messagebox.showerror("Erreur", f"Erreur lors du push: {error_msg}")

def main():
    root = tk.Tk()
    app = GitApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 