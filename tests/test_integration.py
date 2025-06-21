"""
Test rapide pour vérifier l'intégration HuggingFace Pipeline.
Ce script teste la nouvelle approche qui utilise directement les pipelines Transformers.
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

def test_simple_pipeline():
    """Test simple du pipeline HuggingFace comme dans votre exemple"""
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
        from langchain_huggingface import HuggingFacePipeline
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate
        
        logger.info("Chargement du modèle...")
        
        # 1) Charge le modèle localement (comme dans votre exemple)
        tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
        model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
        
        # 2) Crée un pipeline text2text-generation avec les flags corrects
        text2text = pipeline(
            task="text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device="cpu",
            do_sample=True,
            temperature=0.5,
            max_new_tokens=100,
        )
        
        # 3) Enrobe-le dans LangChain
        llm = HuggingFacePipeline(pipeline=text2text)
        
        # 4) Monte ta chaîne
        prompt = PromptTemplate.from_template("Explain this concept in simple terms: {concept}")
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Test avec une question simple
        response = chain.run(concept="phytothérapie")
        logger.info(f"Réponse du modèle: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_function():
    """Test de la fonction generate_chat_response modifiée"""
    try:
        # Importer la fonction de votre module
        from langchain_chains import generate_chat_response
        
        logger.info("Test de la fonction generate_chat_response...")
        response = generate_chat_response("Bonjour, comment utiliser le moringa?")
        logger.info(f"Réponse: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test de generate_chat_response: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Test de l'intégration HuggingFace Pipeline ===")
    
    # Test 1: Pipeline simple (comme votre exemple)
    if input("Tester le pipeline simple? (o/n): ").lower() == 'o':
        success1 = test_simple_pipeline()
        print(f"Test pipeline simple: {'SUCCÈS' if success1 else 'ÉCHEC'}")
    
    # Test 2: Fonction generate_chat_response
    success2 = test_chat_function()
    print(f"Test generate_chat_response: {'SUCCÈS' if success2 else 'ÉCHEC'}")
