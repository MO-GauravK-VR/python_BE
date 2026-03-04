from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, profile, posts

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
