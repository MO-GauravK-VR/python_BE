import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models.post import Post, PostMedia, PollOption
from app.models.user import User
from app.schemas.post import CreatePostRequest, PostTypeEnum

UPLOAD_DIR = "uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_FILE_SIZE_MB = 50


def _ensure_upload_dir():
    os.makedirs(f"{UPLOAD_DIR}/images", exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/videos", exist_ok=True)


def create_post(db: Session, post_data: CreatePostRequest, current_user: User) -> Post:
    """Create a new post (text, image, video, or poll)."""
    new_post = Post(
        post_type=post_data.post_type,
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id,
    )

    # If image/video type, attach media URLs
    if post_data.post_type in (PostTypeEnum.IMAGE, PostTypeEnum.VIDEO) and post_data.media_urls:
        for media in post_data.media_urls:
            new_post.media.append(PostMedia(
                media_type=media.media_type,
                file_url=media.file_url,
                file_name=media.file_name,
            ))

    # If poll type, add poll options
    if post_data.post_type == PostTypeEnum.POLL and post_data.poll_options:
        for option in post_data.poll_options:
            new_post.poll_options.append(PollOption(option_text=option.option_text))

    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def upload_media_to_post(
    db: Session,
    post_id: int,
    files: list[UploadFile],
    current_user: User,
) -> list[PostMedia]:
    """Upload image/video files and attach them to an existing post."""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only upload media to your own posts.")
    if post.post_type not in (PostTypeEnum.IMAGE, PostTypeEnum.VIDEO):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media upload is only allowed for image or video posts.")

    _ensure_upload_dir()
    saved_media: list[PostMedia] = []

    for file in files:
        # Determine media type
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

        # Generate unique filename
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = f"{UPLOAD_DIR}/{sub_dir}/{unique_name}"

        # Save file to disk
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Create DB record
        media_record = PostMedia(
            post_id=post.id,
            media_type=media_type,
            file_url=f"/{file_path}",
            file_name=file.filename,
        )
        db.add(media_record)
        saved_media.append(media_record)

    db.commit()
    for m in saved_media:
        db.refresh(m)

    return saved_media


def get_all_posts(db: Session, skip: int = 0, limit: int = 20) -> list[Post]:
    """Fetch all posts, newest first, with pagination."""
    return (
        db.query(Post)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def vote_on_poll(db: Session, post_id: int, option_id: int, current_user: User) -> PollOption:
    """Increment the vote count on a poll option."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.post_type != PostTypeEnum.POLL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This post is not a poll.")

    option = db.query(PollOption).filter(
        PollOption.id == option_id, PollOption.post_id == post_id
    ).first()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll option not found.")

    option.vote_count += 1
    db.commit()
    db.refresh(option)
    return option
