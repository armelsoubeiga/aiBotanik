#!/usr/bin/env python3
"""
Script pour diagnostiquer le problème de contrainte de clé étrangère en détail
"""

import os
from supabase_client import supabase_admin
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def detailed_user_check():
    """
    Vérification détaillée de l'utilisateur
    """
    print("=== Vérification détaillée de l'utilisateur ===")
    
    user_id = "c504f08f-b443-4ebc-bf8f-68da56fedcf4"
    
    try:
        # Méthode 1: Requête directe
        print("1. Requête directe sur la table users:")
        response1 = supabase_admin.table("users").select("*").eq("id", user_id).execute()
        print(f"   Résultat: {response1.data}")
        
        # Méthode 2: Requête avec différents formats
        print("\n2. Vérification du format UUID:")
        print(f"   UUID original: {user_id}")
        print(f"   Type: {type(user_id)}")
        print(f"   Longueur: {len(user_id)}")
        
        # Méthode 3: Lister tous les IDs pour comparaison
        print("\n3. Tous les IDs utilisateur:")
        all_users = supabase_admin.table("users").select("id, email").execute()
        for user in all_users.data:
            print(f"   ID: {user['id']} (type: {type(user['id'])}, égal: {user['id'] == user_id})")
            print(f"   Email: {user['email']}")
            print(f"   Comparaison byte-by-byte: {user['id'].encode() == user_id.encode()}")
            print("   ---")
        
        # Méthode 4: Essayer avec un autre utilisateur existant
        print("\n4. Test avec un autre utilisateur:")
        if all_users.data and len(all_users.data) > 0:
            other_user = all_users.data[0]
            test_data = {
                "user_id": other_user['id'],
                "title": "Test avec autre utilisateur",
                "type": "discussion",
                "messages": [],
                "messages_count": 0,
                "chat_mode": "discussion"
            }
            
            try:
                result = supabase_admin.table("conversations").insert(test_data).execute()
                print(f"   ✅ Succès avec l'utilisateur {other_user['email']}: {result.data}")
                
                # Nettoyer
                if result.data and len(result.data) > 0:
                    conv_id = result.data[0].get('id')
                    if conv_id:
                        supabase_admin.table("conversations").delete().eq("id", conv_id).execute()
                        print("   ✅ Nettoyage effectué")
                        
            except Exception as e:
                print(f"   ❌ Échec même avec autre utilisateur: {e}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification détaillée: {e}")

def check_foreign_key_constraint():
    """
    Vérifier les contraintes de clé étrangère via des requêtes SQL si possible
    """
    print("=== Vérification des contraintes de clé étrangère ===")
    
    try:
        # Essayer d'obtenir des informations sur les contraintes
        # Note: Cela peut ne pas fonctionner avec tous les clients Supabase
        print("Tentative de récupération des informations de contrainte...")
        
        # Essayer une approche différente : utiliser RPC si disponible
        # Ou essayer de contourner le problème en utilisant le client standard
        from supabase_client import supabase
        
        # Test avec le client normal vs admin
        user_id = "c504f08f-b443-4ebc-bf8f-68da56fedcf4"
        
        print("Test avec client standard:")
        try:
            response = supabase.table("users").select("id").eq("id", user_id).execute()
            print(f"   Client standard - utilisateur trouvé: {len(response.data) > 0}")
        except Exception as e:
            print(f"   Client standard - erreur: {e}")
        
        print("Test avec client admin:")
        try:
            response = supabase_admin.table("users").select("id").eq("id", user_id).execute()
            print(f"   Client admin - utilisateur trouvé: {len(response.data) > 0}")
        except Exception as e:
            print(f"   Client admin - erreur: {e}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des contraintes: {e}")

if __name__ == "__main__":
    print("=== Diagnostic avancé du problème de contrainte ===\n")
    
    detailed_user_check()
    print("\n" + "="*50 + "\n")
    check_foreign_key_constraint()
