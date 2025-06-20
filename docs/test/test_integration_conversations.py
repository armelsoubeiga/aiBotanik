#!/usr/bin/env python3
"""
Test d'intégration complète pour les conversations unifiées
Ce script simule une connexion utilisateur et teste l'ajout de messages
"""

import requests
import json
import uuid
from datetime import datetime

API_URL = "http://localhost:8000/api"

def authenticate_user():
    """
    Authentifie un utilisateur de test et retourne le token
    """
    print("🔐 Authentification de l'utilisateur...")
    
    # Données d'authentification de test (remplace par tes vraies données)
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        
        if response.status_code == 200:
            auth_result = response.json()
            token = auth_result.get("access_token")
            user_info = auth_result.get("user", {})
            print(f"✅ Authentification réussie pour {user_info.get('email', 'utilisateur')}")
            return token, user_info.get("id")
        else:
            print(f"❌ Échec de l'authentification: {response.status_code}")
            print(f"Détails: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return None, None

def create_test_conversation(token, user_id):
    """
    Crée une conversation de test
    """
    print("🆕 Création d'une conversation de test...")
    
    conversation_data = {
        "title": "Test Conversation - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "discussion",
        "chat_mode": "discussion",
        "messages": [
            {
                "content": "Bonjour, ceci est un message de test",
                "sender": "user"
            },
            {
                "content": "Bonjour ! Comment puis-je vous aider ?",
                "sender": "bot"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/conversations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json=conversation_data
        )
        
        if response.status_code in [200, 201]:
            conversation = response.json()
            print(f"✅ Conversation créée: {conversation.get('id')}")
            return conversation.get('id')
        else:
            print(f"❌ Échec de création: {response.status_code}")
            print(f"Détails: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de création: {e}")
        return None

def test_add_message_to_conversation(token, conversation_id):
    """
    Test l'ajout d'un message à la conversation
    """
    print(f"💬 Test d'ajout de message à la conversation {conversation_id}")
    
    test_message = {
        "content": "Nouveau message de test - " + datetime.now().strftime("%H:%M:%S"),
        "sender": "user",
        "recommendation": None
    }
    
    try:
        response = requests.post(
            f"{API_URL}/conversations/{conversation_id}/messages",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json=test_message
        )
        
        print(f"📨 Réponse HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Message ajouté avec succès!")
            print(f"ID du message: {result.get('id')}")
            print(f"Contenu: {result.get('content')}")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Détails: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout: {e}")
        return False

def test_get_conversation_with_messages(token, conversation_id):
    """
    Récupère la conversation avec ses messages pour vérifier la sauvegarde
    """
    print(f"📖 Récupération de la conversation {conversation_id}")
    
    try:
        response = requests.get(
            f"{API_URL}/conversations/{conversation_id}/messages",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 200:
            conversation = response.json()
            messages = conversation.get('messages', [])
            print(f"✅ Conversation récupérée avec {len(messages)} messages")
            
            for i, msg in enumerate(messages):
                print(f"  Message {i+1}: [{msg.get('sender')}] {msg.get('content')[:50]}...")
            
            return conversation
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Détails: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        return None

def main():
    """
    Fonction principale de test
    """
    print("🧪 Test d'intégration des conversations unifiées")
    print("=" * 60)
    
    # Étape 1: Authentification
    token, user_id = authenticate_user()
    if not token:
        print("❌ Impossible de continuer sans authentification")
        print("💡 Assure-toi d'avoir un utilisateur test avec les identifiants:")
        print("   email: test@example.com")
        print("   password: testpassword")
        return
    
    # Étape 2: Création d'une conversation
    conversation_id = create_test_conversation(token, user_id)
    if not conversation_id:
        print("❌ Impossible de continuer sans conversation")
        return
    
    # Étape 3: Ajout d'un message
    success = test_add_message_to_conversation(token, conversation_id)
    if not success:
        print("❌ Échec de l'ajout de message")
        return
    
    # Étape 4: Vérification
    conversation = test_get_conversation_with_messages(token, conversation_id)
    if conversation:
        print(f"✅ Test réussi! Conversation contient {len(conversation.get('messages', []))} messages")
    else:
        print("❌ Impossible de vérifier la conversation")
    
    print("\n🎉 Test d'intégration terminé!")

if __name__ == "__main__":
    main()
