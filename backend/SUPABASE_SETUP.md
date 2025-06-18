# Configuration Supabase pour aiBotanik

Ce document explique comment configurer Supabase pour prendre en charge les fonctionnalités d'authentification et de stockage des consultations pour aiBotanik.

## Tables à créer dans Supabase

Connectez-vous à votre tableau de bord Supabase et créez les tables suivantes :

### 1. Table `users`

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Table `sessions`

```sql
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_sessions_user_id ON public.sessions(user_id);
```

### 3. Table `consultations`

```sql
CREATE TABLE public.consultations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    messages_count INTEGER DEFAULT 0
);

CREATE INDEX idx_consultations_user_id ON public.consultations(user_id);
```

### 4. Table `messages`

```sql
CREATE TABLE public.messages (
    id UUID PRIMARY KEY,
    consultation_id UUID NOT NULL REFERENCES public.consultations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender VARCHAR(10) NOT NULL CHECK (sender IN ('user', 'bot')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    recommendation JSONB
);

CREATE INDEX idx_messages_consultation_id ON public.messages(consultation_id);
```

## Routes API

Le backend implémente les routes API suivantes :

### Authentification

- `POST /api/auth/signup` : Inscription d'un nouvel utilisateur
- `POST /api/auth/login` : Connexion d'un utilisateur

### Consultations

- `GET /api/consultations` : Récupérer toutes les consultations de l'utilisateur connecté
- `POST /api/consultations` : Créer une nouvelle consultation
- `GET /api/consultations/{consultation_id}` : Récupérer une consultation spécifique avec ses messages
- `POST /api/consultations/{consultation_id}/messages` : Ajouter un message à une consultation

## Utilisation depuis le frontend

Le frontend peut utiliser le service API défini dans `/frontend/lib/api.ts` pour interagir avec le backend :

```typescript
import { authApi, consultationsApi } from '../lib/api';

// Inscription
const signupResponse = await authApi.signup({
  name: "John Doe",
  email: "john@example.com",
  password: "password123",
  confirmPassword: "password123"
});

// Connexion
const loginResponse = await authApi.login({
  email: "john@example.com",
  password: "password123"
});

// Après connexion réussie, stocker le token
localStorage.setItem('authToken', loginResponse.access_token);

// Récupérer les consultations
const consultations = await consultationsApi.getAll();

// Créer une nouvelle consultation
const newConsultation = await consultationsApi.create("Ma nouvelle consultation");

// Récupérer une consultation avec ses messages
const consultationWithMessages = await consultationsApi.getById(newConsultation.id);

// Ajouter un message à une consultation
const newMessage = await consultationsApi.addMessage(newConsultation.id, {
  content: "Bonjour, j'ai des maux de tête",
  sender: "user"
});
```
