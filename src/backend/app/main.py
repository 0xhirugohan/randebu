from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, bots, backtest, simulate, config

app = FastAPI(
    title="Randebu Trading Bot API",
    description="AI-powered trading bot platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bots.router, prefix="/api/bots", tags=["bots"])
app.include_router(backtest.router, prefix="/api", tags=["backtest"])
app.include_router(simulate.router, prefix="/api", tags=["simulate"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Randebu Trading Bot API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
