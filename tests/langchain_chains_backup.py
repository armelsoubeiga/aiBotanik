import os
import time
import pickle
import requests
import json
import pandas as pd
import traceback
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceHub
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

# Configurer le logging pour avoir plus d'informations sur les erreurs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fonction pour utiliser l'API HuggingFace Inference directement via requests
def generate_huggingface_response(prompt: str, api_key: str, model_id: str = "google/flan-t5-base", 
                                  max_length: int = 200, temperature: float = 0.7) -> str:
    """
    Utilise l'API HuggingFace Inference directement via requests pour générer une réponse.
    Cette approche évite les problèmes de compatibilité entre les différentes bibliothèques.
    """
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": max_length,
            "temperature": temperature,
            "return_full_text": False
        },
        "options": {
            "wait_for_model": True,
            "use_cache": True
        }    }
    
    try:
        logger.info(f"Envoi de requête à HuggingFace pour le modèle '{model_id}'")
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Vérifier si la requête a réussi
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Réponse API reçue: {result}")
            
            # Gestion des différents formats de réponse selon le modèle
            if isinstance(result, list) and len(result) > 0:
                # Format pour les modèles comme Falcon
                if "generated_text" in result[0]:
                    return result[0]["generated_text"].strip()
                else:
                    return str(result[0]).strip()
            elif isinstance(result, dict):
                # Format pour les modèles comme T5
                if "generated_text" in result:
                    return result["generated_text"].strip()
                else:
                    # Essayer d'extraire le texte, quel que soit le format
                    return str(result.get("text", result)).strip()
            else:
                # Autres formats possibles
                return str(result).strip()
        else:
            # En cas d'erreur, afficher les détails
            logger.error(f"Erreur API HuggingFace: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Exception lors de l'appel à HuggingFace: {str(e)}")
        return ""

# Charger les variables d'environnement
load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# Configurer la clé Hugging Face pour LangChain
if HF_API_KEY:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = HF_API_KEY

# Chemin pour stocker l'index vectoriel
VECTORSTORE_PATH = os.path.join("data", "faiss_index.pkl")
METADATA_PATH = os.path.join("data", "vector_metadata.pkl")

# Initialiser Embeddings 
emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Prompt template
template = """
Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique. Pour les symptômes décrits: {symptoms},
et en considérant les données de la plante: {plant_data}, formule une explication complète et structurée selon les sections suivantes dans cet ordre exact:

Diagnostic possible
Analyse les symptômes avec compassion et explique quelle pathologie est probablement évoquée. Mets en MAJUSCULES le nom de la pathologie identifiée. Parle directement au patient comme dans une consultation en face à face.

Symptômes associés
Présente les symptômes typiques de cette pathologie de manière pédagogique, en expliquant pourquoi ils apparaissent et comment ils se manifestent habituellement.

Présentation de {plant_name}
Présente cette plante comme le ferait un conteur traditionnel, en incluant son histoire, ses usages traditionnels et sa place dans la culture médicinale africaine. Sois passionnant et évocateur, pour donner envie de découvrir cette plante.

Mode d'action
Explique les mécanismes d'action de la plante en termes simples mais scientifiquement exacts, comme un professeur passionné qui veut rendre la science accessible. Explique comment la plante interagit avec le corps pour traiter la pathologie identifiée.

Informations de traitement
Présente les informations de dosage, préparation et parties utilisées en les transformant en véritables conseils pratiques et accessibles, comme le ferait un herboriste expérimenté expliquant un remède à un novice. Intègre les données brutes suivantes de manière fluide et naturelle:
- Préparation: {preparation}
- Dosage: {dosage} 
- Parties utilisées: {parties_utilisees}

Précautions et contre-indications
Transforme les données brutes suivantes: "{contre_indications}" en explications détaillées des risques et précautions. Humanise complètement le langage technique. Explique POURQUOI ces précautions sont importantes pour la sécurité du patient, pas seulement lesquelles. Ajoute des conseils concrets pour minimiser les risques.

Composants actifs
Transforme la liste brute des composants suivants: "{composants}" en explications sur les principaux composés actifs et leurs effets thérapeutiques spécifiques. Explique comment ces composés naturels agissent en synergie.

Résumé de traitement
Synthétise en 3-4 phrases claires le diagnostic et le traitement recommandé, comme si tu devais laisser au patient une ordonnance simple à suivre. Ce résumé doit être facilement mémorisable et expliciter clairement la posologie recommandée et la durée du traitement.

Réponds en français avec un ton chaleureux, rassurant, et conversationnel. Évite absolument le langage technique ou clinique. Chaque section doit commencer par son titre simple sans numérotation ni formatage spécial, et doit être suivie d'un paragraphe substantiel qui humanise complètement les données brutes. Utilise un langage simple mais précis, et assure-toi que tes explications soient accessibles même pour quelqu'un sans formation médicale.
"""
prompt = PromptTemplate(input_variables=["symptoms", "plant_data", "plant_name", "preparation", "dosage", "parties_utilisees", "contre_indications", "composants"], template=template)

