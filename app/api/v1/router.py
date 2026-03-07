from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, profile, posts, media, interactions, chat

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(interactions.router, prefix="/posts", tags=["Likes & Comments"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat Room"])
