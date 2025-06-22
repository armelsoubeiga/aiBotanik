import os
import time
import pickle
import requests
import traceback
import logging
import random
import pandas as pd

from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_huggingface_response(prompt: str, api_key: str, model_id: str = "google/flan-t5-base", 
                                  max_length: int = 200, temperature: float = 0.7) -> str:
    """Génère une réponse via l'API HuggingFace Inference"""
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
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    return result[0]["generated_text"].strip()
                else:
                    return str(result[0]).strip()
            elif isinstance(result, dict):
                if "generated_text" in result:
                    return result["generated_text"].strip()
                else:
                    return str(result.get("text", result)).strip()
            else:
                return str(result).strip()
        else:
            return ""
    except Exception:
        return ""

load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN", os.getenv("HF_API_KEY"))

if HF_API_KEY:
    logger.info("Clé API HuggingFace trouvée")
else:
    logger.warning("Clé API HuggingFace non trouvée")

# Index séparés par type d'embedding pour éviter les conflits
VECTORSTORE_PATH = os.path.join("data", "faiss_index_hf.pkl") 
METADATA_PATH = os.path.join("data", "vector_metadata_hf.pkl")

# Lazy loading du modèle d'embeddings (ne charge qu'à la première utilisation)
_emb = None

def get_embeddings_model():
    """Charge le modèle d'embeddings seulement quand nécessaire (lazy loading)"""
    global _emb
    if _emb is None:
        logger.info("Chargement du modèle all-MiniLM-L6-v2...")
        start_time = time.time()
        
        # Optimisation pour Render : cache local
        cache_dir = os.getenv("TRANSFORMERS_CACHE", "/opt/render/.cache/huggingface")
        
        _emb = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=cache_dir,
            model_kwargs={
                'device': 'cpu',  # Forcer CPU sur Render
                'trust_remote_code': True
            }
        )
        
        load_time = time.time() - start_time
        logger.info(f"Modèle chargé en {load_time:.2f}s")
    return _emb

template = """
Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique. Pour les symptômes décrits: {symptoms},
formule une explication structurée selon les sections suivantes dans CET ORDRE EXACT en utilisant DIRECTEMENT les informations issues du CSV:

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
1. Le nom de la pathologie (en précisant qu'il s'agit d'une possibilité basée sur les symptômes)
2. La plante principale et sa méthode de préparation
3. La posologie exacte (dosage et nombre de prises par jour)
4. La durée recommandée du traitement (7 jours par défaut si non spécifié)
5. Quand consulter un professionnel de santé (si les symptômes persistent après 3 jours)

EXIGENCES STRICTES:
1. Chaque section DOIT être présente, avec son titre exact et dans l'ordre indiqué
2. Utilise UNIQUEMENT les informations fournies dans le contexte du CSV (voir correspondances)
3. Si une information est marquée "Non spécifié", propose une recommandation générale sans inventer
4. Ton langage doit être accessible et chaleureux, mais précis sur les dosages et précautions
5. Réponds UNIQUEMENT en français, structure ta réponse avec des sauts de ligne entre les sections
"""
prompt = PromptTemplate(
    input_variables=[
        "symptoms", "plant_name", "pathology", "preparation", "dosage", "parties_utilisees",
        "contre_indications_recette", "contre_indications_plante", "composants"
    ], 
    template=template
)

class HuggingFaceAPIWrapper:
    """
    Wrapper pour utiliser l'API HuggingFace Inference comme un LLM LangChain compatible.
    """
    def __init__(self, api_key, model_id="google/flan-t5-base", max_length=512, temperature=0.7):
        self.api_key = api_key
        self.model_id = model_id
        self.max_length = max_length
        self.temperature = temperature

    def __call__(self, prompt, **kwargs):
        return self.run(prompt)

    def run(self, prompt, **kwargs):
        response = generate_huggingface_response(
            prompt=prompt,
            api_key=self.api_key,
            model_id=self.model_id,
            max_length=self.max_length,
            temperature=self.temperature
        )
        return response or "[Erreur: aucune réponse du modèle HuggingFace distant]"

def init_llm_model(*, use_local=False, model_id="google/flan-t5-base"):
    """
    Initialise le LLM pour les consultations (API HuggingFace Inference UNIQUEMENT)
    """
    if not HF_API_KEY:
        logger.error("Clé API HuggingFace manquante !")
        return None
    logger.info(f"Utilisation exclusive du modèle distant HuggingFace : {model_id}")
    return HuggingFaceAPIWrapper(
        api_key=HF_API_KEY,
        model_id=model_id,
        max_length=512,
        temperature=0.7
    )


