from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from langchain_chains import get_recommendation

app = FastAPI(title="BotanikAI API")

# Charger la base CSV
df = pd.read_csv("data/baseplante.csv")

class RequestBody(BaseModel):
    symptoms: str

class ResponseBody(BaseModel):
    plant: str
    dosage: str
    prep: str
    image_url: str
    explanation: str

@app.post("/recommend", response_model=ResponseBody)
async def recommend(body: RequestBody):
    try:
        result = get_recommendation(body.symptoms, df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
