import math
import ast
from preTreatmentQuary import process_query_bool, process_query_vect
'''
Partie 3 : 
Développment des modèles vectoriel et booléen
'''
def read_data_file():
    
    stTable = []
    with open('data.txt', 'r' , encoding='utf-8') as file :
        ch = file.read().replace('\n', '')
        
    i = 0
    while i < len(ch):
        indexOfopen = ch.find("{", i)
        if indexOfopen == -1:
            break
        indexOfclose = ch.find("}", indexOfopen)
        stTable.append(ch[indexOfopen:indexOfclose+1])
        i = indexOfclose + 1
    return stTable

def returned_documents():
    stTable = []
    stTable = read_data_file()
    documents = []
    for st in stTable:
        documents.append(ast.literal_eval(st))
    return documents
        
def vect_model_TF() :
    '''
    1. TF (Term Frequency)?
    t = max mot occ; d = document
        TF(t, d) = (nombre d'occurrences de t dans d) / (nombre total de mots dans d)
        Mesure la fréquence d'un mot dans un document.
        Document: "le chat le chien le"
            - Mot "le": 3 occurrences sur 5 mots → TF = 3/5 = 0,6
            - Mot "chat": 1 occurrence sur 5 mots → TF = 1/5 = 0,2
            - Mot "chien": 1 occurrence sur 5 mots → TF = 1/5 = 0,2
            => Chaque mot du document possède une TF.
    '''   
   
    documents = {}
    documents = returned_documents()
    TF_list = []
    #TF (Term Frequency)
    for i, doc in enumerate(documents):
        total = sum(doc.values())
        tf_doc = {}
        for mot, freq in doc.items():
            tf_doc[mot] = freq / total
        TF_list.append(tf_doc)
    
    return TF_list

def vect_model_IDF() :
    '''
        2. IDF (Inverse Document Frequency)?
    Mesure la rareté d'un mot dans l'ensemble des documents.
        IDF(t) = log( N / df(t) )
        N = nombre total de documents
        df(t) = nombre de documents contenant le mot t 
        => fi 9adech mn document mot hedhika mwjouda
        On a 100 documents:
            - Mot "chat" apparaît dans 10 documents → IDF = log(100/10) = log(10) = 1
            - Mot "le" apparaît dans 95 documents → IDF = log(100/95) = log(1,05) ≈ 0,02
            - Mot "rare" apparaît dans 1 document → IDF = log(100/1) = log(100) = 2
    '''
    documents = {}
    documents = returned_documents()
    #IDF (Inverse Document Frequency)
    IDF = {}
    N = len(documents) # nb totale de doc
    for i in range(len(documents)):
        for mot_doc in documents[i]:
            count_df = 0  # count how many documents contain this word
            for doc in documents:
                if mot_doc in doc:
                    count_df += 1
            if count_df > 0:
                IDF[mot_doc] = math.log(N / count_df)
    return IDF

#TF-IDF = TF × IDF
def vect_model_mot_poids_final(TF_list, IDF):
    ''' 
     3. TF-IDF = TF × IDF
    Combine les deux mesures pour donner un poids plus important aux mots fréquents 
    dans un document mais rares dans l'ensemble.
        TF-IDF(t, d) = TF(t, d) × IDF(t)
    '''
    result = []
    for tf_doc in TF_list:
        tfidf_doc = {}
        for mot, tf_val in tf_doc.items():
            tfidf_doc[mot] = tf_val * IDF.get(mot, 0)
        result.append(tfidf_doc)
    
    return result

def vect_model_cosinus(document, requete):
    '''
    4. Cosine Similarity (Similitude Cosinus)?
    Mesure la similarité entre deux documents ou entre un document et une requête.
        cos(θ) = (A · B) / (sqrt(||A||^2) * sqrt(||B||^2))  ||A|| = sqrt(A1^2 + A2^2 + ... + An^2) et ||B|| = sqrt(B1^2 + B2^2 + ... + Bn^2)
        A et B sont les vecteurs de poids des mots dans les documents ou la requête.
        ||A|| et ||B|| sont les normes des vecteurs A et B.
        La similitude cosinus varie entre -1 et 1, où 1 signifie que les vecteurs sont identiques, 
        0 signifie qu'ils sont orthogonaux (pas de similarité), et -1 signifie qu'ils sont opposés.
    ''' 
    # Produit scalaire
    produit = 0
    for mot, poids_doc in document.items():
        if mot in requete:
            produit += poids_doc * requete[mot]
    
    # Normes
    norme_doc = math.sqrt(sum(p ** 2 for p in document.values()))
    norme_req = math.sqrt(sum(p ** 2 for p in requete.values()))
    
    if norme_doc == 0 or norme_req == 0:
        return 0
    
    return produit / (norme_doc * norme_req)   

