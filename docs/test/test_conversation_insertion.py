#!/usr/bin/env python3
"""
Script pour tester l'insertion d'une conversation après la correction de la table
"""

import os
from supabase_client import supabase_admin
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

def test_conversation_insertion():
    """
    Test d'insertion d'une conversation avec l'utilisateur armel.soubeiga@yahoo.fr
    """
    print("=== Test d'insertion de conversation ===")
    
    # Récupérer l'utilisateur par email
    user_email = "armel.soubeiga@yahoo.fr"
    
    try:
        # 1. Vérifier que l'utilisateur existe
        print(f"1. Recherche de l'utilisateur avec l'email: {user_email}")
        user_response = supabase_admin.table("users").select("*").eq("email", user_email).execute()
        
        if not user_response.data or len(user_response.data) == 0:
            print(f"❌ Utilisateur avec l'email {user_email} non trouvé")
            return False
        
        user = user_response.data[0]
        user_id = user['id']
        print(f"✅ Utilisateur trouvé: {user['name']} (ID: {user_id})")
        
        # 2. Créer une conversation de test
        print("\n2. Création d'une conversation de test...")
        
        conversation_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Test de conversation après correction",
            "summary": "Ceci est un test pour vérifier que l'insertion fonctionne correctement",
            "type": "discussion",
            "messages": [
                {
                    "id": "msg1",
                    "content": "Bonjour, je teste l'insertion",
                    "sender": "user",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "id": "msg2", 
                    "content": "Bonjour ! Je confirme que l'insertion fonctionne.",
                    "sender": "bot",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "messages_count": 2,
            "chat_mode": "discussion",
            "last_recommendation": None
        }
        
        print(f"Données de la conversation: {conversation_data['title']}")
        print(f"Nombre de messages: {conversation_data['messages_count']}")
        
        # 3. Tenter l'insertion
        print("\n3. Insertion dans la base de données...")
        result = supabase_admin.table("conversations").insert(conversation_data).execute()
        
        if result.data and len(result.data) > 0:
            inserted_conversation = result.data[0]
            print(f"✅ Conversation créée avec succès !")
            print(f"   ID: {inserted_conversation['id']}")
            print(f"   Titre: {inserted_conversation['title']}")
            print(f"   Utilisateur: {inserted_conversation['user_id']}")
            print(f"   Date de création: {inserted_conversation['created_at']}")
            
            # 4. Vérifier la lecture
            print("\n4. Vérification de la lecture...")
            read_result = supabase_admin.table("conversations").select("*").eq("id", inserted_conversation['id']).execute()
            
            if read_result.data and len(read_result.data) > 0:
                read_conversation = read_result.data[0]
                print(f"✅ Conversation lue avec succès")
                print(f"   Messages stockés: {len(read_conversation['messages'])}")
                print(f"   Premier message: {read_conversation['messages'][0]['content']}")
                
                # 5. Nettoyer (supprimer la conversation de test)
                print("\n5. Nettoyage...")
                delete_result = supabase_admin.table("conversations").delete().eq("id", inserted_conversation['id']).execute()
                print("✅ Conversation de test supprimée")
                
                return True
            else:
                print("❌ Erreur lors de la lecture de la conversation")
                return False
        else:
            print("❌ Aucune donnée retournée après l'insertion")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'insertion: {e}")
        print(f"Type d'erreur: {type(e)}")
        return False

def test_multiple_users():
    """
    Test d'insertion avec plusieurs utilisateurs pour vérifier la robustesse
    """
    print("\n=== Test avec plusieurs utilisateurs ===")
    
    try:
        # Récupérer tous les utilisateurs
        users_response = supabase_admin.table("users").select("id, email, name").execute()
        users = users_response.data
        
        print(f"Nombre d'utilisateurs trouvés: {len(users)}")
        
        success_count = 0
        for user in users[:2]:  # Tester avec les 2 premiers utilisateurs
            print(f"\nTest avec {user['email']}...")
            
            conversation_data = {
                "user_id": user['id'],
                "title": f"Test pour {user['name'] or user['email']}",
                "summary": "Test automatique",
                "type": "discussion",
                "messages": [
                    {
                        "content": "Test message",
                        "sender": "user",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "messages_count": 1,
                "chat_mode": "discussion"
            }
            
            try:
                result = supabase_admin.table("conversations").insert(conversation_data).execute()
                if result.data and len(result.data) > 0:
                    print(f"✅ Succès pour {user['email']}")
                    success_count += 1
                    
                    # Nettoyer
                    conv_id = result.data[0]['id']
                    supabase_admin.table("conversations").delete().eq("id", conv_id).execute()
                else:
                    print(f"❌ Échec pour {user['email']}")
            except Exception as e:
                print(f"❌ Erreur pour {user['email']}: {e}")
        
        print(f"\n📊 Résultat: {success_count}/{min(len(users), 2)} insertions réussies")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur lors du test multiple: {e}")
        return False

if __name__ == "__main__":
    print("=== Test d'insertion de conversations après correction ===\n")
    
    # Test principal
    main_success = test_conversation_insertion()
    
    # Test avec plusieurs utilisateurs
    multi_success = test_multiple_users()
    
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS:")
    print(f"Test principal: {'✅ SUCCÈS' if main_success else '❌ ÉCHEC'}")
    print(f"Test multiple: {'✅ SUCCÈS' if multi_success else '❌ ÉCHEC'}")
    
    if main_success and multi_success:
        print("\n🎉 Tous les tests sont passés ! La table conversations fonctionne correctement.")
        print("Vous pouvez maintenant utiliser le bouton '+' pour créer de nouvelles conversations.")
    else:
        print("\n⚠️  Il reste des problèmes à résoudre.")
