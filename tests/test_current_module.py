#!/usr/bin/env python3
"""
Test pour vérifier quel module est vraiment utilisé
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_current_module():
    """
    Teste quelle configuration est actuellement active
    """
    print("🔍 Test de la configuration actuelle")
    print("=" * 50)
    
    try:
        # Vérifier la config actuelle
        response = requests.get(f"{API_BASE_URL}/admin/config/llm")
        
        if response.status_code == 200:
            config = response.json()
            print(f"📋 Configuration actuelle: {config}")
            print(f"🔧 Backend LLM: {config.get('llm_backend', 'inconnu')}")
            print(f"🎯 Backend actuel: {config.get('current_backend', 'inconnu')}")
            print(f"🔑 Clé OpenAI: {'✅ Présente' if config.get('has_openai_key') else '❌ Absente'}")
            print(f"🔑 Clé HuggingFace: {'✅ Présente' if config.get('has_hf_key') else '❌ Absente'}")
        else:
            print(f"❌ Erreur lors de la récupération de la config: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_simple_call():
    """
    Teste un appel simple à l'API pour voir les logs
    """
    print("\n🧪 Test d'appel simple")
    print("=" * 30)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/recommend",
            json={"symptoms": "paludisme"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Réponse reçue (plante: {data.get('plant', 'inconnu')})")
            print(f"📄 Longueur explication: {len(data.get('explanation', ''))}")
            
            # Vérifier quelques champs structurés clés
            structured_count = 0
            test_fields = ["diagnostic", "symptomes", "presentation", "mode_action"]
            for field in test_fields:
                if field in data and data[field]:
                    structured_count += 1
                    print(f"✅ {field}: {len(str(data[field]))} caractères")
                else:
                    print(f"❌ {field}: Absent ou vide")
            
            print(f"\n📊 Score de structuration: {structured_count}/{len(test_fields)}")
            
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_current_module()
    test_simple_call()
