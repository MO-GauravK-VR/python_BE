from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import engine, Base
from app.models import user  # noqa: F401 — ensure models are registered
from app.models import post  # noqa: F401
from app.models import interaction  # noqa: F401
import os

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for ICT Community Application",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned API routes
app.include_router(api_router, prefix="/api/v1")

# Serve uploaded files at /uploads/...
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
