#!/usr/bin/env python3
"""
Test direct pour voir exactement ce que retourne l'API
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def debug_api_response():
    """
    Teste directement l'API pour voir la structure exacte de la réponse
    """
    print("🔍 Debug direct de la réponse API")
    print("=" * 50)
    
    try:
        # Faire la requête à l'API
        response = requests.post(
            f"{API_BASE_URL}/recommend",
            json={"symptoms": "paludisme"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Réponse API reçue (statut: {response.status_code})")
            print(f"🌿 Plante recommandée: {data.get('plant', 'Non spécifiée')}")
            print()
            print("📋 Structure complète de la réponse:")
            print("-" * 40)
            
            for key, value in data.items():
                if isinstance(value, str):
                    if len(value) > 100:
                        preview = value[:100] + "..."
                        print(f"  {key}: {preview} (longueur: {len(value)})")
                    else:
                        print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
            
            print()
            print("🎯 Champs recherchés:")
            structured_fields = [
                "diagnostic", "symptomes", "presentation", "mode_action",
                "traitement_info", "precautions_info", "composants_info", "resume_traitement"
            ]
            
            for field in structured_fields:
                if field in data:
                    if data[field]:
                        print(f"  ✅ {field}: Présent ({len(str(data[field]))} caractères)")
                    else:
                        print(f"  ⚠️  {field}: Présent mais vide")
                else:
                    print(f"  ❌ {field}: Absent")
            
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    debug_api_response()
