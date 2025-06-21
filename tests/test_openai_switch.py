#!/usr/bin/env python3
"""
Test du changement de backend vers OpenAI et des endpoints
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Charger l'environnement
load_dotenv()

def test_backend_switch_to_openai():
    """Test le changement de backend vers OpenAI"""
    print("=== Test changement de backend vers OpenAI ===")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__)))
        
        # Tester la validation de la clé OpenAI
        from app import verify_openai_key
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            is_valid = verify_openai_key(api_key)
            print(f"Validation de la clé OpenAI: {is_valid}")
            
            if is_valid:
                # Forcer le changement vers OpenAI
                from app import save_config
                save_config({"llm_backend": "openai"})
                print("✅ Configuration changée vers OpenAI")
                
                # Tester le chargement du module
                from app import get_llm_module
                module = get_llm_module()
                print(f"Module chargé: {module.__name__}")
                
                if "openai" in module.__name__:
                    print("✅ Backend OpenAI activé avec succès")
                    return True
                else:
                    print(f"⚠️ Backend inattendu: {module.__name__}")
                    return False
            else:
                print("❌ Clé OpenAI invalide")
                return False
        else:
            print("❌ Aucune clé OpenAI trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_endpoints():
    """Test les endpoints avec OpenAI activé (nécessite un serveur en cours)"""
    print("\n=== Test des endpoints OpenAI ===")
    
    base_url = "http://localhost:8000"
    
    # Test de l'endpoint de configuration
    try:
        response = requests.get(f"{base_url}/admin/config/llm", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"Configuration LLM: {config}")
            
            if config.get("has_openai_key"):
                print("✅ Clé OpenAI détectée dans l'admin")
            else:
                print("⚠️ Clé OpenAI non détectée dans l'admin")
                
        else:
            print(f"❌ Erreur lors de l'accès à la config: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Impossible de tester les endpoints (serveur non démarré?): {e}")
        return False
    
    # Test d'un appel de chat simple
    try:
        chat_data = {
            "message": "Bonjour, que savez-vous sur la phytothérapie africaine?"
        }
        response = requests.post(f"{base_url}/chat", json=chat_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat réussi (longueur: {len(result.get('response', ''))}) caractères")
            print(f"Début de la réponse: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Erreur lors du chat: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau lors du test de chat: {e}")
        
    return True

def main():
    """Exécuter les tests"""
    print("🧪 Test de changement vers OpenAI\n")
    
    # Test du changement de backend
    success = test_backend_switch_to_openai()
    
    if success:
        print("\n⚠️ Pour tester les endpoints, assurez-vous que le serveur FastAPI est démarré")
        print("Commande: python app.py")
        print("Puis testez manuellement l'interface admin et les endpoints")
        
        # Optionnel: tester les endpoints si le serveur est actif
        test_openai_endpoints()
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()
