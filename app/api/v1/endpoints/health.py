from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {
        "status": "healthy",
        "message": "ICT Community API is up and running 🚀"
    }
