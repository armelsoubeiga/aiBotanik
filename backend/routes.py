from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, TypeVar, Generic
from pydantic import create_model
import json
import uuid

from auth import (
    User, UserCreate, UserLogin, Token, PasswordChange,
    get_password_hash, authenticate_user, create_access_token, get_current_active_user, get_user
)
from models import Consultation, ConsultationCreate, ConsultationWithMessages, Message, MessageCreate, MessageBase
from supabase_client import supabase, supabase_admin, safe_get_user_by_email

router = APIRouter()

@router.post("/auth/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Inscription d'un nouvel utilisateur"""
    if user_data.password != user_data.confirmPassword:
        raise HTTPException(status_code=400, detail="Les mots de passe ne correspondent pas")
    
    existing_user = supabase_admin.table("users").select("*").eq("email", user_data.email).execute()
    if existing_user.data and len(existing_user.data) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email est déjà utilisé"
        )
    
    hashed_password = get_password_hash(user_data.password)
    
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
    supabase_admin.table("users").insert(user_dict).execute()
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email},
        expires_delta=access_token_expires
    )
    
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "token": access_token,
        "created_at": now,
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat(),
    }
    supabase_admin.table("sessions").insert(session_data).execute()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Connexion d'un utilisateur existant"""
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token": access_token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat(),
    }
    supabase_admin.table("sessions").insert(session_data).execute()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/validate")
