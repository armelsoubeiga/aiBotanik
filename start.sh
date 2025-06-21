#!/bin/bash

# Script de démarrage pour Render
# Ce script lance l'application FastAPI avec uvicorn

cd backend
python -m uvicorn app:app --host 0.0.0.0 --port $PORT
