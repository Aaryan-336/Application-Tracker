from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserJobUpdate(BaseModel):
    status: Optional[str] = None  # e.g., 'discovered', 'saved', 'applied', 'assessment', 'interview', 'offer', 'rejected', 'ignored'
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
