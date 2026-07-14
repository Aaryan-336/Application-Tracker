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
    gmail_sync_enabled: Optional[bool] = False

@router.post("/connect", status_code=status.HTTP_200_OK)
def connect_gmail(
    credentials: GmailConnectIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Clean inputs (strip whitespace from email, remove spaces from App Password)
    email_addr = credentials.gmail_address.strip() if credentials.gmail_address else ""
    app_pwd = credentials.gmail_app_password.replace(" ", "").strip() if credentials.gmail_app_password else ""

    # Allow disconnect (empty credentials)
    if not email_addr and not app_pwd:
        current_user.gmail_address = None
        current_user.gmail_app_password = None
        db.commit()
        return {"message": "Gmail account disconnected."}

    # Pre-validate App Password format before hitting IMAP
    if len(app_pwd) != 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid App Password: received {len(app_pwd)} characters, expected exactly 16. "
                f"Google App Passwords are 16 lowercase letters (format: 'xxxx xxxx xxxx xxxx'). "
                f"Do NOT enter your regular Gmail password. "
                f"Generate an App Password at: https://myaccount.google.com/apppasswords"
            )
        )

    # Test IMAP connection
    is_valid, error_detail = gmail_service.test_connection(email_addr, app_pwd)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )

    # Save credentials
    current_user.gmail_address = email_addr
    current_user.gmail_app_password = app_pwd
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
        gmail_last_synced=last_synced_str,
        gmail_sync_enabled=bool(current_user.gmail_sync_enabled)
    )

@router.post("/schedule", status_code=status.HTTP_200_OK)
def toggle_gmail_schedule(
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.gmail_sync_enabled = enabled
    db.commit()
    return {"message": f"Gmail daily schedule {'enabled' if enabled else 'disabled'}."}

@router.post("/stop", status_code=status.HTTP_200_OK)
def stop_gmail_sync(current_user: User = Depends(get_current_user)):
    gmail_service.cancel_sync(current_user.id)
    return {"message": "Gmail sync stop signal dispatched."}

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
