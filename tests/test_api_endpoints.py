"""
Test de l'API FastAPI pour vérifier que les corrections fonctionnent.
"""

import requests
import json

def test_chat_endpoint():
    """Test de l'endpoint /chat"""
    url = "http://localhost:8000/chat"
    payload = {
        "symptoms": "Bonjour, comment allez-vous?"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur lors du test chat: {e}")
        return False

def test_recommend_endpoint():
    """Test de l'endpoint /recommend"""
    url = "http://localhost:8000/recommend"
    payload = {
        "symptoms": "J'ai de la fièvre et des maux de tête"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur lors du test recommend: {e}")
        return False

if __name__ == "__main__":
    print("=== Test des endpoints API ===")
    
    # Test du chat
    print("\n1. Test de l'endpoint /chat:")
    chat_success = test_chat_endpoint()
    
    # Test des recommendations
    print("\n2. Test de l'endpoint /recommend:")
    recommend_success = test_recommend_endpoint()
    
    print(f"\nRésultats:")
    print(f"Chat endpoint: {'SUCCÈS' if chat_success else 'ÉCHEC'}")
    print(f"Recommend endpoint: {'SUCCÈS' if recommend_success else 'ÉCHEC'}")
