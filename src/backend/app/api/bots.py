from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from .auth import get_current_user
from ..core.database import get_db
from ..core.config import get_settings
from ..db.schemas import (
    BotCreate,
    BotUpdate,
    BotResponse,
    BotConversationCreate,
    BotConversationResponse,
    BotChatRequest,
    BotChatResponse,
)
from ..db.models import Bot, BotConversation, User
from ..services.ai_agent.crew import get_trading_crew

router = APIRouter()
MAX_BOTS_PER_USER = 3


@router.get("", response_model=List[BotResponse])
def list_bots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    return bots


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
def create_bot(
    bot_data: BotCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    user_bot_count = db.query(Bot).filter(Bot.user_id == current_user.id).count()
    if user_bot_count >= MAX_BOTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_BOTS_PER_USER} bots per user exceeded",
        )

    existing_bot = (
        db.query(Bot)
        .filter(Bot.user_id == current_user.id, Bot.name == bot_data.name)
        .first()
    )
    if existing_bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot name must be unique per user",
        )

    db_bot = Bot(
        user_id=current_user.id,
        name=bot_data.name,
        description=bot_data.description,
        strategy_config=bot_data.strategy_config,
        llm_config=bot_data.llm_config,
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(
    bot_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this bot",
        )
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this bot",
        )

    if bot_data.name is not None:
        existing_bot = (
            db.query(Bot)
            .filter(
                Bot.user_id == current_user.id,
                Bot.name == bot_data.name,
                Bot.id != bot_id,
            )
            .first()
        )
        if existing_bot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot name must be unique per user",
            )
        bot.name = bot_data.name

    if bot_data.description is not None:
        bot.description = bot_data.description
    if bot_data.strategy_config is not None:
        bot.strategy_config = bot_data.strategy_config
    if bot_data.llm_config is not None:
        bot.llm_config = bot_data.llm_config
    if bot_data.status is not None:
        bot.status = bot_data.status

    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bot(
    bot_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this bot",
        )
    db.delete(bot)
    db.commit()


@router.post("/{bot_id}/chat", response_model=BotChatResponse)
def chat(
    bot_id: str,
    request: BotChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to chat with this bot",
        )

    conversation_history = (
        db.query(BotConversation)
        .filter(BotConversation.bot_id == bot_id)
        .order_by(BotConversation.created_at)
        .all()
    )
    history_for_crew = [
        {"role": conv.role, "content": conv.content}
        for conv in conversation_history[-10:]
    ]

    user_message = request.message
    if request.strategy_config:
        crew = get_trading_crew()
        result = crew.chat(user_message, history_for_crew)

        assistant_content = result.get("response", "I couldn't process your request.")
        if result.get("success") and result.get("strategy_config"):
            bot.strategy_config = result["strategy_config"]
            db.commit()

        db_conversation = BotConversation(
            bot_id=bot_id,
            role="user",
            content=user_message,
        )
        db.add(db_conversation)

        db_assistant = BotConversation(
            bot_id=bot_id,
            role="assistant",
            content=assistant_content,
        )
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)

        return BotChatResponse(
            response=assistant_content,
            strategy_config=result.get("strategy_config"),
            success=result.get("success", False),
        )
    else:
        crew = get_trading_crew()
        result = crew.chat(user_message, history_for_crew)

        assistant_content = result.get("response", "I couldn't process your request.")

        db_conversation = BotConversation(
            bot_id=bot_id,
            role="user",
            content=user_message,
        )
        db.add(db_conversation)

        db_assistant = BotConversation(
            bot_id=bot_id,
            role="assistant",
            content=assistant_content,
        )
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)

        return BotChatResponse(
            response=assistant_content,
            strategy_config=result.get("strategy_config"),
            success=result.get("success", False),
        )


@router.get("/{bot_id}/history", response_model=List[BotConversationResponse])
def get_history(
    bot_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this bot's history",
        )

    conversations = (
        db.query(BotConversation)
        .filter(BotConversation.bot_id == bot_id)
        .order_by(BotConversation.created_at)
        .all()
    )
    return conversations
