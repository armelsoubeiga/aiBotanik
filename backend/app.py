from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional, Literal
import pandas as pd
import os
import datetime
import json
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import traceback
import datetime
import importlib.util
import codecs
import secrets

# Modules locaux
import supabase_client
import routes

# Charger .env
load_dotenv()

# Configuration pour assurer un encodage UTF-8 correct
# Assurez-vous que le système peut gérer correctement l'UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Code à exécuter au démarrage
    print("Initialisation de l'application...")
    
    # Initialiser Supabase
    try:
        supabase_client.init_supabase_schema()
        print("Initialisation Supabase terminée")
    except Exception as e:
        print(f"Erreur lors de l'initialisation Supabase: {e}")
    
    yield
    
    # Code à exécuter à l'arrêt
    print("Arrêt de l'application...")

app = FastAPI(
    title="aiBotanik", 
    description="API de recommandation de phytothérapie",
    debug=True,  # Activer le mode debug pour des messages d'erreur détaillés
    openapi_url="/api/openapi.json",  # Déplacer le schéma OpenAPI sous /api pour cohérence
    docs_url="/api/docs",  # Déplacer Swagger sous /api pour cohérence
    redoc_url="/api/redoc",  # Déplacer ReDoc sous /api pour cohérence
    lifespan=lifespan  # Utiliser le nouveau gestionnaire de cycle de vie
)

# Gestion CORS
app.add_middleware(
    CORSMiddleware,    
    allow_origins=["*"],  # Pour autoriser toutes les origines, à restreindre en prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Authorization"],
    expose_headers=["Content-Length"],
    max_age=600,
)

# Middleware pour assurer l'encodage UTF-8 dans toutes les réponses
@app.middleware("http")
async def add_utf8_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# Chemin du fichier de configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Fonction pour charger la configuration
def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            # Configuration par défaut
            default_config = {"llm_backend": "huggingface"}
            save_config(default_config)
            return default_config
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")
        return {"llm_backend": "huggingface"}

# Fonction pour sauvegarder la configuration
def save_config(config):
    global current_llm_backend
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)
        
        # Mettre à jour la variable globale si le backend LLM a changé
        if "llm_backend" in config:
            current_llm_backend = config["llm_backend"]
            print(f"Backend LLM mis à jour vers: {current_llm_backend}")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la configuration: {e}")
        return False

# Charger la configuration au démarrage
config = load_config()
current_llm_backend = config.get("llm_backend", "huggingface")
print(f"Backend LLM actuel: {current_llm_backend}")

# Fonction pour vérifier la validité de la clé API OpenAI
def verify_openai_key(api_key):
    """Vérifie si la clé API OpenAI est valide"""
    if not api_key or api_key.strip() == "":
        return False
    
    # Vérification basique du format de la clé
    if not api_key.startswith("sk-"):
        return False
        
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, timeout=10.0)
        # Simple appel pour vérifier la validité de la clé avec timeout
        response = client.models.list()
        return True
    except openai.AuthenticationError:
        print(f"Clé API OpenAI invalide")
        return False
    except openai.RateLimitError:
        print(f"Limite de taux atteinte pour l'API OpenAI, mais la clé semble valide")
        return True  # La clé est valide même si on a atteint la limite
    except (openai.APIConnectionError, requests.exceptions.RequestException, Exception) as e:
        print(f"Erreur de connexion lors de la vérification de la clé API OpenAI: {e}")
        # En cas d'erreur réseau, on assume que la clé pourrait être valide
        # si elle a le bon format
        if api_key.startswith("sk-") and len(api_key) > 20:
            print("Clé semble avoir le bon format, supposée valide malgré l'erreur réseau")
            return True
        return False

