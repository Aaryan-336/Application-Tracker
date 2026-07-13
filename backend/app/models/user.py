import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    preferred_roles = Column(JSON, nullable=True)  # List of strings
    preferred_locations = Column(JSON, nullable=True)  # List of strings
    salary_expectation = Column(Integer, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    gmail_address = Column(String, nullable=True)
    gmail_app_password = Column(String, nullable=True)
    gmail_last_synced = Column(DateTime, nullable=True)
    experience_level = Column(String, nullable=True)
    apify_api_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    user_jobs = relationship("UserJob", back_populates="user", cascade="all, delete-orphan")
