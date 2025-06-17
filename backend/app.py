from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_chains import get_recommendation
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Charger .env
load_dotenv()

app = FastAPI(title="aiBotanik", description="API de recommandation de phytothérapie")

# Gestion CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour autoriser toutes les origines, à restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Charger la base CSV 
df = pd.read_csv("data/baseplante.csv", sep=";", quotechar='"', encoding='utf-8')

class RequestBody(BaseModel):
    symptoms: str

class ResponseBody(BaseModel):
    plant: str
    dosage: str
    prep: str
    image_url: str
    explanation: str
    contre_indications: str = ""
    partie_utilisee: str = ""
    composants: str = ""
    nom_local: str = ""

@app.post("/recommend", response_model=ResponseBody)
async def recommend(body: RequestBody):
    try:
        # Passer le chemin absolu du CSV pour le monitoring des modifications
        csv_path = os.path.abspath("data/baseplante.csv")
        result = get_recommendation(body.symptoms, df, csv_path)
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
    from langchain_chains import build_and_save_vectorstore
    
    try:
        csv_path = os.path.abspath("data/baseplante.csv")
        # Forcer la reconstruction de l'index
        build_and_save_vectorstore(df, csv_path)
        return {"status": "success", "message": "Index vectoriel reconstruit avec succès"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
