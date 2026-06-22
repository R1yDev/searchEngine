def process_query_bool(query):
   
    # Nettoyage basique de la ponctuation pour aider le split()
    # On remplace la ponctuation par des espaces pour éviter que "mot," ne soit considéré comme un mot unique

    # Define stop words list sans "et", "ou", "sauf"
    stopList = [
        "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", 
        "le", "la","là" ,"j", "les", "l", "un", "une", "des", "du", "de", "au", "aux", 
        "ce", "cet", "cette", "ces","c'est","mon", "ton", "son", "ma", "ta", "sa", 
        "mes", "tes", "ses", "notre", "votre", "nos", "vos", "leur", "leurs",
        "me", "te", "se", "lui", "leur", "eux", "moi", "toi", "soi", 
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
    
    terminaisons_er_list = [
    # je[0:5]
    "e", "ais", "ai", "erai", "asse",
    # tu[5:10]
    "es", "ais", "as", "eras", "asses",
    # il/elle[10:15]
    "e", "ait", "a", "era", "ât",
    # nous[15:20]
    "ons", "ions", "âmes", "erons", "assions",
    # vous[20:25]
    "ez", "iez", "âtes", "erez", "assiez",
    # ils/elles[25:30]
    "ent", "aient", "èrent", "eront", "assent"
   ]

# Terminaisons du 2eme groupe 
    terminaisons_ir_list = [
    # je[0:3]
    "is", "issais", "irai",
    # tu[3:6]
    "is", "issais", "iras",
    # il/elle[6:9]  
    "it", "issait", "ira",
    # nous[9:12]
    "issons", "issions", "irons",
    # vous[12:15]
    "issez", "issiez", "irez",
    # ils/elles[15:18]
    "issent", "issaient", "iront"
    ]

    # Terminaisons du 3eme groupe
    terminaisons_re_list = [
    # je[0:4]
    "s", "x", "ds", "ts",
    # tu[4:8]
    "s", "x", "ds", "ts",
    # il/elle[8:12]
    "t", "d", "c",
    # nous[12:13]
    "ons",
    # vous[13:14]
    "ez",
    # ils/elles[14:18]
    "ent", "nt", "ient", "ennent"
]
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
    
    # Tokenization
    i = 0
    while i < len(query):
        if query[i] in [".", ",", "!", "?", ";", ":", "(", ")", "[", "]", "{", "}", "\"", "'", "-"] :
            query = query[:i] + " " + query[i+1:]  # Remplace la ponctuation par un espace
        else:
            i += 1 
    
    list1 = query.lower().split()
    
    #ÉTAPE 1: Traiter les verbes conjugués partir existence d'un pronom avant le verbe
    i = 0
    while i < len(list1) - 1:
        if list1[i] in stopList[0:9]:
            trouve = False
            for end in range(8, 0, -1):
                if len(list1[i+1]) < end:
                    continue
                terminaison = list1[i+1][-end:]
                # Vérifier dans le 1er groupe
                if terminaison in terminaisons_er_list:
                    list1[i+1] = list1[i+1][:-end] + "er"
                    trouve = True
                    break
                # Vérifier dans le 2ème groupe
                elif terminaison in terminaisons_ir_list:
                    list1[i+1] = list1[i+1][:-end] + "ir"
                    trouve = True
                    break
                # Vérifier dans le 3ème groupe
                elif terminaison in terminaisons_re_list:
                    list1[i+1] = list1[i+1][:-end] + "re"
                    trouve = True
                    break
        i += 1

    # ÉTAPE 2: Traiter les auxiliaires et modaux (sans pronom)
    i = 0
    while i < len(list1):
        if list1[i] in auxiliaires:
            list1[i] = auxiliaires[list1[i]]
        i += 1
        
    #ÉTAPE 3: exclure les mots de la stop_list
    for i in range(len(list1)):
        if list1[i] in stopList: 
            list1[i] = list1[i].replace(list1[i], "") #Exclude stop words from the list
        if list1[i][:2] in ["l'","d'","m'","j'"]: #Exclude stop words that are in the form of l', d' or m'
            list1[i] = list1[i][2:] #Exclude stop words from the list

    #ÉTAPE 4: traiter les mots au pluriel en singulier 
    exceptions = ["deux", "trois", "six", "dix", "neuf", "cinq", "huit", "neuf", "dix", "bras", 
                  "souris", "fois", "pays", "corps","poids", "temps", "voix", "nez", "repas"]
    test = True
    i = 0     
    while test and i < len(list1):
        if  list1[i][-1:] == "s" and list1[i] not in stopList and list1[i] not in exceptions: #remplace plural by singular 
            list1[i] = list1[i][:-1]
        elif list1[i][-4:] == "eaux" and list1[i] not in exceptions:
            list1[i] = list1[i][:-4]+"eau"
        elif list1[i][-3:] in ["aux","oux","eux"] and list1[i] not in exceptions:
            list1[i] = list1[i][:-3]+"al"
        i += 1   
    listMot = []
    
    #ÉTAPE 5: remove empty strings from the list
    for mot in list1:
        if mot != "":
            listMot.append(mot)
    
    return listMot


def process_query_vect(query):
   
    # Nettoyage basique de la ponctuation pour aider le split()
    # On remplace la ponctuation par des espaces pour éviter que "mot," ne soit considéré comme un mot unique

    # Define stop words list adding "et", "ou", "sauf"
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
    
    terminaisons_er_list = [
    # je[0:5]
    "e", "ais", "ai", "erai", "asse",
    # tu[5:10]
    "es", "ais", "as", "eras", "asses",
    # il/elle[10:15]
    "e", "ait", "a", "era", "ât",
    # nous[15:20]
    "ons", "ions", "âmes", "erons", "assions",
    # vous[20:25]
    "ez", "iez", "âtes", "erez", "assiez",
    # ils/elles[25:30]
    "ent", "aient", "èrent", "eront", "assent"
   ]

# Terminaisons du 2eme groupe 
    terminaisons_ir_list = [
    # je[0:3]
    "is", "issais", "irai",
    # tu[3:6]
    "is", "issais", "iras",
    # il/elle[6:9]  
    "it", "issait", "ira",
    # nous[9:12]
    "issons", "issions", "irons",
    # vous[12:15]
    "issez", "issiez", "irez",
    # ils/elles[15:18]
    "issent", "issaient", "iront"
    ]

    # Terminaisons du 3eme groupe
    terminaisons_re_list = [
    # je[0:4]
    "s", "x", "ds", "ts",
    # tu[4:8]
    "s", "x", "ds", "ts",
    # il/elle[8:12]
    "t", "d", "c",
    # nous[12:13]
    "ons",
    # vous[13:14]
    "ez",
    # ils/elles[14:18]
    "ent", "nt", "ient", "ennent"
]
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
    
    # Tokenization
    i = 0
    while i < len(query):
        if query[i] in [".", ",", "!", "?", ";", ":", "(", ")", "[", "]", "{", "}", "\"", "'", "-"] :
            query = query[:i] + " " + query[i+1:]  # Remplace la ponctuation par un espace
        else:
            i += 1 
    
    list1 = query.lower().split()
    
    #ÉTAPE 1: Traiter les verbes conjugués partir existence d'un pronom avant le verbe
    i = 0
    while i < len(list1) - 1:
        if list1[i] in stopList[0:9]:
            trouve = False
            for end in range(8, 0, -1):
                if len(list1[i+1]) < end:
                    continue
                terminaison = list1[i+1][-end:]
                # Vérifier dans le 1er groupe
                if terminaison in terminaisons_er_list:
                    list1[i+1] = list1[i+1][:-end] + "er"
                    trouve = True
                    break
                # Vérifier dans le 2ème groupe
                elif terminaison in terminaisons_ir_list:
                    list1[i+1] = list1[i+1][:-end] + "ir"
                    trouve = True
                    break
                # Vérifier dans le 3ème groupe
                elif terminaison in terminaisons_re_list:
                    list1[i+1] = list1[i+1][:-end] + "re"
                    trouve = True
                    break
        i += 1

    # ÉTAPE 2: Traiter les auxiliaires et modaux (sans pronom)
    i = 0
    while i < len(list1):
        if list1[i] in auxiliaires:
            list1[i] = auxiliaires[list1[i]]
        i += 1
        
    #ÉTAPE 3: exclure les mots de la stop_list
    for i in range(len(list1)):
        if list1[i] in stopList: 
            list1[i] = list1[i].replace(list1[i], "") #Exclude stop words from the list
        if list1[i][:2] in ["l'","d'","m'","j'"]: #Exclude stop words that are in the form of l', d' or m'
            list1[i] = list1[i][2:] #Exclude stop words from the list

    #ÉTAPE 4: traiter les mots au pluriel en singulier 
    exceptions = ["deux", "trois", "six", "dix", "neuf", "cinq", "huit", "neuf", "dix", "bras", 
                  "souris", "fois", "pays", "corps","poids", "temps", "voix", "nez", "repas"]
    test = True
    i = 0     
    while test and i < len(list1):
        if  list1[i][-1:] == "s" and list1[i] not in stopList and list1[i] not in exceptions: #remplace plural by singular 
            list1[i] = list1[i][:-1]
        elif list1[i][-4:] == "eaux" and list1[i] not in exceptions:
            list1[i] = list1[i][:-4]+"eau"
        elif list1[i][-3:] in ["aux","oux","eux"] and list1[i] not in exceptions:
            list1[i] = list1[i][:-3]+"al"
        i += 1   
    listMot = []
    
    #ÉTAPE 5: remove empty strings from the list
    for mot in list1:
        if mot != "":
            listMot.append(mot)
    
    return listMot

