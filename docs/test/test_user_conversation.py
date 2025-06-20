#!/usr/bin/env python3
"""
Script pour tester l'insertion directe d'une conversation avec un utilisateur spécifique
"""

import os
from supabase_client import supabase_admin
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

def test_direct_insertion():
    """
    Test d'insertion directe d'une conversation pour l'utilisateur armel.soubeiga@yahoo.fr
    """
    print("=== Test d'insertion directe de conversation ===")
    
    # Récupérer l'utilisateur par email
    user_email = "armel.soubeiga@yahoo.fr"
    
    try:
        # 1. Récupérer l'utilisateur
        print(f"1. Recherche de l'utilisateur avec email: {user_email}")
        user_response = supabase_admin.table("users").select("*").eq("email", user_email).execute()
        
        if not user_response.data or len(user_response.data) == 0:
            print(f"❌ Utilisateur non trouvé avec l'email: {user_email}")
            return
        
        user = user_response.data[0]
        user_id = user['id']
        print(f"✅ Utilisateur trouvé: {user['name']} (ID: {user_id})")
        
        # 2. Créer une conversation de test
        print(f"\n2. Création d'une conversation de test...")
        
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Messages de test simples
        test_messages = [
            {
                "content": "Bonjour, j'ai mal à la tête",
                "sender": "user",
                "timestamp": now
            },
            {
                "content": "Je recommande une infusion de menthe poivrée pour soulager votre mal de tête.",
                "sender": "bot",
                "timestamp": now,
                "recommendation": {
                    "plant": "Menthe poivrée",
                    "dosage": "1 cuillère à café de feuilles séchées",
                    "prep": "Infusion dans 250ml d'eau chaude pendant 10 minutes",
                    "image_url": "",
                    "explanation": "La menthe poivrée contient du menthol qui a des propriétés antispasmodiques",
                    "contre_indications": "Éviter en cas de reflux gastro-œsophagien",
                    "partie_utilisee": "Feuilles",
                    "composants": "Menthol, menthone",
                    "nom_local": "Menthe"
                }
            }
        ]
        
        conversation_data = {
            "id": conversation_id,
            "user_id": user_id,
            "title": "Test - Mal de tête",
            "type": "consultation",
            "summary": "Consultation pour mal de tête avec recommandation de menthe poivrée",
            "messages": test_messages,
            "messages_count": len(test_messages),
            "chat_mode": "consultation",
            "last_recommendation": test_messages[1]["recommendation"],
            "created_at": now,
            "updated_at": now
        }
        
        print(f"Données de la conversation:")
        print(f"  - ID: {conversation_id}")
        print(f"  - User ID: {user_id}")
        print(f"  - Titre: {conversation_data['title']}")
        print(f"  - Type: {conversation_data['type']}")
        print(f"  - Nombre de messages: {conversation_data['messages_count']}")
        
        # 3. Tenter l'insertion
        print(f"\n3. Tentative d'insertion...")
        result = supabase_admin.table("conversations").insert(conversation_data).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ Conversation créée avec succès!")
            created_conv = result.data[0]
            print(f"   ID de la conversation créée: {created_conv.get('id')}")
            print(f"   Titre: {created_conv.get('title')}")
            print(f"   Créée le: {created_conv.get('created_at')}")
            
            # 4. Vérifier que la conversation existe
            print(f"\n4. Vérification de la conversation créée...")
            check_response = supabase_admin.table("conversations").select("*").eq("id", conversation_id).execute()
            
            if check_response.data and len(check_response.data) > 0:
                conv = check_response.data[0]
                print(f"✅ Conversation vérifiée:")
                print(f"   - Titre: {conv['title']}")
                print(f"   - Messages: {len(conv['messages'])} message(s)")
                print(f"   - Type: {conv['type']}")
                print(f"   - Mode chat: {conv['chat_mode']}")
                
                # Afficher les messages
                print(f"\n   Messages:")
                for i, msg in enumerate(conv['messages']):
                    print(f"     {i+1}. [{msg['sender']}]: {msg['content'][:50]}...")
                    if msg.get('recommendation'):
                        print(f"        Recommandation: {msg['recommendation']['plant']}")
            
            return conversation_id
        else:
            print(f"❌ Échec de la création - aucune donnée retournée")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'insertion: {e}")
        print(f"Type d'erreur: {type(e)}")
        return None

def cleanup_test_conversation(conversation_id):
    """
    Nettoie la conversation de test
    """
    if not conversation_id:
        return
        
    try:
        print(f"\n=== Nettoyage de la conversation de test ===")
        supabase_admin.table("conversations").delete().eq("id", conversation_id).execute()
        print(f"✅ Conversation {conversation_id} supprimée")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

if __name__ == "__main__":
    print("=== Test d'insertion de conversation pour utilisateur spécifique ===\n")
    
    conversation_id = test_direct_insertion()
    
    if conversation_id:
        response = input("\nVoulez-vous supprimer la conversation de test ? (y/N): ")
        if response.lower() == 'y':
            cleanup_test_conversation(conversation_id)
        else:
            print(f"Conversation de test conservée avec l'ID: {conversation_id}")
    
    print("\nTest terminé.")
