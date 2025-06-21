#!/usr/bin/env python3
"""
Script pour forcer le basculement vers OpenAI et tester
"""

import os
import sys
from dotenv import load_dotenv

# Charger l'environnement
load_dotenv()

# Ajouter le répertoire backend au path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def force_switch_to_openai():
    """Force le basculement vers OpenAI"""
    print("=== Basculement forcé vers OpenAI ===")
    
    try:
        # Importer les modules nécessaires
        from app import save_config, verify_openai_key, get_llm_module
        
        # Vérifier que la clé OpenAI est valide
        openai_key = os.getenv("OPENAI_API_KEY")
        print(f"Clé OpenAI trouvée: {bool(openai_key)}")
        
        if openai_key:
            is_valid = verify_openai_key(openai_key)
            print(f"Clé OpenAI valide: {is_valid}")
            
            if is_valid:
                # Sauvegarder la configuration
                result = save_config({"llm_backend": "openai"})
                print(f"Configuration sauvegardée: {result}")
                
                # Recharger le module
                module = get_llm_module()
                print(f"Module chargé: {module.__name__}")
                
                # Tester une génération simple
                if hasattr(module, 'generate_chat_response'):
                    print("Test de génération de chat...")
                    response = module.generate_chat_response("Bonjour")
                    print(f"Réponse reçue (longueur: {len(response)})")
                    print(f"Début: {response[:100]}...")
                    print("✅ Chat OpenAI fonctionne")
                else:
                    print("❌ Fonction generate_chat_response non trouvée")
                
                return True
            else:
                print("❌ Clé OpenAI invalide")
                return False
        else:
            print("❌ Aucune clé OpenAI trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = force_switch_to_openai()
    if success:
        print("\n🎉 Basculement vers OpenAI réussi !")
    else:
        print("\n❌ Échec du basculement vers OpenAI")
