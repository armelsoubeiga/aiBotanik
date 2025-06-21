"""
Test de l'endpoint de configuration admin
"""
import requests
import json

def test_admin_config():
    """Test de la configuration admin"""
    try:
        response = requests.get("http://localhost:8000/admin/config/llm", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Configuration récupérée:")
            print(f"  - Backend LLM: {data.get('llm_backend')}")
            print(f"  - Clé OpenAI: {'✅' if data.get('has_openai_key') else '❌'}")
            print(f"  - Clé HuggingFace: {'✅' if data.get('has_hf_key') else '❌'}")
            return True
        else:
            print(f"Erreur: {response.text}")
            return False
            
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    print("=== Test de la configuration admin ===")
    success = test_admin_config()
    print(f"Résultat: {'SUCCÈS' if success else 'ÉCHEC'}")
