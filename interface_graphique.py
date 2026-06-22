"""
Intègre :
  - Modèles vectoriel (TF-IDF + cosinus) et booléen (ET / OU / SAUF)
  - Détection automatique du modèle ou choix manuel 
  - Correction orthographique (difflib)
  - les synonymes d'une requête données
  - Affichage des résultats avec l'interface graphique (PIL / Pillow)
  - Curseur de seuil de similarite pour filtrer dynamiquement les résultats
  - Courbe évaluation (rappel/précision) 
  - Historique des requêtes (historique.txt)
  - Suggestions de requêtes connexes (similarité cosinus sur l'historique)
  - Filtrage contextuel :les résultats correspondant à la requête données (avec le boutton Affiner (document) et Affichier(image))
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import difflib
import math
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")                       
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Pillow non installé — les miniatures seront désactivées.")
    print("Pour les activer : pip install Pillow")

# ── Imports du projet 
# On importe uniquement les fonctions dont on a besoin depuis chaque module.
# Cela évite de dupliquer la logique métier dans ce fichier.
from MoteurRecherche import (
    returned_documents,           
    vect_model_TF,                
    vect_model_IDF,              
    vect_model_mot_poids_final,   
    search_query,                
    modele_bool,                 
    bool_document,                
    vect_model_cosinus,          
)
from preTreatmentQuary import process_query_vect  
# CONSTANTES & CONFIGURATION

DOSSIER_IMAGES   = "files"          
FICHIER_HISTORIQUE = "historique.txt"  
THUMBNAIL_SIZE   = (90, 90)         

# Correspondance index (0-based) → nom de fichier source (sans extension).
# NOMS_FICHIERS[0] = "AI" correspond au document numéro 1.
NOMS_FICHIERS = [
    "AI", "cuisine", "football", "natation", "basket",
    "athlet", "art", "cinema", "cosmetique", "economie",
    "environnement", "politique", "litterateure", "psychologie",
    "sante", "technologie", "voyage", "music", "reseau", "vehicule"
]

SYNONYMES = {
    "intelligence":  ["ia", "artificielle", "cognitif"],
    "ia":            ["intelligence", "artificielle"],
    "cuisine":       ["gastronomie", "culinaire", "recette"],
    "football":      ["foot", "soccer", "ballon"],
    "foot":          ["football", "soccer"],
    "musique":       ["music", "chanson", "melodie", "rythme"],
    "sante":         ["medical", "medecine", "bien-etre", "hygiene"],
    "voyage":        ["tourisme", "deplacer", "explorer", "destination"],
    "cinema":        ["film", "movie", "pellicule", "realisateur"],
    "art":           ["peinture", "sculpture", "creativite", "tableau"],
    "technologie":   ["tech", "numerique", "digital", "innovation"],
    "economie":      ["finance", "marche", "bourse", "commerce"],
    "sport":         ["athletisme", "competition", "entrainement"],
    "natation":      ["nage", "piscine", "aquatique"],
    "psychologie":   ["mental", "comportement", "therapie"],
    "environnement": ["ecologie", "nature", "climat", "planete"],
}

# Mots-clés par catégorie d'intention.
# L'intersection entre les mots de la requête et ces ensembles détermine l'intention.
INTENTION_INFO  = {"comment", "pourquoi", "qu", "definition", "expliquer",
                   "comprendre", "kesako", "signifie", "signification"}
INTENTION_NAVIG = {"site", "page", "accueil", "officiel", "url", "lien", "aller", "adresse"}
INTENTION_TRANS = {"acheter", "commande", "reservation", "prix", "tarif",
                   "telecharger", "inscription", "abonner", "payer"}

# Jeu de tests prédéfini pour l'évaluation automatique.
# Format : (requête, ensemble des numéros de documents pertinents)
TESTS_EVALUATION = [
    ("intelligence",   {1}),
    ("cuisine",        {2}),
    ("football",       {3}),
    ("natation",       {4}),
    ("basket",         {5}),
    ("art",            {7}),
    ("cinema",         {8}),
    ("economie",       {10}),
    ("environnement",  {11}),
    ("politique",      {12}),
    ("sante",          {15}),
    ("technologie",    {16}),
    ("voyage",         {17}),
]

# On charge tous les modèles ici, en dehors de la classe, pour éviter de les
# recalculer à chaque recherche. C'est le même principe que le "warmup" en prod.

print(" Chargement des documents et des modèles…")

docs       = returned_documents()               # Liste de dicts [{mot: freq}, ...]
TF         = vect_model_TF()                    # Liste de dicts [{mot: tf}, ...]
IDF        = vect_model_IDF()                   # Dict {mot: idf_value}
TF_IDF     = vect_model_mot_poids_final(TF, IDF)# Liste de dicts [{mot: tfidf}, ...]
BOOL_INDEX = bool_document(docs)                # Dict {mot: {doc1, doc2, ...}}

# Le vocabulaire = l'ensemble de tous les termes connus (présents dans l'IDF).
# Il sert de référence pour la correction orthographique.
VOCABULAIRE = set(IDF.keys())

print(f" {len(docs)} documents chargés — {len(VOCABULAIRE)} termes dans le vocabulaire.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – FONCTIONS UTILITAIRES (indépendantes de l'interface)
# ═══════════════════════════════════════════════════════════════════════════════

def detecter_modele(requete: str) -> str:
    """
    Analyse les mots de la requête.
    Retourne 'bool' si ET, OU ou SAUF apparaît (insensible à la casse),
    sinon retourne 'vect'.

    Exemple :
      "intelligence ET ia"   → 'bool'
      "cuisine gastronomie"  → 'vect'
    """
    mots = requete.upper().split()
    if any(op in mots for op in ["ET", "OU", "SAUF"]):
        return "bool"
    return "vect"


def corriger_requete(requete: str, vocabulaire: set) -> tuple:
    """
    Pour chaque mot de la requête (hors opérateurs booléens) absent du vocabulaire,
    cherche la correspondance la plus proche avec difflib.get_close_matches.

    Paramètres de get_close_matches :
      - n=1      : on veut au plus une suggestion
      - cutoff=0.75 : similarité minimale (75%) — assez strict pour éviter les faux positifs

    Retourne :
      - requete_corrigee (str) : requête avec les mots remplacés si une correction existe
      - corrections (list)     : liste de tuples (mot_original, mot_corrigé)

    Exemple :
      "inteligence" → "intelligence"  (correction automatique)
      "xyztqr"      → "xyztqr"        (aucune correspondance assez proche)
    """
    operateurs = {"et", "ou", "sauf"}
    mots = requete.lower().split()
    corrections = []
    mots_corriges = []

    for mot in mots:
        if mot in operateurs or mot in vocabulaire:
            # Mot déjà connu : on ne touche à rien
            mots_corriges.append(mot)
        else:
            suggestions = difflib.get_close_matches(mot, vocabulaire, n=1, cutoff=0.75)
            if suggestions:
                corrections.append((mot, suggestions[0]))
                mots_corriges.append(suggestions[0])
            else:
                # Aucune correction possible : on garde tel quel
                mots_corriges.append(mot)

    return " ".join(mots_corriges), corrections


def expand_requete(requete: str, synonymes: dict) -> str:
    """
    Pour chaque mot de la requête présent dans le dictionnaire SYNONYMES,
    ajoute ses synonymes en fin de requête.

    Note académique vs réalité :
      - En théorie, on devrait appliquer un coefficient réduit aux synonymes
        (ex: poids × 0.5) dans le vecteur requête.
      - En pratique ici, on les concatène simplement : leur TF sera naturellement
        faible (1 occurrence sur N mots) ce qui leur donne un poids moindre.

    Exemple :
      "intelligence cuisine" → "intelligence cuisine ia artificielle cognitif gastronomie culinaire recette"
    """
    mots = requete.lower().split()
    ajouts = []
    for mot in mots:
        if mot in synonymes:
            ajouts.extend(synonymes[mot])

    if ajouts:
        return requete + " " + " ".join(ajouts)
    return requete


def detecter_intention(requete: str) -> str:
    """
    Détecte l'intention de recherche à partir des mots-clés de la requête.
    Trois catégories possibles (du plus spécifique au plus général) :
      - transactionnelle : l'utilisateur veut effectuer une action (acheter, s'inscrire…)
      - navigationnelle  : l'utilisateur cherche un endroit précis (site, page…)
      - informationnelle : l'utilisateur veut comprendre ou apprendre
      - générale         : aucun signal particulier

    L'ordre de priorité : transactionnelle > navigationnelle > informationnelle.
    """
    mots = set(requete.lower().split())
    if mots & INTENTION_TRANS:
        return "transactionnelle"
    if mots & INTENTION_NAVIG:
        return "navigationnelle"
    if mots & INTENTION_INFO:
        return "informationnelle"
    return "🔍"


def charger_historique() -> list:
    """
    Lit historique.txt et retourne une liste des requêtes récentes.
    Format de chaque ligne : "requête | YYYY-MM-DD HH:MM:SS"
    On extrait uniquement la partie avant le séparateur |.
    On limite à 100 entrées pour éviter des fichiers trop longs.
    """
    if not os.path.exists(FICHIER_HISTORIQUE):
        return []
    with open(FICHIER_HISTORIQUE, "r", encoding="utf-8") as f:
        lignes = [l.strip() for l in f if l.strip()]

    requetes = []
    for ligne in lignes:
        parts = ligne.split("|")
        requetes.append(parts[0].strip())
    return requetes[-100:]  # Fenêtre glissante des 100 dernières


def sauvegarder_historique(requete: str):
    """
    Ajoute la requête au fichier historique avec un horodatage.
    Le mode 'a' (append) évite d'écraser les entrées précédentes.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FICHIER_HISTORIQUE, "a", encoding="utf-8") as f:
        f.write(f"{requete} | {ts}\n")


