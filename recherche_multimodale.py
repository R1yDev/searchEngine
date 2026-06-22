
import os
import sys
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from MoteurRecherche import (
    returned_documents,
    vect_model_TF,
    vect_model_IDF,
    vect_model_mot_poids_final,
    search_query
)

IMAGES_FOLDER = "images"
FICHIERS_FOLDER = "files"  # Dossier contenant les images réelles
FICHIERS_DOCUMENTS = [
    "AI", "cuisine", "football", "natation", "basket",
    "athlet", "art", "cinema", "cosmetique", "economie",
    "environnement", "politique", "litterateure", "psychologie",
    "sante", "technologie", "voyage", "music", "reseau", "vehicule"
]

def obtenir_nom_document(numero_doc):
    if 1 <= numero_doc <= len(FICHIERS_DOCUMENTS):
        return FICHIERS_DOCUMENTS[numero_doc - 1]
    return None

def trouver_image(nom_document):
    extensions = [".jpg", ".png", ".jpeg", ".bmp", ".JPG", ".PNG", ".JPEG", ".BMP"]

    # Chercher dans le dossier files/ (images réelles)
    fichiers = os.listdir(FICHIERS_FOLDER) if os.path.exists(FICHIERS_FOLDER) else []

    # Alias pour les documents manquants
    alias = {
        "technologie": ["technologie", "tech"],
        "athlet": ["athletismeGamoudi", "athletismeGamoudi"],
        "reseau": ["reseau", "réseaux"],
        "vehicule": ["vehicule"],
        "basket" : ["basketTN2025", "basketCA"]
    }

    # Stratégie 1: Chercher un match exact
    for fichier in fichiers:
        nom_bas = fichier.lower()
        if nom_bas == nom_document.lower() + ".jpg" or \
           nom_bas == nom_document.lower() + ".png" or \
           nom_bas == nom_document.lower() + ".jpeg" or \
           nom_bas == nom_document.lower() + ".bmp":
            chemin = os.path.join(FICHIERS_FOLDER, fichier)
            if os.path.isfile(chemin):
                return chemin

    # Stratégie 2: Chercher un alias
    if nom_document.lower() in alias:
        for alias_name in alias[nom_document.lower()]:
            for fichier in fichiers:
                nom_bas = fichier.lower()
                if nom_bas.startswith(alias_name.lower()) and \
                   any(nom_bas.endswith(ext.lower()) for ext in extensions):
                    chemin = os.path.join(FICHIERS_FOLDER, fichier)
                    if os.path.isfile(chemin):
                        return chemin

    # Stratégie 3: Chercher un fichier qui commence par le document
    for fichier in fichiers:
        if fichier.lower().startswith(nom_document.lower()) and \
           any(fichier.lower().endswith(ext.lower()) for ext in extensions):
            chemin = os.path.join(FICHIERS_FOLDER, fichier)
            if os.path.isfile(chemin):
                return chemin

    # Pas d'image trouvée
    return None

