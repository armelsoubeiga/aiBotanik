#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table conversations et diagnostiquer les problèmes de contraintes
"""

import os
from supabase_client import supabase_admin
from dotenv import load_dotenv
import uuid

# Charger les variables d'environnement
load_dotenv()

def check_table_structure():
    """
    Vérifie la structure de la table conversations
    """
    print("=== Vérification de la structure de la table conversations ===")
    
    try:
        # Essayer d'insérer un enregistrement de test pour identifier le problème
        test_user_id = "c504f08f-b443-4ebc-bf8f-68da56fedcf4"
        
        # Vérifier d'abord que l'utilisateur existe
        user_check = supabase_admin.table("users").select("id").eq("id", test_user_id).execute()
        print(f"Utilisateur trouvé: {len(user_check.data) > 0}")
        
        if len(user_check.data) > 0:
            print(f"Utilisateur: {user_check.data[0]}")
        
        # Essayer de créer une conversation de test
        test_conversation = {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "title": "Test conversation",
            "type": "discussion",
            "summary": "Test",
            "messages": [],
            "messages_count": 0,
            "chat_mode": "discussion",
            "last_recommendation": None
        }
        
        print(f"\nTentative d'insertion d'une conversation de test...")
        print(f"Données: {test_conversation}")
        
        result = supabase_admin.table("conversations").insert(test_conversation).execute()
        print(f"✅ Conversation de test créée avec succès: {result.data}")
        
        # Supprimer la conversation de test
        supabase_admin.table("conversations").delete().eq("id", test_conversation["id"]).execute()
        print("✅ Conversation de test supprimée")
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'insertion: {e}")
        print(f"Type d'erreur: {type(e)}")
        
        # Analyser l'erreur en détail
        error_str = str(e)
        if "foreign key constraint" in error_str:
            print("🔍 Problème de contrainte de clé étrangère détecté")
            print("Vérification des contraintes...")
            
def test_conversation_creation():
    """
    Test spécifique de création de conversation avec l'utilisateur problématique
    """
    print("=== Test de création de conversation ===")
    
    user_id = "c504f08f-b443-4ebc-bf8f-68da56fedcf4"
    
    try:
        # Données minimales pour test
        conversation_data = {
            "user_id": user_id,
            "title": "Test minimal",
            "type": "discussion",
            "messages": [],
            "messages_count": 0,
            "chat_mode": "discussion"
        }
        
        print(f"Tentative avec données minimales: {conversation_data}")
        
        result = supabase_admin.table("conversations").insert(conversation_data).execute()
        print(f"✅ Succès: {result.data}")
        
        # Nettoyer
        if result.data and len(result.data) > 0:
            conv_id = result.data[0].get('id')
            if conv_id:
                supabase_admin.table("conversations").delete().eq("id", conv_id).execute()
                print("✅ Conversation de test nettoyée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def check_conversations_table():
    """
    Vérifie le contenu actuel de la table conversations
    """
    print("=== Contenu de la table conversations ===")
    
    try:
        response = supabase_admin.table("conversations").select("*").execute()
        conversations = response.data
        
        print(f"Nombre de conversations: {len(conversations)}")
        
        for conv in conversations:
            print(f"ID: {conv.get('id')}, User ID: {conv.get('user_id')}, Titre: {conv.get('title')}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des conversations: {e}")

if __name__ == "__main__":
    print("=== Diagnostic de la table conversations ===\n")
    
    while True:
        print("\nOptions disponibles:")
        print("1. Vérifier la structure de la table")
        print("2. Tester la création de conversation")
        print("3. Vérifier le contenu de la table conversations")
        print("4. Quitter")
        
        choice = input("\nChoisissez une option (1-4): ").strip()
        
        if choice == "1":
            check_table_structure()
        elif choice == "2":
            test_conversation_creation()
        elif choice == "3":
            check_conversations_table()
        elif choice == "4":
            print("Au revoir !")
            break
        else:
            print("Option invalide. Veuillez choisir entre 1 et 4.")
