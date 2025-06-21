# Intégration de Hugging Face dans AiBotanik

## Modernisation de l'accès au modèle Hugging Face

Ce document explique les modifications apportées au système d'inférence de modèles Hugging Face dans le backend d'AiBotanik.

### Changements principaux

1. **Utilisation de `HuggingFacePipeline`** : Le code utilise maintenant la nouvelle approche `langchain-huggingface` avec `HuggingFacePipeline` pour une meilleure intégration entre LangChain et Hugging Face.

2. **Flexibilité local/distant** : Le système peut désormais fonctionner soit avec un modèle chargé localement, soit avec l'API Hugging Face distante.

3. **Fallback robuste** : Un mécanisme de fallback à plusieurs niveaux a été implémenté :
   - Tentative via HuggingFacePipeline (local ou distant)
   - Fallback sur l'API HTTP directe via `generate_huggingface_response`
   - Fallback sur des réponses prédéfinies en cas d'échec

4. **Gestion améliorée des clés API** : Le système recherche la clé API dans les variables d'environnement sous les noms `HUGGINGFACEHUB_API_TOKEN` ou `HF_API_KEY`.

### Configuration

Pour configurer le système, ajoutez les variables suivantes à votre fichier `.env` :

```
# Clé API Hugging Face (nécessaire pour l'API distante)
HUGGINGFACEHUB_API_TOKEN=votre_clé_api_huggingface

# Utiliser le modèle local ou distant (optionnel, false par défaut)
USE_LOCAL_MODEL=false
```

### Utilisation

#### 1. Via la fonction `get_llm_chain()`

Cette fonction est la méthode recommandée pour obtenir une chaîne LLM initialisée :

```python
from langchain_chains import get_llm_chain

# Récupérer la chaîne LLM
chain = get_llm_chain()

# Utiliser la chaîne pour générer une réponse
response = chain.run({
    "symptoms": "fièvre et maux de tête",
    "plant_data": data,
    "plant_name": "Moringa"
})
```

#### 2. Via l'initialisation directe du modèle

Pour des cas d'usage spécifiques :

```python
from langchain_chains import init_llm_model

# Initialiser un modèle local
llm_local = init_llm_model(use_local=True)

# Initialiser un modèle distant
llm_api = init_llm_model(use_local=False)

# Initialiser avec un modèle spécifique
llm_custom = init_llm_model(use_local=False, model_id="google/flan-t5-large")
```

#### 3. Via la fonction `generate_chat_response`

Pour les discussions générales :

```python
from langchain_chains import generate_chat_response

# Générer une réponse de chat
response = generate_chat_response("Quelles plantes peuvent aider contre les maux de tête?")
```

### Tests

Un script de test est disponible pour valider l'intégration :

```bash
python test_huggingface.py
```

Ce script teste :
- L'initialisation du pipeline local
- L'initialisation via l'API distante
- L'utilisation directe de l'API HTTP

### Remarques importantes

1. **Dépendances** : Assurez-vous que les packages `transformers`, `torch` et `langchain-huggingface` sont installés.

2. **Performance** : Le chargement du modèle local peut prendre du temps et de la mémoire. Pour les petites instances, privilégiez l'API distante.

3. **Usage en production** : Pour des raisons de performance et de déploiement, il est recommandé d'utiliser l'API distante en production (paramètre `USE_LOCAL_MODEL=false`).

4. **Modèles compatibles** : Cette implémentation a été testée avec `google/flan-t5-base`. D'autres modèles peuvent nécessiter des ajustements dans les paramètres de génération.
