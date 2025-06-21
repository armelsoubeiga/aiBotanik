#!/usr/bin/env python3
import requests
import json

def test_frontend_integration():
    """Test l'intégration complète frontend/backend pour l'affichage des sections structurées"""
    
    print("🧪 Test d'intégration frontend/backend - Sections structurées")
    print("=" * 60)
    
    # Test 1: Vérifier la configuration actuelle
    config_response = requests.get('http://localhost:8000/admin/config/llm')
    config = config_response.json()
    print(f"✅ Backend actuel: {config['llm_backend']}")
    
    # Test 2: Tester une recommandation complète
    test_cases = [
        {
            "name": "Test paludisme (OpenAI)",
            "request": {"plant_name": "Artemisia", "symptoms": "fièvre et frissons du paludisme", "user_profile": "adulte"},
            "backend": "openai"
        },
        {
            "name": "Test diarrhée (Hugging Face fallback)",
            "request": {"plant_name": "Aloe", "symptoms": "diarrhée", "user_profile": "adulte"},
            "backend": "huggingface"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print("-" * 40)
        
        # Changer de backend si nécessaire
        current_config = requests.get('http://localhost:8000/admin/config/llm').json()
        if current_config['llm_backend'] != test_case['backend']:
            change_response = requests.put('http://localhost:8000/admin/config/llm', 
                                         json={'llm_backend': test_case['backend']})
            print(f"Backend changé pour: {test_case['backend']}")
        
        # Faire la recommandation
        response = requests.post('http://localhost:8000/recommend', json=test_case['request'])
        
        if response.status_code == 200:
            data = response.json()
            
            # Vérifier les champs structurés
            structured_fields = [
                'diagnostic', 'symptomes', 'presentation', 'mode_action', 
                'traitement_info', 'precautions_info', 'composants_info', 'resume_traitement'
            ]
            
            print("📊 Statut des champs structurés:")
            all_present = True
            total_chars = 0
            
            for field in structured_fields:
                value = data.get(field, "")
                if value and len(value.strip()) > 0:
                    char_count = len(value)
                    total_chars += char_count
                    print(f"  ✅ {field}: {char_count} caractères")
                else:
                    all_present = False
                    print(f"  ❌ {field}: MANQUANT ou vide")
            
            if all_present:
                print(f"🎉 Tous les champs structurés sont présents! ({total_chars} caractères au total)")
            else:
                print("⚠️  Certains champs structurés sont manquants")
            
            # Afficher un échantillon de contenu
            if data.get('diagnostic'):
                print(f"📝 Échantillon diagnostic: \"{data['diagnostic'][:100]}...\"")
            
            # Vérifier la cohérence frontend
            print("🖥️  Prêt pour l'affichage frontend:")
            print(f"  - Plante: {data.get('plant', 'N/A')}")
            print(f"  - Image: {'✅' if data.get('image_url') else '❌'}")
            print(f"  - Sections individuelles: {'✅' if all_present else '❌'}")
            print(f"  - Explication complète: {'✅' if data.get('explanation') else '❌'}")
            
        else:
            print(f"❌ Erreur API: {response.status_code} - {response.text}")
    
    # Remettre OpenAI par défaut
    requests.put('http://localhost:8000/admin/config/llm', json={'llm_backend': 'openai'})
    print(f"\n🔄 Backend remis sur OpenAI")
    
    print("\n" + "=" * 60)
    print("✅ Test d'intégration terminé!")
    print("🌐 Ouvrez http://localhost:3000 pour tester l'interface utilisateur")

if __name__ == "__main__":
    test_frontend_integration()