async def validate_token(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Valide qu'un token est toujours valide"""
    return {"valid": True}

@router.get("/consultations", response_model=List[Consultation])
async def get_consultations(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Récupère toutes les consultations de l'utilisateur"""
    response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("date", desc=True) \
        .execute()
    return response.data

@router.post("/consultations", response_model=Consultation, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Crée une nouvelle consultation"""
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        body_dict = json.loads(body_str)
        data = ConsultationCreate(**body_dict)
    except Exception:
        raise HTTPException(status_code=400, detail="Données de requête invalides")
    
    consultation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    title = data.title if data.title else f"Consultation du {datetime.utcnow().strftime('%d %B %Y')}"
    
    try:
        consultation_data = {
            "id": consultation_id,
            "user_id": current_user["id"],
            "title": title,
            "type": data.type,
            "date": now,
            "messages_count": len(data.messages) if data.messages else 0,
            "summary": None
        }
        
        supabase_admin.table("consultations").insert(consultation_data).execute()
        
        if data.messages and len(data.messages) > 0:
            for msg in data.messages:
                message_data = {
                    "id": str(uuid.uuid4()),
                    "consultation_id": consultation_id,
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": now,
                    "recommendation": None
                }
                supabase_admin.table("messages").insert(message_data).execute()
            
            first_user_message = next((msg for msg in data.messages if msg.sender == "user"), None)
            if first_user_message:
                summary = first_user_message.content[:100] + "..." if len(first_user_message.content) > 100 else first_user_message.content
                supabase_admin.table("consultations").update({"summary": summary}).eq("id", consultation_id).execute()
                consultation_data["summary"] = summary
        
        return consultation_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la consultation: {str(e)}"
        )

@router.get("/consultations/{consultation_id}", response_model=ConsultationWithMessages)
async def get_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Récupère une consultation spécifique avec ses messages"""
    try:
        consultation_response = supabase_admin.table("consultations") \
            .select("*") \
            .eq("id", consultation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        if not consultation_response.data or len(consultation_response.data) == 0:
            raise HTTPException(status_code=404, detail="Consultation non trouvée")
        
        consultation = consultation_response.data[0]  # Prendre le premier résultat
        
    except Exception as e:
        # Si c'est une APIError de Supabase, c'est probablement que la consultation n'existe pas
        if "no rows returned" in str(e) or "PGRST116" in str(e):
            raise HTTPException(status_code=404, detail="Consultation non trouvée")
        # Sinon, c'est une autre erreur
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la consultation: {str(e)}")
    
    # Récupérer les messages de la consultation
    messages_response = supabase_admin.table("messages") \
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
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ajoute un message à une consultation existante"""
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    recommendation_data = None
    
    try:
        request_data = await request.json()
        if 'recommendation' in request_data:
            raw_recommendation = request_data['recommendation']
            
            if isinstance(raw_recommendation, str):
                try:
                    recommendation_data = json.loads(raw_recommendation)
                except json.JSONDecodeError:
                    recommendation_data = {"plant": "Format invalide", "explanation": "Données de recommandation mal formatées"}
            elif isinstance(raw_recommendation, dict):
                recommendation_data = raw_recommendation
            else:
                recommendation_data = None
    except Exception as e:
        recommendation_data = None
    message = {
        "id": message_id,
        "consultation_id": consultation_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
        "recommendation": recommendation_data
    }
    
    try:
        supabase_admin.table("messages").insert(message).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du message: {str(e)}")    
    supabase.table("consultations") \
        .update({"messages_count": consultation_response.data["messages_count"] + 1}) \
        .eq("id", consultation_id) \
        .execute()
        
    if message_data.sender == "user" and consultation_response.data["messages_count"] == 0:
        summary = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        supabase_admin.table("consultations") \
            .update({"summary": summary}) \
            .eq("id", consultation_id) \
            .execute()
    
    return message

# Routes pour les conversations unifiées
@router.post("/conversations/{conversation_id}/messages", response_model=Message)
async def add_message_to_conversation(
    conversation_id: str,
    message_data: MessageBase,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Ajoute un message à une conversation unifiée"""
    conversation_response = supabase_admin.table("conversations") \
        .select("*") \
        .eq("id", conversation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not conversation_response.data:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    recommendation_data = None
    if hasattr(message_data, 'recommendation') and message_data.recommendation:
        recommendation_data = message_data.recommendation
        
    message = {
        "id": message_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
        "recommendation": recommendation_data
    }
    
    try:
        existing_messages = conversation_response.data.get("messages", [])
        updated_messages = existing_messages + [message]        
        update_result = supabase_admin.table("conversations") \
            .update({
                "messages": updated_messages,
                "updated_at": now
            }) \
            .eq("id", conversation_id) \
            .execute()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du message: {str(e)}")
        
    existing_messages_count = len(conversation_response.data.get("messages", []))
    if message_data.sender == "user" and existing_messages_count == 0:
        summary = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        supabase_admin.table("conversations") \
            .update({"summary": summary}) \
            .eq("id", conversation_id) \
            .execute()
    
    return message

@router.delete("/consultations/{consultation_id}")
async def delete_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Supprime une consultation existante"""
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not consultation_response.data or len(consultation_response.data) == 0:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    
    try:
        supabase_admin.table("messages") \
            .delete() \
            .eq("consultation_id", consultation_id) \
            .execute()
        
        supabase_admin.table("consultations") \
            .delete() \
            .eq("id", consultation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        return {"success": True, "message": "Consultation supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de la consultation")

@router.put("/consultations/{consultation_id}", response_model=Consultation)
async def update_consultation(
    consultation_id: str,
    data: dict,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Met à jour une consultation existante"""
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
        
    update_data = {k: v for k, v in data.items() if k not in ["id", "user_id"]}
    
    update_response = supabase_admin.table("consultations") \
        .update(update_data) \
        .eq("id", consultation_id) \
        .execute()
    
    return update_response.data[0]

@router.post("/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Change le mot de passe d'un utilisateur"""
    if password_data.email != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email ne correspond pas à l'utilisateur connecté"
        )
        
    user = get_user(current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )    
    try:
        hashed_password = get_password_hash(password_data.new_password)
        
        supabase_admin.table("users") \
            .update({"hashed_password": hashed_password, "updated_at": datetime.utcnow().isoformat()}) \
            .eq("id", current_user["id"]) \
            .execute()
        
        return {"success": True, "message": "Mot de passe changé avec succès"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du mot de passe"
        )

@router.get("/users/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Récupère les informations de l'utilisateur actuellement connecté"""
    user_info = {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name"),
        "created_at": current_user["created_at"],
    }
    
    return user_info

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Supprime une conversation unifiée"""
    conversation_response = supabase_admin.table("conversations") \
        .select("*") \
        .eq("id", conversation_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not conversation_response.data or len(conversation_response.data) == 0:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    try:
        supabase_admin.table("conversations") \
            .delete() \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        return {"message": "Conversation supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
