from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from auth import get_current_active_user
from supabase_client import supabase_admin

# Configurer le logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("conversation_routes")

router = APIRouter(prefix="/api")

# Modèles Pydantic pour la validation des données
class Message(BaseModel):
    content: str
    sender: str
    timestamp: Optional[str] = None
    recommendation: Optional[dict] = None
    id: Optional[str] = None

class ConversationCreate(BaseModel):
    title: str
    type: Optional[str] = "mixed"
    summary: Optional[str] = None
    messages: List[Message]
    messages_count: Optional[int] = None
    chat_mode: Optional[str] = "discussion"
    last_recommendation: Optional[dict] = None

class Conversation(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    title: str
    type: Optional[str] = "mixed"
    summary: Optional[str] = None
    messages: List[Message]
    messages_count: Optional[int] = None
    chat_mode: Optional[str] = "discussion"
    last_recommendation: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Routes pour les conversations unifiées
@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation: ConversationCreate, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Crée une nouvelle conversation unifiée
    """
    logger.info(f"Création d'une nouvelle conversation par l'utilisateur {current_user['id']}")
    
    # Vérifier que l'utilisateur existe dans la base de données
    try:
        user_check = supabase_admin.table("users").select("id").eq("id", current_user["id"]).execute()
        if not user_check.data or len(user_check.data) == 0:
            logger.error(f"Utilisateur {current_user['id']} non trouvé dans la table users")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé. Veuillez vous reconnecter."
            )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification de l'utilisateur"
        )
    
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Calculer le nombre de messages si non fourni
    messages_count = conversation.messages_count or len(conversation.messages)
    
    # Préparer les données de la conversation
    conversation_data = {
        "id": conversation_id,
        "user_id": current_user["id"],
        "title": conversation.title,
        "type": conversation.type or "mixed",
        "summary": conversation.summary,
        "messages": [m.dict() for m in conversation.messages],
        "messages_count": messages_count,
        "chat_mode": conversation.chat_mode or "discussion",
        "last_recommendation": conversation.last_recommendation,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        logger.debug(f"Insertion de la conversation {conversation_id} dans Supabase")
        result = supabase_admin.table("conversations").insert(conversation_data).execute()
        logger.info(f"Conversation {conversation_id} créée avec succès")
        return Conversation(**conversation_data)
    except Exception as e:
        logger.error(f"Erreur lors de la création de la conversation: {e}")
        # Analyser l'erreur pour donner un message plus spécifique
        error_message = str(e)
        if "foreign key constraint" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur de données utilisateur. Veuillez vous reconnecter."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la conversation: {error_message}"
            )

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(current_user: dict = Depends(get_current_active_user)):
    """
    Récupère toutes les conversations unifiées de l'utilisateur
    """
    logger.info(f"Récupération des conversations pour l'utilisateur {current_user['id']}")
    
    try:
        response = supabase_admin.table("conversations") \
            .select("*") \
            .eq("user_id", current_user["id"]) \
            .order("updated_at", desc=True) \
            .execute()
        
        logger.info(f"Récupération réussie: {len(response.data)} conversations trouvées")
        return response.data
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Récupère une conversation unifiée spécifique
    """
    logger.info(f"Récupération de la conversation {conversation_id} pour l'utilisateur {current_user['id']}")
    
    try:
        response = supabase_admin.table("conversations") \
            .select("*") \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Conversation {conversation_id} non trouvée")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        conversation_data = response.data[0]
        logger.info(f"Conversation {conversation_id} récupérée avec succès")
        return conversation_data
    except HTTPException:
        # Re-lever les HTTPException telles quelles
        raise
    except Exception as e:
        # Si c'est une APIError de Supabase liée à l'absence de résultats
        if "no rows returned" in str(e) or "PGRST116" in str(e):
            logger.warning(f"Conversation {conversation_id} non trouvée")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        logger.error(f"Erreur lors de la récupération de la conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération de la conversation: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages", response_model=Conversation)
async def get_conversation_with_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Récupère une conversation unifiée spécifique avec tous ses messages
    Cette route est utilisée par le frontend pour restaurer une conversation complète
    """
    logger.info(f"Récupération complète de la conversation {conversation_id} pour l'utilisateur {current_user['id']}")
    
    try:
        response = supabase_admin.table("conversations") \
            .select("*") \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Conversation {conversation_id} non trouvée")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        conversation_data = response.data[0]
        
        # Les messages sont déjà stockés dans la colonne messages (JSONB)
        # On s'assure juste qu'ils sont bien présents
        if not conversation_data.get("messages"):
            conversation_data["messages"] = []
        
        logger.info(f"Conversation {conversation_id} récupérée avec succès avec {len(conversation_data.get('messages', []))} messages")
        return conversation_data
        
    except HTTPException:
        # Re-lever les HTTPException telles quelles
        raise
    except Exception as e:
        # Si c'est une APIError de Supabase liée à l'absence de résultats
        if "no rows returned" in str(e) or "PGRST116" in str(e):
            logger.warning(f"Conversation {conversation_id} non trouvée")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        logger.error(f"Erreur lors de la récupération complète de la conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération de la conversation: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Supprime une conversation unifiée
    """
    logger.info(f"Suppression de la conversation {conversation_id} par l'utilisateur {current_user['id']}")
    
    try:
        response = supabase_admin.table("conversations") \
            .select("*") \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Conversation {conversation_id} non trouvée lors de la tentative de suppression")
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        supabase_admin.table("conversations") \
            .delete() \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        logger.info(f"Conversation {conversation_id} supprimée avec succès")
        return {"success": True, "message": "Conversation supprimée avec succès"}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        logger.error(f"Erreur lors de la suppression de la conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la conversation: {str(e)}"
        )
