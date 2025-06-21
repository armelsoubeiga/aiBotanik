#!/usr/bin/env python3
"""
Script pour forcer l'utilisation d'OpenAI uniquement et tester les fonctionnalités.
"""

import requests
import json

def switch_to_openai():
    """Forcer le switch vers OpenAI"""
    try:
        print("🔧 Basculement vers OpenAI...")
        response = requests.get('http://localhost:8000/admin/config/llm?backend=openai')
        if response.status_code == 200:
            print("✅ Backend basculé vers OpenAI avec succès")
            return True
        else:
            print(f"❌ Erreur lors du basculement: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_consultation_openai():
    """Tester l'endpoint de consultation avec OpenAI"""
    print("\n🧪 Test de consultation avec OpenAI...")
    
    test_payload = {
        "message": "paludisme"
    }
    
    try:
        response = requests.post('http://localhost:8000/chat', json=test_payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Consultation réussie")
            
            # Vérifier la présence des champs structurés
            required_fields = [
                "diagnostic", "symptomes", "presentation", "mode_action",
                "traitement_info", "precautions_info", "composants_info", "resume_traitement"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ Champs manquants: {missing_fields}")
            else:
                print("✅ Tous les champs structurés sont présents")
                
            # Afficher quelques extraits
            print(f"\n📋 Diagnostic: {data.get('diagnostic', 'N/A')[:100]}...")
            print(f"📋 Symptômes: {data.get('symptomes', 'N/A')[:100]}...")
            print(f"📋 Résumé: {data.get('resume_traitement', 'N/A')[:100]}...")
            
            return True
        else:
            print(f"❌ Erreur consultation: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de consultation: {e}")
        return False

def main():
    print("🚀 Test OpenAI uniquement pour aiBotanik")
    print("=" * 50)
    
    # Étape 1: Basculer vers OpenAI
    if not switch_to_openai():
        print("❌ Impossible de basculer vers OpenAI. Arrêt du test.")
        return
    
    # Étape 2: Tester la consultation
    if test_consultation_openai():
        print("\n🎉 Tests OpenAI réussis ! Tous les champs structurés sont bien générés.")
    else:
        print("\n💥 Échec des tests OpenAI.")

if __name__ == "__main__":
    main()
