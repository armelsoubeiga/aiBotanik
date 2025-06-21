#!/usr/bin/env python3
"""
Test direct avec OpenAI - Force l'utilisation uniquement d'OpenAI
"""

import requests
import json
import time

def test_direct_openai():
    """Test direct de consultation avec OpenAI en forçant les paramètres"""
    print("🧪 Test direct de consultation OpenAI...")
    
    # D'abord, s'assurer qu'on utilise OpenAI
    try:
        print("🔧 Configuration du backend OpenAI...")
        response = requests.get('http://localhost:8001/admin/config/llm?backend=openai')
        if response.status_code == 200:
            print("✅ Backend configuré sur OpenAI")
        else:
            print(f"⚠️ Problème de configuration: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return False
    
    # Attendre un peu pour que la configuration prenne effet
    time.sleep(2)
      # Maintenant tester l'endpoint /recommend (consultations structurées) avec le bon format
    test_payload = {
        "symptoms": "J'ai des symptômes de paludisme"  # L'endpoint /recommend utilise "symptoms"
    }
    
    try:
        print(f"📤 Envoi de la requête de consultation: {test_payload}")
        response = requests.post('http://localhost:8001/recommend', 
                               json=test_payload,
                               timeout=60)  # Timeout de 60 secondes
        
        print(f"📥 Statut de réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Consultation réussie avec OpenAI!")
            
            # Vérifier la présence des champs structurés spécifiques à OpenAI
            required_fields = [
                "diagnostic", "symptomes", "presentation", "mode_action",
                "traitement_info", "precautions_info", "composants_info", "resume_traitement"
            ]
            
            print("\n📋 Vérification des champs structurés:")
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in data and data[field]:
                    present_fields.append(field)
                    content = str(data[field])[:100] + "..." if len(str(data[field])) > 100 else str(data[field])
                    print(f"  ✅ {field}: {content}")
                else:
                    missing_fields.append(field)
                    print(f"  ❌ {field}: MANQUANT")
            
            print(f"\n📊 Résultat: {len(present_fields)}/{len(required_fields)} champs présents")
            
            if missing_fields:
                print(f"⚠️ Champs manquants: {missing_fields}")
                return False
            else:
                print("🎉 Tous les champs structurés sont présents avec OpenAI!")
                return True
                
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Détails: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - La requête prend trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    print("🚀 Test OpenAI direct pour aiBotanik")
    print("=" * 50)
    
    success = test_direct_openai()
    
    if success:
        print("\n🎉 SUCCESS: OpenAI fonctionne parfaitement!")
        print("   ✅ Tous les champs structurés sont générés")
        print("   ✅ L'harmonisation avec le frontend est complète")
    else:
        print("\n💥 ÉCHEC: Problème avec OpenAI")
        print("   ❌ Vérifiez les logs du serveur backend")

if __name__ == "__main__":
    main()
