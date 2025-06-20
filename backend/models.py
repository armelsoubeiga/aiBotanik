from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

class MessageBase(BaseModel):
    content: str
    sender: Literal["user", "bot"]
    
class MessageCreate(MessageBase):
    consultation_id: str

class Message(MessageBase):
    id: str
    timestamp: datetime
    recommendation: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ConsultationBase(BaseModel):
    title: Optional[str] = Field(None, description="Titre de la consultation, généré automatiquement si absent")
    type: Literal["discussion", "consultation"] = Field(default="discussion", description="Type de la consultation (discussion ou consultation)")
    
    class Config:
        extra = "forbid"  # Interdit les champs supplémentaires non définis
        
class ConsultationCreate(ConsultationBase):
    messages: Optional[List[MessageBase]] = Field(
        default_factory=list,  # Factory function pour éviter mutable default
        description="Liste des messages initiaux de la consultation"
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
    user_id: str = Field(..., description="Identifiant de l'utilisateur propriétaire")
    date: datetime = Field(default_factory=lambda: datetime.utcnow(), description="Date de création de la consultation")
    summary: Optional[str] = Field(None, description="Résumé de la consultation")
    messages_count: int = Field(default=0, description="Nombre de messages dans la consultation")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()  # Assurer un encodage JSON cohérent des dates
        }

class ConsultationWithMessages(Consultation):
    messages: List[Message] = []
