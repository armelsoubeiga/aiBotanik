# Configuration des Environnements - aiBotanik Frontend

## Vue d'ensemble

Le frontend aiBotanik utilise un système de configuration automatique qui détecte l'environnement d'exécution et configure automatiquement les URLs du backend.

## Fonctionnement

### Détection automatique

La configuration détecte automatiquement l'environnement basé sur :

1. **Développement local** : `NODE_ENV === 'development'` ou `hostname === 'localhost'`
   - Backend URL : `http://localhost:8000`
   - API URL : `http://localhost:8000/api`

2. **Production** : tous les autres cas
   - Backend URL : `https://aibotanik-backend.onrender.com`
   - API URL : `https://aibotanik-backend.onrender.com/api`

### Override manuel

Vous pouvez forcer l'utilisation d'une URL spécifique en définissant la variable d'environnement :

```bash
NEXT_PUBLIC_API_URL=https://mon-backend-custom.com
```

## Utilisation dans le code

```typescript
import { API_URL, BASE_URL } from "@/lib/config";

// Pour les endpoints API (/api/*)
fetch(`${API_URL}/consultations`)

// Pour les autres endpoints (/chat, /recommend, etc.)
fetch(`${BASE_URL}/chat`)
```

## Variables disponibles

- `API_URL` : URL complète pour les endpoints API (avec `/api`)
- `BASE_URL` : URL de base du backend (sans `/api`)
- `ENVIRONMENT` : 'development' ou 'production'
- `DEBUG` : true en développement, false en production

## Test en local

1. **Backend en local** : Le frontend détecte automatiquement `localhost:8000`
2. **Backend sur Render** : Définir `NEXT_PUBLIC_API_URL=https://aibotanik-backend.onrender.com`

## Déploiement

En production, le frontend utilise automatiquement l'URL de production. Aucune configuration supplémentaire n'est nécessaire.
