from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.chat import ChatRoom, ChatMessage, ChatQuestion, ChatQuestionOption, ChatQuestionAnswer, RoomType
from app.models.user import User


# ─────────────────────────── Room helpers ───────────────────────────

def seed_default_rooms(db: Session) -> None:
    """Create the 3 default rooms if they don't exist yet."""
    defaults = [
        {"name": "main", "room_type": RoomType.MAIN, "display_name": "Main Room"},
        {"name": "MI", "room_type": RoomType.TEAM1, "display_name": "MI Room"},
        {"name": "CSK", "room_type": RoomType.TEAM2, "display_name": "CSK Room"},
    ]
    for room_data in defaults:
        exists = db.query(ChatRoom).filter(ChatRoom.name == room_data["name"]).first()
        if not exists:
            db.add(ChatRoom(**room_data))
    db.commit()


def get_all_rooms(db: Session) -> list[ChatRoom]:
    return db.query(ChatRoom).order_by(ChatRoom.id).all()


def _get_room_or_404(db: Session, room_name: str) -> ChatRoom:
    room = db.query(ChatRoom).filter(ChatRoom.name == room_name).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room '{room_name}' not found.")
    return room


# ─────────────────────────── Messages ───────────────────────────

def send_message(db: Session, room_name: str, content: str, current_user: User) -> ChatMessage:
    room = _get_room_or_404(db, room_name)
    msg = ChatMessage(room_id=room.id, user_id=current_user.id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, room_name: str, limit: int = 50, before_id: int | None = None) -> tuple[ChatRoom, list[ChatMessage]]:
    """
    Fetch the last `limit` messages for a room.
    Optionally pass `before_id` to paginate backwards.
    """
    room = _get_room_or_404(db, room_name)
    query = db.query(ChatMessage).filter(ChatMessage.room_id == room.id)
    if before_id:
        query = query.filter(ChatMessage.id < before_id)
    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()  # return in chronological order
    return room, messages


# ─────────────────────────── Questions ───────────────────────────

def create_question(db: Session, question_text: str, duration_seconds: int, options_data: list[dict]) -> ChatQuestion:
    """Create a new timed question with 4 options. Deactivates any currently active question."""
    # Deactivate all currently active questions
    db.query(ChatQuestion).filter(ChatQuestion.is_active == True).update({"is_active": False})  # noqa: E712

    question = ChatQuestion(
        question_text=question_text,
        duration_seconds=duration_seconds,
        is_active=True,
    )
    for opt in options_data:
        question.options.append(ChatQuestionOption(
            option_text=opt["option_text"],
            option_label=opt["option_label"].upper(),
        ))
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def get_active_question(db: Session) -> ChatQuestion | None:
    return (
        db.query(ChatQuestion)
        .filter(ChatQuestion.is_active == True)  # noqa: E712
        .order_by(ChatQuestion.created_at.desc())
        .first()
    )


def answer_question(db: Session, question_id: int, option_id: int, current_user: User) -> ChatQuestionAnswer:
    question = db.query(ChatQuestion).filter(ChatQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    if not question.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This question is no longer active.")

    # Check option belongs to this question
    option = db.query(ChatQuestionOption).filter(
        ChatQuestionOption.id == option_id,
        ChatQuestionOption.question_id == question_id,
    ).first()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found for this question.")

    # Check if user already answered
    existing = db.query(ChatQuestionAnswer).filter(
        ChatQuestionAnswer.question_id == question_id,
        ChatQuestionAnswer.user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already answered this question.")

    answer = ChatQuestionAnswer(
        question_id=question_id,
        option_id=option_id,
        user_id=current_user.id,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def deactivate_question(db: Session, question_id: int) -> ChatQuestion:
    """Manually deactivate a question (show results)."""
    question = db.query(ChatQuestion).filter(ChatQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    question.is_active = False
    db.commit()
    db.refresh(question)
    return question


def get_question_results(db: Session, question_id: int) -> dict:
    """Get vote counts and percentages for each option."""
    question = db.query(ChatQuestion).filter(ChatQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    total_answers = db.query(ChatQuestionAnswer).filter(
        ChatQuestionAnswer.question_id == question_id
    ).count()

    option_results = []
    for option in question.options:
        vote_count = db.query(ChatQuestionAnswer).filter(
            ChatQuestionAnswer.question_id == question_id,
            ChatQuestionAnswer.option_id == option.id,
        ).count()
        percentage = round((vote_count / total_answers * 100), 1) if total_answers > 0 else 0.0
        option_results.append({
            "id": option.id,
            "option_text": option.option_text,
            "option_label": option.option_label,
            "vote_count": vote_count,
            "percentage": percentage,
        })

    return {
        "id": question.id,
        "question_text": question.question_text,
        "is_active": question.is_active,
        "total_answers": total_answers,
        "options": option_results,
    }
