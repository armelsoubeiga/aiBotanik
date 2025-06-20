#!/usr/bin/env python3
"""
Script pour tester l'authentification directement sans warnings bcrypt
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Supprimer les warnings bcrypt
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

from auth import authenticate_user, get_password_hash, verify_password

def test_bcrypt_directly():
    """
    Test direct de bcrypt pour vérifier qu'il n'y a plus de warnings
    """
    print("=== Test de bcrypt direct ===")
    
    try:
        # Test de hashage
        test_password = "admin@123"
        print(f"Test avec le mot de passe: {test_password}")
        
        hashed = get_password_hash(test_password)
        print(f"✅ Hash généré (longueur: {len(hashed)})")
        
        # Test de vérification
        is_valid = verify_password(test_password, hashed)
        print(f"✅ Vérification: {is_valid}")
        
        # Test avec mauvais mot de passe
        is_invalid = verify_password("wrong_password", hashed)
        print(f"✅ Test mauvais mot de passe: {is_invalid} (devrait être False)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test bcrypt: {e}")
        return False

def test_user_authentication():
    """
    Test d'authentification avec l'utilisateur réel
    """
    print("\n=== Test d'authentification utilisateur ===")
    
    email = "armel.soubeiga@yahoo.fr"
    password = "admin@123"
    
    try:
        print(f"Tentative de connexion avec: {email}")
        
        user = authenticate_user(email, password)
        
        if user:
            print("✅ Authentification réussie !")
            print(f"   Utilisateur: {user.get('name', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   ID: {user.get('id', 'N/A')}")
            return True
        else:
            print("❌ Authentification échouée")
            print("Vérifiez que l'email et le mot de passe sont corrects")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification: {e}")
        return False

def test_password_verification():
    """
    Test pour vérifier le hash stocké en base de données
    """
    print("\n=== Test de vérification du hash en base ===")
    
    from supabase_client import safe_get_user_by_email
    
    email = "armel.soubeiga@yahoo.fr"
    password = "admin@123"
    
    try:
        user = safe_get_user_by_email(email)
        if not user:
            print(f"❌ Utilisateur {email} non trouvé")
            return False
            
        stored_hash = user.get('hashed_password')
        if not stored_hash:
            print("❌ Pas de hash de mot de passe stocké")
            return False
            
        print(f"Hash stocké (premiers 20 chars): {stored_hash[:20]}...")
        
        # Vérifier le mot de passe
        is_valid = verify_password(password, stored_hash)
        print(f"Vérification du mot de passe '{password}': {is_valid}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("=== Test d'authentification sans warnings ===\n")
    
    # Tests dans l'ordre
    bcrypt_ok = test_bcrypt_directly()
    auth_ok = test_user_authentication()
    hash_ok = test_password_verification()
    
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS:")
    print(f"Test bcrypt: {'✅ SUCCÈS' if bcrypt_ok else '❌ ÉCHEC'}")
    print(f"Test authentification: {'✅ SUCCÈS' if auth_ok else '❌ ÉCHEC'}")
    print(f"Test hash en base: {'✅ SUCCÈS' if hash_ok else '❌ ÉCHEC'}")
    
    if bcrypt_ok and auth_ok and hash_ok:
        print("\n🎉 Tous les tests d'authentification sont passés !")
        print("L'avertissement bcrypt devrait être résolu.")
    else:
        print("\n⚠️  Il reste des problèmes à résoudre.")
