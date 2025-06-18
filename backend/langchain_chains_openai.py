import os
import time
import pickle
import requests
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
try:
    # Essayer d'abord avec le nouveau module
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    # Fallback au module community si nécessaire
    from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Chemin pour stocker l'index vectoriel
VECTORSTORE_PATH = os.path.join("data", "faiss_index.pkl")
METADATA_PATH = os.path.join("data", "vector_metadata.pkl")

# Initialiser Embeddings 
# Option: utiliser OpenAI pour les embeddings peut améliorer la qualité des recherches
emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Prompt template pour la consultation
template = """
Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique. Pour les symptômes décrits: {symptoms},
formule une explication structurée selon les sections suivantes dans CET ORDRE EXACT en utilisant DIRECTEMENT les informations issues du CSV (colonne → section):

Diagnostic possible (maladiesoigneeparrecette → pathologie)
Commence par cette phrase EXACTE: "D'après vos symptômes décrits, il est possible que vous souffriez de {pathology}." puis mets le nom de la pathologie en MAJUSCULES. Tu ne dois JAMAIS affirmer avec certitude qu'il s'agit de cette maladie. Sois prudent et précise qu'il s'agit d'une possibilité basée sur les symptômes décrits et non d'un diagnostic médical définitif. Recommande toujours une consultation médicale professionnelle pour confirmer. (3-4 phrases maximum)

Symptômes associés (maladiesoigneeparrecette → symptômes)
Présente les symptômes typiques de cette pathologie de manière pédagogique. Décris précisément comment ils se manifestent pour aider à reconnaître la maladie. (3-5 phrases)

Présentation de {plant_name} (plante_recette → présentation)
Présente cette plante comme un conteur traditionnel, évoquant son histoire et ses usages traditionnels en Afrique. Utilise le nom scientifique et les noms locaux s'ils sont fournis. (4-5 phrases)

Mode d'action (plante_composantechimique → mode d'action)
En t'appuyant sur les composants actifs mentionnés, explique simplement comment la plante agit pour traiter la pathologie. Évite les termes techniques tout en restant scientifiquement correct. (3-4 phrases)

Informations de traitement (recette, plante_quantite_recette, plante_partie_recette → traitement)
Transforme ces données brutes en conseils pratiques et accessibles:
- Préparation: {preparation} 
- Dosage: {dosage}
- Parties utilisées: {parties_utilisees}
Explique clairement comment préparer, doser et utiliser les bonnes parties de la plante. (5-7 phrases maximum au total)

Précautions et contre-indications (recette_contreindication, plante_contreindication → précautions)
Cette section doit être structurée en deux parties:
1. Contre-indications liées à la recette: {contre_indications_recette} 
2. Contre-indications liées à la plante: {contre_indications_plante}
Humanise ces données pour les rendre compréhensibles. (4-6 phrases)

Composants actifs (plante_composantechimique → composants)
Transforme cette liste de composants: "{composants}" en expliquant leurs effets thérapeutiques principaux. Ne mentionne QUE les composés qui apparaissent explicitement dans cette liste. (3-4 phrases)

Résumé de traitement (synthèse des informations précédentes)
Synthétise en 4-5 phrases le diagnostic et le traitement, incluant clairement:
1. Le nom de la pathologie (en précisant qu'il s'agit d'une possibilité)
2. La plante et sa préparation
3. La posologie exacte (nombre de prises par jour, quantité)
4. La durée recommandée du traitement (7 jours par défaut si non spécifié)
5. Quand consulter un professionnel (si les symptômes persistent après 3 jours)

EXIGENCES STRICTES:
1. Chaque section DOIT être présente, avec son titre exact et dans l'ordre indiqué
2. Utilise UNIQUEMENT les informations fournies dans le contexte du CSV (voir correspondances)
3. Si une information est marquée "Non spécifié", propose une recommandation générale sans inventer
4. Ton langage doit être accessible et chaleureux, mais précis sur les dosages et précautions
5. Réponds UNIQUEMENT en français, structure ta réponse avec des sauts de ligne entre les sections
"""
prompt = PromptTemplate(input_variables=["symptoms", "plant_data", "plant_name"], template=template)