def charger_et_afficher_images(resultats, seuil_similarite=0.0):
    resultats_filtres = [
        (doc_num, score) for doc_num, score in resultats
        if score >= seuil_similarite
    ]

    if not resultats_filtres:
        print("")
        print("Aucun document avec une similarite >= {}".format(seuil_similarite))
        return

    resultats_filtres.sort(key=lambda x: x[1], reverse=True)

    num_resultats = len(resultats_filtres)
    num_colonnes = min(2, num_resultats)
    num_lignes = (num_resultats + num_colonnes - 1) // num_colonnes

    fig = plt.figure(figsize=(14, 5 * num_lignes))
    fig.suptitle("Resultats de la Recherche Multimodale",
                 fontsize=16, fontweight="bold", y=0.995)

    gs = gridspec.GridSpec(num_lignes, num_colonnes,figure=fig, hspace=0.3, wspace=0.3)

    for idx, (doc_num, score) in enumerate(resultats_filtres):
        nom_doc = obtenir_nom_document(doc_num)
        ax = fig.add_subplot(gs[idx // num_colonnes, idx % num_colonnes])
        chemin_image = trouver_image(nom_doc)

        ax.set_title(
            "Document {} ({}) | Similarite: {:.4f}".format(doc_num, nom_doc.upper(), score),
            fontsize=12, fontweight="bold", pad=10
        )
        
        if chemin_image:
            try:
                img = Image.open(chemin_image)
                ax.imshow(img)
                ax.axis("off")
                #print("[OK] Document {} ({})".format(doc_num, nom_doc))
                #print("  -> Similarite: {:.4f}".format(score))
                #print("  -> Image: {}".format(chemin_image))
            except Exception as e:
                ax.text(0.5, 0.5, "Erreur de chargement: {}".format(str(e)),
                       ha="center", va="center", transform=ax.transAxes,
                       fontsize=10, color="red")
                ax.axis("off")
                print("[ERREUR] Document {} ({})".format(doc_num, nom_doc))
                print("  -> Erreur: {}".format(str(e)))
        else:
            ax.text(0.5, 0.5,"Image non trouvee Chérchée: images/{}.jpg".format(nom_doc),ha="center", va="center", transform=ax.transAxes,fontsize=10, color="orange", style="italic")
            ax.axis("off")
            print("[MANQUANTE] Document {} ({})".format(doc_num, nom_doc))
            print("  -> Similarite: {:.4f}".format(score))
            print("  -> Image: NON TROUVÉE")

        print("")
    # Afficher les resultats
    try:
        plt.show()
    except Exception as e:
        # Si plt.show() ne fonctionne pas, sauvegarder à la place
        import time
        timestamp = int(time.time())
        chemin_sortie = "resultats_recherche_{}.png".format(timestamp)
        fig.savefig(chemin_sortie, dpi=100, bbox_inches='tight')
        print("\nMATTLOTPLIB INFO: Impossible d'afficher la fenetre graphique.")
        print("Resultats sauvegardes dans: {}".format(chemin_sortie))
        plt.close(fig)

def recherche_multimodale_interactive():
    docs = returned_documents()
    TF = vect_model_TF()
    IDF = vect_model_IDF()
    TF_IDF = vect_model_mot_poids_final(TF, IDF)

    if not os.path.exists(IMAGES_FOLDER):
        print("ATTENTION: images non trouve.")
        print("Les documents seront recherches mais sans images.")

    continuer = True
    while continuer:
        requete = input("Entrez votre requete (ou 'q' pour quitter) : ").strip()

        if requete.lower() == "q":
            print("")
            print("Au revoir!")
            break

        if not requete:
            print("ATTENTION: Requete vide. Veuillez réessayer.")
            continue

        try:
            seuil_input = input("Seuil de similarite (defaut: 0.15) : ").strip()
            seuil = float(seuil_input) if seuil_input else 0.15
        except ValueError:
            print("ATTENTION: Valeur invalide. Utilisation du seuil par defaut (0.15).")
            print("")
            seuil = 0.15

        print("")
        print("Recherche en cours pour : '{}'...".format(requete))
        print("")

        resultats = search_query(requete, TF_IDF, IDF)
        charger_et_afficher_images(resultats, seuil)

        continuer_input = input("Voulez-vous faire une autre recherche ? (o/n) : ").strip()
        if continuer_input.lower() != "o":
            print("")
            print("Au revoir!")
            continuer = False

def afficher_info_systeme():
    ''' 
    print("")
    print("Documents reconnus: {}".format(len(FICHIERS_DOCUMENTS)))
    print("  -> {}".format(', '.join(FICHIERS_DOCUMENTS)))
    '''

    if os.path.exists(FICHIERS_FOLDER):
        print("")
        print("Dossier 'files' trouve")
        fichiers = os.listdir(FICHIERS_FOLDER)
        images = [f for f in fichiers
                 if f.lower().endswith((".jpg", ".png", ".jpeg", ".bmp"))]
        textes = [f for f in fichiers if f.endswith('.txt')]
        print("  -> {} fichier(s) image(s) present(s)".format(len(images)))
        print("  -> {} fichier(s) texte present(s)".format(len(textes)))

        print("")
        print("Correspondances document-image :")
        for nom_doc in FICHIERS_DOCUMENTS:
            chemin = trouver_image(nom_doc)
            ''' 
            if chemin:
                print("  [OK]  {:<15} -> {}".format(nom_doc, os.path.basename(chemin)))
            else:
                print("  [NON]  {:<15} -> [NON TROUVÉE]".format(nom_doc))
            '''

afficher_info_systeme()
recherche_multimodale_interactive()
