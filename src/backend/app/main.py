import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from .api import auth, bots, backtest, simulate, config, ave, conversations
from .core.limiter import limiter
from .core.database import engine, Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # Import all models to ensure they're registered
    from .db.models import (
        User,
        Bot,
        BotConversation,
        Backtest,
        Simulation,
        Signal,
        Conversation,
        Message,
        AnonymousUser,
    )

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

    yield
    # Cleanup on shutdown if needed


app = FastAPI(
    title="Randebu Trading Bot API",
    description="AI-powered trading bot platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bots.router, prefix="/api/bots", tags=["bots"])
app.include_router(
    conversations.router, prefix="/api/conversations", tags=["conversations"]
)
app.include_router(backtest.router, prefix="/api", tags=["backtest"])
app.include_router(simulate.router, prefix="/api", tags=["simulate"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(ave.router, prefix="/api/ave", tags=["ave"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Randebu Trading Bot API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
