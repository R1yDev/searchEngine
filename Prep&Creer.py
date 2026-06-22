import nltk 
import os

# --- Téléchargement des ressources NLTK ---
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("Téléchargement des ressources NLTK...")
    nltk.download('punkt')
    nltk.download('punkt_tab')

from nltk.tokenize import word_tokenize

# --- VOS LISTES PERSONNALISÉES ---

# 1. Stop-Liste
stopList = [
        "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", 
        "le", "la","là" ,"j", "les", "l", "un", "une", "des", "du", "de", "au", "aux", 
        "ce", "cet", "cette", "ces","c'est","mon", "ton", "son", "ma", "ta", "sa", 
        "mes", "tes", "ses", "notre", "votre", "nos", "vos", "leur", "leurs",
        "me", "te", "se", "lui", "leur","et", "ou", "sauf" , "eux", "moi", "toi", "soi", 
        "y", "en", "cela", "celui", "celle", "ceux", "celles", "ceci", "ça",
        "à", "dans", "par", "pour", "en", "vers", "avec", "sans", 
        "sous", "sur", "chez", "entre", "parmi", "pendant", "depuis", 
        "durant", "excepté", "hormis", "selon", "devant", "derrière", "dans",
        "contre", "malgré", "outre", "passé", "sauf",
        "et", "ou", "ni", "mais", "car", "donc", "or", "que","qu'au","tandis", 
        "lorsque","puisque", "quand", "comme", "si","très", "trop",
        "beaucoup", "peu", "moins", "plus", "aussi", "tellement", "comment", 
        "pourquoi", "où", "ici", "dedans", "dehors", "avant", "après", 
        "maintenant", "hier", "aujourd'hui", "demain", "déjà", "jamais", 
        "toujours","parfois", "rarement", "soudain", "enfin", "alors",
        "qui", "quoi", "dont", "lequel", "laquelle", "lesquels", "lesquelles",
        "auquel", "à laquelle", "auxquels", "auxquelles", "duquel", "de laquelle", 
        "desquels", "desquelles","ne", "pas", "plus", "jamais", "rien", "personne",
        "aucun","aucune", "nul", "nulle", "guère", "point", 
        "quelque", "quelqu", "chose", "certains", "certaines",
        "ainsi", "puis", "ensuite", "voici", "voilà", "oui", "non", 
        "merci", "bonjour", "bien", "mal", "mieux", "pire", "tel", "très",
        "telle", "tels", "telles", "tout", "tous", "toute", "toutes",".","!","?",";",":","(",")","[","]","{","}","\"","'","-"
    ]

stop_words = set(stopList) #une collection de valeurs uniques sans ordre(Non ordonné) et Mutable(Modifiable)

# 2. Liste des Auxiliaires
auxiliaires = {
    "suis": "être", "es": "être", "est": "être", "sommes": "être", "êtes": "être", "sont": "être",
    "étais": "être", "était": "être", "étions": "être", "étiez": "être", "étaient": "être",
    "serai": "être", "seras": "être", "sera": "être", "serons": "être", "serez": "être", "seront": "être",
    "ai": "avoir", "as": "avoir", "a": "avoir", "avons": "avoir", "avez": "avoir", "ont": "avoir",
    "avais": "avoir", "avait": "avoir", "avions": "avoir", "aviez": "avoir", "avaient": "avoir",
    "aurai": "avoir", "auras": "avoir", "aura": "avoir", "aurons": "avoir", "aurez": "avoir", "auront": "avoir",
    "peux": "pouvoir", "peut": "pouvoir", "pouvons": "pouvoir", "pouvez": "pouvoir", "peuvent": "pouvoir",
    "veux": "vouloir", "veut": "vouloir", "voulons": "vouloir", "voulez": "vouloir", "veulent": "vouloir",
    "dois": "devoir", "doit": "devoir", "devons": "devoir", "devez": "devoir", "doivent": "devoir",
    "vais": "aller", "vas": "aller", "va": "aller", "allons": "aller", "allez": "aller", "vont": "aller",
    "fais": "faire", "fait": "faire", "faisons": "faire", "faites": "faire", "font": "faire",
    "sais": "savoir", "sait": "savoir", "savons": "savoir", "savez": "savoir", "savent": "savoir",
    "vois": "voir", "voit": "voir", "voyons": "voir", "voyez": "voir", "voient": "voir",
    "viens": "venir", "vient": "venir", "venons": "venir", "venez": "venir", "viennent": "venir",
    "faut": "falloir"
}

