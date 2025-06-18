"""
Script pour créer les tables Supabase nécessaires
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import time

# Charger les variables d'environnement
load_dotenv()

# Récupérer les variables d'environnement Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_ANON_KEY doivent être définies")

# Créer le client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def create_tables():
    """Crée toutes les tables nécessaires dans Supabase"""
    print("Création des tables dans Supabase...")
      # Table des utilisateurs
    print("1. Création de la table 'users'")
    try:
        supabase.table("users").delete().execute()
    except Exception as e:
        print(f"Erreur lors de la suppression de la table users: {e}")
    
    try:
        supabase.postgrest.rpc(
            'schema',
            {
                'query': '''
                CREATE TABLE IF NOT EXISTS public.users (
                    id UUID PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    hashed_password VARCHAR(255) NOT NULL,
                    is_disabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                '''
            }
        ).execute()
    except Exception as e:
        print(f"Erreur lors de la création de la table users: {e}")
    
    # Table des sessions
    print("2. Création de la table 'sessions'")
    supabase.table("sessions").delete().execute()
    
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            CREATE TABLE IF NOT EXISTS public.sessions (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                token TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
            '''
        }
    ).execute()
    
    # Table des consultations
    print("3. Création de la table 'consultations'")
    supabase.table("consultations").delete().execute()
    
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            CREATE TABLE IF NOT EXISTS public.consultations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                messages_count INTEGER DEFAULT 0
            );
            '''
        }
    ).execute()
    
    # Table des messages
    print("4. Création de la table 'messages'")
    supabase.table("messages").delete().execute()
    
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            CREATE TABLE IF NOT EXISTS public.messages (
                id UUID PRIMARY KEY,
                consultation_id UUID NOT NULL REFERENCES public.consultations(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                sender VARCHAR(10) NOT NULL CHECK (sender IN ('user', 'bot')),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                recommendation JSONB
            );
            '''
        }
    ).execute()
    
    # Création des indices
    print("5. Création des indices")
    
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON public.consultations(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_consultation_id ON public.messages(consultation_id);
            '''
        }
    ).execute()
    
    # Création des politiques de sécurité Row Level Security (RLS)
    print("6. Configuration des politiques de sécurité RLS")
    
    # Activer RLS sur toutes les tables
    tables = ["users", "sessions", "consultations", "messages"]
    for table in tables:
        supabase.postgrest.rpc(
            'schema',
            {
                'query': f'''
                ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
                '''
            }
        ).execute()
    
    # Politiques pour users
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            DROP POLICY IF EXISTS "Users can view their own data" ON public.users;
            CREATE POLICY "Users can view their own data" ON public.users
                FOR SELECT USING (auth.uid() = id);
                
            DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
            CREATE POLICY "Users can update their own data" ON public.users
                FOR UPDATE USING (auth.uid() = id);
            '''
        }
    ).execute()
    
    # Politiques pour consultations
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            DROP POLICY IF EXISTS "Users can view their own consultations" ON public.consultations;
            CREATE POLICY "Users can view their own consultations" ON public.consultations
                FOR SELECT USING (auth.uid() = user_id);
                
            DROP POLICY IF EXISTS "Users can create their own consultations" ON public.consultations;
            CREATE POLICY "Users can create their own consultations" ON public.consultations
                FOR INSERT WITH CHECK (auth.uid() = user_id);
                
            DROP POLICY IF EXISTS "Users can update their own consultations" ON public.consultations;
            CREATE POLICY "Users can update their own consultations" ON public.consultations
                FOR UPDATE USING (auth.uid() = user_id);
            '''
        }
    ).execute()
    
    # Politiques pour messages
    supabase.postgrest.rpc(
        'schema',
        {
            'query': '''
            DROP POLICY IF EXISTS "Users can view messages of their consultations" ON public.messages;
            CREATE POLICY "Users can view messages of their consultations" ON public.messages
                FOR SELECT USING (
                    auth.uid() IN (
                        SELECT user_id FROM public.consultations 
                        WHERE id = consultation_id
                    )
                );
                
            DROP POLICY IF EXISTS "Users can create messages in their consultations" ON public.messages;
            CREATE POLICY "Users can create messages in their consultations" ON public.messages
                FOR INSERT WITH CHECK (
                    auth.uid() IN (
                        SELECT user_id FROM public.consultations 
                        WHERE id = consultation_id
                    )
                );
            '''
        }
    ).execute()
    
    print("Création des tables terminée avec succès !")

if __name__ == "__main__":
    create_tables()
    print("\nPour utiliser ces tables, assurez-vous que votre application backend est configurée avec les identifiants Supabase corrects.")
