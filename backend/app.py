import codecs
import datetime
import importlib.util
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from json import JSONDecodeError
from typing import Literal, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

import conversation_unified_routes
import routes
import supabase_client

# Configuration du logging AVANT toute initialisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aibotanik")

# Réduire la verbosité des loggers externes
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

load_dotenv()
os.environ["PYTHONIOENCODING"] = "utf-8"

@asynccontextmanager
async def lifespan(app):
    try:
        supabase_client.init_supabase_schema()
    except Exception as e:
        pass
    
    yield

app = FastAPI(
    title="aiBotanik", 
    description="API de recommandation de phytothérapie",
    debug=False,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Gestion CORS
app.add_middleware(
    CORSMiddleware,    
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Authorization"],
    expose_headers=["Content-Length"],
    max_age=600,
)

@app.middleware("http")
async def add_utf8_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            default_config = {"llm_backend": "huggingface"}
            save_config(default_config)
            return default_config
    except Exception as e:
        return {"llm_backend": "huggingface"}

def save_config(config):
    global current_llm_backend
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)
        
        if "llm_backend" in config:
            current_llm_backend = config["llm_backend"]
        
        return True
    except Exception as e:
        return False

config = load_config()
current_llm_backend = config.get("llm_backend", "huggingface")

def verify_openai_key(api_key):
    """Vérifie la validité d'une clé API OpenAI"""
    if not api_key or api_key.strip() == "":
        return False
    
    if not api_key.startswith("sk-"):
        return False
        
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, timeout=10.0)
        response = client.models.list()
        return True
    except openai.AuthenticationError:
        return False
    except openai.RateLimitError:
        return True
    except (openai.APIConnectionError, requests.exceptions.RequestException, Exception) as e:
        if api_key.startswith("sk-") and len(api_key) > 20:
            return True
        return False

def get_llm_module():
    """Charge le module LLM approprié selon la configuration"""
    global current_llm_backend
      
    if current_llm_backend == "openai":
        try:
            if importlib.util.find_spec("langchain_chains_openai"):
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key and verify_openai_key(api_key):
                    import langchain_chains_openai
                    return langchain_chains_openai
                else:
                    current_llm_backend = "huggingface"
                    save_config({"llm_backend": "huggingface"})
            else:
                current_llm_backend = "huggingface"
                save_config({"llm_backend": "huggingface"})
        except Exception as e:
            current_llm_backend = "huggingface"
            save_config({"llm_backend": "huggingface"})
    
    try:
        import langchain_chains
        return langchain_chains
    except ImportError:
        raise ImportError("Impossible de charger un module LLM fonctionnel")

llm_module = get_llm_module()

try:
    csv_path = os.path.join(os.path.dirname(__file__), "data", "baseplante.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Fichier CSV introuvable: {csv_path}")
        
    df = pd.read_csv(csv_path, sep=";", quotechar='"', encoding='utf-8')
except Exception as e:
    df = pd.DataFrame(columns=["plante_recette", "maladiesoigneeparrecette", "plante_quantite_recette", "recette"])

def normalize_text(text):
    """Normalise le texte pour éviter les problèmes d'encodage"""
    if not text:
        return ""
        
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

class NormalizedResponse(BaseModel):
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = normalize_text(value)
        return result

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

async def get_current_llm_module():
    global llm_module
    return llm_module

