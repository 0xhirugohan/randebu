import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from ..core.database import get_db
from ..db.models import Conversation, Message, User, AnonymousUser, Bot
from ..services.auth import get_current_user
from ..services.rate_limiter import RateLimiter
from ..services.ai_agent import get_conversational_agent

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def get_or_create_anonymous_token(
    request: Request, response: Response, db: Session
) -> str:
    token = request.cookies.get("anonymous_token")
    if not token:
        token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="anonymous_token",
            value=token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
        )
        anon = AnonymousUser(id=token)
        db.add(anon)
        db.commit()
    return token


@router.get("")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user:
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == current_user.id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
    return []


@router.post("")
def create_conversation(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    request: Request = None,
    response: Response = None,
):
    anonymous_token = None
    if not current_user and request:
        anonymous_token = get_or_create_anonymous_token(request, response, db)

    conversation = Conversation(
        user_id=current_user.id if current_user else None,
        anonymous_token=anonymous_token,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(conversation)
    db.commit()


@router.post("/{conversation_id}/set-bot")
def set_bot_for_conversation(
    conversation_id: str,
    bot_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    request: Request = None,
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not current_user:
        anonymous_token = request.cookies.get("anonymous_token") if request else None
        if anonymous_token:
            RateLimiter.check_anonymous_bot_limit(db, anonymous_token)

    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if current_user and bot.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to use this bot")

    conversation.bot_id = bot_id
    db.commit()

    if not current_user and request:
        anonymous_token = request.cookies.get("anonymous_token")
        if anonymous_token:
            RateLimiter.set_bot_created(db, anonymous_token)

    return {"status": "updated", "bot_id": bot_id}


@router.post("/{conversation_id}/chat")
def chat_in_conversation(
    conversation_id: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    request: Request = None,
    response: Response = None,
):
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    warning = None

    if not current_user:
        RateLimiter.check_system_limit(db)

        anon_token = get_or_create_anonymous_token(request, response, db)

        anon = RateLimiter.check_anonymous_limit(db, anon_token)

        RateLimiter.increment_chat_count(db, anon_token)

        if anon and anon.chat_count > 40:
            warning = "Your progress is not saved."

    conversation_history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
    history_for_agent = [
        {"role": msg.role, "content": msg.content} for msg in conversation_history[-10:]
    ]

    if not conversation.bot_id:
        return {
            "response": "No bot selected for this conversation. Please set a bot first.",
            "thinking": None,
            "strategy_config": None,
            "success": False,
            "warning": warning,
        }

    agent = get_conversational_agent(bot_id=conversation.bot_id)
    result = agent.chat(message, history_for_agent)

    assistant_content = result.get("response", "I couldn't process your request.")

    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=message,
    )
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_msg)

    conversation.updated_at = conversation.updated_at
    db.commit()

    return {
        "response": assistant_content,
        "thinking": result.get("thinking"),
        "strategy_config": result.get("strategy_config"),
        "success": result.get("success", False),
        "warning": warning,
    }