def get_llm_chain():
    """Chaîne LLM qui utilise toujours l'API HuggingFace distante"""
    global llm, chain
    if chain is not None:
        return chain
    try:
        if llm is None:
            llm = init_llm_model()
            if llm is None:
                return None
        # Adapter LLMChain pour utiliser le wrapper
        class SimpleLLMChain:
            def __init__(self, llm, prompt):
                self.llm = llm
                self.prompt = prompt
            def run(self, **kwargs):
                prompt_text = self.prompt.format(**kwargs)
                return self.llm.run(prompt_text)
        chain = SimpleLLMChain(llm=llm, prompt=prompt)
        return chain
    except Exception as e:
        logger.error(f"Erreur get_llm_chain: {e}")
        return None

llm = None
chain = None

def fetch_image(plant_name: str) -> str:
    url = f"https://api.unsplash.com/search/photos?query={plant_name}&client_id={UNSPLASH_KEY}&per_page=1"
    resp = requests.get(url).json()
    return resp["results"][0]["urls"]["small"] if resp["results"] else ""

def get_csv_last_modified(csv_path):
    """Retourne la date de dernière modification du fichier CSV"""
    try:
        if not os.path.exists(csv_path):
            return 0
        return os.path.getmtime(csv_path)
    except OSError:
        return 0

def create_documents_from_df(df):
    """Crée les documents vectoriels à partir du DataFrame"""
    documents = []
    for idx, row in df.iterrows():
        content = f"Symptômes: {row.get('maladiesoigneeparrecette', '')}\n"
        content += f"Plante: {row.get('plante_recette', '')}\n"
        content += f"Dosage: {row.get('plante_quantite_recette', '')}\n"
        content += f"Préparation: {row.get('recette', '')}"
        
        metadata = {
            "plant_name": str(row.get('plante_recette', '')).split(';')[0].strip(),
            "index": idx
        }
        documents.append(Document(page_content=content, metadata=metadata))
    return documents

def build_and_save_vectorstore(df, csv_path):
    """Construit et sauvegarde l'index vectoriel"""
    try:
        documents = create_documents_from_df(df)
        emb = get_embeddings_model()  # Lazy loading
        vs = FAISS.from_documents(documents, emb)
        
        os.makedirs(os.path.dirname(VECTORSTORE_PATH), exist_ok=True)
        
        with open(VECTORSTORE_PATH, "wb") as f:
            pickle.dump(vs, f)
        
        metadata = {
            "last_modified": get_csv_last_modified(csv_path),
            "document_count": len(documents),
            "created_at": time.time()
        }
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(metadata, f)
        
        return vs
    except Exception:
        return None

def should_rebuild_index(csv_path):
    """Détermine si l'index doit être reconstruit"""
    if not os.path.exists(VECTORSTORE_PATH) or not os.path.exists(METADATA_PATH):
        return True
    
    try:
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
        
        current_mtime = get_csv_last_modified(csv_path)
        last_indexed_mtime = metadata.get("last_modified", 0)
        
        return current_mtime > last_indexed_mtime
    except Exception:
        return True

def load_or_build_vectorstore(df, csv_path):
    """Charge l'index vectoriel existant ou en crée un nouveau seulement si nécessaire"""
    
    # 1. Si les fichiers n'existent pas, créer l'index
    if not os.path.exists(VECTORSTORE_PATH) or not os.path.exists(METADATA_PATH):
        logger.info("Index vectoriel introuvable, création d'un nouvel index...")
        return build_and_save_vectorstore(df, csv_path)
    
    # 2. Vérifier si le CSV a changé depuis la dernière vectorisation
    try:
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
        
        current_csv_mtime = get_csv_last_modified(csv_path)
        last_indexed_mtime = metadata.get("last_modified", 0)
        
        # Si le CSV est plus récent que l'index, re-vectoriser
        if current_csv_mtime > last_indexed_mtime:
            logger.info(f"CSV modifié (mtime: {current_csv_mtime} > {last_indexed_mtime}), re-vectorisation...")
            return build_and_save_vectorstore(df, csv_path)
        
        # 3. CSV inchangé, charger l'index existant
        logger.info("Index vectoriel existant et à jour, chargement...")
        start_time = time.time()
        with open(VECTORSTORE_PATH, "rb") as f:
            vs = pickle.load(f)
        load_time = time.time() - start_time
        logger.info(f"✅ Index vectoriel chargé en {load_time:.2f}s")
        return vs
        
    except Exception as e:
        logger.warning(f"Erreur lors du chargement des métadonnées: {e}, re-création de l'index...")
        return build_and_save_vectorstore(df, csv_path)

