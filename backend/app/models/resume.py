import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    parsed_text = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)  # List of strings
    experience = Column(JSON, nullable=True)  # List of dicts/roles
    education = Column(JSON, nullable=True)  # List of dicts/degrees
    preferred_roles = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
