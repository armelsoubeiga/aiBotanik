import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_KEY:
    raise ValueError("Les variables d'environnement SUPABASE_URL, SUPABASE_ANON_KEY et SUPABASE_KEY doivent être définies")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_supabase_schema():
    """Vérifie et initialise le schéma Supabase si nécessaire"""
    pass

def safe_get_user_by_email(email):
    """Récupère un utilisateur par email de manière sécurisée"""
    try:
        response = supabase_admin.table("users").select("*").eq("email", email).execute()
        users = response.data
        return users[0] if users and len(users) > 0 else None
    except Exception:
        return None

def safe_get_user_by_id(user_id):
    """Récupère un utilisateur par ID de manière sécurisée"""
    try:
        response = supabase_admin.table("users").select("*").eq("id", user_id).execute()
        users = response.data
        return users[0] if users and len(users) > 0 else None
    except Exception:
        return None