# Fonction principale pour obtenir des recommandations
def get_recommendation(symptoms: str, df, csv_path="data/baseplante.csv", attempt_count=1):
    
    global vectorstore
    
    if 'vectorstore' not in globals() or vectorstore is None:
        vectorstore = load_or_build_vectorstore(df, csv_path)
    
    vectorstore_initialized = vectorstore is not None
    matches = None
    if vectorstore_initialized:
        try:
            similar_docs = vectorstore.similarity_search(symptoms, k=3)
            
            if similar_docs:
                most_similar_doc = similar_docs[0]
                doc_index = most_similar_doc.metadata.get('index')
                
                if doc_index is not None:
                    plant_data = df.iloc[doc_index].to_dict()
                    matches = pd.DataFrame([plant_data])
        except Exception:
            pass
    
    if matches is None or len(matches) == 0:
        clean_symptoms = symptoms.lower()
        
        for phrase in ["je pense que j'ai", "j'ai", "je souffre de", "je crois que", "traitement pour", "soigner", "guérir"]:
            clean_symptoms = clean_symptoms.replace(phrase, "")
        clean_symptoms = clean_symptoms.strip()
        
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
        for keyword, synonyms in symptom_mapping.items():
            if keyword in clean_symptoms or any(syn in clean_symptoms for syn in synonyms):
                search_term = keyword
                matches = df[df["maladiesoigneeparrecette"].str.contains(search_term, case=False, na=False, regex=True)]
                if not matches.empty:                    break
        
        if matches is None or len(matches) == 0:
            matches = df[df["maladiesoigneeparrecette"].str.contains(clean_symptoms, case=False, na=False)]
    
    if matches.empty:
        if "palud" in clean_symptoms or "malaria" in clean_symptoms:
            matches = df[df["maladiesoigneeparrecette"].str.contains("malaria|paludisme", case=False, na=False, regex=True)]
    
    if matches.empty:
        # Gestion intelligente des cas sans correspondance avec système de 2 tentatives basé sur attempt_count
        if attempt_count == 1:
            # Première tentative - demander plus de détails gentiment
            return {
                "plant": "Demande de précisions",
                "explanation": """Je n'ai pas pu identifier une pathologie spécifique correspondant à vos symptômes dans notre base de données actuelle.

Pourriez-vous m'aider en me donnant plus de détails sur ce que vous ressentez ? Par exemple :
• Depuis quand avez-vous ces symptômes ?
• À quel moment de la journée sont-ils plus intenses ?
• Y a-t-il d'autres signes qui les accompagnent ?
• Avez-vous des douleurs particulières ou des zones précises touchées ?

Ces informations supplémentaires m'aideront à mieux vous orienter vers un traitement adapté.""",
                "dosage": "Informations supplémentaires requises",
                "preparation": "Informations supplémentaires requises", 
                "image_url": "",
                "contre_indications": "Veuillez fournir plus de détails sur vos symptômes",
                "partie_utilisee": "Informations supplémentaires requises",
                "composants": "Informations supplémentaires requises",
                "nom_local": "",
                "needs_more_details": True  # Indicateur pour le frontend
            }
        else:
            # Deuxième tentative ou plus - orienter vers un professionnel
            return {
                "plant": "Consultation recommandée",
                "explanation": """Malgré les détails supplémentaires que vous avez fournis, notre base de données actuelle ne nous permet pas de vous proposer une recommandation de traitement spécifique pour vos symptômes.

Dans ce cas, je vous recommande vivement de :

**🌿 Consulter un thérapeute en phytothérapie :**
Vous pouvez trouver des contacts qualifiés sur notre page d'accueil grâce à la fonctionnalité « Contacter un thérapeute ».

**🩺 Consulter un médecin :**
Pour obtenir un diagnostic médical précis et un traitement approprié.

Votre santé est précieuse, et il est important d'obtenir l'avis d'un professionnel de santé qualifié lorsque nos ressources actuelles ne suffisent pas à vous orienter correctement.""",
                "dosage": "Consultation professionnelle requise",
                "preparation": "Consultation professionnelle requise",
                "image_url": "",
                "contre_indications": "Consultez un professionnel de santé",
                "partie_utilisee": "Consultation professionnelle requise", 
                "composants": "Consultation professionnelle requise",
                "nom_local": "",
                "requires_consultation": True  # Indicateur pour le frontend
            }
    
    plant = matches.iloc[0].to_dict()
    plant_data = plant
    
    plant_names = plant.get("plante_recette", "").split(";")[0].strip() if plant.get("plante_recette") else "Plante inconnue"
    
    try:
        image_url = plant.get("image_url") or fetch_image(plant_names)
    except Exception:
        image_url = ""
    
    dosage = plant.get("plante_quantite_recette", "Dosage non spécifié")
    preparation = plant.get("recette", "Préparation non spécifiée")
    contre_indications = plant.get("recette_contreindication", "") or plant.get("plante_contreindication", "Aucune contre-indication spécifiée")
    partie_utilisee = plant.get("plante_partie_recette", "Partie non spécifiée")
    composants = plant.get("plante_composantechimique", "Composants chimiques non spécifiés")
    nom_local = plant.get("plante_nomlocal", "")
    langue = plant.get("nomlocal_danslalangue", "")
    pays = plant.get("danslalangue_dupays", "")    
    if composants and ";" in composants:
        composants_par_plante = {}
        composants_parts = composants.split(";")
        
        for part in composants_parts:
            if ":" in part:
                plante, composant = part.split(":", 1)
                plante = plante.strip()
                composant = composant.strip()
                
                if "NULL" not in composant.upper():
                    if plante not in composants_par_plante:
                        composants_par_plante[plante] = []
                    
                    composants_par_plante[plante].append(composant)
        
        composants_lignes = []
        for plante, comps in composants_par_plante.items():
            if comps:
                composants_lignes.append(f"{plante}: {', '.join(comps)}")
        
        if composants_lignes:
            composants = "\n".join(composants_lignes)
        else:
            composants = "Composants chimiques spécifiques non disponibles actuellement"
    elif "NULL" in composants.upper():
        composants = "Composants chimiques spécifiques non disponibles actuellement"    
    nom_local_info = ""
    if nom_local and langue and pays:
        noms_locaux_simplifies = {}
        
        if ";" in nom_local:
            noms_plantes_raw = nom_local.split(";")
            langues_raw = langue.split(";") if ";" in langue else [langue] * len(noms_plantes_raw)
            pays_raw = pays.split(";") if ";" in pays else [pays] * len(noms_plantes_raw)
            
            plant_counts = {}
            for nom in noms_plantes_raw:
                if ":" in nom:
                    plant_name, local_name = nom.split(":", 1)
                    plant_name = plant_name.strip()
                    if plant_name not in plant_counts:
                        plant_counts[plant_name] = 0
                    plant_counts[plant_name] += 1
            
            main_plants = sorted(plant_counts.keys(), key=lambda x: plant_counts[x], reverse=True)[:3]
            
            for plant_name in main_plants:
                noms_locaux_simplifies[plant_name] = []
                
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
                        
                        if len(noms_locaux_simplifies[plant_name]) < 5:
                            if langue_nom and pays_nom:
                                noms_locaux_simplifies[plant_name].append(f"{local_name} ({langue_nom}, {pays_nom})")
            
            plant_infos = []
            for plant_name, noms in noms_locaux_simplifies.items():
                if noms:
                    noms_valides = [nom for nom in noms if "NULL" not in nom]
                    if noms_valides:
                        noms_text = ", ".join(noms_valides[:5])
                        plant_infos.append(f"{plant_name} est connue sous le nom de: {noms_text}")
            
            if plant_infos:
                nom_local_info = "Noms locaux: " + ". ".join(plant_infos)
        else:
            if "NULL" not in nom_local:
                nom_local_info = f"Nom local: {nom_local} en {langue} ({pays})."    
    pathologies = plant.get('maladiesoigneeparrecette', 'Non spécifié')
    
    if "palud" in symptoms.lower() or "malaria" in symptoms.lower():
        if not ("palud" in pathologies.lower() or "malaria" in pathologies.lower()):
            pathologies = "paludisme"
    
    try:
        llm_chain = get_llm_chain()
        
        if llm_chain is not None:
            explanation = llm_chain.run(
                symptoms=symptoms,
                plant_name=plant_names,
                pathology=pathologies.strip(),
                preparation=preparation,
                dosage=dosage,
                parties_utilisees=partie_utilisee,
                contre_indications_recette=plant.get("recette_contreindication", "Aucune contre-indication spécifique à la recette mentionnée"),
                contre_indications_plante=plant.get("plante_contreindication", "Aucune contre-indication spécifique à la plante mentionnée"),
                composants=composants
            )
            
            sections = extract_sections_from_explanation(explanation)
        else:
            raise Exception("LLM non disponible")
        
    except Exception:
        sections = create_fallback_sections_hf(symptoms, plant_names, pathologies, preparation, dosage, partie_utilisee, contre_indications, composants)
        explanation = f"{sections['diagnostic']}\n\n{sections['symptomes']}\n\n{sections['presentation']}\n\n{sections['mode']}\n\n{sections['traitement']}\n\n{sections['precautions']}\n\n{sections['composants_text']}\n\n{sections['resume']}"    
    result = {
        "plant": plant_names,
        "dosage": dosage,
        "prep": preparation,
        "image_url": image_url,
        "explanation": explanation,
        "contre_indications": contre_indications,
        "partie_utilisee": partie_utilisee,
        "composants": composants,
        "nom_local": nom_local_info if nom_local_info else f"Nom local: {nom_local}" if nom_local else "",
        
        "diagnostic": sections.get('diagnostic', ''),
        "symptomes": sections.get('symptomes', ''),
        "presentation": sections.get('presentation', ''),
        "mode_action": sections.get('mode', ''),
        "traitement_info": sections.get('traitement', ''),
        "precautions_info": sections.get('precautions', ''),
        "composants_info": sections.get('composants_text', ''),
        "resume_traitement": sections.get('resume', '')
    }
    
    return result

