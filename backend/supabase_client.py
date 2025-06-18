import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer les variables d'environnement Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_ANON_KEY doivent être définies")

# Créer le client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def init_supabase_schema():
    """
    Vérifie et initialise le schéma Supabase si nécessaire
    Cette fonction est appelée au démarrage de l'application
    
    Pour utiliser ce système, vous devez créer les tables suivantes dans Supabase:
    
    1. Table 'users':
    - id (UUID, Primary Key)
    - email (VARCHAR, Unique, Not Null)
    - name (VARCHAR, Null)
    - hashed_password (VARCHAR, Not Null)
    - is_disabled (BOOLEAN, Default: false)
    - created_at (TIMESTAMP WITH TIME ZONE, Default: now())
    - updated_at (TIMESTAMP WITH TIME ZONE, Default: now())
    
    2. Table 'sessions':
    - id (UUID, Primary Key)
    - user_id (UUID, Foreign Key -> users.id)
    - token (TEXT, Not Null)
    - created_at (TIMESTAMP WITH TIME ZONE, Default: now())
    - expires_at (TIMESTAMP WITH TIME ZONE, Not Null)
    
    3. Table 'consultations':
    - id (UUID, Primary Key)
    - user_id (UUID, Foreign Key -> users.id)
    - title (VARCHAR, Not Null)
    - date (TIMESTAMP WITH TIME ZONE, Default: now())
    - summary (TEXT, Null)
    - messages_count (INTEGER, Default: 0)
    
    4. Table 'messages':
    - id (UUID, Primary Key)
    - consultation_id (UUID, Foreign Key -> consultations.id)
    - content (TEXT, Not Null)
    - sender (VARCHAR, Check (sender in ('user', 'bot')))
    - timestamp (TIMESTAMP WITH TIME ZONE, Default: now())
    - recommendation (JSONB, Null)
    """
    print("Connexion à Supabase établie. URL:", SUPABASE_URL)

# Fonctions utilitaires pour interagir avec Supabase
def safe_get_user_by_email(email):
    """Récupère un utilisateur par email de manière sécurisée"""
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        users = response.data
        return users[0] if users and len(users) > 0 else None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur par email: {e}")
        return None

def safe_get_user_by_id(user_id):
    """Récupère un utilisateur par ID de manière sécurisée"""
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        users = response.data
        return users[0] if users and len(users) > 0 else None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur par ID: {e}")
        return None