# Fonction pour charger le module approprié selon la configuration
def get_llm_module():
    global current_llm_backend
      # Vérifier si OpenAI est configuré et disponible
    if current_llm_backend == "openai":
        try:
            # Vérifier si le module OpenAI est disponible
            if importlib.util.find_spec("langchain_chains_openai"):
                # Vérifier que la clé API OpenAI est configurée et valide
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key and verify_openai_key(api_key):
                    import langchain_chains_openai
                    print("Module OpenAI chargé avec succès")
                    return langchain_chains_openai
                else:
                    print("AVERTISSEMENT: Clé API OpenAI non configurée ou invalide dans .env, retour à HuggingFace")
                    current_llm_backend = "huggingface"
                    save_config({"llm_backend": "huggingface"})
            else:
                print("Module OpenAI non trouvé, retour à HuggingFace")
                current_llm_backend = "huggingface"
                save_config({"llm_backend": "huggingface"})
        except Exception as e:
            print(f"Erreur lors du chargement du module OpenAI: {e}")
            print("Retour à HuggingFace")
            current_llm_backend = "huggingface"
            save_config({"llm_backend": "huggingface"})
    
    # Charger le module HuggingFace
    try:
        import langchain_chains
        print("Module HuggingFace chargé avec succès")
          # Vérifier que la clé HuggingFace est configurée
        hf_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_API_KEY")
        if not hf_api_key:
            print("AVERTISSEMENT: Clé API HuggingFace non configurée dans .env")
            print("Certaines fonctionnalités peuvent ne pas fonctionner correctement")
        else:
            print("Clé API HuggingFace configurée avec succès")
            
        return langchain_chains
    except ImportError:
        print("ERREUR CRITIQUE: Impossible de charger le module langchain_chains")
        raise ImportError("Impossible de charger un module LLM fonctionnel")

# Obtenir le module actif
llm_module = get_llm_module()

