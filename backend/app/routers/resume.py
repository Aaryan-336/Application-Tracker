import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.utils.auth import get_current_user
from app.config import settings
from app.services.parser_service import parser_service

router = APIRouter(prefix="/resume", tags=["Resumes"])

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resume files are supported in Phase 1."
        )

    # Generate local path
    file_id = uuid.uuid4()
    filename = f"{current_user.id}_{file_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        # Save file locally
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        # Extract text from PDF
        text = parser_service.extract_text_from_pdf(file_path)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume PDF contains no extractable text."
            )
        
        # Parse using Groq
        parsed_profile = parser_service.parse_resume_text(text)
        
        # Save resume to database
        new_resume = Resume(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            parsed_text=text,
            skills=parsed_profile.get("skills", []),
            experience=parsed_profile.get("experience", []),
            education=parsed_profile.get("education", []),
            preferred_roles=parsed_profile.get("preferred_roles", [])
        )
        
        # Update user's profile with preferred roles if user doesn't have any set
        if not current_user.preferred_roles and parsed_profile.get("preferred_roles"):
            current_user.preferred_roles = parsed_profile.get("preferred_roles")
        
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume

    except Exception as e:
        print(f"Error handling resume upload: {e}")
        # Clean up file if saved and failed in subsequent steps
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume processing: {str(e)}"
        )

@router.get("/me", response_model=ResumeResponse)
def get_my_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch most recent resume
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please upload one to build your profile."
        )
    return resume
