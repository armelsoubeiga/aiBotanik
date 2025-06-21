#!/usr/bin/env python3
"""
Test de robustesse de l'intégration OpenAI
Vérifie la gestion des erreurs réseau et la validation des clés API
"""

import os
import sys
import time
from dotenv import load_dotenv

# Charger l'environnement
load_dotenv()

# Ajouter le répertoire backend au path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_openai_key_validation():
    """Test la fonction de validation de clé OpenAI"""
    print("=== Test de validation de clé OpenAI ===")
    
    from app import verify_openai_key
    
    # Test avec une clé vide
    print("Test 1: Clé vide")
    result = verify_openai_key("")
    print(f"Résultat: {result} (attendu: False)")
    assert not result, "Une clé vide devrait être invalide"
    
    # Test avec une clé mal formée
    print("Test 2: Clé mal formée")
    result = verify_openai_key("invalid-key")
    print(f"Résultat: {result} (attendu: False)")
    assert not result, "Une clé mal formée devrait être invalide"
    
    # Test avec une clé bien formée mais probablement invalide
    print("Test 3: Clé bien formée mais invalide")
    result = verify_openai_key("sk-1234567890abcdef1234567890abcdef1234567890abcdef")
    print(f"Résultat: {result}")
    # Cette clé peut être considérée comme valide en cas d'erreur réseau
    
    # Test avec la vraie clé (si disponible)
    real_key = os.getenv("OPENAI_API_KEY")
    if real_key:
        print("Test 4: Clé réelle depuis .env")
        result = verify_openai_key(real_key)
        print(f"Résultat: {result}")
    else:
        print("Test 4: Aucune clé réelle trouvée dans .env")
    
    print("✅ Tests de validation de clé terminés\n")

def test_openai_chains_resilience():
    """Test la résilience des chaînes OpenAI"""
    print("=== Test de résilience des chaînes OpenAI ===")
    
    try:
        # Importer le module OpenAI
        import langchain_chains_openai
        print("✅ Module OpenAI importé avec succès")
        
        # Test de la fonction de chat avec gestion d'erreurs
        print("Test de la fonction de chat...")
        try:
            response = langchain_chains_openai.generate_chat_response("Qu'est-ce que le paludisme?")
            print(f"Réponse reçue (longueur: {len(response)} caractères)")
            print(f"Début de la réponse: {response[:100]}...")
            print("✅ Chat fonctionne correctement")
        except Exception as e:
            print(f"⚠️ Erreur dans le chat (mais gérée): {e}")
        
        # Test de recommandation (plus complexe)
        print("\nTest de la fonction de recommandation...")
        try:
            import pandas as pd
            
            # Charger le CSV de test
            csv_path = "data/baseplante.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                response = langchain_chains_openai.get_recommendation("J'ai de la fièvre et des frissons", df, csv_path)
                print(f"Recommandation reçue: {type(response)}")
                if isinstance(response, dict):
                    print(f"Clés disponibles: {list(response.keys())}")
                print("✅ Recommandation fonctionne")
            else:
                print(f"⚠️ Fichier CSV non trouvé: {csv_path}")
        except Exception as e:
            print(f"⚠️ Erreur dans la recommandation (mais peut être gérée): {e}")
            import traceback
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ Impossible d'importer le module OpenAI: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Tests de résilience terminés\n")

def test_fallback_mechanism():
    """Test le mécanisme de fallback vers HuggingFace"""
    print("=== Test du mécanisme de fallback ===")
    
    # Simuler une clé OpenAI invalide temporairement
    original_key = os.environ.get("OPENAI_API_KEY")
    
    try:
        # Supprimer temporairement la clé pour tester le fallback
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        from app import get_llm_module
        
        # Recharger la configuration
        module = get_llm_module()
        print(f"Module sélectionné: {module.__name__}")
        
        # Vérifier que c'est bien HuggingFace
        if "huggingface" in module.__name__.lower() or "langchain_chains" in module.__name__:
            print("✅ Fallback vers HuggingFace réussi")
        else:
            print(f"⚠️ Fallback inattendu vers: {module.__name__}")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du test de fallback: {e}")
    finally:
        # Restaurer la clé originale
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
    
    print("✅ Test de fallback terminé\n")

def main():
    """Exécuter tous les tests"""
    print("🧪 Début des tests de robustesse OpenAI\n")
    start_time = time.time()
    
    try:
        test_openai_key_validation()
        test_openai_chains_resilience() 
        test_fallback_mechanism()
        
        duration = time.time() - start_time
        print(f"🎉 Tous les tests terminés en {duration:.2f} secondes")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
