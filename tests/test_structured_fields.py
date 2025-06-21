#!/usr/bin/env python3
"""
Test pour vérifier que les champs structurés sont bien retournés par l'API de consultation
et que l'affichage sera harmonisé entre tous les backends (OpenAI, Hugging Face, fallback).
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_structured_fields():
    """
    Teste que les endpoints de consultation retournent tous les champs structurés nécessaires
    pour un affichage harmonisé dans le frontend.
    """
    print("🧪 Test des champs structurés pour l'harmonisation de l'affichage")
    print("=" * 70)
    
    # Champs structurés attendus dans la réponse
    expected_structured_fields = [
        "diagnostic",
        "symptomes", 
        "presentation",
        "mode_action",
        "traitement_info",
        "precautions_info",
        "composants_info",
        "resume_traitement"
    ]
    
    # Champs de base attendus
    expected_base_fields = [
        "plant",
        "dosage",
        "prep", 
        "image_url",
        "explanation",
        "contre_indications",
        "partie_utilisee",
        "composants",
        "nom_local"
    ]
    
    # Test avec différents symptômes
    test_cases = [
        "paludisme",
        "fièvre et frissons",
        "maux de tête",
        "diarrhée"
    ]
    
    for i, symptoms in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: Symptômes = '{symptoms}'")
        print("-" * 50)
        
        try:
            # Faire la requête à l'API
            response = requests.post(
                f"{API_BASE_URL}/recommend",
                json={"symptoms": symptoms},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Réponse API reçue (statut: {response.status_code})")
                print(f"🌿 Plante recommandée: {data.get('plant', 'Non spécifiée')}")
                
                # Vérifier les champs de base
                missing_base_fields = []
                for field in expected_base_fields:
                    if field not in data:
                        missing_base_fields.append(field)
                
                if missing_base_fields:
                    print(f"⚠️  Champs de base manquants: {missing_base_fields}")
                else:
                    print("✅ Tous les champs de base sont présents")
                
                # Vérifier les champs structurés (nouveaux)
                missing_structured_fields = []
                present_structured_fields = []
                
                for field in expected_structured_fields:
                    if field not in data:
                        missing_structured_fields.append(field)
                    else:
                        present_structured_fields.append(field)
                        # Vérifier que le contenu n'est pas vide
                        if data[field] and data[field].strip():
                            print(f"✅ {field}: Contenu présent ({len(data[field])} caractères)")
                        else:
                            print(f"⚠️  {field}: Champ présent mais vide")
                
                if missing_structured_fields:
                    print(f"❌ Champs structurés manquants: {missing_structured_fields}")
                    print("💡 Ces champs sont nécessaires pour l'affichage harmonisé!")
                else:
                    print("🎉 Tous les champs structurés sont présents!")
                
                # Vérifier que l'explication complète existe aussi
                if data.get('explanation'):
                    print(f"✅ Explication complète: {len(data['explanation'])} caractères")
                else:
                    print("⚠️  Explication complète manquante")
                
                # Afficher un extrait du diagnostic pour vérifier le contenu
                if data.get('diagnostic'):
                    diagnostic_preview = data['diagnostic'][:100] + "..." if len(data['diagnostic']) > 100 else data['diagnostic']
                    print(f"📄 Extrait du diagnostic: {diagnostic_preview}")
                
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"Réponse: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 Résumé du test:")
    print("   - Si tous les champs structurés sont présents, l'affichage sera harmonisé")
    print("   - Le frontend peut utiliser les champs structurés en priorité")
    print("   - L'explication complète reste disponible comme fallback")
    print("=" * 70)

if __name__ == "__main__":
    test_structured_fields()
