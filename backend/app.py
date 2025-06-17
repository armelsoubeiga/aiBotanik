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
        result = get_recommendation(body.symptoms, df)
        return result
    except Exception as e:
        # Afficher la trace complète de l'erreur dans la console
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
