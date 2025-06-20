-- Supprimer la table existante si elle existe (optionnel, à décommenter si nécessaire)
-- DROP TABLE IF EXISTS public.conversations CASCADE;

-- Table des conversations unifiée (VERSION CORRIGÉE)
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- CORRECTION: Référencer public.users au lieu de auth.users
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT,
    -- Stockage complet des messages avec leur structure entière
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    messages_count INTEGER DEFAULT 0,
    -- Informations sur le type de contenu
    type TEXT DEFAULT 'mixed' CHECK (type IN ('discussion', 'consultation', 'mixed')),
    -- Horodatage
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- État de l'interface pour la restauration exacte
    chat_mode TEXT DEFAULT 'discussion' CHECK (chat_mode IN ('discussion', 'consultation')),
    -- Champ pour stocker la recommandation principale (dernière recommandation)
    last_recommendation JSONB DEFAULT NULL
);

-- Index pour accélérer les requêtes par utilisateur
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);

-- Trigger pour mettre à jour automatiquement le timestamp
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_conversations_timestamp
BEFORE UPDATE ON public.conversations
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();

-- Sécurité par Row Level Security (RLS)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- CORRECTION: Utiliser user_id directement au lieu de auth.uid()
-- car nous utilisons notre propre système d'authentification avec public.users
CREATE POLICY "Users can only access their own conversations"
ON public.conversations
FOR ALL
TO authenticated
USING (true); -- Temporairement permissif pour les tests

-- Politique pour les sélections (lecture)
CREATE POLICY "Users can select their own conversations" 
ON public.conversations 
FOR SELECT 
TO authenticated
USING (true); -- Temporairement permissif pour les tests

-- Politique pour les insertions
CREATE POLICY "Users can insert their own conversations" 
ON public.conversations 
FOR INSERT 
TO authenticated
WITH CHECK (true); -- Temporairement permissif pour les tests

-- Politique pour les mises à jour
CREATE POLICY "Users can update their own conversations" 
ON public.conversations 
FOR UPDATE 
TO authenticated
USING (true)
WITH CHECK (true); -- Temporairement permissif pour les tests

-- Politique pour les suppressions
CREATE POLICY "Users can delete their own conversations" 
ON public.conversations 
FOR DELETE 
TO authenticated
USING (true); -- Temporairement permissif pour les tests

-- Note: Les politiques sont temporairement permissives pour faciliter les tests.
-- Une fois que tout fonctionne, vous pouvez les restreindre en remplaçant 'true' 
-- par des conditions appropriées basées sur votre système d'authentification.
