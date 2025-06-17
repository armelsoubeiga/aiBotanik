import os
import time
import pickle
import requests
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import HuggingFaceHub
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

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
- Préparation: {plant_data.get('recette', 'Préparation non spécifiée')}
- Dosage: {plant_data.get('plante_quantite_recette', 'Non spécifié')} 
- Parties utilisées: {plant_data.get('plante_partie_recette', 'Non spécifié')}

Précautions et contre-indications
Transforme les données brutes suivantes: "{plant_data.get('recette_contreindication', '')} {plant_data.get('plante_contreindication', '')}" en explications détaillées des risques et précautions. Humanise complètement le langage technique. Explique POURQUOI ces précautions sont importantes pour la sécurité du patient, pas seulement lesquelles. Ajoute des conseils concrets pour minimiser les risques.

Composants actifs
Transforme la liste brute des composants suivants: "{plant_data.get('plante_composantechimique', '')}" en explications sur les principaux composés actifs et leurs effets thérapeutiques spécifiques. Explique comment ces composés naturels agissent en synergie.

Résumé de traitement
Synthétise en 3-4 phrases claires le diagnostic et le traitement recommandé, comme si tu devais laisser au patient une ordonnance simple à suivre. Ce résumé doit être facilement mémorisable et expliciter clairement la posologie recommandée et la durée du traitement.

Réponds en français avec un ton chaleureux, rassurant, et conversationnel. Évite absolument le langage technique ou clinique. Chaque section doit commencer par son titre simple sans numérotation ni formatage spécial, et doit être suivie d'un paragraphe substantiel qui humanise complètement les données brutes. Utilise un langage simple mais précis, et assure-toi que tes explications soient accessibles même pour quelqu'un sans formation médicale.
"""
prompt = PromptTemplate(input_variables=["symptoms", "plant_data", "plant_name"], template=template)

# Utilisation d'un modèle plus petit et plus stable
llm = HuggingFaceHub(
    repo_id="google/flan-t5-large",
    huggingfacehub_api_token=HF_API_KEY,
    model_kwargs={"temperature": 0.7, "max_tokens": 512},
    task="text2text-generation"
)
chain = LLMChain(llm=llm, prompt=prompt)

def fetch_image(plant_name: str) -> str:
    url = f"https://api.unsplash.com/search/photos?query={plant_name}&client_id={UNSPLASH_KEY}&per_page=1"
    resp = requests.get(url).json()
    return resp["results"][0]["urls"]["small"] if resp["results"] else ""

# Fonctions pour la gestion de l'index vectoriel
def get_csv_last_modified(csv_path):
    """Obtenir la date de dernière modification du fichier CSV source"""
    try:
        return os.path.getmtime(csv_path)
    except OSError:
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
            # Effectuer une recherche par similarité sémantique
            similar_docs = vectorstore.similarity_search(symptoms, k=3)
            
            if similar_docs:
                # Récupérer l'index du document le plus similaire
                most_similar_doc = similar_docs[0]
                doc_index = most_similar_doc.metadata.get('index')
                
                if doc_index is not None:
                    plant_data = df.iloc[doc_index].to_dict()
                    matches = pd.DataFrame([plant_data])
                    print(f"RAG: Document trouvé avec similarité: {most_similar_doc.metadata.get('plant_name')}")
        except Exception as e:
            print(f"Erreur lors de la recherche sémantique: {e}")
    
    # Fallback: méthode de recherche par mots-clés si la recherche sémantique échoue
    if matches is None or len(matches) == 0:
        print("Fallback à la recherche par mots-clés")
        # Nettoyage et préparation du texte de recherche
        clean_symptoms = symptoms.lower()
        
        # Enlever les expressions courantes
        for phrase in ["je pense que j'ai", "j'ai", "je souffre de", "je crois que"]:
            clean_symptoms = clean_symptoms.replace(phrase, "")
        clean_symptoms = clean_symptoms.strip()
        
        # Vérifier d'abord les mots-clés essentiels de maladie
        for keyword in ["paludisme", "malaria", "palu"]:
            if keyword in clean_symptoms:
                matches = df[df["maladiesoigneeparrecette"].str.contains("malaria|paludisme", case=False, na=False, regex=True)]
                if not matches.empty:
                    print(f"Correspondance trouvée pour le mot-clé: {keyword}")
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
                
                if plante not in composants_par_plante:
                    composants_par_plante[plante] = []
                
                composants_par_plante[plante].append(composant)
        
        composants_lignes = []
        for plante, comps in composants_par_plante.items():
            composants_lignes.append(f"{plante}: {', '.join(comps)}")
        
        composants = "\n".join(composants_lignes)
    
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
                    noms_text = ", ".join(noms[:5])  # Limiter à 5 noms locaux par plante
                    plant_infos.append(f"{plant_name} est connue sous le nom de: {noms_text}")
            
            if plant_infos:
                nom_local_info = "Noms locaux: " + ". ".join(plant_infos)
        else:
            # Cas simple: un seul nom local
            nom_local_info = f"Nom local: {nom_local} en {langue} ({pays})."    # Extraire les pathologies traitées
    pathologies = plant.get('maladiesoigneeparrecette', 'Non spécifié')
    
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
        dosage_info = "Posologie journalière (en grammes de plante séchée par litre d'eau):\n"
        for part in dosage_parts:
            if ":" in part:
                plante, quantite = part.split(":", 1)
                dosage_info += f"- {plante.strip()}: {quantite.strip()}g\n"
            else:
                dosage_info += f"- {part.strip()}\n"
    else:
        dosage_info = f"Dosage recommandé: {dosage}"
    
    # Formatter les parties de plantes utilisées
    parties_info = ""
    if ";" in partie_utilisee:
        parties_parts = partie_utilisee.split(";")
        parties_info = "Parties des plantes à utiliser:\n"
        for part in parties_parts:
            if ":" in part:
                plante, partie = part.split(":", 1)
                # Traduire les parties en français
                partie_fr = partie.strip().lower()
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
                
                parties_info += f"- {plante.strip()}: {partie_fr}\n"
            else:
                parties_info += f"- {part.strip()}\n"
    else:
        parties_info = f"Parties utilisées: {partie_utilisee}"
    
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
      # Générer une explication structurée même sans LLM, en respectant le même ordre que le nouveau prompt
    fallback_explanation = f"""
    Diagnostic possible
    
    D'après vos symptômes décrits: "{symptoms}", il est possible que vous souffriez de {pathologie_maj}. Cette condition requiert une attention particulière et un traitement approprié.

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
    
    try:
        # Génère explication avec LLM
        explanation = chain.run(symptoms=symptoms, plant_data=plant_data, plant_name=plant_names)
    except Exception as e:
        print(f"Erreur lors de la génération d'explication: {e}")
        explanation = fallback_explanation
    
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