# 3. Exceptions Pluriel
EXCEPTIONS_PLURIEL = [
    "deux", "trois", "six", "dix", "neuf", "cinq", "huit", "quatre", "sept", "onze", "douze",
    "bras", "souris", "fois", "pays", "corps", "poids", "temps", "voix", "nez", "repas",
    "bis", "tas", "dos", "pas", "cas", "autobus", "tas"
]

# --- Configuration ---
DOSSIER_FILES = "files" 
FICHIER_SORTIE = "data.txt"



def nettoyer_apostrophe(mot):
    """
    Supprime les préfixes d'apostrophe (l', d', m', j', c', qu', n', s')
    pour récupérer le mot racine (ex: l'intelligence -> intelligence).
    """
    prefixes_a_supprimer = ["l'", "d'", "m'", "j'", "c'", "qu'", "n'", "s'"]
    # On vérifie les 2 premiers caractères pour voir s'ils correspondent à un préfixe
    if mot[:2] in prefixes_a_supprimer:
        return mot[2:]
    return mot

#mettre le verbe conjugué en l'infinitif
def lemmatiser(mot):
    if mot in auxiliaires:
        return auxiliaires[mot]

    if mot not in EXCEPTIONS_PLURIEL and mot.endswith('s'):
        return mot[:-1]
    return mot

def process_text_file(nom_fichier):
    chemin_complet = os.path.join(DOSSIER_FILES, nom_fichier)
    with open(chemin_complet, 'r', encoding='utf-8', errors='ignore') as f:
        texte = f.read()

    mots = word_tokenize(texte, language='french')
    
    mots_propres = []
    for mot in mots:
        mot_lower = mot.lower()
        
        # 1. Nettoyage des apostrophes (l', d', m'...) AVANT la stop-list
        mot_nettoye = nettoyer_apostrophe(mot_lower)
        
        # 2. Vérification : est-ce que le mot est vide après nettoyage ? (ex: "d'" seul)
        if not mot_nettoye:
            continue
            
        # 3. Vérification Stop-Liste et Alphabétique
        if mot_nettoye.isalpha() and mot_nettoye not in stop_words:
            mots_propres.append(mot_nettoye)

    lemmes = []
    for mot in mots_propres:
        lemme = lemmatiser(mot)
        lemmes.append(lemme)

    occurrences = {}
    for lemme in lemmes:
        occurrences[lemme] = occurrences.get(lemme, 0) + 1

    return occurrences

fichiers_a_traiter = [
    "AI.txt", "cuisine.txt", "football.txt", "natation.txt", "basket.txt", 
    "athlet.txt", "art.txt", "cinema.txt", "cosmetique.txt", "economie.txt", 
    "environnement.txt", "politique.txt", "litterateure.txt", "psychologie.txt", 
    "sante.txt", "technologie.txt", "voyage.txt", "music.txt", "reseau.txt", 
    "vehicule.txt"
]

def create_file():
    print(f"Traitement de {len(fichiers_a_traiter)} fichiers...")
    print(f"Dossier source : {os.path.abspath(DOSSIER_FILES)}")
    
    if not os.path.exists(DOSSIER_FILES):
        print(f"ERREUR : Le dossier '{DOSSIER_FILES}' n'existe pas.")
        return

    with open(FICHIER_SORTIE, 'w', encoding='utf-8') as fichier:
        
        for nom_fichier in fichiers_a_traiter:
            resultat = process_text_file(nom_fichier)
            fichier.write(f"======== Résultat du traitement du fichier {nom_fichier} =======\n")
            fichier.write(str(resultat) + "\n\n")

    print(f"Succès ! Fichier '{FICHIER_SORTIE}' généré.")

create_file()