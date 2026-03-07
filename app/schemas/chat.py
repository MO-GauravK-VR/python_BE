from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum


# --- Enums ---

class RoomTypeEnum(str, Enum):
    MAIN = "main"
    MI = "MI"
    CSK = "CSK"


# --- Chat Room ---

class ChatRoomResponse(BaseModel):
    id: int
    name: str
    room_type: str
    display_name: str

    class Config:
        from_attributes = True


class ChatRoomListResponse(BaseModel):
    rooms: list[ChatRoomResponse]


# --- Chat Message ---

class SendMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty.")
        return v.strip()


class MessageAuthor(BaseModel):
    id: int
    full_name: str

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    content: str
    user: MessageAuthor
    room_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    room_name: str
    count: int
    messages: list[ChatMessageResponse]


# --- Chat Question ---

class QuestionOptionCreate(BaseModel):
    option_text: str
    option_label: str   # A, B, C, D


class CreateQuestionRequest(BaseModel):
    question_text: str
    duration_seconds: int = 30
    options: list[QuestionOptionCreate]

    @field_validator("options")
    @classmethod
    def validate_options(cls, v):
        if len(v) != 4:
            raise ValueError("A question must have exactly 4 options.")
        labels = {opt.option_label.upper() for opt in v}
        if labels != {"A", "B", "C", "D"}:
            raise ValueError("Options must have labels A, B, C, D.")
        return v


class AnswerQuestionRequest(BaseModel):
    option_id: int


class QuestionOptionResponse(BaseModel):
    id: int
    option_text: str
    option_label: str

    class Config:
        from_attributes = True


class QuestionOptionResultResponse(BaseModel):
    id: int
    option_text: str
    option_label: str
    vote_count: int
    percentage: float

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    duration_seconds: int
    is_active: bool
    options: list[QuestionOptionResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionResultResponse(BaseModel):
    id: int
    question_text: str
    is_active: bool
    total_answers: int
    options: list[QuestionOptionResultResponse]


class QuestionCreateResponse(BaseModel):
    message: str
    question: QuestionResponse


class AnswerQuestionResponse(BaseModel):
    message: str
    selected_option: str
