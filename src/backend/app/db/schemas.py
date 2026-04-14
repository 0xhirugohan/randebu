from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: EmailStr
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
    strategy_config: Optional[dict] = {}
    llm_config: Optional[dict] = {}


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
    token_name: Optional[str] = None
    chain: str
    timeframe: str
    start_date: str
    end_date: str

    @field_validator("chain")
    @classmethod
    def chain_must_be_bsc(cls, v: str) -> str:
        if v != "bsc":
            raise ValueError("Phase 1 only supports BSC (bnb chain)")
        return v


class BacktestResponse(BaseModel):
    id: str
    bot_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    config: dict
    result: Optional[dict]
    progress: Optional[int] = None

    class Config:
        from_attributes = True


class SimulationCreate(BaseModel):
    token: str
    chain: str
    kline_interval: str = "1m"

    @field_validator("chain")
    @classmethod
    def chain_must_be_bsc(cls, v: str) -> str:
        if v != "bsc":
            raise ValueError("Phase 1 only supports BSC (bnb chain)")
        return v


class SimulationResponse(BaseModel):
    id: str
    bot_id: str
    started_at: datetime
    status: str
    config: dict
    signals: Optional[List[dict]]
    klines: Optional[List[dict]] = None  # Price data for chart
    trade_log: Optional[List[dict]] = None  # Trade activity log
    portfolio: Optional[dict] = None  # Portfolio data
    current_candle_index: Optional[int] = None  # Progress: current candle
    total_candles: Optional[int] = None  # Progress: total candles
    candles_processed: Optional[int] = None  # Progress: candles processed

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


class BotChatRequest(BaseModel):
    message: str
    strategy_config: Optional[bool] = False


class BotChatResponse(BaseModel):
    response: str
    thinking: Optional[str] = None
    strategy_config: Optional[dict] = None
    success: bool = False
    strategy_needs_confirmation: Optional[bool] = False
    strategy_data: Optional[dict] = None
    token_search_results: Optional[List[dict]] = None


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


class AveTokenSearchResponse(BaseModel):
    tokens: List[dict]
    upsell_message: Optional[str] = None


class AveBatchPricesRequest(BaseModel):
    token_ids: List[str]


class AveBatchPricesResponse(BaseModel):
    prices: Dict[str, dict]
    upsell_message: Optional[str] = None


class AveTokenDetailsResponse(BaseModel):
    token: Optional[dict] = None
    upsell_message: Optional[str] = None


class AveKlinesRequest(BaseModel):
    token_id: str
    interval: str = "1h"
    limit: int = 100
    start_time: Optional[int] = None
    end_time: Optional[int] = None


class AveKlinesResponse(BaseModel):
    klines: List[dict]
    upsell_message: Optional[str] = None


class AveTrendingTokensResponse(BaseModel):
    tokens: List[dict]
    upsell_message: Optional[str] = None


class AveTokenRiskResponse(BaseModel):
    risk: Optional[dict] = None
    upsell_message: Optional[str] = None


class AveChainQuoteRequest(BaseModel):
    chain: str
    from_token: str
    to_token: str
    amount: str
    slippage: float = 0.5


class AveChainQuoteResponse(BaseModel):
    quote: Optional[dict] = None
    upsell_message: Optional[str] = None


class AveChainSwapRequest(BaseModel):
    chain: str
    from_token: str
    to_token: str
    amount: str
    slippage: float = 0.5
    wallet_address: Optional[str] = None


class AveChainSwapResponse(BaseModel):
    swap: Optional[dict] = None
    upsell_message: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str]
    anonymous_token: Optional[str]
    bot_id: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    conversation_id: Optional[str]
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessagesResponse(BaseModel):
    id: str
    user_id: Optional[str]
    anonymous_token: Optional[str]
    bot_id: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SetBotRequest(BaseModel):
    bot_id: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    thinking: Optional[str] = None
    strategy_config: Optional[dict] = None
    success: bool = False
    warning: Optional[str] = None