def generate_chat_response(prompt: str):
    """
    Génère une réponse pour le mode discussion en utilisant le modèle LLM hugging face optimisé.
    """
    global llm_chat
    
    logger.info(f"Mode discussion: Génération d'une réponse pour: '{prompt}'")
    
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
        "[⚠️ Mode assistance] Je n'ai pas pu analyser votre demande en profondeur. Les guérisseurs traditionnels africains possèdent un savoir immense sur les propriétés des plantes médicinales, incluant non seulement les plantes elles-mêmes mais aussi les méthodes de préparation qui optimisent leur efficacité. Sans accès au modèle principal, je vous invite à utiliser le mode Consultation pour des recommandations plus structurées, tout en consultant un professionnel de santé."    ]
    
    try:
        # Étape 1: Essayer d'utiliser le modèle LLM optimisé
        use_local = os.getenv("USE_LOCAL_MODEL", "False").lower() in ("true", "1", "t")
        formatted_prompt = chat_template.replace("{question}", prompt)
        
        # Initialiser le modèle chat si ce n'est pas déjà fait
        if llm_chat is None:
            logger.info("Initialisation du modèle LLM pour le chat")
            llm_chat = init_llm_model(use_local=use_local)
            
        # Si le modèle est disponible, l'utiliser
        if llm_chat is not None:
            from langchain_core.prompts import PromptTemplate
            chat_prompt = PromptTemplate(
                template=chat_template,
                input_variables=["question"]
            )
            
            chat_chain = LLMChain(llm=llm_chat, prompt=chat_prompt)
            logger.info("Utilisation du modèle LLM pour générer une réponse")
            response = chat_chain.run(question=prompt)
            
            # Vérifier si la réponse est valide
            if response and len(response.strip()) > 20:
                logger.info(f"Réponse générée avec succès via LangChain (longueur: {len(response)})")
                return response.strip()
            logger.warning("Réponse du modèle LLM trop courte ou invalide")
        else:
            logger.warning("Modèle LLM non disponible pour le chat")
        
        # Étape 2: Fallback sur l'API HTTP directe
        logger.info("Fallback: Utilisation de l'API HuggingFace via requête HTTP directe")
        response = generate_huggingface_response(
            prompt=formatted_prompt,
            api_key=HF_API_KEY,
            model_id="google/flan-t5-base",  
            max_length=200,
            temperature=0.7
        )
        
        # Vérifier si la réponse est valide
        if response and len(response.strip()) > 20:
            logger.info(f"Réponse générée avec succès via API HTTP (longueur: {len(response)})")
            return response.strip()
            
        # Étape 3: Fallback sur les réponses prédéfinies
        logger.warning("Réponse API trop courte ou vide, utilisation des fallbacks prédéfinis")
        
        # Vérifier si un mot clé est présent dans la requête
        prompt_lower = prompt.lower()
        for keyword, fallback_response in fallback_keywords.items():
            if keyword in prompt_lower:
                logger.info(f"Mot-clé '{keyword}' détecté, utilisation de la réponse spécifique")
                return fallback_response
        
        # Si aucun mot-clé spécifique, retourner une réponse générique aléatoire
        return random.choice(phyto_responses)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de réponse chat: {str(e)}")
        traceback.print_exc()
        return random.choice(phyto_responses) if random.random() < 0.7 else default_response

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

