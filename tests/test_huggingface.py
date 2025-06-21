"""
Test de l'intégration de HuggingFace avec LangChain.
Ce script teste les deux approches :
1. Local avec HuggingFacePipeline
2. API distante avec HuggingFaceHub

Exécutez ce script pour valider que l'intégration fonctionne correctement.
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN", os.getenv("HF_API_KEY"))

if not HF_API_KEY:
    logger.error("La clé API HuggingFace est manquante. Définissez HUGGINGFACEHUB_API_TOKEN dans le fichier .env")
    sys.exit(1)

# Importer les fonctions à tester
from langchain_chains import init_llm_model, generate_huggingface_response

def test_huggingface_pipeline():
    """Teste l'initialisation du modèle avec HuggingFacePipeline (local)"""
    logger.info("=== Test du pipeline HuggingFace local ===")
    
    try:
        # Initialiser le modèle local
        llm = init_llm_model(use_local=True)
        
        if llm:
            # Essayer une requête simple
            response = llm.invoke("Quelles plantes sont efficaces contre la fièvre?")
            logger.info(f"Réponse du modèle local: {response}")
            return True
        else:
            logger.error("Échec de l'initialisation du modèle local")
            return False
    except Exception as e:
        logger.error(f"Exception lors du test du pipeline local: {e}")
        return False

def test_huggingface_hub():
    """Teste l'initialisation du modèle avec HuggingFaceHub (API distante)"""
    logger.info("=== Test de l'API HuggingFace distante ===")
    
    try:
        # Initialiser le modèle via API
        llm = init_llm_model(use_local=False)
        
        if llm:
            # Essayer une requête simple
            response = llm.invoke("Quelles plantes sont efficaces contre la fièvre?")
            logger.info(f"Réponse de l'API distante: {response}")
            return True
        else:
            logger.error("Échec de l'initialisation de l'API distante")
            return False
    except Exception as e:
        logger.error(f"Exception lors du test de l'API distante: {e}")
        return False

def test_direct_api():
    """Teste la fonction generate_huggingface_response (API HTTP directe)"""
    logger.info("=== Test de l'API HTTP directe ===")
    
    try:
        # Appeler directement l'API
        response = generate_huggingface_response(
            prompt="Quelles plantes sont efficaces contre la fièvre?",
            api_key=HF_API_KEY,
            model_id="google/flan-t5-base",
            max_length=100
        )
        
        if response:
            logger.info(f"Réponse de l'API HTTP directe: {response}")
            return True
        else:
            logger.error("Échec de l'appel à l'API HTTP directe")
            return False
    except Exception as e:
        logger.error(f"Exception lors du test de l'API HTTP directe: {e}")
        return False

if __name__ == "__main__":
    results = {
        "Local Pipeline": "NON TESTÉ",
        "API Distante": "NON TESTÉ",
        "API HTTP Directe": "NON TESTÉ"
    }
    
    # Tester le pipeline local (peut être lent au chargement)
    if input("Tester le pipeline local? (o/n): ").lower() == 'o':
        results["Local Pipeline"] = "SUCCÈS" if test_huggingface_pipeline() else "ÉCHEC"
    
    # Tester l'API distante
    results["API Distante"] = "SUCCÈS" if test_huggingface_hub() else "ÉCHEC"
    
    # Tester l'API HTTP directe
    results["API HTTP Directe"] = "SUCCÈS" if test_direct_api() else "ÉCHEC"
    
    # Afficher les résultats
    print("\n=== RÉSULTATS DES TESTS ===")
    for test, result in results.items():
        print(f"{test}: {result}")
