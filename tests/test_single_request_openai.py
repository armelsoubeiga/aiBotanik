#!/usr/bin/env python3
"""
Test pour vérifier qu'UNE SEULE REQUÊTE est faite vers OpenAI
"""

import requests
import json
from unittest.mock import patch
import logging

def test_single_openai_request():
    """Test pour confirmer qu'une seule requête OpenAI est faite par consultation"""
    print("🔍 Test de vérification : UNE SEULE requête OpenAI par consultation")
    print("=" * 70)
    
    # Compter les appels vers OpenAI
    openai_call_count = 0
    openai_urls = []
    
    # Capturer les requêtes HTTP vers OpenAI
    original_requests_post = requests.post
    
    def count_openai_http_calls(url, *args, **kwargs):
        global openai_call_count, openai_urls
        if "api.openai.com" in url:
            openai_call_count += 1
            openai_urls.append(url)
            print(f"� Requête HTTP OpenAI #{openai_call_count}: {url}")
        return original_requests_post(url, *args, **kwargs)
    
    try:
        print("📡 Test via API REST...")
        payload = {"symptoms": "j'ai des symptômes de paludisme"}
        headers = {"Content-Type": "application/json"}
        
        # Patch les requêtes pour compter les appels vers OpenAI
        with patch('requests.post', side_effect=count_openai_http_calls):
            print("📤 Envoi de la requête de consultation...")
            response = requests.post('http://localhost:8001/recommend', json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Consultation réussie via API")
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return
        
        print("\n" + "=" * 70)
        print(f"📊 RÉSULTAT DU COMPTAGE:")
        print(f"🔢 Nombre total d'appels OpenAI: {openai_call_count}")
        
        if openai_urls:
            print("📋 URLs appelées:")
            for i, url in enumerate(openai_urls, 1):
                print(f"   {i}. {url}")
        
        if openai_call_count == 1:
            print("✅ SUCCÈS: UNE SEULE requête OpenAI effectuée !")
            print("✅ La contrainte est respectée.")
        elif openai_call_count == 0:
            print("⚠️ ATTENTION: Aucun appel OpenAI détecté")
            print("   Possible utilisation de cache ou configuration incorrecte")
        else:
            print(f"❌ ÉCHEC: {openai_call_count} requêtes OpenAI détectées")
            print("❌ La contrainte d'une seule requête n'est PAS respectée")
        
        print("=" * 70)
        
        # Vérifier que tous les champs structurés sont présents
        if 'result' in locals() and result:
            required_fields = ['diagnostic', 'symptomes', 'presentation', 'mode_action', 
                             'traitement_info', 'precautions_info', 'composants_info', 'resume_traitement']
            
            present_fields = [field for field in required_fields if result.get(field)]
            missing_fields = [field for field in required_fields if not result.get(field)]
            
            print(f"📋 Champs structurés présents: {len(present_fields)}/{len(required_fields)}")
            if missing_fields:
                print(f"⚠️ Champs manquants: {missing_fields}")
            else:
                print("✅ Tous les champs structurés sont présents")
                
            print("\n📝 Aperçu des champs extraits:")
            for field in present_fields[:3]:  # Afficher les 3 premiers champs
                content = str(result.get(field, ''))[:80] + "..." if len(str(result.get(field, ''))) > 80 else str(result.get(field, ''))
                print(f"   {field}: {content}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_openai_request()
