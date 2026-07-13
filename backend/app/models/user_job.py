import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class UserJob(Base):
    __tablename__ = "user_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    match_score = Column(Integer, nullable=False)
    match_rationale = Column(Text, nullable=True)
    missing_skills = Column(JSON, nullable=True)  # List of strings
    matching_skills = Column(JSON, nullable=True)  # List of strings
    status = Column(String, default="discovered")  # e.g., 'discovered', 'saved', 'applied', 'assessment', 'interview', 'offer', 'rejected', 'ignored'
    applied_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_jobs")
    job = relationship("Job", back_populates="user_jobs")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job"),
    )
