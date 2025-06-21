# Intégration de Supabase pour l'authentification et l'historique des consultations

Ce document décrit l'implémentation de l'authentification et du stockage des historiques de consultation dans le projet aiBotanik.

## Structure des données

### Tables Supabase

1. **users** - Stockage des utilisateurs
   - id (UUID)
   - email (VARCHAR)
   - name (VARCHAR)
   - hashed_password (VARCHAR)
   - is_disabled (BOOLEAN)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

2. **sessions** - Gestion des sessions de connexion
   - id (UUID)
   - user_id (UUID -> users.id)
   - token (TEXT)
   - created_at (TIMESTAMP)
   - expires_at (TIMESTAMP)

3. **consultations** - Stockage unifié des consultations/discussions
   - id (UUID)
   - user_id (UUID -> users.id)
   - title (VARCHAR)
   - date (TIMESTAMP)
   - summary (TEXT)
   - messages_count (INTEGER)

4. **messages** - Messages des consultations
   - id (UUID)
   - consultation_id (UUID -> consultations.id)
   - content (TEXT)
   - sender (VARCHAR, 'user' ou 'bot')
   - timestamp (TIMESTAMP)
   - recommendation (JSONB)

## Configuration initiale

1. Créer un projet Supabase sur https://supabase.com/
2. Configurer le fichier `.env` dans le dossier backend:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   SECRET_KEY=votre-cle-secrete-jwt
   ```
3. Exécuter le script d'initialisation pour créer les tables:
   ```
   cd backend
   python init_supabase.py
   ```

## Flux d'authentification

1. L'utilisateur s'inscrit via `/api/auth/signup`
2. L'utilisateur se connecte via `/api/auth/login`
3. Un JWT est généré et retourné au frontend
4. Le frontend stocke ce JWT et l'inclut dans l'en-tête `Authorization` de toutes les requêtes

## Gestion des consultations

1. Seuls les utilisateurs connectés peuvent sauvegarder des consultations
2. Si un utilisateur non connecté tente de sauvegarder une consultation:
   - Un modal s'affiche proposant de se connecter
   - L'utilisateur peut choisir de continuer sans connexion (la conversation ne sera pas sauvegardée)
   - Ou il peut se connecter pour sauvegarder sa conversation

3. Routes API pour les consultations:
   - `GET /api/consultations` - Liste des consultations de l'utilisateur
   - `POST /api/consultations` - Créer une nouvelle consultation
   - `GET /api/consultations/{id}` - Détails d'une consultation
   - `POST /api/consultations/{id}/messages` - Ajouter un message

## Points techniques à noter

1. Le fichier `init_supabase.py` est uniquement destiné à l'initialisation, pas à l'utilisation en production
2. L'authentification est obligatoire pour accéder aux routes de consultations
3. Les politiques RLS (Row Level Security) de Supabase garantissent que chaque utilisateur ne peut voir que ses propres données

## Intégration frontend

1. Le frontend affiche un bouton "Sauvegarder" dans l'interface de chat
2. Lors du clic, si l'utilisateur n'est pas connecté, le modal d'authentification s'affiche
3. L'historique des consultations est accessible uniquement aux utilisateurs connectés
4. La page d'historique permet de reprendre une conversation précédente
