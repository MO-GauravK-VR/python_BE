import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


def _ensure_upload_dir():
    os.makedirs(f"{UPLOAD_DIR}/images", exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/videos", exist_ok=True)


def save_uploaded_file(file: UploadFile) -> dict:
    """Save a single file to disk and return its metadata."""
    _ensure_upload_dir()

    if file.content_type in ALLOWED_IMAGE_TYPES:
        media_type = "image"
        sub_dir = "images"
    elif file.content_type in ALLOWED_VIDEO_TYPES:
        media_type = "video"
        sub_dir = "videos"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, GIF, WebP, MP4, WebM, MOV.",
        )

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = f"{UPLOAD_DIR}/{sub_dir}/{unique_name}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "media_type": media_type,
        "file_url": f"/uploads/{sub_dir}/{unique_name}",
        "file_name": file.filename,
    }