# Fonction pour initialiser le modèle LLM Hugging Face
def initialize_llm():
    """Initialise le modèle LLM Hugging Face avec gestion d'erreurs"""
    try:
        if not HF_API_KEY:
            logger.error("❌ Clé API Hugging Face non configurée dans le fichier .env")
            return None
            
        logger.info(f"🔧 Initialisation du modèle Hugging Face avec la clé: {HF_API_KEY[:10]}...")
        
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-base",
            model_kwargs={
                "temperature": 0.7,
                "max_length": 512,
                "do_sample": True,
                "return_full_text": False
            }
        )
        
        # Test rapide du modèle
        test_response = llm.invoke("Test: Hello")
        logger.info(f"✅ Modèle Hugging Face initialisé avec succès. Test: '{test_response}'")
        return llm
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation du modèle Hugging Face: {e}")
        import traceback
        traceback.print_exc()
        return None

# Modèle LLM pour les consultations (recommandations spécifiques)
llm = initialize_llm()
# Chaîne LLM pour les consultations
chain = LLMChain(llm=llm, prompt=prompt) if llm else None

# Modèle LLM séparé pour le chat (discussions générales)
# Sera initialisé lors du premier appel à generate_chat_response()
llm_chat = None

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
    
    # Déclarer les variables globales au début
    global vectorstore, llm, chain
    
    # Initialiser le vectorstore une seule fois et le mettre en cache
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
    
    # Améliorer la description des symptômes pour le paludisme
    symptomes_detailles = ""
    if "palud" in pathologies.lower() or "malaria" in pathologies.lower():
        symptomes_detailles = "fièvre intermittente avec pics élevés, maux de tête intenses, frissons, sueurs, fatigue extrême, douleurs musculaires et articulaires, parfois nausées et vomissements"
    else:
        symptomes_detailles = "fièvre, douleurs, faiblesse générale"
    
    # Améliorer la description du mode d'action
    mode_action = ""
    if "cryptolepia" in plant_names.lower():
        mode_action = f"{plant_names} contient de la cryptolépine et d'autres alcaloïdes qui possèdent des propriétés antiparasitaires puissantes contre le Plasmodium (parasite responsable du paludisme). Ces composés inhibent la croissance du parasite dans les globules rouges et réduisent la charge parasitaire dans le sang."
    elif "cymbopogon" in plant_names.lower():
        mode_action = f"{plant_names} contient du citral et d'autres composés terpéniques qui possèdent des propriétés anti-inflammatoires et antipyrétiques (contre la fièvre). Cette plante aide à soulager les symptômes du paludisme tout en renforçant le système immunitaire."
    elif "khaya" in plant_names.lower():
        mode_action = f"{plant_names} (acajou du Sénégal) contient des limonoïdes et des saponines qui ont démontré des effets antipaludiques significatifs. Ces composés aident à réduire la parasitémie et à soulager les symptômes liés à l'infection."
    elif "moringa" in plant_names.lower():
        mode_action = f"{plant_names} est extrêmement nutritif et contient des composés anti-inflammatoires et antioxydants qui aident l'organisme à combattre l'infection paludique tout en renforçant le système immunitaire affaibli par la maladie."
    else:
        mode_action = f"{plant_names} est efficace contre {pathologies} grâce à ses composés actifs qui agissent sur les symptômes et aident à combattre les agents pathogènes responsables de la maladie."
    
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
    
    # Formatter les précautions et contre-indications
    precautions_info = contre_indications
    if contre_indications:
        # Traduire les contre-indications en français
        precautions_info = contre_indications.lower()
        precautions_info = precautions_info.replace("child under", "Enfants de moins de")
        precautions_info = precautions_info.replace("gastric ulceration", "Ulcère gastrique")
        precautions_info = precautions_info.replace("a mother who is producing milk and breastfeeding", "Femmes allaitantes")
        precautions_info = precautions_info.replace("pregnancy", "Femmes enceintes")
        precautions_info = precautions_info.replace(";", ", ")
      # Mettre en majuscules la pathologie pour la mettre en évidence
    pathologie_maj = pathologies.upper() if pathologies else "NON SPÉCIFIÉ"
      # Générer une explication structurée même sans LLM

    fallback_explanation = f"""
    [AVERTISSEMENT] Diagnostic informatif (mode assistance)
    
    Notre système d'intelligence artificielle principal n'a pas pu analyser votre cas de manière approfondie. Les informations suivantes sont basées sur des correspondances générales dans notre base de données. D'après vos symptômes décrits: "{symptoms}", les données suggèrent qu'il pourrait s'agir de {pathologie_maj}. Cette évaluation n'est pas un diagnostic médical définitif. Cette condition requiert une attention particulière et un avis médical professionnel.

    Symptômes associés
    
    Les symptômes typiquement associés au {pathologies} incluent: {symptomes_detailles}. Ces manifestations sont causées par la réaction du corps à l'infection ou au déséquilibre qu'il subit.
    
    Présentation de {plant_names}
    
    La plante {plant_names} est une espèce médicinale très valorisée dans la pharmacopée traditionnelle africaine. Elle est utilisée depuis des générations par les guérisseurs pour traiter diverses affections, particulièrement le {pathologies}. Son utilisation s'inscrit dans une longue tradition de médecine naturelle développée par les communautés locales.
    
    Mode d'action
    
    {mode_action} Cette plante agit progressivement et de façon naturelle pour rétablir l'équilibre du corps et renforcer ses défenses naturelles.
    
    Informations de traitement
    
    Préparation: {preparation}
    
    {dosage_info}
    Pour une efficacité optimale, respectez précisément ce dosage. Ces quantités correspondent à la dose journalière pour un adulte, à diviser en 2-3 prises par jour.
    
    {parties_info}
    Ces parties spécifiques contiennent la plus forte concentration de principes actifs thérapeutiques nécessaires au traitement.
    
    Précautions et contre-indications
    
    Pour votre sécurité, veuillez noter les contre-indications suivantes: {precautions_info}
    
    Ces précautions sont importantes car certains composés de la plante peuvent interagir avec d'autres médicaments ou aggraver certaines conditions médicales préexistantes. En cas de doute, consultez toujours un professionnel de santé.
    
    Composants actifs
    
    La plante {plant_names} contient des composants actifs naturels comme {composants[:100]}... qui agissent ensemble pour créer un effet thérapeutique synergique. Ces substances sont à l'origine de l'efficacité traditionnellement reconnue de cette plante.
      Résumé de traitement
    
    Pour traiter le {pathologies}, préparez une décoction de {plant_names} selon les instructions. Prenez la dose recommandée 2-3 fois par jour pendant 7 jours. Si les symptômes persistent après 3 jours ou s'aggravent, consultez immédiatement un professionnel de santé. Respectez les précautions mentionnées pour un traitement sûr et efficace.
    """
      # Extraction des variables de toute façon pour les utiliser dans l'explication
    preparation = plant_data.get('recette', 'Préparation non spécifiée')
    dosage = plant_data.get('plante_quantite_recette', 'Non spécifié')
    parties_utilisees = plant_data.get('plante_partie_recette', 'Non spécifié')
    contre_indications = f"{plant_data.get('recette_contreindication', '')} {plant_data.get('plante_contreindication', '')}"
    composants = plant_data.get('plante_composantechimique', '')
    
    # Utiliser directement l'explication de secours pour éviter les problèmes avec l'API Hugging Face
    print("Utilisation de l'explication de secours pour éviter les problèmes d'API")    # Créer les sections individuelles pour plus de clarté
    diagnostic = f"Diagnostic possible\n\nAVERTISSEMENT: Je ne peux pas accéder au modèle d'IA principal pour le moment. D'après vos symptômes décrits: \"{symptoms}\", il est possible que vous souffriez de {pathologies.upper()}. Je ne suis pas en mesure de générer un diagnostic précis. Cette suggestion est basée uniquement sur des correspondances générales dans notre base de données et non sur une analyse médicale. Une consultation avec un professionnel de santé est fortement recommandée."
    
    symptomes = f"Symptômes associés\n\nLes symptômes typiquement associés au {pathologies} incluent: {symptomes_detailles}. Ces manifestations sont causées par l'action du parasite Plasmodium sur l'organisme."
    
    presentation = f"Présentation de {plant_names}\n\nLa plante {plant_names} est une espèce médicinale traditionnelle très valorisée dans la pharmacopée africaine. Les guérisseurs l'utilisent depuis des générations pour traiter diverses affections, particulièrement le {pathologies}."
    
    mode = f"Mode d'action\n\n{mode_action} Cette plante agit progressivement et de façon naturelle pour rétablir l'équilibre du corps."
    
    traitement = f"Informations de traitement\n\nPréparation: {preparation}\n\n{dosage_info}\nPour une efficacité optimale, respectez précisément ce dosage. Ces quantités correspondent à la dose journalière pour un adulte, à diviser en 2-3 prises.\n\n{parties_info}\nCes parties spécifiques contiennent la plus forte concentration de principes actifs nécessaires au traitement."
    
    precautions = f"Précautions et contre-indications\n\nPour votre sécurité, veuillez noter les contre-indications suivantes: {precautions_info}\n\nCes précautions sont importantes car certains composés de la plante peuvent interagir avec d'autres médicaments ou aggraver certaines conditions médicales préexistantes."
    
    composants_text = f"Composants actifs\n\nLa plante {plant_names} contient des composants actifs naturels comme {composants[:100]}... qui agissent ensemble pour créer un effet thérapeutique."
    
    resume = f"Résumé de traitement\n\nPour traiter le {pathologies}, préparez une décoction de {plant_names} selon les instructions indiquées. Prenez la dose recommandée 2-3 fois par jour pendant 7 jours. Si les symptômes persistent après 3 jours ou s'aggravent, consultez immédiatement un professionnel de santé."
      # Combiner toutes les sections
    explanation = f"{diagnostic}\n\n{symptomes}\n\n{presentation}\n\n{mode}\n\n{traitement}\n\n{precautions}\n\n{composants_text}\n\n{resume}"
      # 🎯 PRIORITÉ: Utiliser LangChain avec le modèle Hugging Face
    llm_success = False
    try:
        if chain is not None:
            logger.info("🚀 PRIORITÉ: Tentative d'utilisation de LangChain avec le modèle Hugging Face...")
            
            # Formatter les données pour le prompt
            plant_data_formatted = f"Plante: {plant_names}, Pathologies traitées: {pathologies}, Préparation: {preparation}, Dosage: {dosage}"
            
            logger.info(f"📝 Envoi du prompt à LangChain pour les symptômes: '{symptoms}'")
            
            # Appeler la chaîne LangChain
            llm_response = chain.run({
                "symptoms": symptoms,
                "plant_data": plant_data_formatted,
                "plant_name": plant_names,
                "preparation": preparation,
                "dosage": dosage,
                "parties_utilisees": partie_utilisee,
                "contre_indications": contre_indications,
                "composants": composants            })
            
            logger.info(f"📨 Réponse reçue de LangChain (longueur: {len(llm_response) if llm_response else 0})")
            
            if llm_response and len(llm_response.strip()) > 50:  # Réduire le seuil pour accepter plus de réponses
                logger.info("✅ Réponse LangChain acceptée et utilisée")
                explanation = llm_response.strip()
                llm_success = True
            else:
                logger.warning(f"⚠️ Réponse LangChain trop courte ({len(llm_response) if llm_response else 0} caractères), contenu: '{llm_response}'")
        else:
            logger.error("❌ LangChain non disponible - chain est None")
            # Tenter de réinitialiser le LLM
            logger.info("🔄 Tentative de réinitialisation du LLM...")
            llm = initialize_llm()
            if llm:
                chain = LLMChain(llm=llm, prompt=prompt)
                logger.info("🔧 LLM réinitialisé, nouvelle tentative...")
                
                # Nouvelle tentative après réinitialisation
                plant_data_formatted = f"Plante: {plant_names}, Pathologies traitées: {pathologies}, Préparation: {preparation}, Dosage: {dosage}"
                
                llm_response = chain.run({
                    "symptoms": symptoms,
                    "plant_data": plant_data_formatted,
                    "plant_name": plant_names,
                    "preparation": preparation,
                    "dosage": dosage,
                    "parties_utilisees": partie_utilisee,
                    "contre_indications": contre_indications,
                    "composants": composants
                })
                
                if llm_response and len(llm_response.strip()) > 50:
                    logger.info("✅ Réponse LangChain acceptée après réinitialisation")
                    explanation = llm_response.strip()
                    llm_success = True
                else:
                    logger.warning(f"⚠️ Réponse toujours insuffisante après réinitialisation")
                    
    except Exception as e:
        logger.error(f"❌ Erreur avec LangChain: {e}")
        import traceback
        traceback.print_exc()
        
    # Fallback seulement si le LLM a échoué
    if not llm_success:
        logger.warning("⚠️ Utilisation du fallback car le LLM a échoué")
    
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
    Génère une réponse pour le mode discussion en utilisant directement l'API HuggingFace Inference.
    Inclut un mécanisme de fallback en cas d'échec de l'API.
    """
    global llm, chain
    
    print(f"Mode discussion: Génération d'une réponse pour: '{prompt}'")
    
    # Template pour les discussions générales sur la phytothérapie africaine
    chat_template = """
    Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique.
    Réponds à la question suivante de manière concise, informative et bienveillante, en privilégiant
    toujours la sécurité du patient et l'exactitude des informations. Si la question concerne un traitement spécifique ou des symptômes particuliers, suggère poliment de passer en mode Consultation pour obtenir une recommandation plus détaillée et personnalisée.
    
    Question: {question}
    """
      # Dictionnaire de réponses de secours pour les mots-clés courants
    fallback_keywords = {
        "paludisme": "[⚠️ Mode assistance] Je n'ai pas pu réaliser une analyse complète de votre demande concernant le paludisme. Sans accès au modèle linguistique principal, il m'est impossible d'établir un diagnostic fiable. Le paludisme est une maladie grave nécessitant un avis médical professionnel. Certaines plantes comme la Cryptolepia sanguinolenta sont traditionnellement utilisées, mais uniquement comme complément au traitement médical. Pour explorer des options de phytothérapie, utilisez le mode Consultation tout en consultant un médecin.",
        "malaria": "[⚠️ Mode assistance] Je n'ai pas pu établir de diagnostic précis concernant votre question sur la malaria (paludisme). Cette infection grave requiert un diagnostic médical formel. Des plantes comme l'Artemisia annua sont utilisées traditionnellement, mais ne peuvent remplacer un traitement médical approprié. Pour des informations structurées sur ces plantes, utilisez le mode Consultation, mais consultez impérativement un médecin si vous suspectez cette maladie.",
        "fièvre": "[⚠️ Mode assistance] Je n'ai pas pu analyser correctement la cause de votre fièvre. Ce symptôme pouvant être lié à de nombreuses pathologies, il serait imprudent de suggérer un traitement spécifique sans diagnostic médical. Certaines plantes comme le Nauclea latifolia sont traditionnellement utilisées en phytothérapie africaine pour soulager la fièvre, mais cela ne remplace jamais un avis médical. Pour des informations structurées, utilisez le mode Consultation.",
        "tête": "[⚠️ Mode assistance] Je n'ai pas pu analyser la nature de vos maux de tête, qui peuvent avoir diverses causes. Sans examen médical, je ne peux recommander un traitement spécifique. Des plantes comme le Securidaca longipedunculata sont utilisées traditionnellement, mais uniquement après avoir écarté des causes plus graves nécessitant une intervention médicale. Pour des informations plus structurées sur les approches traditionnelles, utilisez le mode Consultation.",
        "toux": "[⚠️ Mode assistance] Je n'ai pas pu analyser la nature exacte de votre toux, symptôme qui peut relever de diverses affections respiratoires. Sans examen médical, il m'est impossible de déterminer sa cause. L'Eucalyptus globulus ou le gingembre sont traditionnellement utilisés en phytothérapie africaine, mais une toux persistante nécessite un avis médical. Pour des informations sur ces plantes, utilisez le mode Consultation tout en consultant un professionnel de santé.",
        "digestion": "[⚠️ Mode assistance] Je n'ai pas pu analyser précisément votre problème digestif, qui peut avoir de nombreuses causes différentes. Sans diagnostic médical, je ne peux recommander un traitement spécifique. Le Moringa oleifera ou l'Aloe vera sont traditionnellement utilisés en phytothérapie africaine, mais leur pertinence dépend de la cause exacte de votre trouble. Pour des informations plus structurées, utilisez le mode Consultation.",
        "insomnie": "[⚠️ Mode assistance] Je n'ai pas pu analyser la cause de votre insomnie, qui peut être liée à divers facteurs physiologiques ou psychologiques. Sans évaluation complète, je ne peux recommander un traitement spécifique. La passiflore ou la valériane sont utilisées traditionnellement, mais leur efficacité varie selon les causes. Pour des approches de phytothérapie plus détaillées, utilisez le mode Consultation.",
        "stress": "[⚠️ Mode assistance] Je n'ai pas pu analyser les facteurs précis de votre stress, qui nécessitent une évaluation personnalisée. Des plantes comme le rooibos ou le basilic africain sont traditionnellement utilisées pour leurs propriétés apaisantes, mais leur pertinence dépend de votre situation spécifique. Pour des approches de phytothérapie plus détaillées et adaptées, je vous invite à utiliser le mode Consultation.",
        "peau": "[⚠️ Mode assistance] Je n'ai pas pu analyser précisément votre problème de peau, qui peut relever de nombreuses affections différentes. Sans diagnostic, je ne peux recommander un traitement spécifique. L'Aloe vera ou le Centella asiatica sont traditionnellement utilisés en phytothérapie africaine, mais leur pertinence dépend de la nature exacte de votre affection. Pour des informations plus adaptées, utilisez le mode Consultation."
    }
      # Réponse par défaut en cas d'échec
    default_response = "[⚠️ Mode assistance] Je n'ai pas pu analyser votre demande de manière fiable. Sans accès au modèle linguistique principal, il m'est impossible de formuler une réponse précise sur votre question médicale. La phytothérapie africaine propose diverses plantes médicinales selon les symptômes spécifiques. Pour une approche plus structurée et prudente, je vous invite à décrire précisément vos symptômes via le mode Consultation. Toutefois, gardez à l'esprit que ces informations ne remplacent jamais l'avis d'un professionnel de santé qualifié."
      # Utilisations de réponses enrichies sur la phytothérapie africaine pour le fallback
    phyto_responses = [
        "[⚠️ Mode assistance] Je n'ai pas pu analyser précisément votre demande. La phytothérapie africaine repose sur des traditions et connaissances ancestrales précieuses. Sans accès au modèle principal, je ne peux vous offrir qu'une information générale : des plantes comme le Moringa oleifera, l'Artemisia annua ou la Cryptolepia sanguinolenta sont utilisées pour diverses affections. Pour des recommandations plus précises tout en gardant la prudence médicale nécessaire, utilisez le mode Consultation.",
        "[⚠️ Mode assistance] Je n'ai pas pu traiter votre requête de manière optimale. En Afrique, le savoir sur les plantes médicinales est transmis de génération en génération, avec des plantes comme l'Acacia senegal ou le Tamarindus indica utilisées depuis des siècles. Sans accès au modèle principal, je ne peux proposer de traitement spécifique. Pour explorer des options de phytothérapie, utilisez le mode Consultation tout en consultant un professionnel de santé.",
        "[⚠️ Mode assistance] Je n'ai pas pu analyser votre demande en profondeur. Les guérisseurs traditionnels africains possèdent un savoir immense sur les propriétés des plantes médicinales, incluant non seulement les plantes elles-mêmes mais aussi les méthodes de préparation qui optimisent leur efficacité. Sans accès au modèle principal, je vous invite à utiliser le mode Consultation pour des recommandations plus structurées, tout en consultant un professionnel de santé."    ]      try:
        # 🎯 PRIORITÉ: Utiliser LangChain avec le modèle Hugging Face pour le chat
        if chain is not None:
            logger.info("🚀 PRIORITÉ Chat: Tentative d'utilisation de LangChain...")
            
            # Créer un prompt simple pour le chat
            chat_prompt = f"Tu es un expert en phytothérapie africaine. Réponds de manière concise et bienveillante à cette question: {prompt}"
            
            logger.info(f"📝 Envoi du prompt de chat à LangChain: '{chat_prompt[:100]}...'")
            
            # Utiliser la chaîne existante avec des paramètres adaptés au chat
            llm_response = chain.llm.invoke(chat_prompt)
            
            logger.info(f"📨 Réponse chat reçue de LangChain (longueur: {len(llm_response) if llm_response else 0})")
            
            if llm_response and len(llm_response.strip()) > 20:
                logger.info("✅ Réponse chat LangChain acceptée")
                return llm_response.strip()
            else:
                logger.warning(f"⚠️ Réponse chat LangChain trop courte: '{llm_response}'")
        else:
            logger.error("❌ LangChain non disponible pour le chat - chain est None")
            # Tenter de réinitialiser
            llm = initialize_llm()
            if llm:
                chain = LLMChain(llm=llm, prompt=prompt)
                logger.info("🔧 LLM réinitialisé pour le chat, nouvelle tentative...")
                
                chat_prompt = f"Tu es un expert en phytothérapie africaine. Réponds de manière concise et bienveillante à cette question: {prompt}"
                llm_response = chain.llm.invoke(chat_prompt)
                
                if llm_response and len(llm_response.strip()) > 20:
                    logger.info("✅ Réponse chat acceptée après réinitialisation")
                    return llm_response.strip()
        
        # Fallback : Utiliser la fonction generate_huggingface_response
        logger.warning("⚠️ Passage au fallback API directe pour le chat")
        formatted_prompt = chat_template.replace("{question}", prompt)
        logger.info("🔄 Utilisation de l'API HuggingFace directement via requests...")
        
        response = generate_huggingface_response(
            prompt=formatted_prompt,
            api_key=HF_API_KEY,
            model_id="google/flan-t5-base",  
            max_length=200,
            temperature=0.7
        )
        
        # Vérifier si la réponse est valide
        if response and len(response.strip()) > 20:
            print(f"Réponse API directe générée avec succès (longueur: {len(response)})")
            return response.strip()
        else:
            print("La réponse est vide ou trop courte, utilisation du fallback final")
    except Exception as e:
        print(f"Erreur lors de l'appel aux modèles: {e}")
        import traceback
        traceback.print_exc()
        print("Passage au fallback après erreur")
        
    # Fallback: recherche de mots-clés dans la question si l'API échoue
    print("Utilisation du système de fallback basé sur les mots-clés")
    prompt_lower = prompt.lower()
    
    # Vérifier les mots-clés spécifiques
    for keyword, response in fallback_keywords.items():
        if keyword in prompt_lower:
            return response
      # Si la question est une salutation ou générale
    if any(word in prompt_lower for word in ["bonjour", "salut", "comment", "ca va", "ça va", "hello"]):
        return "[⚠️ Mode assistance] Bonjour ! Je suis l'assistant aiBotanik, spécialiste en phytothérapie africaine. Actuellement, j'éprouve une difficulté technique qui limite l'accès à mes ressources d'IA. Cependant, je reste à votre disposition pour vous fournir des informations détaillées sur les plantes médicinales africaines ou pour vous orienter vers des recommandations personnalisées en mode Consultation."
      # Si la question parle de plantes ou de traitement mais sans mot-clé spécifique
    if any(word in prompt_lower for word in ["plante", "herbe", "traitement", "remède", "soigner", "traiter", "phyto", "médecine", "traditionnelle"]):
        # Choisir une réponse enrichie aléatoirement
        import random
        return random.choice(phyto_responses)
    
    # Réponse générale si aucun mot-clé n'est trouvé
    return default_response

def clean_null_values(text):
    """
    Nettoie le texte en remplaçant les valeurs NULL par des informations plus utiles
    """
    if not text:
        return ""
    
    # Remplacer les formes NULL simples
    replacements = [
        ("NULL", "non spécifié"),
        ("null", "non spécifié"),
        ("Null", "non spécifié")
    ]
    
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    
    return result
