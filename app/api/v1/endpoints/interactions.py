from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.interaction import (
    LikeToggleResponse,
    CreateCommentRequest,
    CommentCreateResponse,
    CommentListResponse,
    CommentResponse,
    CommentAuthor,
)
from app.services.interaction_service import (
    toggle_like,
    create_comment,
    get_comments_for_post,
    delete_comment,
)

router = APIRouter()


# ---------- LIKE ---------- #

@router.post("/{post_id}/like/", response_model=LikeToggleResponse)
def like_or_unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = toggle_like(db, post_id, current_user)
    message = "Post liked." if result["liked"] else "Post unliked."
    return LikeToggleResponse(
        message=message,
        liked=result["liked"],
        like_count=result["like_count"],
    )


# ---------- COMMENT ---------- #

def _build_comment_response(comment) -> CommentResponse:
    """Recursively build a CommentResponse with nested replies."""
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        user=CommentAuthor(
            id=comment.user.id,
            full_name=comment.user.full_name,
            email=comment.user.email,
        ),
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=[_build_comment_response(r) for r in comment.replies],
    )


@router.post("/{post_id}/comments/", response_model=CommentCreateResponse)
def add_comment(
    post_id: int,
    payload: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = create_comment(db, post_id, payload.content, current_user, payload.parent_id)
    return CommentCreateResponse(
        message="Comment added.",
        comment=_build_comment_response(comment),
    )


@router.get("/{post_id}/comments/", response_model=CommentListResponse)
def list_comments(
    post_id: int,
    db: Session = Depends(get_db),
):
    comments = get_comments_for_post(db, post_id)
    return CommentListResponse(
        message="Comments fetched successfully.",
        count=len(comments),
        comments=[_build_comment_response(c) for c in comments],
    )


@router.delete("/comments/{comment_id}/")
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_comment(db, comment_id, current_user)
    return {"message": "Comment deleted."}
