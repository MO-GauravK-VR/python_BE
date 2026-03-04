from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# --- Like Schemas ---

class LikeToggleResponse(BaseModel):
    message: str
    liked: bool
    like_count: int


# --- Comment Schemas ---

class CreateCommentRequest(BaseModel):
    content: str
    parent_id: Optional[int] = None  # for replies


class CommentAuthor(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    content: str
    user: CommentAuthor
    post_id: int
    parent_id: Optional[int] = None
    replies: list["CommentResponse"] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommentCreateResponse(BaseModel):
    message: str
    comment: CommentResponse


class CommentListResponse(BaseModel):
    message: str
    count: int
    comments: list[CommentResponse]
