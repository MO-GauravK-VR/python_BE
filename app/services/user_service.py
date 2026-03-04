from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserSignUpRequest, LoginRequest, ProfileUpdateRequest
from app.core.security import hash_password, verify_password, create_access_token


def create_user(db: Session, user_data: UserSignUpRequest) -> User:
    """Register a new user after checking for duplicate email."""

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        phone=user_data.phone,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, login_data: LoginRequest) -> dict:
    """Authenticate user by email & password and return user + JWT token."""

    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return {"user": user, "access_token": access_token}


def update_profile(db: Session, current_user: User, update_data: ProfileUpdateRequest) -> User:
    """Update the current user's profile fields."""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.phone is not None:
        current_user.phone = update_data.phone

    db.commit()
    db.refresh(current_user)
    return current_user
