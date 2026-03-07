from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.ws_manager import manager
from app.models.user import User
from app.schemas.chat import (
    ChatRoomListResponse,
    ChatRoomResponse,
    SendMessageRequest,
    ChatMessageResponse,
    ChatMessageListResponse,
    MessageAuthor,
    CreateQuestionRequest,
    AnswerQuestionRequest,
    QuestionResponse,
    QuestionCreateResponse,
    QuestionResultResponse,
    AnswerQuestionResponse,
)
from app.services.chat_service import (
    get_all_rooms,
    send_message,
    get_messages,
    create_question,
    get_active_question,
    answer_question,
    deactivate_question,
    get_question_results,
)

router = APIRouter()


# ─────────────────────────── Rooms ───────────────────────────

@router.get("/rooms/", response_model=ChatRoomListResponse)
def list_rooms(db: Session = Depends(get_db)):
    """Get all chat rooms (main, MI, CSK)."""
    rooms = get_all_rooms(db)
    return ChatRoomListResponse(rooms=rooms)


# ─────────────────────────── Messages (REST) ───────────────────────────

@router.post("/rooms/{room_name}/messages/", response_model=ChatMessageResponse)
def post_message(
    room_name: str,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a chat message to a room."""
    msg = send_message(db, room_name, payload.content, current_user)
    return ChatMessageResponse(
        id=msg.id,
        content=msg.content,
        user=MessageAuthor(id=current_user.id, full_name=current_user.full_name),
        room_id=msg.room_id,
        created_at=msg.created_at,
    )


@router.get("/rooms/{room_name}/messages/", response_model=ChatMessageListResponse)
def list_messages(
    room_name: str,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to fetch"),
    before_id: int | None = Query(None, description="Fetch messages before this ID (for pagination)"),
    db: Session = Depends(get_db),
):
    """
    Fetch the last N messages for a room.
    Pass `before_id` to paginate backwards.
    """
    room, messages = get_messages(db, room_name, limit=limit, before_id=before_id)
    return ChatMessageListResponse(
        room_name=room.name,
        count=len(messages),
        messages=[
            ChatMessageResponse(
                id=m.id,
                content=m.content,
                user=MessageAuthor(id=m.user.id, full_name=m.user.full_name),
                room_id=m.room_id,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


# ─────────────────────────── Questions ───────────────────────────

@router.post("/questions/", response_model=QuestionCreateResponse)
def create_new_question(
    payload: CreateQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new timed question with 4 options (A/B/C/D).
    Automatically deactivates any previously active question.
    """
    question = create_question(
        db,
        question_text=payload.question_text,
        duration_seconds=payload.duration_seconds,
        options_data=[opt.model_dump() for opt in payload.options],
    )
    return QuestionCreateResponse(message="Question created.", question=question)


@router.get("/questions/active/", response_model=QuestionResponse | None)
def get_current_question(db: Session = Depends(get_db)):
    """Get the currently active question (if any)."""
    question = get_active_question(db)
    if not question:
        return None
    return question


@router.post("/questions/{question_id}/answer/", response_model=AnswerQuestionResponse)
def submit_answer(
    question_id: int,
    payload: AnswerQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit your answer to the active question."""
    ans = answer_question(db, question_id, payload.option_id, current_user)
    return AnswerQuestionResponse(
        message="Answer submitted.",
        selected_option=ans.option.option_label,
    )


@router.post("/questions/{question_id}/deactivate/", response_model=QuestionResultResponse)
def close_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a question and return results with percentages."""
    deactivate_question(db, question_id)
    return get_question_results(db, question_id)


@router.get("/questions/{question_id}/results/", response_model=QuestionResultResponse)
def question_results(
    question_id: int,
    db: Session = Depends(get_db),
):
    """Get results (vote counts & percentages) for a question."""
    return get_question_results(db, question_id)


# ─────────────────────────── WebSocket (Live Chat) ───────────────────────────

def _authenticate_ws_token(token: str, db: Session) -> User | None:
    """Validate JWT token for WebSocket connections."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except JWTError:
        return None


@router.websocket("/rooms/{room_name}/ws")
async def websocket_chat(websocket: WebSocket, room_name: str):
    """
    WebSocket endpoint for live chat in a room.

    Connect: ws://host/api/v1/chat/rooms/{room_name}/ws?token=YOUR_JWT
    Send:    {"content": "Hello!"}
    Receive: {"type": "message", "id": 1, "content": "Hello!", "user": {"id": 1, "full_name": "..."}, "room": "main", "created_at": "..."}
    """
    # Authenticate via query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    db = next(get_db())
    try:
        user = _authenticate_ws_token(token, db)
        if not user:
            await websocket.close(code=4003, reason="Invalid token")
            return

        user_info = {"id": user.id, "full_name": user.full_name}
        await manager.connect(websocket, room_name, user_info)

        try:
            while True:
                data = await websocket.receive_json()
                content = data.get("content", "").strip()
                if not content:
                    continue

                # Persist message
                msg = send_message(db, room_name, content, user)

                # Broadcast to all clients in the room
                await manager.broadcast_to_room(room_name, {
                    "type": "message",
                    "id": msg.id,
                    "content": msg.content,
                    "user": user_info,
                    "room": room_name,
                    "created_at": msg.created_at.isoformat(),
                })
        except WebSocketDisconnect:
            manager.disconnect(websocket, room_name)
    finally:
        db.close()
