from fastapi import APIRouter, Depends, HTTPException, status, Body
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from auth import (
    User, UserCreate, UserLogin, Token,
    get_password_hash, authenticate_user, create_access_token, get_current_active_user
)
from models import Consultation, ConsultationCreate, ConsultationWithMessages, Message, MessageCreate
from supabase_client import supabase, safe_get_user_by_email

router = APIRouter()

# Routes d'authentification
@router.post("/auth/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Inscription d'un nouvel utilisateur
    """
    if user_data.password != user_data.confirmPassword:
        raise HTTPException(status_code=400, detail="Les mots de passe ne correspondent pas")
    
    # Vérifier que l'email n'est pas déjà utilisé
    existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()
    if existing_user.data and len(existing_user.data) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email est déjà utilisé"
        )
    
    # Hacher le mot de passe
    hashed_password = get_password_hash(user_data.password)
    
    # Préparer les données pour insertion
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    user_dict = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "created_at": now,
        "updated_at": now,
    }
    
    # Insérer le nouvel utilisateur
    supabase.table("users").insert(user_dict).execute()
    
    # Créer un token d'accès
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email},
        expires_delta=access_token_expires
    )
    
    # Enregistrer également la session
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "token": access_token,
        "created_at": now,
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat(),
    }
    supabase.table("sessions").insert(session_data).execute()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    Connexion d'un utilisateur existant
    """
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer un token d'accès
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    # Enregistrer la session
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token": access_token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat(),
    }
    supabase.table("sessions").insert(session_data).execute()
    
    return {"access_token": access_token, "token_type": "bearer"}

# Routes pour les consultations
@router.get("/consultations", response_model=List[Consultation])
async def get_consultations(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Récupère toutes les consultations de l'utilisateur
    """
    response = supabase.table("consultations") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("date", desc=True) \
        .execute()
    return response.data

@router.post("/consultations", response_model=Consultation, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    data: ConsultationCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Crée une nouvelle consultation
    """
    consultation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Si le titre n'est pas fourni, générer un titre par défaut
    title = data.title if data.title else f"Consultation du {datetime.utcnow().strftime('%d %B %Y')}"
    
    # Créer la consultation
    consultation_data = {
        "id": consultation_id,
        "user_id": current_user["id"],
        "title": title,
        "date": now,
        "messages_count": len(data.messages) if data.messages else 0,
        "summary": None  # Sera mis à jour après l'ajout des messages
    }
    
    supabase.table("consultations").insert(consultation_data).execute()
    
    # Si des messages sont fournis, les ajouter
    if data.messages and len(data.messages) > 0:
        for msg in data.messages:
            message_data = {
                "id": str(uuid.uuid4()),
                "consultation_id": consultation_id,
                "content": msg.content,
                "sender": msg.sender,
                "timestamp": now,
            }
            supabase.table("messages").insert(message_data).execute()
        
        # Mettre à jour le résumé avec le premier message utilisateur
        first_user_message = next((msg for msg in data.messages if msg.sender == "user"), None)
        if first_user_message:
            summary = first_user_message.content[:100] + "..." if len(first_user_message.content) > 100 else first_user_message.content
            supabase.table("consultations").update({"summary": summary}).eq("id", consultation_id).execute()
            consultation_data["summary"] = summary
    
    return consultation_data

@router.get("/consultations/{consultation_id}", response_model=ConsultationWithMessages)
async def get_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Récupère une consultation spécifique avec ses messages
    """
    # Récupérer la consultation
    consultation_response = supabase.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    
    consultation = consultation_response.data
    
    # Récupérer les messages de la consultation
    messages_response = supabase.table("messages") \
        .select("*") \
        .eq("consultation_id", consultation_id) \
        .order("timestamp", desc=False) \
        .execute()
    
    consultation["messages"] = messages_response.data or []
    
    return consultation

@router.post("/consultations/{consultation_id}/messages", response_model=Message)
async def add_message(
    consultation_id: str,
    message_data: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Ajoute un message à une consultation existante
    """
    # Vérifier que la consultation existe et appartient à l'utilisateur
    consultation_response = supabase.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    
    # Créer le message
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    message = {
        "id": message_id,
        "consultation_id": consultation_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
    }
    
    supabase.table("messages").insert(message).execute()
    
    # Mettre à jour le nombre de messages dans la consultation
    supabase.table("consultations") \
        .update({"messages_count": consultation_response.data["messages_count"] + 1}) \
        .eq("id", consultation_id) \
        .execute()
    
    # Si c'est le premier message utilisateur, mettre à jour le résumé
    if message_data.sender == "user" and consultation_response.data["messages_count"] == 0:
        summary = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        supabase.table("consultations") \
            .update({"summary": summary}) \
            .eq("id", consultation_id) \
            .execute()
    
    return message
