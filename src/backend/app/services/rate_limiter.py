import os
from datetime import datetime, timedelta
from sqlalchemy import func
from fastapi import HTTPException
from ..db.models import Message, AnonymousUser

MAX_CHATS_PER_5HOURS = int(os.getenv("MAX_CHATS_PER_5HOURS", "500"))
MAX_ANONYMOUS_CHATS = 50
MAX_ANONYMOUS_BOTS = 1
MAX_ANONYMOUS_BACKTESTS = 1


class RateLimiter:
    @staticmethod
    def check_system_limit(db):
        cutoff = datetime.utcnow() - timedelta(hours=5)
        count = (
            db.query(func.count(Message.id))
            .filter(Message.created_at >= cutoff)
            .scalar()
        )

        if count >= MAX_CHATS_PER_5HOURS:
            raise HTTPException(
                status_code=429,
                detail="Rate limited from the agent service. Please come back later.",
            )

    @staticmethod
    def check_anonymous_limit(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon and anon.chat_count >= MAX_ANONYMOUS_CHATS:
            raise HTTPException(
                status_code=403,
                detail="You've reached the limit. Please create an account to continue.",
            )

        return anon

    @staticmethod
    def check_anonymous_bot_limit(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon and anon.bot_created:
            raise HTTPException(
                status_code=403,
                detail="You've reached the limit. Please create an account to continue.",
            )

    @staticmethod
    def check_anonymous_backtest_limit(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon and anon.backtest_count >= MAX_ANONYMOUS_BACKTESTS:
            raise HTTPException(
                status_code=403,
                detail="You've reached the limit. Please create an account to continue.",
            )

    @staticmethod
    def increment_chat_count(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon:
            anon.chat_count += 1
            db.commit()

    @staticmethod
    def set_bot_created(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon:
            anon.bot_created = True
            db.commit()

    @staticmethod
    def increment_backtest_count(db, anonymous_token: str):
        anon = (
            db.query(AnonymousUser).filter(AnonymousUser.id == anonymous_token).first()
        )

        if anon:
            anon.backtest_count += 1
            db.commit()
