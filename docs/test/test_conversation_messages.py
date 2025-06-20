#!/usr/bin/env python3
"""
Test script pour vérifier l'ajout de messages dans les conversations unifiées
"""

import requests
import json
import uuid
from datetime import datetime

API_URL = "http://localhost:8000/api"

def test_add_message_to_conversation():
    """
    Test l'ajout d'un message à une conversation unifiée
    """
    print("🧪 Test d'ajout de message à une conversation unifiée")
    
    # Données de test - utilise des IDs que tu peux remplacer par de vrais IDs de ta DB
    test_user_id = "c504f08f-b443-4ebc-bf8f-68da56fedcf4"  # Remplace par un vrai ID utilisateur
    test_conversation_id = "e3694d3b-ff21-4192-a409-15181b859c4b"  # Remplace par un vrai ID de conversation
    
    # Tu devrais d'abord obtenir un vrai token d'authentification
    # Pour ce test, je vais utiliser un token fictif - remplace par un vrai token JWT
    test_token = "your_jwt_token_here"
    
    # Message de test
    test_message = {
        "content": "Test message from script",
        "sender": "user",
        "recommendation": None
    }
    
    print(f"📤 Envoi du message à la conversation {test_conversation_id}")
    print(f"Message: {test_message}")
    
    try:
        response = requests.post(
            f"{API_URL}/conversations/{test_conversation_id}/messages",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {test_token}"
            },
            json=test_message
        )
        
        print(f"📨 Réponse HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Message ajouté avec succès!")
            print(f"Réponse: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Détails: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")

def test_conversation_endpoint():
    """
    Test simple pour vérifier que l'endpoint existe
    """
    print("\n🧪 Test de l'existence de l'endpoint")
    
    try:
        # Test sans token pour voir la réponse d'erreur d'auth
        response = requests.post(
            f"{API_URL}/conversations/test-id/messages",
            headers={"Content-Type": "application/json"},
            json={"content": "test", "sender": "user"}
        )
        
        print(f"📨 Réponse HTTP (sans auth): {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Endpoint existe - erreur d'authentification attendue")
        elif response.status_code == 422:
            print("✅ Endpoint existe - erreur de validation attendue")
        else:
            print(f"⚠️ Réponse inattendue: {response.status_code}")
            print(f"Détails: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    print("🚀 Test des messages dans les conversations unifiées")
    print("=" * 50)
    
    test_conversation_endpoint()
    # test_add_message_to_conversation()  # Décommenter si tu as un vrai token
    
    print("\n📋 Instructions pour un test complet:")
    print("1. Remplace test_user_id par un vrai ID utilisateur de ta DB")
    print("2. Remplace test_conversation_id par un vrai ID de conversation de ta DB")
    print("3. Obtiens un vrai token JWT en te connectant via l'interface")
    print("4. Remplace test_token par ce token")
    print("5. Décommenter l'appel à test_add_message_to_conversation()")