def suggestions_connexes(requete: str, historique: list, idf: dict, n: int = 3) -> list:
    """
    Trouve les n requêtes de l'historique les plus similaires à la requête courante
    en utilisant la similarité cosinus dans l'espace TF-IDF.

    Algorithme :
      1. Construire le vecteur TF-IDF de la requête courante.
      2. Pour chaque requête unique de l'historique (≠ requête courante),
         construire son vecteur TF-IDF.
      3. Calculer cos(vecteur_courant, vecteur_hist) et trier.

    Pourquoi TF-IDF et non TF seul ?
      L'IDF pénalise les mots très fréquents dans le corpus (mots banals),
      ce qui rend la comparaison plus significative.
    """
    def vecteur(q: str) -> dict:
        """Construit le vecteur TF-IDF d'une requête."""
        mots = process_query_vect(q)
        if not mots:
            return {}
        total = len(mots)
        freq = {}
        for m in mots:
            freq[m] = freq.get(m, 0) + 1
        tf = {m: c / total for m, c in freq.items()}
        return {m: tf[m] * idf.get(m, 0) for m in tf}

    vec_courant = vecteur(requete)
    if not vec_courant:
        return []

    scores = []
    vus = set()
    for hist_q in historique:
        cle = hist_q.lower()
        if cle == requete.lower() or cle in vus:
            continue
        vus.add(cle)
        vec_h = vecteur(hist_q)
        if vec_h:
            score = vect_model_cosinus(vec_courant, vec_h)
            if score > 0:
                scores.append((hist_q, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [q for q, _ in scores[:n]]


def charger_miniature(nom_base: str) -> object:
    """
    Tente de charger l'image files/<nom_base>.jpg (ou .jpeg, .png).
    Redimensionne à THUMBNAIL_SIZE et retourne un objet ImageTk.PhotoImage.
    Retourne None si PIL est indisponible ou si le fichier n'existe pas.

    Pourquoi conserver la référence ?
      Tkinter ne garde pas de référence forte aux images PIL.
      Si on ne stocke pas l'objet PhotoImage, le garbage collector Python
      le supprime et l'image disparaît à l'écran. C'est un piège classique.
    """
    if not PIL_AVAILABLE:
        return None
    for ext in [".jpg", ".jpeg", ".png"]:
        chemin = os.path.join(DOSSIER_IMAGES, nom_base + ext)
        if os.path.exists(chemin):
            try:
                img = Image.open(chemin).resize(THUMBNAIL_SIZE, Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Impossible de charger {chemin} : {e}")
                return None
    return None

class AppRecherche(tk.Tk):
    """
    Fenêtre principale de l'application.

    On hérite directement de tk.Tk pour que l'instance soit elle-même
    la fenêtre racine — ce qui évite d'avoir à gérer un objet 'root' séparé.

    Architecture :
      - _construire_interface() : crée tous les widgets
      - _lancer_recherche()     : pipeline complet de recherche
      - _filtrer_resultats()    : réaffichage dynamique selon le seuil
      - _afficher_resultats()   : rendu visuel des cartes de résultats
      - _ouvrir_evaluation()    : fenêtre d'évaluation avec courbe P-R
      - _afficher_historique()  : fenêtre de consultation de l'historique
      - Filtrage contextuel     : _selectionner_doc(), _appliquer_contexte()
    """

    def __init__(self):
        super().__init__()
        self.title(" Moteur de Recherche Documentaire")
        self.geometry("900x900")
        self.configure(bg="#f0f4f8")
        self.resizable(True, True)

        # ── Variables d'état de l'interface ─────────────────────────────────
        # quand leur valeur change, les widgets liés se mettent à jour automatiquement.

        self.modele_force = tk.StringVar(value="auto")
        # 'auto' = détection automatique, 'vect' = vectoriel forcé, 'bool' = booléen forcé

        self.seuil_var = tk.DoubleVar(value=0.0)
        # Seuil de score minimum pour l'affichage des résultats

        # ── Données internes ─────────────────────────────────────────────────
        self.historique = charger_historique()
        self.poids_contexte: dict = {}   # {mot: bonus_poids} pour le filtrage contextuel
        self._thumbnails: list = []      # Références PIL pour éviter le GC (voir charger_miniature)
        self._resultats_courants: list = []  # Cache des résultats de la dernière recherche
        self._modele_courant: str = "vect"

        self._construire_interface()

    def _construire_interface(self):
        """
        Construit la hiérarchie complète des widgets.
        Organisation :
          [Titre]
          [Zone saisie : champ + bouton rechercher]
          [Choix du modèle : boutons radio]
          [Curseur de seuil]
          [Label info : modèle utilisé, intention, corrections]
          [Label suggestions connexes]
          [Séparateur]
          [Zone résultats scrollable]
          [Barre de boutons en bas]
        """

        # ── Titre ────────────────────────────────────────────────────────────
        tk.Label(self,
                 text="Moteur de Recherche Documentaire",
                 font=("Helvetica", 18, "bold"),
                 bg="#f0f4f8", fg="#2c3e50"
                 ).pack(pady=(14, 4))

        # ── Zone de saisie ───────────────────────────────────────────────────
        frame_saisie = tk.Frame(self, bg="#f0f4f8")
        frame_saisie.pack(fill="x", padx=20, pady=4)

        tk.Label(frame_saisie, text="Requête :",
                 font=("Helvetica", 11), bg="#f0f4f8"
                 ).grid(row=0, column=0, sticky="w")

        self.champ_requete = tk.Entry(
            frame_saisie, font=("Helvetica", 13), width=52,
            relief="solid", bd=1
        )
        self.champ_requete.grid(row=0, column=1, padx=8, ipady=5)
        # Lier la touche Entrée à la recherche — UX plus naturelle
        self.champ_requete.bind("<Return>", lambda e: self._lancer_recherche())

        tk.Button(
            frame_saisie, text="🔍 Rechercher",
            font=("Helvetica", 11, "bold"),
            bg="#3498db", fg="white", relief="flat", padx=10,
            activebackground="#2980b9",
            command=self._lancer_recherche
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            frame_saisie, text="✖ Effacer",
            font=("Helvetica", 10),
            bg="#ecf0f1", relief="flat", padx=6,
            command=lambda: (self.champ_requete.delete(0, tk.END),
                             self._vider_resultats())
        ).grid(row=0, column=3, padx=2)

        # ── Choix du modèle (boutons radio) ──────────────────────────────────
        frame_modele = tk.Frame(self, bg="#f0f4f8")
        frame_modele.pack(fill="x", padx=22, pady=(4, 0))

        tk.Label(frame_modele, text="Modèle :",
                 font=("Helvetica", 10), bg="#f0f4f8"
                 ).pack(side="left")

        for val, txt, couleur in [
            ("auto",  " Auto",      "#2c3e50"),
            ("vect",  " Vectoriel", "#27ae60"),
            ("bool",  " Booléen",   "#e67e22"),
        ]:
            tk.Radiobutton(
                frame_modele, text=txt, variable=self.modele_force,
                value=val, bg="#f0f4f8", fg=couleur,
                font=("Helvetica", 10), selectcolor="#dfe6e9"
            ).pack(side="left", padx=8)

        # ── Curseur de seuil ─────────────────────────────────────────────────
        # Le curseur appelle _filtrer_resultats() à chaque mouvement,
        # ce qui refiltre les résultats existants sans relancer la recherche.
        frame_seuil = tk.Frame(self, bg="#f0f4f8")
        frame_seuil.pack(fill="x", padx=22, pady=(4, 0))

        tk.Label(frame_seuil, text="Seuil de score minimum :",
                 font=("Helvetica", 10), bg="#f0f4f8"
                 ).pack(side="left")

        tk.Scale(
            frame_seuil, variable=self.seuil_var,
            from_=0.0, to=1.0, resolution=0.01,
            orient="horizontal", length=220, bg="#f0f4f8",
            showvalue=True, troughcolor="#dfe6e9",
            command=lambda v: self._filtrer_resultats()
        ).pack(side="left", padx=8)

        # ── Labels d'information ─────────────────────────────────────────────
        self.lbl_info = tk.Label(
            self, text="", font=("Helvetica", 10, "italic"),
            bg="#f0f4f8", fg="#7f8c8d", anchor="w"
        )
        self.lbl_info.pack(fill="x", padx=22, pady=(4, 0))

        self.lbl_suggestions = tk.Label(
            self, text="", font=("Helvetica", 10),
            bg="#f0f4f8", fg="#8e44ad", anchor="w"
        )
        self.lbl_suggestions.pack(fill="x", padx=22, pady=(2, 0))

        # ── Séparateur visuel ────────────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=14, pady=8)

        # ── Zone de résultats scrollable ─────────────────────────────────────
        # Architecture : Canvas + Scrollbar + Frame interne
        # Le Canvas est la zone scrollable ; la Frame interne contient les cartes.
        # La liaison <Configure> met à jour la région scrollable quand le contenu change.
        frame_res = tk.Frame(self, bg="#f0f4f8")
        frame_res.pack(fill="both", expand=True, padx=14)

        self._canvas_res = tk.Canvas(frame_res, bg="#f0f4f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_res, orient="vertical",
                                   command=self._canvas_res.yview)
        self.frame_interne = tk.Frame(self._canvas_res, bg="#f0f4f8")

        self.frame_interne.bind(
            "<Configure>",
            lambda e: self._canvas_res.configure(
                scrollregion=self._canvas_res.bbox("all")
            )
        )
        self._canvas_res.create_window((0, 0), window=self.frame_interne, anchor="nw")
        self._canvas_res.configure(yscrollcommand=scrollbar.set)

        self._canvas_res.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll avec la molette de la souris (Windows & Linux)
        self._canvas_res.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas_res.yview_scroll(-1 * int(e.delta / 120), "units")
        )

        # ── Barre de boutons en bas ──────────────────────────────────────────
        frame_bas = tk.Frame(self, bg="#dfe6e9", pady=4)
        frame_bas.pack(fill="x", side="bottom")

        for texte, couleur, cmd in [
            ("📊 Évaluation",          "#27ae60", self._ouvrir_evaluation),
            ("🕒 Historique",          "#e67e22", self._afficher_historique),
            ("🔄 Réinitialiser contexte", "#8e44ad", self._reinit_contexte),
        ]:
            tk.Button(
                frame_bas, text=texte, font=("Helvetica", 10),
                bg=couleur, fg="white", relief="flat", padx=10,
                activebackground=couleur, command=cmd
            ).pack(side="left", padx=8, pady=4)

        tk.Button(
            frame_bas, text=" Quitter",
            font=("Helvetica", 10), bg="#e74c3c", fg="white",
            relief="flat", padx=10, command=self.destroy
        ).pack(side="right", padx=10)

    # ── 4.2 Pipeline principal de recherche ──────────────────────────────────

    def _lancer_recherche(self):
        """
        Orchestrateur principal.
        Étapes dans l'ordre :
          1. Lire et valider la requête
          2. Correction orthographique (difflib)
          3. Détecter ou forcer le modèle
          4. Expansion par synonymes (vectoriel uniquement)
          5. Exécuter la recherche (vectorielle ou booléenne)
          6. Appliquer le contexte si présent
          7. Sauvegarder dans l'historique
          8. Calculer les suggestions connexes
          9. Mettre à jour l'interface
        """
        requete_brute = self.champ_requete.get().strip()
        if not requete_brute:
            messagebox.showwarning("Requête vide", "Veuillez entrer une requête.")
            return

        # ── Étape 1 : Correction orthographique ──────────────────────────────
        requete_corrigee, corrections = corriger_requete(requete_brute, VOCABULAIRE)

        msg_corr = ""
        if corrections:
            details = ", ".join(f"«{a}»→«{b}»" for a, b in corrections)
            msg_corr = f"   {details}"
            # Mettre à jour le champ visuellement pour que l'utilisateur voie la correction
            self.champ_requete.delete(0, tk.END)
            self.champ_requete.insert(0, requete_corrigee)

        # ── Étape 2 : Intention ───────────────────────────────────────────────
        intention = detecter_intention(requete_corrigee)

        # ── Étape 3 : Choix du modèle ─────────────────────────────────────────
        choix = self.modele_force.get()
        modele = detecter_modele(requete_corrigee) if choix == "auto" else choix
        self._modele_courant = modele

        # ── Étape 4 : Expansion synonymes (vectoriel seulement) ───────────────
        # On n'élargit pas la requête booléenne car les opérateurs ET/OU/SAUF
        # ont une sémantique précise qui serait perturbée par des mots supplémentaires.
        requete_finale = requete_corrigee
        if modele == "vect":
            requete_finale = expand_requete(requete_corrigee, SYNONYMES)

        # ── Mise à jour du label d'info ───────────────────────────────────────
        nom_modele = "modele Vectoriel" if modele == "vect" else "modele Booléen"
        self.lbl_info.config(
            text=f" {nom_modele}  |  {intention}{msg_corr}"
        )
        self.update_idletasks()

        # ── Étape 5 : Recherche ────────────────────────────────────────────────
        try:
            if modele == "vect":
                # search_query retourne [(doc_num, score), ...]  (doc_num est 1-indexé)
                bruts = search_query(requete_finale, TF_IDF, IDF)
                resultats = [
                    (num, score,
                     NOMS_FICHIERS[num - 1] if 0 < num <= len(NOMS_FICHIERS) else f"doc{num}")
                    for num, score in bruts
                ]
            else:
                # modele_bool retourne un set d'entiers (numéros de documents)
                set_docs = modele_bool(requete_finale, BOOL_INDEX)
                resultats = [
                    (num, 1.0,
                     NOMS_FICHIERS[num - 1] if 0 < num <= len(NOMS_FICHIERS) else f"doc{num}")
                    for num in sorted(set_docs)
                ]
        except Exception as e:
            messagebox.showerror("Erreur lors de la recherche", str(e))
            return

        # ── Étape 6 : Contexte ────────────────────────────────────────────────
        # Si l'utilisateur a cliqué sur "Affiner" pour un ou plusieurs documents,
        # on augmente légèrement leur score (et celui des docs similaires).
        if self.poids_contexte and modele == "vect":
            resultats = self._appliquer_contexte(resultats)

        # Trier par score décroissant (utile surtout pour le vectoriel)
        resultats.sort(key=lambda x: x[1], reverse=True)
        self._resultats_courants = resultats

        # ── Étape 7 : Historique ──────────────────────────────────────────────
        sauvegarder_historique(requete_brute)
        self.historique = charger_historique()

        # ── Étape 8 : Suggestions connexes ────────────────────────────────────
        suggestions = suggestions_connexes(requete_brute, self.historique, IDF, n=3)
        if suggestions:
            self.lbl_suggestions.config(
                text="💡 Requêtes similaires : " + "  |  ".join(suggestions)
            )
        else:
            self.lbl_suggestions.config(text="")

        # ── Étape 9 : Affichage (avec application du seuil) ───────────────────
        self._filtrer_resultats()

    # ── 4.3 Filtrage dynamique par seuil ────────────────────────────────────

    def _filtrer_resultats(self):
        """
        Réaffiche les résultats en ne conservant que ceux dont score ≥ seuil.
        Appelée :
          - Après chaque recherche (via _lancer_recherche)
          - À chaque mouvement du curseur de seuil
        Cela évite de relancer la recherche complète juste pour changer le seuil.
        """
        seuil = self.seuil_var.get()
        filtrés = [(n, s, f) for n, s, f in self._resultats_courants if s >= seuil]
        self._afficher_resultats(filtrés)

    # ── 4.4 Rendu visuel des résultats ───────────────────────────────────────

    def _afficher_resultats(self, resultats: list):
        """
        Vide le panneau et crée une carte par document.
        On vide _thumbnails AVANT de créer de nouvelles images pour libérer la mémoire.
        """
        for widget in self.frame_interne.winfo_children():
            widget.destroy()
        self._thumbnails.clear()

        if not resultats:
            tk.Label(
                self.frame_interne,
                text="Aucun résultat pour ce seuil de score.",
                font=("Helvetica", 12), bg="#f0f4f8", fg="#95a5a6"
            ).pack(pady=30)
            return

        for doc_num, score, nom in resultats:
            self._creer_carte(doc_num, score, nom)

    def _creer_carte(self, doc_num: int, score: float, nom: str):
        """
        Crée un widget "carte" pour un document résultat.


        Deux boutons en bas à droite :
          - " Afficher" : ouvre l'image en grand dans une fenêtre popup
          - " Affiner"  : mémorise ce document comme contexte de recherche
        """
        carte = tk.Frame(
            self.frame_interne, bg="white",
            bd=1, relief="solid", padx=8, pady=6
        )
        carte.pack(fill="x", padx=6, pady=4)

        # ── Miniature (colonne gauche) ────────────────────────────────────────
        # IMPORTANT : on fixe width ET height pour que pack_propagate(False)
        # ne réduise pas le frame à une hauteur de 0 (bug classique Tkinter).
        frame_img = tk.Frame(carte, bg="#ecf0f1",
                             width=THUMBNAIL_SIZE[0] + 8,
                             height=THUMBNAIL_SIZE[1] + 8)
        frame_img.pack(side="left", padx=(0, 12))
        frame_img.pack_propagate(False)   # Fige les dimensions à width×height

        thumb = charger_miniature(nom)
        if thumb:
            # Stocker la référence dans self._thumbnails est OBLIGATOIRE :
            # Tkinter ne garde pas de référence forte sur les PhotoImage,
            # donc sans ça le garbage collector Python supprime l'image
            # et le label affiche un carré vide.
            self._thumbnails.append(thumb)
            tk.Label(frame_img, image=thumb, bg="#ecf0f1",
                     cursor="hand2").place(relx=0.5, rely=0.5, anchor="center")
        else:
            tk.Label(
                frame_img, text="📄\npas d'image",
                bg="#ecf0f1", font=("Helvetica", 8), fg="#95a5a6",
                justify="center"
            ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Informations texte (colonne centrale) ────────────────────────────
        frame_txt = tk.Frame(carte, bg="white")
        frame_txt.pack(side="left", fill="both", expand=True)

        tk.Label(
            frame_txt,
            text=f"📄 Document {doc_num}  —  {nom.capitalize()}",
            font=("Helvetica", 12, "bold"), bg="white", fg="#2c3e50",
            anchor="w"
        ).pack(anchor="w")

        # Couleur du score : vert > 50%, orange > 20%, rouge sinon
        pct = min(int(score * 100), 100)
        couleur = "#27ae60" if pct > 50 else "#e67e22" if pct > 20 else "#e74c3c"

        tk.Label(
            frame_txt,
            text=f"Score de similarité : {score:.4f}  ({pct}%)",
            font=("Helvetica", 10), bg="white", fg=couleur, anchor="w"
        ).pack(anchor="w")

        # Barre de progression proportionnelle au score
        barre = tk.Canvas(frame_txt, height=6, width=320,
                          bg="#ecf0f1", highlightthickness=0)
        barre.pack(anchor="w", pady=3)
        barre.create_rectangle(0, 0, pct * 3.2, 6, fill=couleur, outline="")

        # ── Boutons d'action (colonne droite) ────────────────────────────────
        frame_btns = tk.Frame(carte, bg="white")
        frame_btns.pack(side="right", padx=6, pady=2)

        # Bouton "Afficher" : ouvre l'image en grand dans une popup
        tk.Button(
            frame_btns, text="🖼 Afficher",
            font=("Helvetica", 9, "bold"),
            bg="#3498db", fg="white", relief="flat",
            activebackground="#2980b9", cursor="hand2",
            # lambda capture 'nom' par valeur par défaut — sans ça,
            # toutes les lambdas référenceraient la même variable 'nom'
            # (valeur de la dernière itération).
            command=lambda n=nom, d=doc_num: self._afficher_image_doc(n, d)
        ).pack(pady=(0, 4))

        # Bouton "Affiner" : filtrage contextuel
        tk.Button(
            frame_btns, text="🎯 Affiner",
            font=("Helvetica", 9), bg="#dfe6e9", relief="flat",
            activebackground="#bdc3c7",
            command=lambda n=doc_num: self._selectionner_doc(n)
        ).pack()

    # ── 4.4b Popup d'affichage d'image ───────────────────────────────────────

    def _afficher_image_doc(self, nom: str, doc_num: int):
        """
        Ouvre une fenêtre Toplevel affichant l'image complète du document.

        Paramètres :
          nom     : nom de base du fichier (ex: "AI", "cuisine") → cherche files/AI.jpg
          doc_num : numéro du document (pour le titre de la fenêtre)

        Si l'image n'existe pas, on affiche un message d'erreur clair
        plutôt que de laisser la fenêtre vide ou de crasher.

        Redimensionnement :
          On agrandit l'image à max 500×400 px en conservant le ratio,
          ce qui évite d'avoir une image minuscule ou déformée.
        """
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "PIL manquant",
                "Pillow n'est pas installé.\n"
                "Exécutez : pip install Pillow"
            )
            return

        # Chercher le fichier image dans files/ avec plusieurs extensions possibles
        chemin_trouve = None
        for ext in [".jpg", ".jpeg", ".png"]:
            chemin = os.path.join(DOSSIER_IMAGES, nom + ext)
            if os.path.exists(chemin):
                chemin_trouve = chemin
                break

        # Créer la fenêtre popup dans tous les cas (même sans image)
        win = tk.Toplevel(self)
        win.title(f"  Document {doc_num} — {nom.capitalize()}")
        win.configure(bg="#2c3e50")
        win.transient(self)   # Reste au premier plan de la fenêtre principale
        win.resizable(True, True)

        if chemin_trouve is None:
            # Aucun fichier image trouvé : afficher un message
            win.geometry("520x420")
            tk.Label(
                win,
                text=f"❌  Aucune image trouvée pour\n« {nom} »\n\n"
                     f"Cherché dans : {os.path.abspath(DOSSIER_IMAGES)}/",
                font=("Helvetica", 11), bg="#2c3e50", fg="#e74c3c",
                justify="center"
            ).pack(expand=True)
            tk.Button(win, text="Fermer", command=win.destroy,
                      bg="#e74c3c", fg="white", relief="flat", padx=12
                      ).pack(pady=10)
            return

        try:
            # Charger l'image originale (sans redimensionner)
            img_orig = Image.open(chemin_trouve)
            larg_orig, haut_orig = img_orig.size

            # Redimensionner à max 500×400 px en conservant le ratio
            # thumbnail() modifie l'image EN PLACE et respecte le ratio automatiquement
            max_taille = (500, 400)
            img_affich = img_orig.copy()
            img_affich.thumbnail(max_taille, Image.LANCZOS)
            larg, haut = img_affich.size

            photo = ImageTk.PhotoImage(img_affich)

            # Dimensionner la fenêtre selon l'image (+ espace pour titre/bouton)
            win.geometry(f"{larg + 30}x{haut + 90}")

            # Label image centré
            lbl_img = tk.Label(win, image=photo, bg="#2c3e50",
                               relief="flat", bd=0)
            lbl_img.image = photo   # Référence forte sur le widget lui-même
            lbl_img.pack(padx=15, pady=(15, 5))

            # Infos sous l'image
            tk.Label(
                win,
                text=f"{nom.capitalize()}  •  {larg_orig}×{haut_orig} px  •  {os.path.basename(chemin_trouve)}",
                font=("Helvetica", 9), bg="#2c3e50", fg="#bdc3c7"
            ).pack()

        except Exception as e:
            tk.Label(win, text=f"Erreur lors du chargement :\n{e}",
                     font=("Helvetica", 10), bg="#2c3e50", fg="#e74c3c"
                     ).pack(expand=True, pady=20)

        tk.Button(win, text="✖ Fermer", command=win.destroy,
                  bg="#e74c3c", fg="white", relief="flat", padx=14
                  ).pack(pady=8)

    def _vider_resultats(self):
        """Efface les résultats affichés et réinitialise l'état."""
        self._resultats_courants = []
        self._thumbnails.clear()
        for w in self.frame_interne.winfo_children():
            w.destroy()
        self.lbl_info.config(text="")
        self.lbl_suggestions.config(text="")

    # ── 4.5 Filtrage contextuel ──────────────────────────────────────────────

    def _selectionner_doc(self, doc_num: int):
        """
        Mémorise les mots-clés du document sélectionné comme contexte.
        Lors de la prochaine recherche, ces mots augmenteront légèrement
        le score des documents qui les contiennent.

        Formule du bonus :
          bonus(mot) += (freq_dans_doc / total_mots_doc) × 0.3
        Le facteur 0.3 est empirique : assez faible pour ne pas dominer le score TF-IDF.
        """
        if 0 < doc_num <= len(docs):
            doc_mots = docs[doc_num - 1]  # dict {mot: freq}
            total = sum(doc_mots.values()) or 1
            for mot, freq in doc_mots.items():
                self.poids_contexte[mot] = (
                    self.poids_contexte.get(mot, 0) + (freq / total) * 0.3
                )
            nom = NOMS_FICHIERS[doc_num - 1] if doc_num - 1 < len(NOMS_FICHIERS) else "?"
            messagebox.showinfo(
                "Contexte mis à jour",
                f"✅ Document {doc_num} ({nom}) sélectionné comme contexte.\n")
        else:
            messagebox.showwarning("Erreur", f"Document {doc_num} introuvable.")

    def _appliquer_contexte(self, resultats: list) -> list:
        """
        Ajoute un bonus de score aux documents dont les termes
        correspondent aux poids contextuels mémorisés.
        Le score final est plafonné à 1.0 pour rester cohérent.
        """
        ajustes = []
        for doc_num, score, nom in resultats:
            if 0 < doc_num <= len(TF_IDF):
                vec = TF_IDF[doc_num - 1]
                bonus = sum(vec.get(m, 0) * w for m, w in self.poids_contexte.items())
                ajustes.append((doc_num, min(score + bonus, 1.0), nom))
            else:
                ajustes.append((doc_num, score, nom))
        return ajustes

    def _reinit_contexte(self):
        """Réinitialise le contexte de filtrage."""
        self.poids_contexte.clear()
        messagebox.showinfo("Contexte réinitialisé",
                            "Le contexte de filtrage a été effacé. "
                            "La prochaine recherche utilisera uniquement TF-IDF.")


    def _afficher_historique(self):
        """
        Ouvre une fenêtre Toplevel listant les requêtes récentes.
        Double-clic sur une entrée : remplit le champ et relance la recherche.
        """
        win = tk.Toplevel(self)
        win.title(" Historique des requêtes")
        win.geometry("420x380")
        win.configure(bg="#f0f4f8")
        win.transient(self)   # La fenêtre reste au premier plan de l'application

        tk.Label(win, text="Double-clic pour réutiliser une requête",
                 font=("Helvetica", 10, "italic"), bg="#f0f4f8", fg="#7f8c8d"
                 ).pack(pady=(10, 4))

        frame_list = tk.Frame(win)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(frame_list)
        scroll.pack(side="right", fill="y")

        listbox = tk.Listbox(frame_list, font=("Helvetica", 11),
                             yscrollcommand=scroll.set, selectbackground="#3498db")
        listbox.pack(side="left", fill="both", expand=True)
        scroll.config(command=listbox.yview)

        historique = charger_historique()
        for q in reversed(historique):  # La plus récente en premier
            listbox.insert(tk.END, q)

        def reutiliser(_event):
            sel = listbox.curselection()
            if sel:
                self.champ_requete.delete(0, tk.END)
                self.champ_requete.insert(0, listbox.get(sel[0]))
                win.destroy()
                self._lancer_recherche()

        listbox.bind("<Double-Button-1>", reutiliser)

        tk.Button(win, text="Fermer", command=win.destroy,
                  bg="#e74c3c", fg="white", relief="flat", padx=10
                  ).pack(pady=8)

    # ── 4.7 Fenêtre Évaluation ───────────────────────────────────────────────

    def _ouvrir_evaluation(self):
        """
        Ouvre une fenêtre dédiée à l'évaluation du moteur de recherche.
        Utilise le jeu de tests TESTS_EVALUATION (défini en haut du fichier).

        Algorithme (courbe précision-rappel interpolée) :
          Pour 50 seuils s ∈ [0, 1] :
            Pour chaque (requête_test, docs_pertinents) :
              resultats  = search_query(requête_test)
              sélection  = [doc | score ≥ s]
              TP         = |sélection ∩ pertinents|
              précision  = TP / |sélection|   (0 si sélection vide)
              rappel     = TP / |pertinents|  (0 si pertinents vide)
            Moyenner sur toutes les requêtes.

        La courbe P-R est tracée avec matplotlib et intégrée dans le Canvas Tkinter
        (FigureCanvasTkAgg) pour rester dans la même application.

        Note académique vs réel :
          En production, on évaluerait sur un gold standard annoté manuellement
          par des experts du domaine, avec des milliers de requêtes.
          Ici le jeu de tests est minimal et les pertinences sont simplifiées (1 doc).
        """
        win = tk.Toplevel(self)
        win.title("📊 Évaluation — Courbe Précision-Rappel")
        win.geometry("720x560")
        win.configure(bg="#f0f4f8")
        win.transient(self)

        # Label temporaire pendant le calcul
        lbl_attente = tk.Label(win, text="⏳ Calcul en cours…",
                               font=("Helvetica", 12), bg="#f0f4f8")
        lbl_attente.pack(pady=20)
        win.update()

        # ── Calcul des métriques ──────────────────────────────────────────────
        seuils = np.linspace(0, 1, 50)
        precision_moy, rappel_moy = [], []

        for s in seuils:
            tot_prec, tot_rapp = 0.0, 0.0
            for requete, pertinents in TESTS_EVALUATION:
                bruts = search_query(requete, TF_IDF, IDF)
                # Filtrer par seuil
                selection = [d for d, sc in bruts if sc >= s]
                tp = sum(1 for d in selection if d in pertinents)
                prec = tp / len(selection) if selection else 0.0
                rapp = tp / len(pertinents) if pertinents else 0.0
                tot_prec += prec
                tot_rapp += rapp
            precision_moy.append(tot_prec / len(TESTS_EVALUATION))
            rappel_moy.append(tot_rapp / len(TESTS_EVALUATION))

        # ── Tracé matplotlib intégré ──────────────────────────────────────────
        lbl_attente.destroy()

        fig, ax = plt.subplots(figsize=(6.8, 4.8), dpi=90)
        ax.plot(rappel_moy, precision_moy,
                "b-o", markersize=3, linewidth=1.8, label="P-R interpolée")
        ax.fill_between(rappel_moy, precision_moy, alpha=0.08, color="blue")
        ax.set_xlabel("Rappel moyen", fontsize=12)
        ax.set_ylabel("Précision moyenne", fontsize=12)
        ax.set_title("Courbe Précision-Rappel\n"
                     f"({len(TESTS_EVALUATION)} requêtes × 50 seuils)", fontsize=13)
        ax.set_xlim(0, 1.05)
        ax.set_ylim(0, 1.05)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(fontsize=10)
        fig.tight_layout()

        # Intégrer la figure matplotlib dans la fenêtre Tkinter
        canvas_fig = FigureCanvasTkAgg(fig, master=win)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

        tk.Label(
            win,
            text=f"Requêtes de test : {', '.join(r for r, _ in TESTS_EVALUATION[:5])}…",
            font=("Helvetica", 9, "italic"), bg="#f0f4f8", fg="#7f8c8d"
        ).pack(pady=2)

        tk.Button(win, text="Fermer", command=win.destroy,
                  bg="#e74c3c", fg="white", relief="flat", padx=10
                  ).pack(pady=6)

if __name__ == "__main__":
    app = AppRecherche()
    # mainloop() démarre la boucle d'événements Tkinter.
    # Elle bloque jusqu'à ce que la fenêtre soit fermée.
    app.mainloop()
