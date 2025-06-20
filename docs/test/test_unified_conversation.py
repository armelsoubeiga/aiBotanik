#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour les conversations unifiées
Ce script teste la création, récupération et suppression de conversations
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "test@aibotanik.com"
TEST_PASSWORD = "testpassword123"

def test_unified_conversations():
    """Test complet des conversations unifiées"""
    
    print("=== Test des conversations unifiées ===")
    
    # 1. Connexion pour obtenir un token
    print("\n1. Connexion...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Échec de la connexion: {response.status_code} - {response.text}")
        return False
    
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Connexion réussie")
    
    # 2. Création d'une conversation de test
    print("\n2. Création d'une conversation de test...")
    conversation_data = {
        "title": "Test Conversation - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "discussion",
        "chat_mode": "discussion",
        "messages": [
            {
                "content": "Bonjour, j'aimerais des conseils pour la digestion",
                "sender": "user"
            },
            {
                "content": "Bonjour ! Je peux vous recommander plusieurs plantes médicinales pour améliorer la digestion.",
                "sender": "bot",
                "recommendation": {
                    "plant": "Gingembre",
                    "dosage": "1 cuillère à café de poudre dans de l'eau chaude",
                    "prep": "Infusion de 10 minutes",
                    "explanation": "Le gingembre stimule la digestion et réduit les nausées",
                    "contre_indications": "Éviter en cas d'ulcère gastrique",
                    "partie_utilisee": "Rhizome",
                    "composants": "Gingérol, shogaol",
                    "nom_local": "Jenjibre",
                    "image_url": ""
                }
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/conversations", json=conversation_data, headers=headers)
    if response.status_code != 201:
        print(f"❌ Échec de la création: {response.status_code} - {response.text}")
        return False
    
    conversation = response.json()
    conversation_id = conversation["id"]
    print(f"✅ Conversation créée avec l'ID: {conversation_id}")
    
    # 3. Récupération de l'historique
    print("\n3. Récupération de l'historique...")
    response = requests.get(f"{BASE_URL}/conversations/history", headers=headers)
    if response.status_code != 200:
        print(f"❌ Échec de récupération de l'historique: {response.status_code} - {response.text}")
        return False
    
    history = response.json()
    print(f"✅ Historique récupéré: {len(history)} conversations")
    
    # Vérifier que notre conversation est dans l'historique
    found = False
    for conv in history:
        if conv["id"] == conversation_id:
            found = True
            print(f"✅ Conversation trouvée dans l'historique: {conv['title']}")
            break
    
    if not found:
        print("❌ Conversation non trouvée dans l'historique")
        return False
    
    # 4. Récupération d'une conversation complète avec messages
    print("\n4. Récupération de la conversation complète...")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages", headers=headers)
    if response.status_code != 200:
        print(f"❌ Échec de récupération complète: {response.status_code} - {response.text}")
        return False
    
    full_conversation = response.json()
    print(f"✅ Conversation complète récupérée: {len(full_conversation.get('messages', []))} messages")
    
    # Vérifier que la recommandation est bien présente
    for msg in full_conversation.get('messages', []):
        if msg['sender'] == 'bot' and msg.get('recommendation'):
            print(f"✅ Recommandation trouvée: {msg['recommendation']['plant']}")
            break
    
    # 5. Suppression de la conversation de test
    print("\n5. Suppression de la conversation de test...")
    response = requests.delete(f"{BASE_URL}/conversations/{conversation_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Échec de la suppression: {response.status_code} - {response.text}")
    else:
        print("✅ Conversation supprimée avec succès")
    
    print("\n=== Test terminé avec succès ! ===")
    return True

if __name__ == "__main__":
    test_unified_conversations()
