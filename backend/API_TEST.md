# Test de l'API aiBotanik avec Postman ou Curl

## 1. Authentification - Création d'un utilisateur

**URL**: `POST http://localhost:8000/api/auth/signup`

**Headers**:
```
Content-Type: application/json
```

**Body (Raw JSON)**:
```json
{
  "email": "test@example.com",
  "name": "Utilisateur Test",
  "password": "password123",
  "confirmPassword": "password123"
}
```

## 2. Authentification - Login

**URL**: `POST http://localhost:8000/api/auth/login`

**Headers**:
```
Content-Type: application/json
```

**Body (Raw JSON)**:
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

*Note: Conservez le token retourné dans la réponse pour les requêtes suivantes*

## 3. Création d'une consultation

**URL**: `POST http://localhost:8000/api/consultations`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN_HERE
```

**Body (Raw JSON)**:
```json
{
  "title": "Test consultation",
  "type": "consultation",
  "messages": [
    {
      "content": "Bonjour, j'ai besoin d'aide pour une plante qui pourrait aider contre l'insomnie",
      "sender": "user"
    },
    {
      "content": "Je peux vous aider. Avez-vous déjà essayé certaines plantes pour l'insomnie ?",
      "sender": "bot"
    }
  ]
}
```

## 4. Récupération de toutes les consultations

**URL**: `GET http://localhost:8000/api/consultations`

**Headers**:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

## 5. Récupération d'une consultation spécifique avec messages

**URL**: `GET http://localhost:8000/api/consultations/{consultation_id}`

**Headers**:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

*Note: Remplacez {consultation_id} par l'ID obtenu lors de la création ou de la liste des consultations*

## 6. Ajout d'un message à une consultation existante

**URL**: `POST http://localhost:8000/api/consultations/{consultation_id}/messages`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN_HERE
```

**Body (Raw JSON)**:
```json
{
  "content": "Oui, j'ai déjà essayé la camomille, mais sans grand effet",
  "sender": "user"
}
```

*Note: Remplacez {consultation_id} par l'ID d'une consultation existante*

## Vérification des erreurs

Pour tester la robustesse de l'API, essayez ces requêtes invalides :

### Test 1: JSON malformé

```json
{
  "title": "Test consultation"
  "type": "discussion", // Virgule manquante sur la ligne précédente
  "messages": []
}
```

### Test 2: Valeur de type incorrecte

```json
{
  "title": "Test consultation",
  "type": "autre_type", // Seul "discussion" ou "consultation" sont valides
  "messages": []
}
```

### Test 3: Structure du message incorrecte

```json
{
  "title": "Test consultation",
  "type": "discussion",
  "messages": [
    {
      "contenu": "Texte", // Devrait être "content"
      "emetteur": "user" // Devrait être "sender"
    }
  ]
}
```
