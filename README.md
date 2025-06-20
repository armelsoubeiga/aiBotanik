# BotanikAI

**BotanikAI** is a professional plant-based treatment recommendation app using LLMs.

## Architecture

```mermaid
flowchart LR
  User --> Frontend
  Frontend --> API
  API --> LangChain

  subgraph RAG Engine
    LangChain --> Mistral
    LangChain --> BaseCSV
    LangChain --> Unsplash
  end
```

```mermaid
flowchart TB
  subgraph RAG Engine
    UserQuery["🧑‍🌾 Question utilisateur"]
    Embedder["🔤 Embedding via Mistral"]
    Retriever["📂 Recherche dans CSV / base enrichie"]
    Context["📄 Contexte pertinent"]
    PromptTemplate["🧩 Prompt Template"]
    LLM["🤖 Mistral (LLM)"]
    Response["✅ Réponse générée"]

    UserQuery --> Embedder
    Embedder --> Retriever
    Retriever --> Context
    Context --> PromptTemplate
    PromptTemplate --> LLM
    LLM --> Response
  end
```


## Structure

```
Botanikai/
├── logo.svg
├── backend/
│   ├── app.py
│   ├── langchain_chains.py
│   ├── requirements.txt
│   └── .github/
│       └── workflows/
│           └── hf_deploy.yml
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── components/
│   │   │   ├── SearchForm.jsx
│   │   │   └── Recommendation.jsx
│   │   └── index.js
│   └── vercel.json
├── README.md
└── LICENSE
```

## Features
- **Plant-based treatment recommendations**: Get personalized treatment plans based on your symptoms.
- **LLM-powered**: Utilizes advanced language models for accurate and relevant recommendations.
- **Image search**: Find images of plants and treatments using Unsplash API.