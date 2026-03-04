from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.post import (
    CreatePostRequest,
    PostCreateResponse,
    PostListResponse,
    MediaUploadResponse,
    PollOptionResponse,
)
from app.services.post_service import create_post, get_all_posts, upload_media_to_post, vote_on_poll

router = APIRouter()


@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_post(
    post_data: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new post. Requires authentication.

    **post_type** options:
    - `text`  — plain text post (provide `title` and/or `content`)
    - `image` — image post (create first, then upload files via `/posts/{id}/media`)
    - `video` — video post (create first, then upload files via `/posts/{id}/media`)
    - `poll`  — poll post (provide `poll_options` with 2–10 choices)
    """
    post = create_post(db=db, post_data=post_data, current_user=current_user)
    return PostCreateResponse(
        message="Post created successfully.",
        post=post,
    )


@router.post("/{post_id}/media", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_post_media(
    post_id: int,
    files: list[UploadFile] = File(..., description="Image or video files to attach"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload images/videos to an existing image or video post.
    Allowed types: JPEG, PNG, GIF, WebP, MP4, WebM, MOV.
    """
    media = upload_media_to_post(db=db, post_id=post_id, files=files, current_user=current_user)
    return MediaUploadResponse(
        message=f"{len(media)} file(s) uploaded successfully.",
        media=media,
    )


@router.post("/{post_id}/poll/{option_id}/vote", response_model=PollOptionResponse)
async def vote_poll_option(
    post_id: int,
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Vote on a poll option. Requires authentication."""
    option = vote_on_poll(db=db, post_id=post_id, option_id=option_id, current_user=current_user)
    return option


@router.get("/", response_model=PostListResponse)
async def list_posts(
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max posts to return"),
    db: Session = Depends(get_db),
):
    """List all posts (newest first). Public — no auth required."""
    posts = get_all_posts(db=db, skip=skip, limit=limit)
    return PostListResponse(
        message="Posts fetched successfully.",
        count=len(posts),
        posts=posts,
    )
