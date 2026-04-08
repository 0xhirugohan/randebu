from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class UserSettings(BaseModel):
    email: EmailStr


class UserSettingsUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_config: dict
    llm_config: dict


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategy_config: Optional[dict] = None
    llm_config: Optional[dict] = None
    status: Optional[str] = None


class BotResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    strategy_config: dict
    llm_config: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BacktestCreate(BaseModel):
    token: str
    chain: str
    timeframe: str
    start_date: str
    end_date: str


class BacktestResponse(BaseModel):
    id: str
    bot_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    config: dict
    result: Optional[dict]

    class Config:
        from_attributes = True


class SimulationCreate(BaseModel):
    token: str
    chain: str
    duration_seconds: int = 3600
    auto_execute: bool = False


class SimulationResponse(BaseModel):
    id: str
    bot_id: str
    started_at: datetime
    status: str
    config: dict
    signals: Optional[List[dict]]

    class Config:
        from_attributes = True


class BotConversationCreate(BaseModel):
    role: str
    content: str


class BotConversationResponse(BaseModel):
    id: str
    bot_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SignalResponse(BaseModel):
    id: str
    bot_id: str
    run_id: str
    signal_type: str
    token: str
    price: float
    confidence: Optional[float]
    reasoning: Optional[str]
    executed: bool
    created_at: datetime

    class Config:
        from_attributes = True
