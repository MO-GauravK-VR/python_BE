from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import (
    UserSignUpRequest, SignUpResponse,
    LoginRequest, LoginResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
)
from app.services.user_service import create_user, authenticate_user, forgot_password, reset_password

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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password_endpoint(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset token.
    In production, the token would be sent via email.
    For now, it is returned in the response for testing.
    """
    reset_token = forgot_password(db=db, email=data.email)
    return ForgotPasswordResponse(
        message="Password reset token generated. Use it to reset your password.",
        reset_token=reset_token,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_endpoint(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset password using the token from forgot-password."""
    reset_password(db=db, token=data.reset_token, new_password=data.new_password)
    return ResetPasswordResponse(
        message="Password reset successfully. You can now login with your new password.",
    )