@app.post("/recommend", response_model=ResponseBody)
async def recommend(body: RequestBody):
    try:
        csv_path = os.path.abspath("data/baseplante.csv")
        result = llm_module.get_recommendation(body.symptoms, df, csv_path)
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la génération de recommandation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/rebuild-index")
async def rebuild_index():
    """Force la reconstruction de l'index vectoriel"""
    try:
        csv_path = os.path.abspath("data/baseplante.csv")
        llm_module.build_and_save_vectorstore(df, csv_path)
        return {"status": "success", "message": "Index vectoriel reconstruit avec succès"}
    except Exception as e:
        logger.error(f"Erreur lors de la reconstruction de l'index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(body: ChatRequestBody):
    """Endpoint pour les questions générales en mode Discussion"""
    try:
        start_time = datetime.datetime.now()
        
        result = llm_module.generate_chat_response(body.message)
        
        if result:
            result = normalize_text(result)
        
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        backend_name = "OpenAI" if current_llm_backend == "openai" else "HuggingFace"
        
        return {
            "response": result,
            "timestamp": str(datetime.datetime.now()),
            "processing_time": elapsed_time,
            "question": normalize_text(body.message),
            "mode": "discussion",
            "status": "success",
            "backend": backend_name        }
    except Exception as e:
        logger.error(f"Erreur lors de la génération de réponse chat: {str(e)}")
        
        fallback_response = "Je suis désolé, je rencontre des difficultés techniques pour répondre à votre question. Veuillez réessayer ou passer en mode Consultation pour obtenir des recommandations spécifiques."
        
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
    """Configuration du backend LLM"""
    global current_llm_backend, llm_module
    
    try:
        if body.llm_backend != current_llm_backend:
            config = {"llm_backend": body.llm_backend}
            
            if body.llm_backend == "openai" and body.api_key:
                try:
                    if not verify_openai_key(body.api_key):
                        return ConfigResponseBody(
                            llm_backend=current_llm_backend,
                            status="error",
                            message="La clé API OpenAI fournie est invalide"
                        )
                    
                    env_path = os.path.join(os.path.dirname(__file__), ".env")
                    env_content = ""
                    
                    if os.path.exists(env_path):
                        with open(env_path, "r") as env_file:
                            env_content = env_file.read()
                    
                    if "OPENAI_API_KEY" in env_content:
                        env_lines = env_content.split("\n")
                        for i, line in enumerate(env_lines):
                            if line.startswith("OPENAI_API_KEY"):
                                env_lines[i] = f"OPENAI_API_KEY = '{body.api_key}'"
                                break
                        env_content = "\n".join(env_lines)
                    else:
                        env_content += f"\nOPENAI_API_KEY = '{body.api_key}'"
                    
                    with open(env_path, "w") as env_file:
                        env_file.write(env_content)
                    
                    load_dotenv(override=True)
                except Exception as e:
                    return ConfigResponseBody(
                        llm_backend=current_llm_backend,
                        status="error",
                        message=f"Erreur lors de la mise à jour de la clé API: {str(e)}"
                    )            
            if save_config(config):
                current_llm_backend = body.llm_backend
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
            return ConfigResponseBody(
                llm_backend=current_llm_backend,
                status="success",
                message=f"Backend LLM déjà configuré sur {current_llm_backend}"
            )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la configuration LLM: {str(e)}")
        return ConfigResponseBody(
            llm_backend=current_llm_backend,
            status="error",
            message=f"Erreur lors de la mise à jour de la configuration: {str(e)}"
        )

@app.get("/admin/config/llm")
async def get_llm_config():
    """Configuration actuelle du backend LLM"""
    hf_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_API_KEY")
    
    return {
        "llm_backend": current_llm_backend,
        "current_backend": current_llm_backend,
        "status": "success",
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_hf_key": bool(hf_api_key)
    }

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé pour le monitoring"""
    return {
        "status": "healthy",
        "service": "aiBotanik API",
        "version": "1.0.0",
        "timestamp": str(datetime.datetime.now()),
        "backend": current_llm_backend,
        "database": "supabase",
        "data_loaded": len(df) > 0
    }

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Bienvenue sur aiBotanik API",
        "description": "API de recommandation de phytothérapie africaine",
        "docs": "/api/docs",
        "health": "/health",
        "version": "1.0.0"
    }

app.include_router(routes.router, prefix="/api")
app.include_router(conversation_unified_routes.router)

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Erreur de validation: {exc}")
    
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
    logger.error(f"Exception non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur interne du serveur",
            "message": str(exc) if app.debug else "Une erreur s'est produite lors du traitement de votre requête"
        }
    )
