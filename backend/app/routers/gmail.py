from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.gmail_service import gmail_service

router = APIRouter(prefix="/gmail", tags=["Gmail Sync"])

class GmailConnectIn(BaseModel):
    gmail_address: EmailStr
    gmail_app_password: str

class GmailStatusOut(BaseModel):
    is_connected: bool
    gmail_address: Optional[str] = None
    gmail_last_synced: Optional[str] = None

@router.post("/connect", status_code=status.HTTP_200_OK)
def connect_gmail(
    credentials: GmailConnectIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Test IMAP connection
    is_valid = gmail_service.test_connection(credentials.gmail_address, credentials.gmail_app_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to gmail. Please check your credentials and make sure you've enabled IMAP and generated a 16-character App Password."
        )

    # Save credentials
    current_user.gmail_address = credentials.gmail_address
    current_user.gmail_app_password = credentials.gmail_app_password
    db.commit()
    db.refresh(current_user)

    return {"message": "Gmail account connected and verified successfully."}

@router.get("/status", response_model=GmailStatusOut)
def get_gmail_status(current_user: User = Depends(get_current_user)):
    is_connected = bool(current_user.gmail_address and current_user.gmail_app_password)
    last_synced_str = current_user.gmail_last_synced.isoformat() if current_user.gmail_last_synced else None
    
    return GmailStatusOut(
        is_connected=is_connected,
        gmail_address=current_user.gmail_address,
        gmail_last_synced=last_synced_str
    )

@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_gmail(
    days_back: int = 14,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.gmail_address or not current_user.gmail_app_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail account is not connected."
        )
    
    try:
        updates = await gmail_service.sync_user_emails(db, current_user, days_back=days_back)
        return {
            "message": "Gmail sync completed successfully.",
            "updates_count": len(updates),
            "updates": updates
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during Gmail sync: {str(e)}"
        )
