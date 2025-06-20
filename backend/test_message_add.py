"""
Script de test pour valider la fonctionnalité d'ajout de message à une consultation existante
"""
import requests
import json
import sys
import uuid
from datetime import datetime

# URL de l'API
API_URL = "http://localhost:8000/api"

# Fonction pour se connecter et récupérer un token
def login():
    url = f"{API_URL}/auth/login"
    data = {
        "email": "test@example.com",  # Utilisez un email valide
        "password": "password123"      # Utilisez le mot de passe correspondant
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code != 200:
        print(f"Erreur de connexion: {response.status_code} - {response.text}")
        sys.exit(1)
        
    token_data = response.json()
    return token_data["access_token"]

# Fonction pour créer une nouvelle consultation
def create_consultation(token):
    url = f"{API_URL}/consultations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "title": f"Test consultation {datetime.now().isoformat()}",
        "type": "discussion",
        "messages": [
            {
                "content": "Bonjour, c'est un test",
                "sender": "user"
            },
            {
                "content": "Bonjour, je vous réponds",
                "sender": "bot"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 201:
        print(f"Erreur lors de la création de la consultation: {response.status_code} - {response.text}")
        sys.exit(1)
        
    print("Consultation créée avec succès")
    return response.json()

# Fonction pour ajouter un message à une consultation
def add_message(token, consultation_id, content, sender):
    url = f"{API_URL}/consultations/{consultation_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Créer un message avec le bon format
    data = {
        "content": content,
        "sender": sender,
        "consultation_id": consultation_id  # Vérifier si ce champ est nécessaire dans le body
    }
    
    print(f"Envoi du message: {json.dumps(data)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"Erreur lors de l'ajout du message: {response.status_code} - {response.text}")
        return None
        
    print("Message ajouté avec succès")
    return response.json()

# Fonction pour récupérer une consultation avec ses messages
def get_consultation(token, consultation_id):
    url = f"{API_URL}/consultations/{consultation_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur lors de la récupération de la consultation: {response.status_code} - {response.text}")
        return None
        
    print(f"Consultation récupérée avec {len(response.json().get('messages', []))} messages")
    return response.json()

# Test principal
def main():
    print("Début du test d'ajout de message")
    
    # Connexion
    token = login()
    print(f"Token obtenu: {token[:10]}...")
    
    # Création d'une consultation
    consultation = create_consultation(token)
    consultation_id = consultation["id"]
    
    # Vérifier que la consultation a été créée correctement
    fetched_consultation = get_consultation(token, consultation_id)
    if not fetched_consultation:
        print("Impossible de récupérer la consultation créée")
        sys.exit(1)
        
    initial_message_count = len(fetched_consultation.get("messages", []))
    print(f"Consultation initiale avec {initial_message_count} messages")
    
    # Ajouter un nouveau message à la consultation
    new_message = add_message(token, consultation_id, 
                             f"Nouveau message de test {uuid.uuid4()}", 
                             "user")
    
    if not new_message:
        print("Erreur: impossible d'ajouter un message")
        sys.exit(1)
        
    # Vérifier que le message a bien été ajouté
    updated_consultation = get_consultation(token, consultation_id)
    if not updated_consultation:
        print("Impossible de récupérer la consultation mise à jour")
        sys.exit(1)
        
    final_message_count = len(updated_consultation.get("messages", []))
    print(f"Consultation finale avec {final_message_count} messages")
    
    # Vérifier que le nombre de messages a augmenté
    if final_message_count <= initial_message_count:
        print("Erreur: le message n'a pas été ajouté correctement")
        sys.exit(1)
        
    print("Test réussi: message ajouté correctement à la consultation")
    
    # Ajouter un message bot pour compléter la conversation
    bot_message = add_message(token, consultation_id, 
                             f"Réponse du bot: {uuid.uuid4()}", 
                             "bot")
    
    if not bot_message:
        print("Erreur: impossible d'ajouter un message bot")
        sys.exit(1)
    
    print("Test complet réussi!")

if __name__ == "__main__":
    main()
