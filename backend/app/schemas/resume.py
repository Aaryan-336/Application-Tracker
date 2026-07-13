from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    skills: Optional[List[str]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    preferred_roles: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True