# Initialisation des modèles OpenAI de façon robuste
try:
    # Initialisation du modèle OpenAI pour la consultation
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY
    )

    # Chaîne pour la consultation
    chain = LLMChain(llm=llm, prompt=prompt)

    # Modèle LLM séparé pour le chat (discussions générales)
    llm_chat = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        openai_api_key=OPENAI_API_KEY
    )
    
    # Vérifier que les modèles sont correctement initialisés
    if not llm or not llm_chat:
        raise ValueError("Erreur d'initialisation des modèles OpenAI")
        
    print("Modèles OpenAI initialisés avec succès")
except Exception as e:
    print(f"Erreur lors de l'initialisation des modèles OpenAI: {e}")
    # Ne pas lever d'exception pour permettre au reste du code de fonctionner
    # Les erreurs seront gérées lors de l'appel des fonctions

def fetch_image(plant_name: str) -> str:
    url = f"https://api.unsplash.com/search/photos?query={plant_name}&client_id={UNSPLASH_KEY}&per_page=1"
    resp = requests.get(url).json()
    return resp["results"][0]["urls"]["small"] if resp["results"] else ""

# Fonctions pour la gestion de l'index vectoriel
def get_csv_last_modified(csv_path):
    """Obtenir la date de dernière modification du fichier CSV source"""
    try:
        if not os.path.exists(csv_path):
            print(f"AVERTISSEMENT: Le fichier CSV n'existe pas: {csv_path}")
            return 0
        mtime = os.path.getmtime(csv_path)
        print(f"Dernière modification du CSV: {csv_path} - {mtime}")
        return mtime
    except OSError as e:
        print(f"Erreur lors de l'accès au fichier CSV: {e}")
        return 0

def create_documents_from_df(df):
    """Créer les documents à vectoriser à partir du DataFrame"""
    documents = []
    for idx, row in df.iterrows():
        # Créer un contenu enrichi pour chaque plante avec les symptômes qu'elle traite
        content = f"Symptômes: {row.get('maladiesoigneeparrecette', '')}\n"
        content += f"Plante: {row.get('plante_recette', '')}\n"
        content += f"Dosage: {row.get('plante_quantite_recette', '')}\n"
        content += f"Préparation: {row.get('recette', '')}"
        
        # Créer un document avec metadata pour faciliter la récupération
        metadata = {
            "plant_name": str(row.get('plante_recette', '')).split(';')[0].strip(),
            "index": idx
        }
        documents.append(Document(page_content=content, metadata=metadata))
    return documents

def build_and_save_vectorstore(df, csv_path):
    """Construire et sauvegarder l'index vectoriel"""
    try:
        # Créer les documents
        documents = create_documents_from_df(df)
        
        # Vectoriser les documents
        vs = FAISS.from_documents(documents, emb)
        
        # Créer le dossier de données s'il n'existe pas
        os.makedirs(os.path.dirname(VECTORSTORE_PATH), exist_ok=True)
        
        # Sauvegarder le vectorstore
        with open(VECTORSTORE_PATH, "wb") as f:
            pickle.dump(vs, f)
        
        # Sauvegarder les métadonnées
        metadata = {
            "last_modified": get_csv_last_modified(csv_path),
            "document_count": len(documents),
            "created_at": time.time()
        }
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(metadata, f)
        
        print(f"Vectorstore créé et sauvegardé avec {len(documents)} documents")
        return vs
    except Exception as e:
        print(f"Erreur lors de la création du vectorstore: {e}")
        return None

def should_rebuild_index(csv_path):
    """Déterminer si l'index doit être reconstruit en fonction des modifications du fichier CSV"""
    # Si les fichiers de l'index n'existent pas, reconstruire
    if not os.path.exists(VECTORSTORE_PATH) or not os.path.exists(METADATA_PATH):
        print("Index vectoriel non trouvé, création requise")
        return True
    
    try:
        # Charger les métadonnées
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
        
        # Vérifier si le CSV a été modifié depuis la dernière construction
        current_mtime = get_csv_last_modified(csv_path)
        last_indexed_mtime = metadata.get("last_modified", 0)
        
        if current_mtime > last_indexed_mtime:
            print(f"Le fichier CSV a été modifié ({time.ctime(current_mtime)})")
            print(f"Dernière indexation: {time.ctime(last_indexed_mtime)}")
            return True
        
        return False
    except Exception as e:
        print(f"Erreur lors de la vérification de l'index: {e}")
        return True

