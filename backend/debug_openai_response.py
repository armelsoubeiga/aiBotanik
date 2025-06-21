#!/usr/bin/env python3
"""
Test de debug pour voir la réponse complète d'OpenAI
"""

import requests
import json

def debug_openai_response():
    """Afficher la réponse complète d'OpenAI pour débugger l'extraction"""
    print("🔍 Debug de la réponse OpenAI complète...")
    
    test_payload = {
        "symptoms": "paludisme"
    }
    
    try:
        response = requests.post('http://localhost:8000/recommend', 
                               json=test_payload,
                               timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📋 Réponse complète reçue:")
            print("=" * 80)
            
            # Afficher l'explication complète générée par OpenAI
            explanation = data.get('explanation', 'Pas d\'explication')
            print("🤖 EXPLICATION GÉNÉRÉE PAR OPENAI:")
            print("-" * 50)
            print(explanation)
            print("-" * 50)
            
            print("\n📊 CHAMPS STRUCTURÉS EXTRAITS:")
            print("-" * 50)
            
            structured_fields = [
                "diagnostic", "symptomes", "presentation", "mode_action",
                "traitement_info", "precautions_info", "composants_info", "resume_traitement"
            ]
            
            for field in structured_fields:
                content = data.get(field, 'ABSENT')
                status = "✅" if content and content != 'ABSENT' else "❌"
                print(f"{status} {field}:")
                if content and content != 'ABSENT':
                    # Afficher les premiers 150 caractères
                    preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"    {preview}")
                else:
                    print("    [MANQUANT]")
                print()
            
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Détails: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    debug_openai_response()
