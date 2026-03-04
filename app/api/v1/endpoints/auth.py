from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserSignUpRequest, SignUpResponse, LoginRequest, LoginResponse
from app.services.user_service import create_user, authenticate_user

router = APIRouter()


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(user_data: UserSignUpRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    user = create_user(db=db, user_data=user_data)
    return SignUpResponse(
        message="User registered successfully.",
        user=user,
    )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password. Returns a JWT access token."""
    result = authenticate_user(db=db, login_data=login_data)
    return LoginResponse(
        message="Login successful.",
        access_token=result["access_token"],
        user=result["user"],
    )