def load_or_build_vectorstore(df, csv_path):
    """Charger l'index vectoriel existant ou en créer un nouveau si nécessaire"""
    if should_rebuild_index(csv_path):
        print("Construction d'un nouvel index vectoriel...")
        return build_and_save_vectorstore(df, csv_path)
    
    try:
        # Charger l'index existant
        with open(VECTORSTORE_PATH, "rb") as f:
            vs = pickle.load(f)
        print("Index vectoriel chargé avec succès depuis le disque")
        return vs
    except Exception as e:
        print(f"Erreur lors du chargement de l'index: {e}, reconstruction...")
        return build_and_save_vectorstore(df, csv_path)

# Fonction principale pour obtenir des recommandations
def get_recommendation(symptoms: str, df, csv_path="data/baseplante.csv"):
    import pandas as pd
    
    # Initialiser le vectorstore une seule fois et le mettre en cache
    global vectorstore
    
    if 'vectorstore' not in globals() or vectorstore is None:
        # Charge ou construit l'index vectoriel selon si le fichier source a été modifié
        vectorstore = load_or_build_vectorstore(df, csv_path)
    
    # Vérifier si le vectorstore a été initialisé avec succès
    vectorstore_initialized = vectorstore is not None    # Approche RAG: Recherche sémantique avec embeddings
    matches = None
    if vectorstore_initialized:
        try:
            print(f"Recherche sémantique pour les symptômes: '{symptoms}'")
            # Effectuer une recherche par similarité sémantique
            similar_docs = vectorstore.similarity_search(symptoms, k=3)
            
            if similar_docs:
                # Récupérer l'index du document le plus similaire
                most_similar_doc = similar_docs[0]
                doc_index = most_similar_doc.metadata.get('index')
                
                if doc_index is not None:
                    print(f"Document similaire trouvé avec index: {doc_index}")
                    plant_data = df.iloc[doc_index].to_dict()
                    matches = pd.DataFrame([plant_data])
                    print(f"RAG: Document trouvé avec similarité: {most_similar_doc.metadata.get('plant_name')}")
                else:
                    print("Document trouvé mais sans index dans les métadonnées")
            else:
                print("Aucun document similaire trouvé")
        except Exception as e:
            print(f"Erreur lors de la recherche sémantique: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback: méthode de recherche par mots-clés si la recherche sémantique échoue
    if matches is None or len(matches) == 0:
        print("Fallback à la recherche par mots-clés")
        # Nettoyage et préparation du texte de recherche
        clean_symptoms = symptoms.lower()
        
        # Enlever les expressions courantes et nettoyer le texte
        for phrase in ["je pense que j'ai", "j'ai", "je souffre de", "je crois que", "traitement pour", "soigner", "guérir"]:
            clean_symptoms = clean_symptoms.replace(phrase, "")
        clean_symptoms = clean_symptoms.strip()
        
        # Dictionnaire de synonymes et termes associés pour améliorer la recherche
        symptom_mapping = {
            "palud": ["malaria", "palu", "fièvre", "frissons"],
            "malaria": ["paludisme", "palu", "fièvre", "frissons"],
            "diarrhée": ["ventre", "intestin", "selles", "liquide"],
            "constipation": ["intestin", "selles", "difficile"],
            "fièvre": ["température", "chaud", "corps"],
            "toux": ["respiration", "poumon", "gorge"],
            "mal de tête": ["tête", "migraine", "céphalée"],
            "douleur": ["mal", "souffrance"]
        }
        
        # Vérifier d'abord les correspondances directes
        for keyword, synonyms in symptom_mapping.items():
            if keyword in clean_symptoms or any(syn in clean_symptoms for syn in synonyms):
                search_term = keyword  # Utiliser le terme principal pour la recherche
                print(f"Correspondance trouvée pour le terme: {keyword} via {synonyms if keyword not in clean_symptoms else 'correspondance directe'}")
                matches = df[df["maladiesoigneeparrecette"].str.contains(search_term, case=False, na=False, regex=True)]
                if not matches.empty:
                    break
        
        # Si toujours pas de correspondance, essayer une recherche plus générale
        if matches is None or len(matches) == 0:
            matches = df[df["maladiesoigneeparrecette"].str.contains(clean_symptoms, case=False, na=False)]
    
    # Si toujours pas de correspondance, renvoyer le paludisme par défaut
    if matches.empty:
        if "palud" in clean_symptoms or "malaria" in clean_symptoms:
            matches = df[df["maladiesoigneeparrecette"].str.contains("malaria|paludisme", case=False, na=False, regex=True)]
    
    # Si toujours pas de correspondance, renvoyer une erreur
    if matches.empty:
        raise ValueError(f"Aucune plante trouvée pour les symptômes: {symptoms}. Veuillez essayer une description plus précise comme 'paludisme', 'diarrhée', etc.")
    
    # Récupérer la première correspondance
    plant = matches.iloc[0].to_dict()
    plant_data = plant
    
    # Extraire le nom de la plante (première plante de la liste)
    plant_names = plant.get("plante_recette", "").split(";")[0].strip() if plant.get("plante_recette") else "Plante inconnue"
    
    # Obtenir l'image
    try:
        image_url = plant.get("image_url") or fetch_image(plant_names)
    except Exception as e:
        print(f"Erreur lors de la récupération d'image: {e}")
        image_url = ""
    
    # Extraire les informations importantes
    dosage = plant.get("plante_quantite_recette", "Dosage non spécifié")
    preparation = plant.get("recette", "Préparation non spécifiée")
    contre_indications = plant.get("recette_contreindication", "") or plant.get("plante_contreindication", "Aucune contre-indication spécifiée")
    partie_utilisee = plant.get("plante_partie_recette", "Partie non spécifiée")
    composants = plant.get("plante_composantechimique", "Composants chimiques non spécifiés")
    nom_local = plant.get("plante_nomlocal", "")
    langue = plant.get("nomlocal_danslalangue", "")
    pays = plant.get("danslalangue_dupays", "")
    
    # Formater les composants chimiques pour une meilleure lisibilité
    if composants and ";" in composants:
        composants_par_plante = {}
        composants_parts = composants.split(";")
        
        for part in composants_parts:
            if ":" in part:
                plante, composant = part.split(":", 1)
                plante = plante.strip()
                composant = composant.strip()
                
                # Ne pas ajouter les composants NULL
                if "NULL" not in composant.upper():
                    if plante not in composants_par_plante:
                        composants_par_plante[plante] = []
                    
                    composants_par_plante[plante].append(composant)
        
        composants_lignes = []
        for plante, comps in composants_par_plante.items():
            if comps:  # S'assurer qu'il y a des composants valides
                composants_lignes.append(f"{plante}: {', '.join(comps)}")
        
        if composants_lignes:
            composants = "\n".join(composants_lignes)
        else:
            # Si aucun composant valide n'est trouvé
            composants = "Composants chimiques spécifiques non disponibles actuellement"
    elif "NULL" in composants.upper():
        composants = "Composants chimiques spécifiques non disponibles actuellement"
    
    # Traitement des noms locaux pour un affichage plus compact
    nom_local_info = ""
    if nom_local and langue and pays:
        # Extraction des noms principaux
        noms_locaux_simplifies = {}
        
        # Si les chaînes contiennent des points-virgules, les traiter comme des listes
        if ";" in nom_local:
            noms_plantes_raw = nom_local.split(";")
            langues_raw = langue.split(";") if ";" in langue else [langue] * len(noms_plantes_raw)
            pays_raw = pays.split(";") if ";" in pays else [pays] * len(noms_plantes_raw)
            
            # Extraire uniquement les 3 premiers noms locaux les plus courants
            plant_counts = {}
            for nom in noms_plantes_raw:
                # Extraire juste le nom sans la partie plante
                if ":" in nom:
                    plant_name, local_name = nom.split(":", 1)
                    plant_name = plant_name.strip()
                    # Compter les occurrences de chaque plante principale
                    if plant_name not in plant_counts:
                        plant_counts[plant_name] = 0
                    plant_counts[plant_name] += 1
            
            # Trier par nombre d'occurrences et prendre les 3 plus fréquentes
            main_plants = sorted(plant_counts.keys(), key=lambda x: plant_counts[x], reverse=True)[:3]
            
            # Construire une liste des noms locaux par plante principale
            for plant_name in main_plants:
                noms_locaux_simplifies[plant_name] = []
                
            # Limiter à 5 noms locaux maximum par plante principale
            for i, nom in enumerate(noms_plantes_raw):
                if i >= len(langues_raw) or i >= len(pays_raw):
                    break
                    
                if ":" in nom:
                    plant_name, local_name = nom.split(":", 1)
                    plant_name = plant_name.strip()
                    local_name = local_name.strip()
                    
                    if plant_name in main_plants:
                        langue_nom = langues_raw[i].strip() if i < len(langues_raw) else ""
                        pays_nom = pays_raw[i].strip() if i < len(pays_raw) else ""
                        
                        if len(noms_locaux_simplifies[plant_name]) < 5:  # Limiter à 5 noms par plante
                            if langue_nom and pays_nom:
                                noms_locaux_simplifies[plant_name].append(f"{local_name} ({langue_nom}, {pays_nom})")
            
            # Formatage du texte final
            plant_infos = []
            for plant_name, noms in noms_locaux_simplifies.items():
                if noms:
                    # Filtrer les noms contenant "NULL"
                    noms_valides = [nom for nom in noms if "NULL" not in nom]
                    if noms_valides:
                        noms_text = ", ".join(noms_valides[:5])  # Limiter à 5 noms locaux par plante
                        plant_infos.append(f"{plant_name} est connue sous le nom de: {noms_text}")
            
            if plant_infos:
                nom_local_info = "Noms locaux: " + ". ".join(plant_infos)
        else:
            # Cas simple: un seul nom local, vérifier qu'il n'est pas NULL
            if "NULL" not in nom_local:
                nom_local_info = f"Nom local: {nom_local} en {langue} ({pays})."
            else:
                nom_local_info = ""
    
    # Extraire les pathologies traitées
    pathologies = plant.get('maladiesoigneeparrecette', 'Non spécifié')
    
    # Correction des pathologies en cas d'incohérence
    # Corriger spécifiquement le cas où les symptômes contiennent "paludisme" mais 
    # la pathologie renvoyée est autre chose que paludisme/malaria
    if "palud" in symptoms.lower() or "malaria" in symptoms.lower():
        if not ("palud" in pathologies.lower() or "malaria" in pathologies.lower()):
            print(f"Correction de la pathologie: {pathologies} -> paludisme (basé sur les symptômes)")
            pathologies = "paludisme"
    
    # Utiliser GPT-3.5-Turbo pour générer une explication détaillée
    print("Utilisation de GPT-3.5-Turbo pour la génération d'explication enrichie...")
    
    try:        # Extraction des variables pour les utiliser dans le prompt avec des mappings clairs vers les colonnes du CSV
        explanation = chain.run(
            symptoms=symptoms,
            plant_data=plant_data,
            plant_name=plant_names,
            pathology=pathologies.strip(),  # De la colonne maladiesoigneeparrecette
            preparation=preparation,        # De la colonne recette
            dosage=dosage,                  # De la colonne plante_quantite_recette
            parties_utilisees=partie_utilisee,  # De la colonne plante_partie_recette
            contre_indications_recette=plant.get("recette_contreindication", "Aucune contre-indication spécifique à la recette mentionnée"),
            contre_indications_plante=plant.get("plante_contreindication", "Aucune contre-indication spécifique à la plante mentionnée"),
            composants=composants           # De la colonne plante_composantechimique
        )
        print("Explication générée avec succès par GPT")
          # Vérifier que toutes les sections sont présentes avec une validation plus stricte
        required_sections = [
            "Diagnostic possible", 
            "Symptômes associés", 
            "Présentation de", 
            "Mode d'action", 
            "Informations de traitement", 
            "Précautions et contre-indications", 
            "Composants actifs", 
            "Résumé de traitement"
        ]
        
        # Vérification approfondie des sections et de leur contenu
        missing_sections = [section for section in required_sections if section not in explanation]
        if missing_sections:
            print(f"Sections manquantes dans la réponse OpenAI: {missing_sections}")
            raise ValueError(f"Réponse OpenAI incomplète, sections manquantes: {missing_sections}")
        
        # Validation de contenu supplémentaire
        content_validations = [
            (f"D'après vos symptômes décrits, il est possible que vous souffriez de {pathologies}", "format de diagnostic incorrect"),
            (f"{pathologies.upper()}", "pathologie non mise en majuscules"),
            (f"{plant_names}", "nom de plante manquant"),
            (f"{preparation[:15]}", "préparation non mentionnée"),
            (f"{dosage[:10]}", "dosage non mentionné")
        ]
        
        for text, error_msg in content_validations:
            if text and text.strip() and text.strip().lower() not in explanation.lower():
                print(f"Validation de contenu échouée: {error_msg}")
                raise ValueError(f"Réponse OpenAI insuffisante: {error_msg}")
        
        # Nettoyer et formater l'explication pour correspondre au format attendu
        explanation = explanation.strip()
        
    except Exception as e:
        print(f"Erreur lors de la génération de l'explication avec GPT: {e}")
        import traceback
        traceback.print_exc()
          # Créer une explication de secours améliorée et structurée avec une mise en forme identique
        # Préparation des symptômes typiques selon la pathologie
        symptomes_mapping = {
            "palud": "fièvre intermittente, frissons, maux de tête, fatigue, douleurs musculaires et articulaires",
            "malaria": "fièvre intermittente, frissons, maux de tête, fatigue, douleurs musculaires et articulaires",
            "diarrhée": "selles liquides fréquentes, crampes abdominales, déshydratation possible, faiblesse",
            "dysenterie": "selles liquides sanglantes ou muqueuses, crampes abdominales sévères, fièvre",
            "fièvre": "température corporelle élevée, frissons, maux de tête, fatigue, déshydratation",
            "toux": "irritation de la gorge, expectorations, gêne respiratoire, douleurs thoraciques"
        }
        
        # Déterminer les symptômes typiques selon la pathologie
        symptomes_detailles = "symptômes variés selon les personnes"
        for key, symptomes in symptomes_mapping.items():
            if key.lower() in pathologies.lower():
                symptomes_detailles = symptomes
                break
        
        # Déterminer les parties des plantes utilisées pour le mode d'action
        if "racin" in partie_utilisee.lower():
            mode_action = "Les racines contiennent des principes actifs puissants qui agissent directement sur l'agent pathogène."
        elif "feuill" in partie_utilisee.lower():
            mode_action = "Les feuilles contiennent des composés qui agissent comme antipyrétiques et anti-inflammatoires."
        elif "écorce" in partie_utilisee.lower() or "ecorce" in partie_utilisee.lower():
            mode_action = "L'écorce renferme des alcaloïdes et des tanins aux propriétés antiparasitaires."
        else:
            mode_action = "La plante contient des composés qui agissent directement sur l'agent pathogène tout en renforçant le système immunitaire."
        
        # Format plus clair pour le dosage
        dosage_info = ""
        if ";" in dosage:
            dosage_parts = dosage.split(";")
            dosage_info = "Posologie recommandée (en grammes de plante séchée par litre d'eau):\n"
            for part in dosage_parts:
                if ":" in part:
                    plante, quantite = part.split(":", 1)
                    plante = plante.strip()
                    quantite = quantite.strip()
                    if quantite and quantite.lower() != "null":
                        dosage_info += f"- {plante}: {quantite}g\n"
                    else:
                        dosage_info += f"- {plante}: quantité standard (1 poignée ou 20-30g)\n"
                else:
                    part = part.strip()
                    if part and part.lower() != "null":
                        dosage_info += f"- {part}\n"
        else:
            if dosage and dosage.lower() != "null":
                dosage_info = f"Dosage recommandé: {dosage}"
            else:
                dosage_info = "Dosage recommandé: une poignée (environ 20-30g) de plante séchée dans un litre d'eau"
        
        # Formatter les parties de plantes utilisées avec une meilleure présentation
        parties_info = ""
        if ";" in partie_utilisee:
            parties_parts = partie_utilisee.split(";")
            parties_info = "Parties des plantes à utiliser:\n"
            for part in parties_parts:
                if ":" in part:
                    plante, partie = part.split(":", 1)
                    plante = plante.strip()
                    partie = partie.strip()
                    
                    # Ne pas afficher les NULL
                    if partie.lower() == "null":
                        partie = "parties habituellement utilisées en phytothérapie"
                        
                    # Traduire les parties en français
                    partie_fr = partie.lower()
                    if "root" in partie_fr:
                        partie_fr = "racines"
                    elif "leaves" in partie_fr:
                        partie_fr = "feuilles"
                    elif "bark" in partie_fr:
                        partie_fr = "écorce"
                    elif "fruit" in partie_fr:
                        partie_fr = "fruits"
                    elif "seed" in partie_fr:
                        partie_fr = "graines"
                    elif "flower" in partie_fr:
                        partie_fr = "fleurs"
                    elif "stem" in partie_fr:
                        partie_fr = "tiges"
                    
                    parties_info += f"- {plante}: {partie_fr}\n"
                else:
                    part = part.strip()
                    if part and part.lower() != "null":
                        parties_info += f"- {part}\n"
        else:
            if partie_utilisee and partie_utilisee.lower() != "null":
                parties_info = f"Parties utilisées: {partie_utilisee}"
            else:
                parties_info = "Parties utilisées: les parties habituellement employées en phytothérapie pour cette plante"
        
        # Préparer les précautions
        precautions_info = contre_indications if contre_indications else "Évitez l'usage chez les femmes enceintes ou allaitantes, les jeunes enfants et en cas de problèmes hépatiques ou rénaux connus."
          # Explication de secours structurée et complète avec avertissement explicite
        explanation = f"""⚠️ Diagnostic informatif (mode assistance)

Notre système d'intelligence artificielle principal n'a pas pu analyser votre cas de manière approfondie. Les informations suivantes sont basées sur des correspondances générales dans notre base de données. D'après vos symptômes décrits: "{symptoms}", les données suggèrent qu'il pourrait s'agir de {pathologies.upper()}. Cette évaluation n'est pas un diagnostic médical définitif. Cette condition requiert une attention particulière et un avis médical professionnel.

Symptômes associés

Cette pathologie se manifeste généralement par {symptomes_detailles}. Ces symptômes apparaissent en réaction à l'infection ou au déséquilibre que subit l'organisme et nécessitent un traitement adapté.

Présentation de {plant_names}

La plante {plant_names} est une espèce médicinale précieuse dans la pharmacopée traditionnelle africaine. Utilisée depuis des générations par les guérisseurs locaux, elle est reconnue pour ses propriétés thérapeutiques particulièrement efficaces contre {pathologies}. Son usage est ancré dans les traditions ancestrales et continue d'être valorisé pour ses bienfaits.

Mode d'action

{mode_action} Les principes actifs naturels de cette plante agissent en synergie pour combattre les symptômes et restaurer l'équilibre du corps. Cette approche traditionnelle s'avère efficace pour soulager les manifestations de la maladie.

Informations de traitement

Préparation: {preparation}

{dosage_info} Pour une efficacité optimale, respectez ce dosage précisément. Ces quantités correspondent à la dose journaliire pour un adulte, à diviser en 2-3 prises, idéalement après les repas pour limiter l'irritation gastrique.

{parties_info} Ces parties spécifiques contiennent la plus forte concentration de principes actifs thérapeutiques nécessaires pour traiter efficacement la pathologie concernée.

Précautions et contre-indications

Pour votre sécurité, veuillez noter les contre-indications suivantes: {precautions_info}

Ces précautions sont importantes car certains composés de la plante peuvent interagir avec d'autres médicaments ou aggraver certaines conditions médicales préexistantes. En cas de doute, consultez un professionnel de santé avant utilisation.

Composants actifs

La plante {plant_names} contient des composants actifs naturels comme {composants[:150]}... qui travaillent ensemble pour créer un effet thérapeutique synergique. Ces substances sont responsables de l'efficacité traditionnellement reconnue de cette plante contre les symptômes décrits.

Résumé de traitement

Pour traiter {pathologies.upper()}, préparez une décoction de {plant_names} selon les instructions détaillées. Prenez la dose recommandée de {dosage} 2-3 fois par jour pendant 7 jours. Si les symptômes persistent après 3 jours ou s'aggravent, consultez immédiatement un professionnel de santé. Respectez les précautions mentionnées pour garantir un traitement sûr et efficace."""
    
    return {
        "plant": plant_names,
        "dosage": dosage,
        "prep": preparation,
        "image_url": image_url,
        "explanation": explanation,
        "contre_indications": contre_indications,
        "partie_utilisee": partie_utilisee,
        "composants": composants,
        "nom_local": nom_local_info if nom_local_info else f"Nom local: {nom_local}" if nom_local else ""
    }

def generate_chat_response(prompt: str):
    """
    Génère une réponse pour le mode discussion en utilisant GPT-3.5-Turbo.
    """
    print(f"Mode discussion: Génération d'une réponse avec GPT-3.5-Turbo pour: '{prompt}'")
    
    # Template pour les discussions générales sur la phytothérapie africaine
    chat_template = """
    Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique.
    Réponds à la question suivante de manière concise (maximum 6-8 phrases), informative et bienveillante.
    Privilégie toujours la sécurité du patient et l'exactitude des informations.
    
    Si la question concerne un traitement spécifique ou des symptômes particuliers, suggère poliment de passer en mode Consultation pour obtenir une recommandation plus détaillée et personnalisée.
    
    Sois chaleureux et empathique, mais surtout précis et informatif.
    Ton message doit être clair et compréhensible pour quelqu'un sans connaissances médicales.
    
    Question: {question}
    
    Réponse: 
    """
    # Utilise le modèle global llm_chat défini précédemment
    global llm_chat
    
    # Vérifier si le modèle est correctement initialisé
    if not llm_chat:
        error_message = "Modèle OpenAI non initialisé correctement. Vérifiez votre clé API."
        print(error_message)
        raise ValueError(error_message)
    
    try:
        # Vérifier que la clé API est présente
        if not OPENAI_API_KEY:
            raise ValueError("La clé API OpenAI n'est pas configurée")
            
        # Créer et exécuter la chaîne
        chat_prompt = PromptTemplate(
            template=chat_template,
            input_variables=["question"]
        )
        
        # Définition de timeouts explicites pour éviter les blocages
        chat_chain = LLMChain(
            llm=llm_chat,
            prompt=chat_prompt,
            verbose=True  # Pour obtenir plus d'informations sur le processus
        )
        
        # Exécution avec gestion de timeout
        response = chat_chain.run(question=prompt)
        
        # Vérifier que la réponse est valide
        if not response or len(response.strip()) < 10:
            raise ValueError("La réponse générée est trop courte ou vide")
            
        print("Réponse générée avec succès par GPT")
        return response.strip()
        
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse avec GPT: {e}")
        import traceback
        traceback.print_exc()
          # Dictionnaire de réponses de secours pour les mots-clés courants avec un avertissement clair
        fallback_keywords = {
            "paludisme": "[⚠️ Mode assistance] Je n'ai pas pu réaliser une analyse complète de votre demande. Il m'est impossible de formuler un diagnostic fiable concernant le paludisme, qui est une maladie grave nécessitant un diagnostic médical professionnel. Bien que des plantes comme la Cryptolepia sanguinolenta soient traditionnellement utilisées, aucune recommandation ne peut remplacer l'avis d'un médecin. Si vous pensez souffrir de paludisme, consultez immédiatement un professionnel de santé. Pour explorer des options de phytothérapie complémentaires, utilisez le mode Consultation.",
            "malaria": "[⚠️ Mode assistance] Je n'ai pas pu établir de diagnostic précis concernant votre demande sur la malaria (paludisme). Cette infection grave nécessite un diagnostic médical formel et je ne peux pas me substituer à l'expertise d'un professionnel de santé. Si vous recherchez des informations sur les plantes traditionnellement utilisées comme l'Artemisia annua, utilisez le mode Consultation, mais consultez impérativement un médecin en cas de suspicion de malaria.",
            "fièvre": "[⚠️ Mode assistance] Je n'ai pas pu analyser correctement la cause de votre fièvre, ce symptôme pouvant être lié à de nombreuses pathologies différentes. Sans diagnostic médical, il serait imprudent de vous recommander un traitement spécifique. En phytothérapie africaine, certaines plantes comme le Nauclea latifolia sont traditionnellement utilisées pour soulager la fièvre, mais cela ne remplace pas un avis médical. Pour des recommandations plus précises tout en gardant cette prudence médicale, utilisez le mode Consultation.",
            "toux": "[⚠️ Mode assistance] Je n'ai pas pu analyser la nature exacte de votre toux, qui peut être le symptôme de diverses affections respiratoires. Sans examen médical, il m'est impossible de déterminer sa cause et de proposer un traitement adapté. Si vous cherchez des informations sur les plantes traditionnellement utilisées comme l'Eucalyptus ou le gingembre en médecine africaine, utilisez le mode Consultation, mais gardez à l'esprit que ces suggestions ne peuvent remplacer l'avis d'un professionnel de santé."
        }
        
        # Vérifier les mots-clés dans la question
        prompt_lower = prompt.lower()
        for keyword, response_text in fallback_keywords.items():
            if keyword in prompt_lower:
                print(f"Utilisation de la réponse de secours pour le mot-clé: {keyword}")
                return response_text
          # Réponse générique de secours avec avertissement
        fallback_response = "[⚠️ Mode assistance] Je n'ai pas pu traiter votre demande de manière fiable. Sans pouvoir accéder au modèle principal, il m'est impossible de formuler une réponse précise sur votre question médicale. En matière de phytothérapie africaine, particulièrement pour les questions liées à la santé, je dois faire preuve d'une extrême prudence. Je vous invite à utiliser le mode Consultation pour obtenir des informations plus structurées, tout en gardant à l'esprit que ces informations ne remplacent jamais l'avis d'un professionnel de santé qualifié. Pour tout problème de santé, consultez en priorité un médecin ou un spécialiste en médecine traditionnelle."
        print("Utilisation de la réponse de secours générique")
        return fallback_response
