import os
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

# Initialiser Embeddings 
emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Prompt template
template = """
Tu es un expert en phytothérapie africaine. Pour les symptômes décrits: {symptoms},
et en considérant les données de la plante: {plant_data}, formule une explication complète et structurée avec:

1. Une présentation de la plante principale ({plant_name}) et ses propriétés médicinales
2. Comment cette plante aide à traiter spécifiquement les symptômes mentionnés
3. La posologie recommandée (méthode de préparation et dosage)
4. Les précautions et contre-indications importantes
5. Les principes actifs de la plante qui agissent sur les symptômes

Réponds en français avec un ton rassurant et informatif, comme un guérisseur traditionnel moderne.
"""
prompt = PromptTemplate(input_variables=["symptoms","plant_data", "plant_name"], template=template)

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

# Initialiser vectorstore avec les données du DataFrame
def get_recommendation(symptoms: str, df):
    import pandas as pd
    
    # Initialiser le vectorstore une seule fois (idéalement à l'extérieur de cette fonction)
    # pour éviter de le recréer à chaque requête
    global vectorstore_initialized, vectorstore
    
    if 'vectorstore_initialized' not in globals():
        vectorstore_initialized = False
        
    if not vectorstore_initialized:
        try:
            # Préparer les documents avec des informations significatives
            documents = []
            for _, row in df.iterrows():
                # Créer un contenu enrichi pour chaque plante avec les symptômes qu'elle traite
                content = f"Symptômes: {row.get('maladiesoigneeparrecette', '')}\n"
                content += f"Plante: {row.get('plante_recette', '')}\n"
                content += f"Dosage: {row.get('plante_quantite_recette', '')}\n"
                content += f"Préparation: {row.get('recette', '')}"
                
                # Créer un document avec metadata pour faciliter la récupération
                metadata = {
                    "plant_name": str(row.get('plante_recette', '')).split(';')[0].strip(),
                    "index": _
                }
                documents.append(Document(page_content=content, metadata=metadata))
            
            # Créer le vectorstore
            globals()['vectorstore'] = FAISS.from_documents(documents, emb)
            globals()['vectorstore_initialized'] = True
            print("Vectorstore initialisé avec succès")
        except Exception as e:
            print(f"Erreur lors de la création de vectorstore: {e}")
            # Continuer avec la recherche par mots clés si la méthode vectorielle échoue
            globals()['vectorstore'] = None
            globals()['vectorstore_initialized'] = False
      # Approche RAG: Recherche sémantique avec embeddings
    matches = None
    if 'vectorstore_initialized' in globals() and vectorstore_initialized and 'vectorstore' in globals():
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
    
    # Information sur le nom local
    nom_local_info = ""
    if nom_local and langue and pays:
        nom_local_info = f"Cette plante est connue localement sous le nom de '{nom_local}' en {langue} ({pays})."
    
    # Générer une explication structurée même sans LLM
    fallback_explanation = f"""
    La plante {plant_names} est recommandée pour traiter les symptômes décrits: {symptoms}.
    
    Cette plante est particulièrement efficace pour soigner: {plant.get('maladiesoigneeparrecette', 'Non spécifié')}.
    
    Pour la préparation: {preparation}
    
    Dosage recommandé: {dosage}
    
    Parties de la plante utilisées: {partie_utilisee}
    
    {nom_local_info}
    
    Composants actifs: {composants}
    
    Précautions et contre-indications: {contre_indications}
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