# Charger la base CSV avec gestion d'erreurs et messages explicites
try:
    csv_path = os.path.join(os.path.dirname(__file__), "data", "baseplante.csv")
    print(f"Chargement du CSV depuis: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"ERREUR: Le fichier CSV n'existe pas à l'emplacement: {csv_path}")
        available_files = os.listdir(os.path.dirname(csv_path)) if os.path.exists(os.path.dirname(csv_path)) else []
        print(f"Fichiers disponibles dans le répertoire: {available_files}")
        raise FileNotFoundError(f"Fichier CSV introuvable: {csv_path}")
        
    df = pd.read_csv(csv_path, sep=";", quotechar='"', encoding='utf-8')
    print(f"CSV chargé avec succès: {len(df)} enregistrements")
except Exception as e:
    print(f"ERREUR lors du chargement du CSV: {str(e)}")
    traceback.print_exc()
    # Créer un DataFrame vide mais avec les colonnes nécessaires pour éviter les erreurs
    df = pd.DataFrame(columns=["plante_recette", "maladiesoigneeparrecette", "plante_quantite_recette", "recette"])

# Fonction pour normaliser le texte dans les réponses
def normalize_text(text):
    """
    Normalise le texte pour éviter les problèmes d'encodage
    """
    if not text:
        return ""
        
    # Remplacer les formes mal encodées qui pourraient déjà exister
    replacements = {
        "Ã©": "é", "Ã¨": "è", "Ãª": "ê", "Ã«": "ë",
        "Ã ": "à", "Ã¢": "â",
        "Ã®": "î", "Ã¯": "ï",
        "Ã´": "ô", "Ã¶": "ö",
        "Ã¹": "ù", "Ã»": "û", "Ã¼": "ü",
        "Ã§": "ç", "Ã‰": "É", "Ãˆ": "È"
    }
    
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    return text

# Classe pour la normalisation des réponses
class NormalizedResponse(BaseModel):
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        # Normaliser toutes les chaînes de caractères dans le dictionnaire
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = normalize_text(value)
        return result

# Modifier les classes de modèles pour hériter de NormalizedResponse
class RequestBody(BaseModel):
    symptoms: str

class ChatRequestBody(BaseModel):
    message: str

class ResponseBody(NormalizedResponse):
    plant: str
    dosage: str
    prep: str
    image_url: str
    explanation: str
    contre_indications: str = ""
    partie_utilisee: str = ""
    composants: str = ""
    nom_local: str = ""
    # Champs structurés pour l'affichage frontend
    diagnostic: str = ""
    symptomes: str = ""
    presentation: str = ""
    mode_action: str = ""
    traitement_info: str = ""
    precautions_info: str = ""
    composants_info: str = ""
    resume_traitement: str = ""

class ConfigUpdateBody(BaseModel):
    llm_backend: Literal["huggingface", "openai"]
    api_key: Optional[str] = None

class ConfigResponseBody(NormalizedResponse):
    llm_backend: str
    status: str
    message: str

# Dépendance pour obtenir le module LLM actuel
async def get_current_llm_module():
    global llm_module
    return llm_module

@app.post("/recommend", response_model=ResponseBody)
async def recommend(body: RequestBody):
    try:
        # Passer le chemin absolu du CSV pour le monitoring des modifications
        csv_path = os.path.abspath("data/baseplante.csv")
        result = llm_module.get_recommendation(body.symptoms, df, csv_path)
        return result
    except Exception as e:
        # Afficher la trace complète de l'erreur dans la console
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/rebuild-index")
async def rebuild_index():
    """
    Endpoint administrateur pour forcer la reconstruction de l'index vectoriel.
    Utile après des mises à jour manuelles du CSV ou pour les tests.
    """
    try:
        csv_path = os.path.abspath("data/baseplante.csv")
        # Forcer la reconstruction de l'index avec le module actif
        llm_module.build_and_save_vectorstore(df, csv_path)
        return {"status": "success", "message": "Index vectoriel reconstruit avec succès"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(body: ChatRequestBody):
    """
    Endpoint pour répondre aux questions générales sur la phytothérapie en mode Discussion.
    Utilise un LLM pour générer des réponses dynamiques avec un fallback en cas d'échec.
    """
    try:
        # Mesure du temps de réponse
        start_time = datetime.datetime.now()
        
        # Génération de la réponse en utilisant le module actif
        result = llm_module.generate_chat_response(body.message)
        
        # Normaliser le texte de la réponse pour éviter les problèmes d'encodage
        if result:
            result = normalize_text(result)
        
        # Calcul de la durée
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        
        # Indiquer quel backend a été utilisé
        backend_name = "OpenAI" if current_llm_backend == "openai" else "HuggingFace"        # Structure de réponse améliorée
        return {
            "response": result,
            "timestamp": str(datetime.datetime.now()),
            "processing_time": elapsed_time,
            "question": normalize_text(body.message),  # Normaliser aussi la question
            "mode": "discussion",
            "status": "success",
            "backend": backend_name
        }
    except Exception as e:
        traceback.print_exc()
        # Message d'erreur plus convivial
        error_message = f"Erreur lors de la génération de la réponse: {str(e)}"
        print(error_message)
        
        # Réponse de secours en cas d'erreur
        fallback_response = "Je suis désolé, je rencontre des difficultés techniques pour répondre à votre question. Veuillez réessayer ou passer en mode Consultation pour obtenir des recommandations spécifiques."
        
        # Renvoyer un message d'erreur convivial plutôt qu'une erreur 500
        return {
            "response": fallback_response,
            "timestamp": str(datetime.datetime.now()),
            "status": "error",
            "error_details": str(e),
            "mode": "discussion",
            "backend": current_llm_backend
        }

@app.put("/admin/config/llm", response_model=ConfigResponseBody)
async def update_llm_config(body: ConfigUpdateBody):
    """
    Endpoint d'administration pour changer le backend LLM (HuggingFace ou OpenAI)
    """
    global current_llm_backend, llm_module
    
    try:
        # Vérifier si le backend demandé est différent de l'actuel
        if body.llm_backend != current_llm_backend:
            print(f"Changement de backend LLM de {current_llm_backend} à {body.llm_backend}")
            
            # Mettre à jour la configuration
            config = {"llm_backend": body.llm_backend}
              # Si API key fournie pour OpenAI, la valider et la sauvegarder dans .env
            if body.llm_backend == "openai" and body.api_key:
                try:
                    # Vérifier si la clé API est valide
                    if not verify_openai_key(body.api_key):
                        return ConfigResponseBody(
                            llm_backend=current_llm_backend,
                            status="error",
                            message="La clé API OpenAI fournie est invalide"
                        )
                    
                    # Mettre à jour le fichier .env
                    env_path = os.path.join(os.path.dirname(__file__), ".env")
                    env_content = ""
                    
                    # Lire le contenu actuel
                    if os.path.exists(env_path):
                        with open(env_path, "r") as env_file:
                            env_content = env_file.read()
                    
                    # Mettre à jour ou ajouter la clé OpenAI
                    if "OPENAI_API_KEY" in env_content:
                        # Remplacer la ligne existante
                        env_lines = env_content.split("\n")
                        for i, line in enumerate(env_lines):
                            if line.startswith("OPENAI_API_KEY"):
                                env_lines[i] = f"OPENAI_API_KEY = '{body.api_key}'"
                                break
                        env_content = "\n".join(env_lines)
                    else:
                        # Ajouter une nouvelle ligne
                        env_content += f"\nOPENAI_API_KEY = '{body.api_key}'"
                    
                    # Sauvegarder le fichier .env
                    with open(env_path, "w") as env_file:
                        env_file.write(env_content)
                    
                    print("Clé API OpenAI mise à jour avec succès")
                    # Recharger les variables d'environnement
                    load_dotenv(override=True)
                except Exception as e:
                    print(f"Erreur lors de la mise à jour du fichier .env: {e}")
                    return ConfigResponseBody(
                        llm_backend=current_llm_backend,
                        status="error",
                        message=f"Erreur lors de la mise à jour de la clé API: {str(e)}"
                    )
            
            # Sauvegarder la configuration
            if save_config(config):
                current_llm_backend = body.llm_backend
                # Recharger le module LLM
                llm_module = get_llm_module()
                return ConfigResponseBody(
                    llm_backend=current_llm_backend,
                    status="success",
                    message=f"Backend LLM changé pour {current_llm_backend}"
                )
            else:
                return ConfigResponseBody(
                    llm_backend=current_llm_backend,
                    status="error",
                    message="Erreur lors de la sauvegarde de la configuration"
                )
        else:
            # Le backend est déjà celui demandé
            return ConfigResponseBody(
                llm_backend=current_llm_backend,
                status="success",
                message=f"Backend LLM déjà configuré sur {current_llm_backend}"
            )
    except Exception as e:
        traceback.print_exc()
        return ConfigResponseBody(
            llm_backend=current_llm_backend,
            status="error",
            message=f"Erreur lors de la mise à jour de la configuration: {str(e)}"
        )

@app.get("/admin/config/llm")
async def get_llm_config():
    """
    Récupérer la configuration actuelle du backend LLM
    """
    # Vérifier la présence de la clé HuggingFace (deux noms possibles)
    hf_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_API_KEY")
    
    return {
        "llm_backend": current_llm_backend,
        "current_backend": current_llm_backend,  # Alias pour compatibilité
        "status": "success",
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_hf_key": bool(hf_api_key)
    }

# Inclure les routes d'authentification et de consultation
app.include_router(routes.router, prefix="/api")

# Importer et inclure les routes pour les conversations unifiées
import conversation_unified_routes
app.include_router(conversation_unified_routes.router)

# Générer une clé secrète si elle n'existe pas
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)

# L'initialisation de Supabase se fait maintenant via le gestionnaire de cycle de vie défini plus haut

# Point d'entrée pour exécuter le serveur directement avec python app.py
if __name__ == "__main__":
    import uvicorn
    print("Démarrage du serveur aiBotanik sur http://localhost:8000")
    print("Pour arrêter le serveur, appuyez sur CTRL+C")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Ajout de gestionnaires d'erreurs
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from json import JSONDecodeError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configurer le logger
logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)
logger = logging.getLogger("aibotanik")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Handler personnalisé pour les erreurs de validation des requêtes
    """
    logger.error(f"Erreur de validation: {exc}")
    
    # Formatter les erreurs de manière plus conviviale
    error_details = []
    for error in exc.errors():
        error_location = " -> ".join(str(loc) for loc in error.get("loc", []))
        error_details.append({
            "location": error_location,
            "message": error.get("msg", "Erreur de validation"),
            "type": error.get("type", "unknown_error_type")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Erreur de validation des données de la requête",
            "errors": error_details
        }
    )

@app.exception_handler(JSONDecodeError)
async def json_decode_exception_handler(request, exc):
    """
    Handler personnalisé pour les erreurs de décodage JSON
    """
    logger.error(f"Erreur de décodage JSON: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Erreur de décodage JSON",
            "message": str(exc),
            "suggestion": "Vérifiez que votre requête contient un JSON valide et bien formatté"
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    Handler personnalisé pour les erreurs HTTP
    """
    logger.error(f"Erreur HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """
    Handler pour les exceptions non gérées
    """
    logger.error(f"Exception non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur interne du serveur",
            "message": str(exc) if app.debug else "Une erreur s'est produite lors du traitement de votre requête"        }
    )
