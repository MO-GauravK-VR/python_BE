from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class PostType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    POLL = "poll"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    post_type = Column(Enum(PostType), nullable=False, default=PostType.TEXT)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)  # text body (optional for image/video posts)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("User", back_populates="posts")
    media = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")
    poll_options = relationship("PollOption", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, type='{self.post_type}', title='{self.title}')>"


class PostMedia(Base):
    """Stores image/video file URLs attached to a post."""
    __tablename__ = "post_media"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    media_type = Column(String(10), nullable=False)   # "image" or "video"
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    post = relationship("Post", back_populates="media")

    def __repr__(self):
        return f"<PostMedia(id={self.id}, type='{self.media_type}')>"


class PollOption(Base):
    """Stores poll choices for a poll-type post."""
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(255), nullable=False)
    vote_count = Column(Integer, default=0)

    # Relationship
    post = relationship("Post", back_populates="poll_options")

    def __repr__(self):
        return f"<PollOption(id={self.id}, text='{self.option_text}')>"
