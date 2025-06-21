import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    content: str
    sender: Literal["user", "bot"]
    recommendation: Optional[Dict[str, Any]] = None
    
class MessageCreate(MessageBase):
    consultation_id: str

class Message(MessageBase):
    id: str
    timestamp: datetime
    recommendation: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ConsultationBase(BaseModel):
    title: Optional[str] = Field(None, description="Titre de la consultation")
    type: Literal["discussion", "consultation"] = Field(default="discussion", description="Type de consultation")
    
    class Config:
        extra = "forbid"
        
class ConsultationCreate(ConsultationBase):
    messages: Optional[List[MessageBase]] = Field(
        default_factory=list,
        description="Messages initiaux de la consultation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Consultation pour plante médicinale",
                "type": "consultation",
                "messages": [
                    {"content": "Bonjour, j'ai besoin de conseils pour une plante.", "sender": "user"},
                    {"content": "Je vous écoute, quelle est votre question ?", "sender": "bot"}
                ]
            }
        }

class Consultation(ConsultationBase):
    id: str = Field(..., description="Identifiant unique de la consultation")
    user_id: str = Field(..., description="Identifiant de l'utilisateur")
    date: datetime = Field(default_factory=lambda: datetime.utcnow(), description="Date de création")
    summary: Optional[str] = Field(None, description="Résumé de la consultation")
    messages_count: int = Field(default=0, description="Nombre de messages")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ConsultationWithMessages(Consultation):
    messages: List[Message] = []

class ConversationMessageCreate(MessageBase):
    pass

class ConversationWithMessages(BaseModel):
    id: str
    title: str
    user_id: str
    chat_mode: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    summary: Optional[str] = None
    messages: List[Message] = []
    
    class Config:
        from_attributes = True
