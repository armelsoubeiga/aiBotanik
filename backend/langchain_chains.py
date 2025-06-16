import os
import requests
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# Embeddings + vectorstore
emb = OpenAIEmbeddings(openai_api_key=HF_API_KEY)
vectorstore = FAISS.from_documents([Document(page_content=row.to_json()),], emb)

# Prompt template
template = """
You are a phytotherapy expert. Given the symptoms: {symptoms},
and plant data: {plant_data}, recommend the best plant treatment,
including dosage, preparation, and any precautions. Provide a concise explanation.
"""
prompt = PromptTemplate(input_variables=["symptoms","plant_data"], template=template)
llm = ChatOpenAI(model="mistralai/Mistral-7B-Instruct-v0.2", openai_api_key=HF_API_KEY)
chain = LLMChain(llm=llm, prompt=prompt)

def fetch_image(plant_name: str) -> str:
    url = f"https://api.unsplash.com/search/photos?query={plant_name}&client_id={UNSPLASH_KEY}&per_page=1"
    resp = requests.get(url).json()
    return resp["results"][0]["urls"]["small"] if resp["results"] else ""

def get_recommendation(symptoms: str, df):
    # Recherche simple dans CSV
    matches = df[df["symptoms"].str.contains(symptoms, case=False, na=False)]
    if matches.empty:
        raise ValueError("No matching plant found")
    plant = matches.iloc[0].to_dict()
    plant_data = plant
    # Génère explication
    explanation = chain.run(symptoms=symptoms, plant_data=plant_data)
    # Image
    image_url = plant.get("image_url") or fetch_image(plant["plant_name"])
    return {
        "plant": plant["plant_name"],
        "dosage": plant["dosage"],
        "prep": plant["preparation"],
        "image_url": image_url,
        "explanation": explanation
    }
