from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import ProfileUpdateRequest, ProfileResponse, UserResponse
from app.services.user_service import update_profile

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return ProfileResponse(
        message="Profile fetched successfully.",
        user=current_user,
    )


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    update_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current authenticated user's profile."""
    updated_user = update_profile(db=db, current_user=current_user, update_data=update_data)
    return ProfileResponse(
        message="Profile updated successfully.",
        user=updated_user,
    )