# Fonction pour extraire les sections structurées (harmonisée avec OpenAI)
def extract_sections_from_explanation(explanation):
    """
    Extrait les sections structurées d'une explication générée par le LLM Hugging Face
    et les retourne sous forme de dictionnaire pour l'affichage individuel.
    """
    sections = {
        "diagnostic": "",
        "symptomes": "",
        "presentation": "",
        "mode": "",
        "traitement": "",
        "precautions": "",
        "composants_text": "",
        "resume": ""
    }
    
    # Titres des sections à chercher (versions flexibles)
    section_patterns = [
        (["Diagnostic possible", "Diagnostic"], "diagnostic"),
        (["Symptômes associés", "Symptômes"], "symptomes"),
        (["Présentation de", "Présentation"], "presentation"),
        (["Mode d'action", "Mode"], "mode"),
        (["Informations de traitement", "Traitement", "Informations"], "traitement"),
        (["Précautions et contre-indications", "Précautions", "Contre-indications"], "precautions"),
        (["Composants actifs", "Composants"], "composants_text"),
        (["Résumé de traitement", "Résumé"], "resume")
    ]
    
    try:
        # Diviser le texte en lignes pour faciliter l'analyse
        lines = explanation.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Vérifier si la ligne correspond à un titre de section
            found_section = None
            for patterns, key in section_patterns:
                for pattern in patterns:
                    # Recherche flexible : le titre peut apparaître au début de la ligne
                    if line_stripped.startswith(pattern) or pattern in line_stripped:
                        found_section = key
                        break
                if found_section:
                    break
            
            if found_section:
                # Sauvegarder la section précédente
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Commencer une nouvelle section
                current_section = found_section
                current_content = []
                
                # Si la ligne contient du contenu après le titre, l'ajouter
                for pattern in [p for patterns, k in section_patterns if k == found_section for p in patterns]:
                    if line_stripped.startswith(pattern):
                        remaining_text = line_stripped[len(pattern):].strip()
                        if remaining_text and not remaining_text.startswith("(") and not remaining_text.startswith(":"):
                            current_content.append(remaining_text)
                        break
                    
            elif current_section and line_stripped:
                # Ajouter à la section courante si ce n'est pas une ligne vide
                current_content.append(line.strip())
        
        # Sauvegarder la dernière section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Debug: afficher ce qui a été extrait
        print("=== Extraction des sections HF ===")
        for key, value in sections.items():
            if value:
                print(f"{key}: {len(value)} caractères")
            else:
                print(f"{key}: VIDE")
        print("===================================")
            
    except Exception as e:
        print(f"Erreur lors de l'extraction des sections: {e}")
        # En cas d'erreur, mettre tout dans le diagnostic
        sections["diagnostic"] = explanation
    
    return sections

