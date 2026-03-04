from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.interaction import Like, Comment
from app.models.post import Post
from app.models.user import User


def toggle_like(db: Session, post_id: int, current_user: User) -> dict:
    """Like or unlike a post. Returns the new state and total count."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id,
    ).first()

    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        liked = False
    else:
        # Like
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        db.commit()
        liked = True

    like_count = db.query(Like).filter(Like.post_id == post_id).count()
    return {"liked": liked, "like_count": like_count}


def create_comment(db: Session, post_id: int, content: str, current_user: User, parent_id: int | None = None) -> Comment:
    """Add a comment (or reply) to a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    if parent_id:
        parent_comment = db.query(Comment).filter(
            Comment.id == parent_id,
            Comment.post_id == post_id,
        ).first()
        if not parent_comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found on this post.")

    new_comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id,
        parent_id=parent_id,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def get_comments_for_post(db: Session, post_id: int) -> list[Comment]:
    """Get all top-level comments for a post (replies are nested via relationship)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    return (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .all()
    )


def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    """Delete a comment (only by its author)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own comments.")

    db.delete(comment)
    db.commit()
