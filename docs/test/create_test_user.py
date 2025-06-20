#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de création d'un utilisateur de test
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "test@aibotanik.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Utilisateur Test"

def create_test_user():
    """Crée un utilisateur de test"""
    
    print("=== Création d'un utilisateur de test ===")
    
    user_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirmPassword": TEST_PASSWORD,
        "name": TEST_NAME
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=user_data)
    if response.status_code == 201:
        print("✅ Utilisateur de test créé avec succès")
        token_data = response.json()
        print(f"Token: {token_data['access_token'][:20]}...")
        return True
    elif response.status_code == 400 and "déjà utilisé" in response.text:
        print("ℹ️  Utilisateur de test existe déjà")
        return True
    else:
        print(f"❌ Échec de la création: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_test_user()
