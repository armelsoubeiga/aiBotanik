#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test complet pour valider le fonctionnement des deux modes aiBotanik
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_discussion_mode():
    """Test du mode Discussion (chat)"""
    print("🔥 Test du mode Discussion...")
    
    url = f"{BASE_URL}/chat"
    data = {"message": "Bonjour, pouvez-vous me parler de la phytothérapie africaine?"}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Statut: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Réponse reçue: {result.get('response', 'Aucune réponse')[:100]}...")
            print(f"Backend utilisé: {result.get('backend', 'Non spécifié')}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_consultation_mode():
    """Test du mode Consultation (recommend)"""
    print("🔥 Test du mode Consultation...")
    
    url = f"{BASE_URL}/recommend"
    data = {"symptoms": "Je pense avoir le paludisme avec de la fièvre et des frissons"}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Statut: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Vérifier les champs requis
            required_fields = [
                "plant", "dosage", "prep", "image_url", "explanation", 
                "contre_indications", "partie_utilisee", "composants", "nom_local"
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                print(f"❌ Champs manquants: {missing_fields}")
                return False
            
            print(f"✅ Plante recommandée: {result.get('plant', 'Non spécifié')}")
            print(f"✅ Explanation présente: {len(result.get('explanation', ''))} caractères")
            
            # Vérifier que l'explication contient les sections attendues
            explanation = result.get('explanation', '')
            required_sections = [
                "Diagnostic possible", "Symptômes associés", "Présentation de", 
                "Mode d'action", "Informations de traitement", 
                "Précautions et contre-indications", "Composants actifs", "Résumé de traitement"
            ]
            
            missing_sections = [section for section in required_sections if section not in explanation]
            if missing_sections:
                print(f"⚠️ Sections manquantes dans l'explication: {missing_sections}")
            else:
                print("✅ Toutes les sections structurées sont présentes")
            
            # Vérifier que les champs n'affichent pas "NULL"
            for field_name, field_value in result.items():
                if isinstance(field_value, str) and "NULL" in field_value.upper():
                    print(f"⚠️ Le champ '{field_name}' contient encore NULL: {field_value}")
            
            return True
            
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_llm_configuration():
    """Test de la configuration LLM"""
    print("🔥 Test de la configuration LLM...")
    
    url = f"{BASE_URL}/admin/config/llm"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Statut: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backend actuel: {result.get('current_backend', 'Non spécifié')}")
            print(f"✅ Clé OpenAI configurée: {result.get('has_openai_key', False)}")
            print(f"✅ Clé HuggingFace configurée: {result.get('has_hf_key', False)}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests aiBotanik")
    print("=" * 50)
    
    # Test de la configuration
    config_ok = test_llm_configuration()
    print("-" * 50)
    
    # Test du mode Discussion
    discussion_ok = test_discussion_mode()
    print("-" * 50)
    
    # Test du mode Consultation
    consultation_ok = test_consultation_mode()
    print("-" * 50)
    
    # Résumé
    print("📊 RÉSUMÉ DES TESTS:")
    print(f"Configuration LLM: {'✅ OK' if config_ok else '❌ ÉCHEC'}")
    print(f"Mode Discussion: {'✅ OK' if discussion_ok else '❌ ÉCHEC'}")
    print(f"Mode Consultation: {'✅ OK' if consultation_ok else '❌ ÉCHEC'}")
    
    if config_ok and discussion_ok and consultation_ok:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! Le système fonctionne correctement.")
        return True
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez les détails ci-dessus.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
