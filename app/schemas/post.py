from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum


class PostTypeEnum(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    POLL = "poll"


# --- Request Schemas ---

class PollOptionCreate(BaseModel):
    option_text: str


class MediaAttachment(BaseModel):
    media_type: str       # "image" or "video"
    file_url: str         # URL returned from /api/v1/media/upload
    file_name: Optional[str] = None


class CreatePostRequest(BaseModel):
    post_type: PostTypeEnum = PostTypeEnum.TEXT
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[list[MediaAttachment]] = None       # for image/video posts
    poll_options: Optional[list[PollOptionCreate]] = None     # for poll posts

    @field_validator("poll_options")
    @classmethod
    def validate_poll_options(cls, v, info):
        post_type = info.data.get("post_type")
        if post_type == PostTypeEnum.POLL:
            if not v or len(v) < 2:
                raise ValueError("Poll posts must have at least 2 options.")
            if len(v) > 10:
                raise ValueError("Poll posts can have at most 10 options.")
        return v


# --- Response Schemas ---

class PostAuthor(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class MediaResponse(BaseModel):
    id: int
    media_type: str
    file_url: str
    file_name: Optional[str] = None

    class Config:
        from_attributes = True


class PollOptionResponse(BaseModel):
    id: int
    option_text: str
    vote_count: int

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    post_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: PostAuthor
    media: list[MediaResponse] = []
    poll_options: list[PollOptionResponse] = []
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    message: str
    count: int
    posts: list[PostResponse]


class PostCreateResponse(BaseModel):
    message: str
    post: PostResponse


class MediaUploadResponse(BaseModel):
    message: str
    media: list[MediaResponse]
