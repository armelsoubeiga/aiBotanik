"""
SCRIPT SQL POUR CRÉER LES TABLES SUPABASE - aiBotanik

Instructions:
1. Connectez-vous à votre dashboard Supabase
2. Allez dans "Database" > "SQL Editor"
3. Créez une nouvelle requête (+ New query)
4. Copiez-collez tout le code SQL ci-dessous
5. Exécutez la requête

Ce script crée toutes les tables nécessaires pour l'authentification
et le stockage des consultations/messages pour le projet aiBotanik.
"""

# ---------------- DÉBUT DU CODE SQL À COPIER-COLLER ----------------

"""
-- Attention: Ce script supprime les tables existantes, commentez ces lignes si vous voulez préserver les données
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.consultations CASCADE;
DROP TABLE IF EXISTS public.sessions CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des sessions (pour la gestion de l'authentification)
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Table des consultations (tous types de conversations - discussion et consultation)
CREATE TABLE IF NOT EXISTS public.consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('discussion', 'consultation')), -- Type de conversation
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    messages_count INTEGER DEFAULT 0
);

-- Table des messages
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL REFERENCES public.consultations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender VARCHAR(10) NOT NULL CHECK (sender IN ('user', 'bot')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    recommendation JSONB -- Pour stocker des informations supplémentaires (plantes recommandées, etc.)
);

-- Création des indices pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON public.consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_type ON public.consultations(type);
CREATE INDEX IF NOT EXISTS idx_messages_consultation_id ON public.messages(consultation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON public.messages(sender);

-- Activer Row Level Security (RLS) pour toutes les tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Politiques RLS pour users
DROP POLICY IF EXISTS "Users can view their own data" ON public.users;
CREATE POLICY "Users can view their own data" ON public.users
    FOR SELECT USING (auth.uid() = id);
    
DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
CREATE POLICY "Users can update their own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Politiques RLS pour consultations
DROP POLICY IF EXISTS "Users can view their own consultations" ON public.consultations;
CREATE POLICY "Users can view their own consultations" ON public.consultations
    FOR SELECT USING (auth.uid() = user_id);
    
DROP POLICY IF EXISTS "Users can create their own consultations" ON public.consultations;
CREATE POLICY "Users can create their own consultations" ON public.consultations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
DROP POLICY IF EXISTS "Users can update their own consultations" ON public.consultations;
CREATE POLICY "Users can update their own consultations" ON public.consultations
    FOR UPDATE USING (auth.uid() = user_id);

-- Politiques RLS pour messages
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

"""

# ---------------- FIN DU CODE SQL À COPIER-COLLER ----------------

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Ce code permet de tester la connexion à Supabase après création des tables
def test_connexion_supabase():
    """Test la connexion à Supabase et vérifie que les tables existent"""
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Récupérer les variables d'environnement Supabase
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
        
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print("❌ ERREUR: Variables d'environnement SUPABASE_URL et SUPABASE_ANON_KEY manquantes")
            return False
        
        print("📡 Tentative de connexion à Supabase...")
        
        # Créer le client Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Vérifier que les tables existent en essayant de récupérer leur structure
        tables = ["users", "sessions", "consultations", "messages"]
        tables_existantes = []
        
        for table in tables:
            try:
                # On tente de récupérer 0 ligne de chaque table pour vérifier qu'elle existe
                response = supabase.table(table).select("*").limit(0).execute()
                tables_existantes.append(table)
            except Exception as e:
                print(f"❌ Table '{table}' n'existe pas ou erreur: {e}")
        
        # Afficher les résultats
        if len(tables_existantes) == 0:
            print("❌ AUCUNE table n'a été trouvée. Avez-vous exécuté le script SQL?")
            return False
        elif len(tables_existantes) < len(tables):
            print(f"⚠️ Seulement {len(tables_existantes)} tables sur {len(tables)} ont été trouvées:")
            print(f"   Tables trouvées: {', '.join(tables_existantes)}")
            print(f"   Tables manquantes: {', '.join(set(tables) - set(tables_existantes))}")
            return False
        else:
            print("✅ Connexion réussie! Toutes les tables ont été créées avec succès:")
            for table in tables_existantes:
                print(f"   ▸ Table '{table}' existe")
            return True
            
    except Exception as e:
        print(f"❌ ERREUR lors de la connexion à Supabase: {e}")
        return False

