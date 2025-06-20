#!/usr/bin/env python3
"""
Script pour corriger les problèmes de données utilisateur dans Supabase
Ce script permet de nettoyer les tokens/sessions invalides et de vérifier la cohérence des données
"""

import os
from supabase_client import supabase_admin
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def check_user_consistency():
    """
    Vérifie la cohérence entre les tokens JWT et les utilisateurs en base
    """
    print("=== Vérification de la cohérence des données utilisateur ===")
    
    try:
        # Récupérer tous les utilisateurs
        users_response = supabase_admin.table("users").select("id, email, created_at").execute()
        users = users_response.data
        
        print(f"Nombre d'utilisateurs trouvés: {len(users)}")
        
        for user in users:
            print(f"- ID: {user['id']}, Email: {user['email']}, Créé: {user['created_at']}")
        
        # Récupérer les conversations avec des user_id qui n'existent pas
        conversations_response = supabase_admin.table("conversations").select("id, user_id, title").execute()
        conversations = conversations_response.data
        
        print(f"\nNombre de conversations trouvées: {len(conversations)}")
        
        user_ids = {user['id'] for user in users}
        orphaned_conversations = []
        
        for conv in conversations:
            if conv['user_id'] not in user_ids:
                orphaned_conversations.append(conv)
                print(f"- Conversation orpheline: {conv['id']}, User ID: {conv['user_id']}, Titre: {conv['title']}")
        
        if orphaned_conversations:
            print(f"\n⚠️  {len(orphaned_conversations)} conversation(s) orpheline(s) détectée(s)")
            response = input("Voulez-vous supprimer ces conversations orphelines ? (y/N): ")
            if response.lower() == 'y':
                for conv in orphaned_conversations:
                    supabase_admin.table("conversations").delete().eq("id", conv['id']).execute()
                    print(f"✅ Conversation {conv['id']} supprimée")
        else:
            print("✅ Aucune conversation orpheline détectée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def list_users():
    """
    Liste tous les utilisateurs dans la base de données
    """
    print("=== Liste des utilisateurs ===")
    
    try:
        response = supabase_admin.table("users").select("*").execute()
        users = response.data
        
        if not users:
            print("Aucun utilisateur trouvé dans la base de données")
            return
            
        for user in users:
            print(f"""
ID: {user['id']}
Email: {user['email']}
Nom: {user.get('name', 'Non défini')}
Créé le: {user['created_at']}
Modifié le: {user['updated_at']}
Désactivé: {user.get('is_disabled', False)}
---""")
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")

def cleanup_sessions():
    """
    Nettoie les sessions expirées
    """
    print("=== Nettoyage des sessions expirées ===")
    
    try:
        # Supprimer les sessions expirées
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        response = supabase_admin.table("sessions").delete().lt("expires_at", now).execute()
        print(f"✅ Sessions expirées nettoyées")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage des sessions: {e}")

if __name__ == "__main__":
    print("=== Script de maintenance des données utilisateur ===\n")
    
    while True:
        print("\nOptions disponibles:")
        print("1. Vérifier la cohérence des données")
        print("2. Lister tous les utilisateurs")
        print("3. Nettoyer les sessions expirées")
        print("4. Quitter")
        
        choice = input("\nChoisissez une option (1-4): ").strip()
        
        if choice == "1":
            check_user_consistency()
        elif choice == "2":
            list_users()
        elif choice == "3":
            cleanup_sessions()
        elif choice == "4":
            print("Au revoir !")
            break
        else:
            print("Option invalide. Veuillez choisir entre 1 et 4.")
