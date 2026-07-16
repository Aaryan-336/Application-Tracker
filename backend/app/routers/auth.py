from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.utils.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_pw = get_password_hash(user_in.password)
    
    # Create user
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        preferred_roles=[],
        preferred_locations=[]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name
    if profile_in.preferred_roles is not None:
        current_user.preferred_roles = profile_in.preferred_roles
    if profile_in.preferred_locations is not None:
        current_user.preferred_locations = profile_in.preferred_locations
    if profile_in.salary_expectation is not None:
        current_user.salary_expectation = profile_in.salary_expectation
    if profile_in.experience_level is not None:
        current_user.experience_level = profile_in.experience_level
    if profile_in.apify_api_token is not None:
        current_user.apify_api_token = profile_in.apify_api_token
    if profile_in.jsearch_api_key is not None:
        current_user.jsearch_api_key = profile_in.jsearch_api_key
    if profile_in.adzuna_app_id is not None:
        current_user.adzuna_app_id = profile_in.adzuna_app_id
    if profile_in.adzuna_app_key is not None:
        current_user.adzuna_app_key = profile_in.adzuna_app_key
    if profile_in.groq_api_key is not None:
        current_user.groq_api_key = profile_in.groq_api_key
    if profile_in.gmail_sync_enabled is not None:
        current_user.gmail_sync_enabled = profile_in.gmail_sync_enabled
    
    db.commit()
    db.refresh(current_user)
    return current_user
