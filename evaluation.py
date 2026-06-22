''' 
#C'est un outil d'évaluation d'un moteur de recherche 

#   Ce programme évalue la qualité du moteur de recherche en mesurant sa précision 
et son rappel à travers une interface graphique (courbe précision-rappel). 
L'utilisateur peut entrer des requêtes et indiquer quels documents sont pertinents 
pour ces requêtes.

#   Le programme calcule ensuite la précision et le rappel pour différents 
 seuils de pertinence et affiche la courbe correspondante.
'''

import matplotlib.pyplot as plt
import numpy as np
from MoteurRecherche import returned_documents, vect_model_TF, vect_model_IDF, vect_model_mot_poids_final, search_query

# Charger les documents 
# Initialisation des modèles TF, IDF et TF-IDF
'''
Les documents disponibles
Les modèles TF (Term Frequency), IDF (Inverse Document Frequency), 
et TF-IDF ()
'''

docs = returned_documents()
TF = vect_model_TF()
IDF = vect_model_IDF()
TF_IDF = vect_model_mot_poids_final(TF, IDF)

# L'utilisateur va entrer ses propres requêtes et indiquer les documents pertinents
print("=== Mode évaluation : entrée manuelle des requêtes et des pertinences ===")
print("Pour chaque requête, entrez les numéros des documents pertinents (ex: 1 2 3)")
print("Tapez 'fin' pour arrêter.")

'''
Tu entres manuellement :
Une requête (ex: "intelligence artificielle")
Les numéros des documents pertinents (ex: 1 2 3)
Le programme répète jusqu'à ce que tu tapes "fin".
'''

tests = []
while True:
    requete = input("\nRequête (ou 'fin') : ").strip()
    if requete.lower() == 'fin':
        break
    pertinents_str = input("Documents pertinents (numéros séparés par des espaces) : ")
    pertinents = set(map(int, pertinents_str.split())) if pertinents_str else set()
    tests.append((requete, pertinents))

if not tests:
    print("Aucune requête saisie. Sortie.")
    exit()

# Calcul des métriques pour différents seuils
seuils = np.linspace(0, 1, 50)
precision_moy = []
rappel_moy = []

for s in seuils:
    total_prec = 0
    total_rapp = 0
    for requete, pertinents in tests:
        resultats = search_query(requete, TF_IDF, IDF)  # liste de (doc, score)
        selection = [doc for doc, score in resultats if score >= s]
        pert_retournes = len([d for d in selection if d in pertinents])
        prec = pert_retournes / len(selection) if selection else 0
        rapp = pert_retournes / len(pertinents) if pertinents else 0
        total_prec += prec
        total_rapp += rapp
    precision_moy.append(total_prec / len(tests))
    rappel_moy.append(total_rapp / len(tests))

# Tracé
plt.plot(rappel_moy, precision_moy, 'b-')
plt.xlabel('Rappel moyen')
plt.ylabel('Précision moyenne')
plt.title('Courbe Précision-Rappel (évaluation interactive)')
plt.grid(True)
plt.show()