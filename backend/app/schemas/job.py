from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobMatchResponse(BaseModel):
    id: UUID  # user_job.id
    job_id: UUID
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    match_score: int
    match_rationale: Optional[str] = None
    missing_skills: Optional[List[str]] = None
    matching_skills: Optional[List[str]] = None
    status: str
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
