import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    strategy_config = Column(JSON, nullable=False)
    llm_config = Column(JSON, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="bots")
    conversations = relationship(
        "BotConversation", back_populates="bot", cascade="all, delete-orphan"
    )
    backtests = relationship(
        "Backtest", back_populates="bot", cascade="all, delete-orphan"
    )
    simulations = relationship(
        "Simulation", back_populates="bot", cascade="all, delete-orphan"
    )
    signals = relationship("Signal", back_populates="bot", cascade="all, delete-orphan")


class BotConversation(Base):
    __tablename__ = "bot_conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bot = relationship("Bot", back_populates="conversations")


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(String, primary_key=True, default=generate_uuid)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    status = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    result = Column(JSON)

    bot = relationship("Bot", back_populates="backtests")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, default=generate_uuid)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    signals = Column(JSON)
    klines = Column(JSON)  # Price data for chart display
    trade_log = Column(JSON)  # Trade activity log

    bot = relationship("Bot", back_populates="simulations")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=generate_uuid)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False)
    run_id = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)
    token = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    confidence = Column(Float)
    reasoning = Column(Text)
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bot = relationship("Bot", back_populates="signals")


Index("idx_bots_user_id", Bot.user_id)
Index("idx_conversations_bot_id", BotConversation.bot_id)
Index("idx_backtests_bot_id", Backtest.bot_id)
Index("idx_simulations_bot_id", Simulation.bot_id)
Index("idx_signals_bot_id", Signal.bot_id)
Index("idx_signals_run_id", Signal.run_id)
