#!/usr/bin/env python3
"""
Test des endpoints avec OpenAI activé
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_admin_config():
    """Test de l'endpoint de configuration admin"""
    print("=== Test de la configuration admin ===")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/config/llm", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"Configuration reçue: {json.dumps(config, indent=2)}")
            
            # Vérifications
            if config.get("has_openai_key"):
                print("✅ Clé OpenAI détectée")
            else:
                print("❌ Clé OpenAI non détectée")
                
            if config.get("current_backend") == "openai":
                print("✅ Backend OpenAI activé")
            else:
                print(f"⚠️ Backend inattendu: {config.get('current_backend')}")
                
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test admin: {e}")
        return False

def test_chat_endpoint():
    """Test de l'endpoint de chat"""
    print("\n=== Test de l'endpoint chat ===")
    
    try:
        chat_data = {
            "message": "Qu'est-ce que la phytothérapie africaine ?"
        }
        
        print("Envoi de la requête chat...")
        response = requests.post(f"{BASE_URL}/chat", json=chat_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat réussi")
            print(f"Longueur de la réponse: {len(result.get('response', ''))} caractères")
            print(f"Début de la réponse: {result.get('response', '')[:150]}...")
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test chat: {e}")
        return False

def test_consultation_endpoint():
    """Test de l'endpoint de consultation"""
    print("\n=== Test de l'endpoint consultation ===")
    
    try:
        consultation_data = {
            "symptoms": "J'ai de la fièvre et des frissons depuis 2 jours"
        }
        
        print("Envoi de la requête consultation...")
        response = requests.post(f"{BASE_URL}/recommend", json=consultation_data, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Consultation réussie")
            print(f"Plante recommandée: {result.get('plant', 'Non spécifiée')}")
            print(f"Dosage: {result.get('dosage', 'Non spécifié')}")
            print(f"Longueur de l'explication: {len(result.get('explanation', ''))} caractères")
            print(f"Image URL: {result.get('image_url', 'Aucune')}")
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test consultation: {e}")
        return False

def main():
    """Exécuter tous les tests"""
    print("🧪 Test des endpoints OpenAI")
    print("Assurez-vous que le serveur FastAPI est démarré sur le port 8000\n")
    
    # Attendre un peu que le serveur soit prêt
    print("Attente de 3 secondes pour que le serveur soit prêt...")
    time.sleep(3)
    
    # Tests
    success_count = 0
    total_tests = 3
    
    if test_admin_config():
        success_count += 1
        
    if test_chat_endpoint():
        success_count += 1
        
    if test_consultation_endpoint():
        success_count += 1
    
    print(f"\n📊 Résultats: {success_count}/{total_tests} tests réussis")
    
    if success_count == total_tests:
        print("🎉 Tous les tests sont passés avec succès !")
    else:
        print("⚠️ Certains tests ont échoué")

if __name__ == "__main__":
    main()
