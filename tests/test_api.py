#!/usr/bin/env python
"""
Script de test de l'API aiBotanik
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def print_response(resp):
    """Affiche une réponse de manière formatée"""
    print(f"Status: {resp.status_code}")
    print(f"Headers: {resp.headers}")
    try:
        print(f"Content: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Content: {resp.text}")
    print("---")

def test_signup():
    """Teste la création d'un compte"""
    print("Test de création d'un compte...")
    data = {
        "email": "nouveautest@example.com",  # Email modifié pour éviter les conflits
        "name": "Test User",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    
    resp = requests.post(f"{BASE_URL}/auth/signup", json=data)
    print_response(resp)
    return resp.json() if resp.status_code in (200, 201) else None

def test_login():
    """Teste la connexion"""
    print("Test de connexion...")
    data = {
        "email": "nouveautest@example.com",  # Utiliser le même email que pour l'inscription
        "password": "Password123!"
    }
    
    resp = requests.post(f"{BASE_URL}/auth/login", json=data)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else None

def test_create_consultation(token):
    """Teste la création d'une consultation"""
    print("Test de création d'une consultation...")
    data = {
        "title": "Consultation de test",
        "type": "discussion",
        "messages": [
            {
                "content": "Bonjour, j'ai des problèmes digestifs",
                "sender": "user"
            },
            {
                "content": "Je peux vous aider avec ça. Quels sont vos symptômes exacts ?",
                "sender": "bot"
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/consultations", json=data, headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 201 else None

def test_get_consultations(token):
    """Teste la récupération des consultations"""
    print("Test de récupération des consultations...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/consultations", headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else []

def test_add_message(token, consultation_id):
    """Teste l'ajout d'un message à une consultation"""
    print("Test d'ajout de message...")
    data = {
        "content": "J'ai aussi des maux de tête",
        "sender": "user",
        "consultation_id": consultation_id  # Ajout de l'ID de consultation pour la validation
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/consultations/{consultation_id}/messages", 
                       json=data, headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else None

def test_update_consultation(token, consultation_id):
    """Teste la mise à jour d'une consultation"""
    print("Test de mise à jour d'une consultation...")
    data = {
        "title": "Consultation mise à jour",
        "summary": "Problèmes digestifs et maux de tête"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.put(f"{BASE_URL}/consultations/{consultation_id}", 
                      json=data, headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else None

def test_get_current_user(token):
    """Teste la récupération de l'utilisateur actuel"""
    print("Test de récupération de l'utilisateur actuel...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else None

def test_validate_token(token):
    """Teste la validation du token"""
    print("Test de validation du token...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/auth/validate", headers=headers)
    print_response(resp)
    return resp.json() if resp.status_code == 200 else None

def main():
    """Fonction principale de test"""
    print("=== Début des tests API ===")
    
    # Tentative de connexion directement
    token_data = None
    try:
        token_data = test_login()
        print("Connexion réussie")
    except Exception as e:
        print(f"Erreur lors de la connexion: {e}")
        print("Tentative d'inscription...")
        try:
            token_data = test_signup()
            print("Inscription réussie")
        except Exception as e:
            print(f"Erreur lors de l'inscription: {e}")
            sys.exit(1)
    
    if not token_data or "access_token" not in token_data:
        print("Impossible d'obtenir un token d'accès")
        sys.exit(1)
        
    token = token_data["access_token"]
    
    # Valider le token
    if not test_validate_token(token):
        print("Validation du token échouée")
        sys.exit(1)
        
    # Récupérer l'utilisateur actuel
    if not test_get_current_user(token):
        print("Récupération de l'utilisateur échouée")
        sys.exit(1)
    
    # Créer une consultation
    consultation = test_create_consultation(token)
    if not consultation or "id" not in consultation:
        print("Création de consultation échouée")
        sys.exit(1)
        
    consultation_id = consultation["id"]
    
    # Ajouter un message
    if not test_add_message(token, consultation_id):
        print("Ajout de message échoué")
    
    # Mettre à jour la consultation
    if not test_update_consultation(token, consultation_id):
        print("Mise à jour de consultation échouée")
    
    # Récupérer les consultations
    consultations = test_get_consultations(token)
    if not consultations:
        print("Récupération des consultations échouée")
    
    print("=== Fin des tests API ===")

if __name__ == "__main__":
    main()
