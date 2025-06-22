import os
import pickle
import requests
import time

from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain_community.embeddings import OpenAIEmbeddings

load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

VECTORSTORE_PATH = os.path.join("data", "faiss_index_openai.pkl")  # Spécifique OpenAI
METADATA_PATH = os.path.join("data", "vector_metadata_openai.pkl")

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
        "symptoms", "plant_name", "pathology", "preparation", "dosage", 
        "parties_utilisees", "contre_indications_recette", "contre_indications_plante", "composants"
    ], 
    template=template
)

try:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        request_timeout=30,
        max_retries=2,
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    
    llm_chat = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        openai_api_key=OPENAI_API_KEY,
        request_timeout=30,
        max_retries=2,
    )
    
    if not llm or not llm_chat:
        raise ValueError("Erreur d'initialisation des modèles OpenAI")
        
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Erreur lors de l'initialisation des modèles OpenAI: {e}")
    logger.error(f"❌ Type d'erreur: {type(e).__name__}")
    logger.error(f"❌ Détails: {str(e)}")
    # Les variables restent None, ce qui causera les fallbacks
    llm = None
    llm_chat = None

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
    """Charge l'index vectoriel existant ou en crée un nouveau"""
    if should_rebuild_index(csv_path):
        return build_and_save_vectorstore(df, csv_path)
    
    try:
        with open(VECTORSTORE_PATH, "rb") as f:
            vs = pickle.load(f)
        return vs
    except Exception:
        return build_and_save_vectorstore(df, csv_path)

def extract_sections_from_explanation(explanation):
    """
    Extrait les sections structurées d'une explication générée par le LLM
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
        lines = explanation.split('\n')
        current_section = None
        current_content = []
        
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            if line_idx == 0 and line_stripped and line_stripped.startswith("D'après"):
                sections["diagnostic"] = line_stripped
                continue
            
            found_section = None
            for patterns, key in section_patterns:
                for pattern in patterns:
                    if line_stripped.startswith(pattern) or pattern in line_stripped:
                        found_section = key
                        break
                if found_section:
                    break
            
            if found_section:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                current_section = found_section
                current_content = []
                
                for pattern in [p for patterns, k in section_patterns if k == found_section for p in patterns]:
                    if pattern in line_stripped:
                        after_pattern = line_stripped.split(pattern, 1)[1].strip()
                        if after_pattern.startswith(':'):
                            after_pattern = after_pattern[1:].strip()
                        if after_pattern:
                            current_content.append(after_pattern)
                        break
                    
            elif current_section and line_stripped:
                current_content.append(line.strip())
        
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
            
    except Exception:
        sections["diagnostic"] = explanation
    
    return sections

def create_fallback_sections(symptoms, plant_names, pathologies, preparation, dosage, partie_utilisee, contre_indications, composants):
    """Crée des sections de secours en cas d'échec du LLM"""
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

def get_recommendation(symptoms: str, df, csv_path="data/baseplante.csv", attempt_count=1):
    import pandas as pd
    
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
                if not matches.empty:
                    break
        
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
                "prep": "Informations supplémentaires requises", 
                "image_url": "",
                "contre_indications": "Veuillez fournir plus de détails sur vos symptômes",
                "partie_utilisee": "Informations supplémentaires requises",                "composants": "Informations supplémentaires requises",
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

Votre santé est précieuse, et il est important d'obtenir l'avis d'un professionnel de santé qualifié lorsque nos ressources actuelles ne suffisent pas à vous orienter correctement.""",                "dosage": "Consultation professionnelle requise",
                "prep": "Consultation professionnelle requise",
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
                    
                    if plant_name in main_plants and "NULL" not in local_name.upper():
                        langue_nom = langues_raw[i].strip() if i < len(langues_raw) else ""
                        pays_nom = pays_raw[i].strip() if i < len(pays_raw) else ""
                        
                        if len(noms_locaux_simplifies[plant_name]) < 5:
                            if langue_nom and pays_nom and "NULL" not in langue_nom.upper() and "NULL" not in pays_nom.upper():
                                noms_locaux_simplifies[plant_name].append(f"{local_name} ({langue_nom}, {pays_nom})")
            
            plant_infos = []
            for plant_name, noms in noms_locaux_simplifies.items():
                if noms:
                    noms_valides = [nom for nom in noms if "NULL" not in nom.upper()]
                    if noms_valides:
                        noms_text = ", ".join(noms_valides[:5])
                        plant_infos.append(f"{plant_name} est connue sous le nom de: {noms_text}")
            
            if plant_infos:
                nom_local_info = "Noms locaux: " + ". ".join(plant_infos)
            else:
                nom_local_info = "Noms locaux non disponibles dans les données actuelles"
        else:
            if "NULL" not in nom_local.upper():
                nom_local_info = f"Nom local: {nom_local} en {langue} ({pays})."
            else:
                nom_local_info = "Noms locaux non disponibles dans les données actuelles"
    else:
        nom_local_info = "Noms locaux non disponibles dans les données actuelles"
    
    pathologies = plant.get('maladiesoigneeparrecette', 'Non spécifié')
    
    if "palud" in symptoms.lower() or "malaria" in symptoms.lower():
        if not ("palud" in pathologies.lower() or "malaria" in pathologies.lower()):
            pathologies = "paludisme"    
    try:        
        explanation = chain.run(
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
        
    except Exception:
        sections = create_fallback_sections(symptoms, plant_names, pathologies, preparation, dosage, partie_utilisee, contre_indications, composants)
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
    Génère une réponse pour les discussions générales sur la phytothérapie africaine
    """
    chat_template = """
    Tu es un expert en phytothérapie africaine avec une approche très humaine et pédagogique.
    Réponds à la question suivante de manière concise, informative et bienveillante, en privilégiant
    toujours la sécurité du patient et l'exactitude des informations. Si la question concerne un traitement spécifique ou des symptômes particuliers, suggère poliment de passer en mode Consultation pour obtenir une recommandation plus détaillée et personnalisée.
    
    Question: {question}
    
    Réponds en français avec un ton chaleureux et professionnel. Maximum 200 mots.
    """
    
    fallback_responses = {
        "bonjour": "Bonjour ! Je suis là pour vous accompagner dans vos questions sur la phytothérapie africaine. Comment puis-je vous aider aujourd'hui ?",
        "salut": "Salut ! Comment allez-vous ? Je suis disponible pour répondre à vos questions sur les plantes médicinales africaines.",
        "merci": "Je vous en prie ! C'est un plaisir de vous aider dans votre découverte des remèdes traditionnels africains.",
        "aide": "Je peux vous renseigner sur les plantes médicinales africaines, leurs usages traditionnels et leurs propriétés. Pour des conseils spécifiques à vos symptômes, utilisez le mode Consultation.",
        "comment": "Pour obtenir des conseils personnalisés selon vos symptômes, je vous recommande d'utiliser le mode Consultation. Pour des questions générales, je suis là pour vous aider !",
        "default": "C'est une excellente question sur la phytothérapie africaine ! Pour des conseils spécifiques adaptés à vos besoins, je vous encourage à utiliser le mode Consultation. Sinon, n'hésitez pas à me poser d'autres questions générales."
    }
    
    try:
        if llm_chat is None:
            raise ValueError("Modèle OpenAI non initialisé")
        
        response = llm_chat.predict(chat_template.format(question=prompt))
        return response.strip()
        
    except Exception:
        prompt_lower = prompt.lower()
        for keyword, response in fallback_responses.items():
            if keyword in prompt_lower:
                return response
        
        return fallback_responses["default"]