def create_fallback_sections_hf(symptoms, plant_names, pathologies, preparation, dosage, partie_utilisee, contre_indications, composants):
    """
    Crée des sections de secours structurées en cas d'échec du LLM Hugging Face
    (identique à la fonction OpenAI pour harmonisation)
    """
    # Déterminer les symptômes typiques selon la pathologie
    symptomes_mapping = {
        "palud": "fièvre intermittente, frissons, maux de tête, fatigue, douleurs musculaires et articulaires",
        "malaria": "fièvre intermittente, frissons, maux de tête, fatigue, douleurs musculaires et articulaires",
        "diarrhée": "selles liquides fréquentes, crampes abdominales, déshydratation possible, faiblesse",
        "dysenterie": "selles liquides sanglantes ou muqueuses, crampes abdominales sévères, fièvre",
        "fièvre": "température corporelle élevée, frissons, maux de tête, fatigue, déshydratation",
        "toux": "irritation de la gorge, expectorations, gêne respiratoire, douleurs thoraciques"
    }
    
    symptomes_detailles = "symptômes variés selon les personnes"
    for key, symptomes in symptomes_mapping.items():
        if key.lower() in pathologies.lower():
            symptomes_detailles = symptomes
            break
    
    # Déterminer le mode d'action selon les parties utilisées
    if "racin" in partie_utilisee.lower():
        mode_action = "Les racines contiennent des principes actifs puissants qui agissent directement sur l'agent pathogène."
    elif "feuill" in partie_utilisee.lower():
        mode_action = "Les feuilles contiennent des composés qui agissent comme antipyrétiques et anti-inflammatoires."
    elif "écorce" in partie_utilisee.lower() or "ecorce" in partie_utilisee.lower():
        mode_action = "L'écorce renferme des alcaloïdes et des tanins aux propriétés antiparasitaires."
    else:
        mode_action = "La plante contient des composés qui agissent directement sur l'agent pathogène tout en renforçant le système immunitaire."
    
    return {
        "diagnostic": f"AVERTISSEMENT: Je ne peux pas accéder au modèle d'IA principal pour le moment. D'après vos symptômes décrits: \"{symptoms}\", il est possible que vous souffriez de {pathologies.upper()}. Cette suggestion est basée uniquement sur des correspondances générales dans notre base de données et non sur une analyse médicale. Une consultation avec un professionnel de santé est fortement recommandée.",
        
        "symptomes": f"Les symptômes typiquement associés au {pathologies} incluent: {symptomes_detailles}. Ces manifestations sont causées par la réaction du corps à l'infection ou au déséquilibre qu'il subit.",
        
        "presentation": f"La plante {plant_names} est une espèce médicinale très valorisée dans la pharmacopée traditionnelle africaine. Elle est utilisée depuis des générations par les guérisseurs pour traiter diverses affections, particulièrement le {pathologies}. Son utilisation s'inscrit dans une longue tradition de médecine naturelle développée par les communautés locales.",
        
        "mode": f"{mode_action} Cette plante agit progressivement et de façon naturelle pour rétablir l'équilibre du corps et renforcer ses défenses naturelles.",
        
        "traitement": f"Préparation: {preparation}\n\nDosage: {dosage}\nPour une efficacité optimale, respectez précisément ce dosage. Ces quantités correspondent à la dose journalière pour un adulte, à diviser en 2-3 prises par jour.\n\nParties utilisées: {partie_utilisee}\nCes parties spécifiques contiennent la plus forte concentration de principes actifs thérapeutiques nécessaires au traitement.",
        
        "precautions": f"Pour votre sécurité, veuillez noter les contre-indications suivantes: {contre_indications}\n\nCes précautions sont importantes car certains composés de la plante peuvent interagir avec d'autres médicaments ou aggraver certaines conditions médicales préexistantes. En cas de doute, consultez toujours un professionnel de santé.",
        
        "composants_text": f"La plante {plant_names} contient des composants actifs naturels comme {composants[:100] if composants else 'composés traditionnels'}... qui agissent ensemble pour créer un effet thérapeutique synergique. Ces substances sont à l'origine de l'efficacité traditionnellement reconnue de cette plante.",
        
        "resume": f"Pour traiter le {pathologies}, préparez une décoction de {plant_names} selon les instructions indiquées. Prenez la dose recommandée 2-3 fois par jour pendant 7 jours. Si les symptômes persistent après 3 jours ou s'aggravent, consultez immédiatement un professionnel de santé. Respectez les précautions mentionnées pour un traitement sûr et efficace."
    }

def initialize_models():
    """Pré-charge les modèles au démarrage de l'application pour éviter les latences"""
    try:
        logger.info("Initialisation des modèles au démarrage...")
        
        # Pré-charger le modèle d'embeddings
        emb = get_embeddings_model()
        logger.info("✅ Modèle d'embeddings pré-chargé")
        
        # Test rapide pour vérifier que ça fonctionne
        test_text = "test"
        emb.embed_query(test_text)
        logger.info("✅ Test d'embedding réussi")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des modèles: {e}")
        return False

# Initialiser les modèles au chargement du module (pour Render)
if os.getenv("RENDER"):
    logger.info("Environnement Render détecté, pré-chargement des modèles...")
    initialize_models()
