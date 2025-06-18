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
    
class ConsultationCreate(ConsultationBase):
    messages: Optional[List[MessageBase]] = []

class Consultation(ConsultationBase):
    id: str
    user_id: str
    date: datetime
    summary: Optional[str] = None
    messages_count: int = 0
    
    class Config:
        from_attributes = True

class ConsultationWithMessages(Consultation):
    messages: List[Message] = []