def search_query(query, tfidf_documents, idf):
    """
    Convertit une requête en vecteur TF-IDF et calcule la similarité cosinus
    avec chaque document en utilisant vect_model_cosinus.
    """
    # 1. Tokenisation et calcul des fréquences dans la requête

    mots = process_query_vect(query)
    total = len(mots)
    freq = {}
    for mot in mots:
        freq[mot] = freq.get(mot, 0) + 1
    
    # 2. TF de la requête
    tf_query = {mot: count/total for mot, count in freq.items()}
    
    # 3. TF-IDF de la requête
    vecteur_requete = {}
    for mot, tf_val in tf_query.items():
        vecteur_requete[mot] = tf_val * idf.get(mot, 0)
    
    # 4. Comparaison avec chaque document via vect_model_cosinus
    results = []
    for i, doc_vec in enumerate(tfidf_documents):
        score = vect_model_cosinus(doc_vec, vecteur_requete)
        results.append((i+1, score))   # (numéro du document, score)
    
    return results

def bool_document(documents):
    """
    Construit un index booléen : pour chaque terme, l'ensemble des documents où il apparaît.
    Retourne : dict {terme: set(num_documents)} (numéros 1-indexés)
    """
    index = {}
    for i, doc in enumerate(documents, start=1):
        for mot in doc.keys():
            if mot not in index:
                index[mot] = set()
            index[mot].add(i)
    return index

def modele_bool(requete, bool_index):
    """
    Modèle booléen : requête avec opérateurs ET, OU, SAUF (insensibles à la casse).
    Retourne un set de numéros de documents pertinents.
    Exemples : "intelligence ET ia", "cuisine OU football", "être SAUF intelligence"
    """
    tokens = process_query_bool(requete)
    if not tokens:
        return set()
    
    # Cas d'un seul terme
    if len(tokens) == 1:
        return bool_index.get(tokens[0], set())
    
    # Opérateur ET
    if "et" in tokens:
        pos = tokens.index("et")
        gauche = ' '.join(tokens[:pos])
        droite = ' '.join(tokens[pos+1:])
        set_gauche = modele_bool(gauche, bool_index)
        set_droite = modele_bool(droite, bool_index)
        return set_gauche.intersection(set_droite)
 # Opérateur OU
    elif "ou" in tokens:
        pos = tokens.index("ou")
        gauche = ' '.join(tokens[:pos])
        droite = ' '.join(tokens[pos+1:])
        set_gauche = modele_bool(gauche, bool_index)
        set_droite = modele_bool(droite, bool_index)
        return set_gauche.union(set_droite)
    
    # Opérateur SAUF
    elif "sauf" in tokens:
        pos = tokens.index("sauf")
        gauche = ' '.join(tokens[:pos])
        droite = ' '.join(tokens[pos+1:])
        set_gauche = modele_bool(gauche, bool_index)
        set_droite = modele_bool(droite, bool_index)
        return set_gauche.difference(set_droite)
    
    else:
        # Pas d'opérateur : ET implicite entre tous les mots
        result = bool_index.get(tokens[0], set())
        for t in tokens[1:]:
            result = result.intersection(bool_index.get(t, set()))
        return result
 
docs = returned_documents()
TF = vect_model_TF()
IDF = vect_model_IDF()
TF_IDF = vect_model_mot_poids_final(TF,IDF)
'''
print("=====================================================================================================\n")
print("IDF:", IDF)
print("\n=====================================================================================================\n")
print("TF-IDF:", TF_IDF)
print("\n=====================================================================================================\n")
'''

# Ce code ne s'exécute que si le fichier est lancé directement
# (pas quand il est importé par un autre fichier)
if __name__ == "__main__":
    reponse = input("\nVoulez-vous tester le modèle booléen ? (o/n) : ")
    if reponse.lower() == 'o':
        requete = input("Entrez votre requête booléenne : ")
        #requete = process_query(requete)
        bool_index = bool_document(docs)
        resultats = modele_bool(requete, bool_index)
        if resultats:
            print(f"Documents pertinents : {sorted(resultats)}")
        else:
            print("Aucun document pertinent.")
    else :
        requete = input("Entrez votre requête vectorielle : ")
        #requete = process_query(requete)
        resultats = search_query(requete, TF_IDF, IDF)
        print("\nRésultats (document, similarité cosinus) :")
        for doc_num, score in resultats:
            print(f"  Document {doc_num} : {score}")