def create_tables():
    """Crée toutes les tables nécessaires dans Supabase"""
    print("Création des tables dans Supabase...")
    
    # Créer la fonction SQL execute_sql si elle n'existe pas déjà
    create_execute_sql_function = """
    CREATE OR REPLACE FUNCTION execute_sql(query text)
    RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
      EXECUTE query;
    END;
    $$;
    """
    
    # Créer la fonction via l'API REST avec la clé de service
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/",
            headers=headers,
            data=create_execute_sql_function
        )
        
        if response.status_code >= 300:
            print(f"Erreur lors de la création de la fonction execute_sql: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur lors de la création de la fonction execute_sql: {e}")
    
    # Table des utilisateurs
    print("1. Création de la table 'users'")
    users_table = """
    DROP TABLE IF EXISTS public.users CASCADE;
    CREATE TABLE IF NOT EXISTS public.users (
        id UUID PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255),
        hashed_password VARCHAR(255) NOT NULL,
        is_disabled BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_sql(users_table)
    
    # Table des sessions
    print("2. Création de la table 'sessions'")
    sessions_table = """
    DROP TABLE IF EXISTS public.sessions CASCADE;
    CREATE TABLE IF NOT EXISTS public.sessions (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
        token TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL
    );
    """
    execute_sql(sessions_table)
    
    # Table des consultations
    print("3. Création de la table 'consultations'")
    consultations_table = """
    DROP TABLE IF EXISTS public.consultations CASCADE;
    CREATE TABLE IF NOT EXISTS public.consultations (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        summary TEXT,
        messages_count INTEGER DEFAULT 0
    );
    """
    execute_sql(consultations_table)
      # Table des messages
    print("4. Création de la table 'messages'")
    messages_table = """
    DROP TABLE IF EXISTS public.messages CASCADE;
    CREATE TABLE IF NOT EXISTS public.messages (
        id UUID PRIMARY KEY,
        consultation_id UUID NOT NULL REFERENCES public.consultations(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        sender VARCHAR(10) NOT NULL CHECK (sender IN ('user', 'bot')),
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        recommendation JSONB
    );
    """
    execute_sql(messages_table)
    
    # Création des indices
    print("5. Création des indices")
    indices = """
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON public.consultations(user_id);
    CREATE INDEX IF NOT EXISTS idx_messages_consultation_id ON public.messages(consultation_id);
    """
    execute_sql(indices)
    
    # Création des politiques de sécurité Row Level Security (RLS)
    print("6. Configuration des politiques de sécurité RLS")
    
    # Activer RLS sur toutes les tables
    tables = ["users", "sessions", "consultations", "messages"]
    for table in tables:
        rls_enable = f"""
        ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
        """
        execute_sql(rls_enable)
    
    # Politiques pour users
    users_policies = """
    DROP POLICY IF EXISTS "Users can view their own data" ON public.users;
    CREATE POLICY "Users can view their own data" ON public.users
        FOR SELECT USING (auth.uid() = id);
        
    DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
    CREATE POLICY "Users can update their own data" ON public.users
        FOR UPDATE USING (auth.uid() = id);
    """
    execute_sql(users_policies)
    
    # Politiques pour consultations
    consultation_policies = """
    DROP POLICY IF EXISTS "Users can view their own consultations" ON public.consultations;
    CREATE POLICY "Users can view their own consultations" ON public.consultations
        FOR SELECT USING (auth.uid() = user_id);
        
    DROP POLICY IF EXISTS "Users can create their own consultations" ON public.consultations;
    CREATE POLICY "Users can create their own consultations" ON public.consultations
        FOR INSERT WITH CHECK (auth.uid() = user_id);
        
    DROP POLICY IF EXISTS "Users can update their own consultations" ON public.consultations;
    CREATE POLICY "Users can update their own consultations" ON public.consultations
        FOR UPDATE USING (auth.uid() = user_id);
    """
    execute_sql(consultation_policies)
    
    # Politiques pour messages
    messages_policies = """
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
        );    """
    execute_sql(messages_policies)
    print("Création des tables terminée avec succès !")

def main():
    """Point d'entrée principal pour tester la connexion"""
    print("\n" + "="*80)
    print("SCRIPT D'INITIALISATION DES TABLES SUPABASE POUR AIBOTANIK")
    print("="*80)
    print("\n1. Veuillez d'abord exécuter le script SQL dans l'éditeur SQL de Supabase")
    print("2. Ensuite, lancez ce script pour tester la connexion")
    print("\n")
    
    choix = input("Voulez-vous tester la connexion à Supabase maintenant ? (o/n): ")
    if choix.lower() == 'o':
        test_connexion_supabase()
    else:
        print("\nPour tester la connexion plus tard, relancez ce script et choisissez 'o'")
        
    print("\nRappel: Ce script est uniquement destiné à l'initialisation et à des fins de test.")
    print("Il n'est pas nécessaire en production.")
    print("="*80)

if __name__ == "__main__":
    main()
