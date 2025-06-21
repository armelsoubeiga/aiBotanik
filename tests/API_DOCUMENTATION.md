# Documentation API aiBotanik

## Authentification

### Inscription
**POST** `/api/auth/signup`

Crée un nouvel utilisateur.

**Corps de la requête** :
```json
{
  "email": "utilisateur@example.com",
  "name": "Nom Complet",
  "password": "motdepassesecret",
  "confirmPassword": "motdepassesecret"
}
```

**Réponse** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

### Connexion
**POST** `/api/auth/login`

Connecte un utilisateur existant.

**Corps de la requête** :
```json
{
  "email": "utilisateur@example.com",
  "password": "motdepassesecret"
}
```

**Réponse** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

## Consultations

### Créer une nouvelle consultation
**POST** `/api/consultations`

Crée une nouvelle consultation et ajoute éventuellement des messages initiaux.

**En-têtes** :
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Corps de la requête** :
```json
{
  "title": "Ma consultation sur les plantes médicinales",
  "type": "consultation",
  "messages": [
    {
      "content": "Bonjour, je cherche une plante pour soulager mes maux de tête.",
      "sender": "user"
    },
    {
      "content": "Je peux vous aider à trouver une plante adaptée. Avez-vous des allergies connues ?",
      "sender": "bot"
    }
  ]
}
```

**Réponse** :
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Ma consultation sur les plantes médicinales",
  "type": "consultation",
  "date": "2025-06-19T10:30:00.000Z",
  "summary": "Bonjour, je cherche une plante pour soulager mes maux de tête...",
  "messages_count": 2
}
```

### Obtenir toutes les consultations
**GET** `/api/consultations`

Récupère toutes les consultations de l'utilisateur connecté.

**En-têtes** :
```
Authorization: Bearer <token>
```

**Réponse** :
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Ma consultation sur les plantes médicinales",
    "type": "consultation",
    "date": "2025-06-19T10:30:00.000Z",
    "summary": "Bonjour, je cherche une plante pour soulager mes maux de tête...",
    "messages_count": 2
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Question sur l'aloe vera",
    "type": "discussion",
    "date": "2025-06-18T14:15:00.000Z",
    "summary": "Bonjour, j'aimerais savoir comment cultiver l'aloe vera...",
    "messages_count": 5
  }
]
```

### Obtenir une consultation avec ses messages
**GET** `/api/consultations/{consultation_id}`

Récupère une consultation spécifique avec tous ses messages.

**En-têtes** :
```
Authorization: Bearer <token>
```

**Réponse** :
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Ma consultation sur les plantes médicinales",
  "type": "consultation",
  "date": "2025-06-19T10:30:00.000Z",
  "summary": "Bonjour, je cherche une plante pour soulager mes maux de tête...",
  "messages_count": 2,
  "messages": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "content": "Bonjour, je cherche une plante pour soulager mes maux de tête.",
      "sender": "user",
      "timestamp": "2025-06-19T10:30:00.000Z",
      "recommendation": null
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "content": "Je peux vous aider à trouver une plante adaptée. Avez-vous des allergies connues ?",
      "sender": "bot",
      "timestamp": "2025-06-19T10:30:00.000Z",
      "recommendation": null
    }
  ]
}
```

### Ajouter un message à une consultation
**POST** `/api/consultations/{consultation_id}/messages`

Ajoute un nouveau message à une consultation existante.

**En-têtes** :
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Corps de la requête** :
```json
{
  "content": "Non, je n'ai pas d'allergies connues.",
  "sender": "user"
}
```

**Réponse** :
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "content": "Non, je n'ai pas d'allergies connues.",
  "sender": "user",
  "timestamp": "2025-06-19T10:35:00.000Z",
  "recommendation": null
}
```

## Notes pour les développeurs

### Exemples de requêtes avec Curl

#### Inscription
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"password123","confirmPassword":"password123"}'
```

#### Connexion
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

#### Créer une consultation
```bash
curl -X POST http://localhost:8000/api/consultations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "Test de consultation",
    "type": "discussion",
    "messages": [
      {
        "content": "Bonjour, ceci est un test",
        "sender": "user"
      }
    ]
  }'
```

### Exemple pour Postman

1. Créez une nouvelle requête POST vers `http://localhost:8000/api/auth/signup`
2. Dans l'onglet "Headers", ajoutez `Content-Type: application/json`
3. Dans l'onglet "Body", sélectionnez "raw" et "JSON", puis entrez les données d'inscription
4. Exécutez la requête pour obtenir un token
5. Pour les requêtes protégées, ajoutez l'en-tête `Authorization: Bearer YOUR_TOKEN_HERE`

### Remarques importantes

- Tous les timestamps sont au format UTC ISO-8601
- Les tokens d'authentification expirent après 30 minutes
- Les types de consultation acceptés sont uniquement "discussion" ou "consultation"
- Les types d'expéditeur de message acceptés sont uniquement "user" ou "bot"
