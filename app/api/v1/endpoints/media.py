from fastapi import APIRouter, Depends, UploadFile, File, status
from app.core.deps import get_current_user
from app.models.user import User
from app.services.media_service import save_uploaded_file
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class FileUploadResult(BaseModel):
    media_type: str
    file_url: str
    file_name: Optional[str] = None


class UploadResponse(BaseModel):
    message: str
    files: list[FileUploadResult]


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    files: list[UploadFile] = File(..., description="Image or video files to upload"),
    current_user: User = Depends(get_current_user),
):
    """
    Upload one or more image/video files. Returns URLs that can be used
    when creating a post.

    Allowed types: JPEG, PNG, GIF, WebP, MP4, WebM, MOV.
    """
    results = [save_uploaded_file(file) for file in files]
    return UploadResponse(
        message=f"{len(results)} file(s) uploaded successfully.",
        files=results,
    )
