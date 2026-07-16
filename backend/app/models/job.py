import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    source = Column(String, nullable=False)  # e.g., 'LinkedIn', 'Indeed'
    seniority_level = Column(String, nullable=True)  # 'entry', 'mid', 'senior'
    posted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_jobs = relationship("UserJob", back_populates="job", cascade="all, delete-orphan")
