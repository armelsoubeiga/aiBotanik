from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, TypeVar, Generic
from pydantic import create_model
import uuid
import logging

from auth import (
    User, UserCreate, UserLogin, Token, PasswordChange,
    get_password_hash, authenticate_user, create_access_token, get_current_active_user, get_user
)
from models import Consultation, ConsultationCreate, ConsultationWithMessages, Message, MessageCreate, MessageBase
from supabase_client import supabase, supabase_admin, safe_get_user_by_email

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
    existing_user = supabase_admin.table("users").select("*").eq("email", user_data.email).execute()
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
    
    # Insérer le nouvel utilisateur avec le client admin (nécessite des privilèges élevés)
    supabase_admin.table("users").insert(user_dict).execute()
    
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
    supabase_admin.table("sessions").insert(session_data).execute()
    
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
    supabase_admin.table("sessions").insert(session_data).execute()
    
    return {"access_token": access_token, "token_type": "bearer"}

# Route pour valider le token d'authentification
@router.get("/auth/validate")
async def validate_token(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Route pour valider qu'un token est toujours valide
    """
    return {"valid": True}

# Routes pour les consultations
@router.get("/consultations", response_model=List[Consultation])
async def get_consultations(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Récupère toutes les consultations de l'utilisateur
    """
    response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("date", desc=True) \
        .execute()
    return response.data

@router.post("/consultations", response_model=Consultation, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    request: Request,  # Ajouter la requête brute
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Crée une nouvelle consultation
    """
    import logging
    from fastapi.exceptions import RequestValidationError
    import json
    
    # Configurer le logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("consultation_route")
    
    # Log de la requête brute
    try:
        # Lire le corps brut de la requête
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        logger.debug(f"Corps brut de la requête: {body_str}")
        
        # Parser le JSON
        try:
            body_dict = json.loads(body_str)
            logger.debug(f"Dictionnaire parsé: {body_dict}")
            logger.debug(f"Types des champs: {[(k, type(v)) for k, v in body_dict.items()]}")
            
            # Valider avec Pydantic manuellement
            try:
                data = ConsultationCreate(**body_dict)
                logger.debug(f"Validation Pydantic réussie: {data.dict()}")
            except Exception as validation_error:
                logger.error(f"Erreur de validation Pydantic: {validation_error}")
                raise RequestValidationError(errors=[{
                    "loc": ["body"],
                    "msg": f"Erreur de validation: {str(validation_error)}",
                    "type": "value_error"
                }])
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}")
            raise RequestValidationError(errors=[{
                "loc": ["body"],
                "msg": f"JSON invalide: {str(e)}",
                "type": "json_invalid"
            }])
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la requête: {e}")
        raise HTTPException(status_code=400, detail=f"Erreur de lecture de la requête: {str(e)}")
    
    consultation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Si le titre n'est pas fourni, générer un titre par défaut
    title = data.title if data.title else f"Consultation du {datetime.utcnow().strftime('%d %B %Y')}"
    
    logger.debug(f"Titre de consultation résolu: {title}")
    logger.debug(f"Type de consultation: {data.type}")
    logger.debug(f"Nombre de messages: {len(data.messages) if data.messages else 0}")
      # Créer la consultation avec gestion d'erreurs
    try:
        consultation_data = {
            "id": consultation_id,
            "user_id": current_user["id"],
            "title": title,
            "type": data.type,  # Utiliser le type fourni (discussion ou consultation)
            "date": now,
            "messages_count": len(data.messages) if data.messages else 0,
            "summary": None  # Sera mis à jour après l'ajout des messages
        }
        
        logger.debug(f"Données de consultation à insérer: {consultation_data}")
        
        # Insérer la consultation dans Supabase
        try:
            supabase_admin.table("consultations").insert(consultation_data).execute()
            logger.debug(f"Consultation créée avec l'ID: {consultation_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la consultation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Erreur lors de la création de la consultation: {str(e)}"
            )
        
        # Si des messages sont fournis, les ajouter
        if data.messages and len(data.messages) > 0:
            logger.debug(f"Ajout de {len(data.messages)} messages")
            
            for idx, msg in enumerate(data.messages):
                try:
                    message_data = {
                        "id": str(uuid.uuid4()),
                        "consultation_id": consultation_id,
                        "content": msg.content,
                        "sender": msg.sender,
                        "timestamp": now,
                        "recommendation": None  # Champ ajouté pour correspondre au schéma
                    }
                    
                    logger.debug(f"Insertion du message {idx+1}: {message_data}")
                    supabase_admin.table("messages").insert(message_data).execute()
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout du message {idx+1}: {e}")
                    # On continue malgré l'erreur pour les messages
            
            # Mettre à jour le résumé avec le premier message utilisateur
            first_user_message = next((msg for msg in data.messages if msg.sender == "user"), None)
            if first_user_message:
                summary = first_user_message.content[:100] + "..." if len(first_user_message.content) > 100 else first_user_message.content
                logger.debug(f"Mise à jour du résumé: {summary}")
                
                try:
                    supabase_admin.table("consultations").update({"summary": summary}).eq("id", consultation_id).execute()
                    consultation_data["summary"] = summary
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour du résumé: {e}")
        
        return consultation_data
        
    except Exception as e:
        logger.error(f"Erreur non gérée lors de la création de la consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur est survenue lors de la création de la consultation: {str(e)}"
        )

@router.get("/consultations/{consultation_id}", response_model=ConsultationWithMessages)
async def get_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Récupère une consultation spécifique avec ses messages
    """
    try:
        # Récupérer la consultation
        consultation_response = supabase_admin.table("consultations") \
            .select("*") \
            .eq("id", consultation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        # Vérifier si la consultation existe
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
    """
    Ajoute un message à une consultation existante
    """
    import json# Vérifier que la consultation existe et appartient à l'utilisateur
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
      # Créer le message avec gestion améliorée de la recommandation
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Vérifier si la requête contient une recommandation (peut être dans le body)
    recommendation_data = None
    
    try:
        # La recommandation peut être présente dans le corps de la requête
        request_data = await request.json()
        if 'recommendation' in request_data:
            raw_recommendation = request_data['recommendation']
            
            # Si c'est une chaîne, essayer de la parser
            if isinstance(raw_recommendation, str):
                try:
                    recommendation_data = json.loads(raw_recommendation)
                    print(f"Recommandation désérialisée depuis une chaîne JSON: {recommendation_data.get('plant', 'unknown')}")
                except json.JSONDecodeError:
                    print(f"Recommandation reçue sous forme de chaîne, mais pas au format JSON valide")
                    recommendation_data = {"plant": "Format invalide", "explanation": "Données de recommandation mal formatées"}
            # Si c'est déjà un objet (dict), l'utiliser directement
            elif isinstance(raw_recommendation, dict):
                recommendation_data = raw_recommendation
                print(f"Recommandation reçue sous forme d'objet: {recommendation_data.get('plant', 'unknown')}")
            else:
                print(f"Format de recommandation non géré: {type(raw_recommendation)}")
                recommendation_data = None
    except Exception as e:
        print(f"Erreur lors du traitement de la recommandation: {e}")
        recommendation_data = None
    
    # Créer le message final
    message = {
        "id": message_id,
        "consultation_id": consultation_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
        "recommendation": recommendation_data  # Utiliser la recommandation traitée
    }
    
    # Insérer le message dans la base
    try:
        supabase_admin.table("messages").insert(message).execute()
        print(f"Message inséré avec succès: {message_id}")
    except Exception as e:
        print(f"Erreur lors de l'insertion du message: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du message: {str(e)}")
    
    # Mettre à jour le nombre de messages dans la consultation
    supabase.table("consultations") \
        .update({"messages_count": consultation_response.data["messages_count"] + 1}) \
        .eq("id", consultation_id) \
        .execute()
      # Si c'est le premier message utilisateur, mettre à jour le résumé
    if message_data.sender == "user" and consultation_response.data["messages_count"] == 0:
        summary = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        supabase_admin.table("consultations") \
            .update({"summary": summary}) \
            .eq("id", consultation_id) \
            .execute()
    
    return message

# Routes pour les conversations unifiées (système unifié)
@router.post("/conversations/{conversation_id}/messages", response_model=Message)
async def add_message_to_conversation(
    conversation_id: str,
    message_data: MessageBase,  # Utiliser MessageBase au lieu de MessageCreate
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Ajoute un message à une conversation unifiée (table conversations)
    """
    import json
    
    print(f"Ajout d'un message à la conversation unifiée {conversation_id}")
    print(f"Données du message reçues: {message_data.dict()}")
    
    # Vérifier que la conversation existe et appartient à l'utilisateur
    conversation_response = supabase_admin.table("conversations") \
        .select("*") \
        .eq("id", conversation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not conversation_response.data:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Créer le message avec gestion de la recommandation
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Récupérer la recommandation depuis message_data si elle existe
    recommendation_data = None
    if hasattr(message_data, 'recommendation') and message_data.recommendation:
        recommendation_data = message_data.recommendation
        print(f"Recommandation trouvée: {recommendation_data}")
    else:
        print("Aucune recommandation dans les données du message")      # Créer le message final
    message = {
        "id": message_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
        "recommendation": recommendation_data  # Utiliser la recommandation traitée
    }
    
    # Pour les conversations unifiées, les messages sont stockés dans un champ JSON
    # Il faut récupérer les messages existants et ajouter le nouveau
    try:
        existing_messages = conversation_response.data.get("messages", [])
        print(f"Messages existants dans la conversation: {len(existing_messages)}")
        
        # Ajouter le nouveau message à la liste
        updated_messages = existing_messages + [message]
          # Mettre à jour la conversation avec la nouvelle liste de messages
        # Note: Utiliser seulement les colonnes qui existent dans la table
        update_result = supabase_admin.table("conversations") \
            .update({
                "messages": updated_messages,
                "updated_at": now
            }) \
            .eq("id", conversation_id) \
            .execute()
        
        print(f"Message ajouté avec succès à la conversation unifiée: {message_id}")
        print(f"Conversation maintenant avec {len(updated_messages)} messages")
        
    except Exception as e:
        print(f"Erreur lors de l'ajout du message à la conversation unifiée: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du message: {str(e)}")
      # Mettre à jour le résumé si c'est le premier message utilisateur
    existing_messages_count = len(conversation_response.data.get("messages", []))
    if message_data.sender == "user" and existing_messages_count == 0:
        summary = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        supabase_admin.table("conversations") \
            .update({"summary": summary}) \
            .eq("id", conversation_id) \
            .execute()
        print(f"Résumé de la conversation mis à jour: {summary}")
    
    return message

@router.delete("/consultations/{consultation_id}")
async def delete_consultation(
    consultation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Supprime une consultation existante
    """
    # Vérifier que la consultation existe et appartient à l'utilisateur
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not consultation_response.data or len(consultation_response.data) == 0:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    
    try:
        # Supprimer d'abord les messages associés
        supabase_admin.table("messages") \
            .delete() \
            .eq("consultation_id", consultation_id) \
            .execute()
        
        # Puis supprimer la consultation
        supabase_admin.table("consultations") \
            .delete() \
            .eq("id", consultation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        return {"success": True, "message": "Consultation supprimée avec succès"}
    except Exception as e:
        logging.error(f"Erreur lors de la suppression de la consultation {consultation_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de la consultation")

@router.put("/consultations/{consultation_id}", response_model=Consultation)
async def update_consultation(
    consultation_id: str,
    data: dict,  # Utiliser un dict au lieu de Partial[Consultation]
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Met à jour une consultation existante
    """
    # Vérifier que la consultation existe et appartient à l'utilisateur
    consultation_response = supabase_admin.table("consultations") \
        .select("*") \
        .eq("id", consultation_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()
    
    if not consultation_response.data:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
      # Filtrer les champs modifiables
    update_data = {k: v for k, v in data.items() if k not in ["id", "user_id"]}
    
    # Mise à jour dans Supabase
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
    """
    Change le mot de passe d'un utilisateur
    """
    # Vérifier que l'email correspond à l'utilisateur connecté
    if password_data.email != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email ne correspond pas à l'utilisateur connecté"
        )
      # La vérification du mot de passe actuel n'est plus requise
    user = get_user(current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Mettre à jour le mot de passe
    try:
        # Hacher le nouveau mot de passe
        hashed_password = get_password_hash(password_data.new_password)
        
        # Mettre à jour dans Supabase
        supabase_admin.table("users") \
            .update({"hashed_password": hashed_password, "updated_at": datetime.utcnow().isoformat()}) \
            .eq("id", current_user["id"]) \
            .execute()
        
        return {"success": True, "message": "Mot de passe changé avec succès"}
    except Exception as e:
        logging.error(f"Erreur lors du changement de mot de passe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du mot de passe"
        )

@router.get("/users/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Récupère les informations de l'utilisateur actuellement connecté
    """
    # Filtrer les données sensibles
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
    """
    Supprime une conversation unifiée
    """
    print(f"Suppression de la conversation unifiée {conversation_id}")
    
    # Vérifier que la conversation existe et appartient à l'utilisateur
    conversation_response = supabase_admin.table("conversations") \
        .select("*") \
        .eq("id", conversation_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not conversation_response.data or len(conversation_response.data) == 0:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    try:
        # Supprimer la conversation
        supabase_admin.table("conversations") \
            .delete() \
            .eq("id", conversation_id) \
            .eq("user_id", current_user["id"]) \
            .execute()
        
        print(f"Conversation unifiée {conversation_id} supprimée avec succès")
        return {"message": "Conversation supprimée avec succès"}
    except Exception as e:
        print(f"Erreur lors de la suppression de la conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
