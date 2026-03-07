import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class RoomType(str, enum.Enum):
    MAIN = "main"
    TEAM1 = "MI"
    TEAM2 = "CSK"


class ChatRoom(Base):
    """Predefined chat rooms: main, MI, CSK."""
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)          # "main", "MI", "CSK"
    room_type = Column(Enum(RoomType), nullable=False)
    display_name = Column(String(100), nullable=False)              # "Main Room", "MI Room", "CSK Room"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatRoom(id={self.id}, name='{self.name}')>"


class ChatMessage(Base):
    """Live chat messages in a room."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    user = relationship("User")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, room_id={self.room_id})>"


class ChatQuestion(Base):
    """
    A timed question displayed at the top of the chat room.
    Active for `duration_seconds` (default 30s), then results are shown.
    """
    __tablename__ = "chat_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    duration_seconds = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    options = relationship("ChatQuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("ChatQuestionAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatQuestion(id={self.id}, active={self.is_active})>"


class ChatQuestionOption(Base):
    """One of the 4 answer options for a chat question."""
    __tablename__ = "chat_question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("chat_questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(255), nullable=False)
    option_label = Column(String(1), nullable=False)  # A, B, C, D

    # Relationships
    question = relationship("ChatQuestion", back_populates="options")

    def __repr__(self):
        return f"<ChatQuestionOption(id={self.id}, label='{self.option_label}')>"


class ChatQuestionAnswer(Base):
    """A user's answer to a chat question (one answer per user per question)."""
    __tablename__ = "chat_question_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("chat_questions.id", ondelete="CASCADE"), nullable=False)
    option_id = Column(Integer, ForeignKey("chat_question_options.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    question = relationship("ChatQuestion", back_populates="answers")
    option = relationship("ChatQuestionOption")
    user = relationship("User")

    # One answer per user per question
    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("question_id", "user_id", name="uq_question_user_answer"),
    )

    def __repr__(self):
        return f"<ChatQuestionAnswer(user_id={self.user_id}, option_id={self.option_id})>"
