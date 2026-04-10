import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .auth import get_current_user
from ..core.database import get_db
from ..core.config import get_settings
from ..db.schemas import BacktestCreate, BacktestResponse
from ..db.models import Bot, Backtest, Signal, User

router = APIRouter()

running_backtests: Dict[str, Any] = {}
executor = ThreadPoolExecutor(max_workers=4)


def run_backtest_sync(
    backtest_id: str, db_url: str, bot_id: str, config: Dict[str, Any]
):
    import asyncio
    import json
    from ..services.backtest.engine import BacktestEngine
    from ..core.database import SessionLocal

    async def _run():
        engine = BacktestEngine(config)
        engine.run_id = backtest_id
        running_backtests[backtest_id] = engine
        try:
            results = await engine.run()
            
            # Convert datetime objects to ISO strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(i) for i in obj]
                return obj
            
            results = convert_datetime(results)
            
            db = SessionLocal()
            try:
                backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
                if backtest:
                    backtest.status = engine.status
                    backtest.ended_at = datetime.utcnow()
                    backtest.result = results
                    db.commit()

                for signal in engine.signals:
                    signal_data = convert_datetime(signal)
                    db_signal = Signal(
                        id=signal_data["id"],
                        bot_id=signal_data["bot_id"],
                        run_id=signal_data["run_id"],
                        signal_type=signal_data["signal_type"],
                        token=signal_data["token"],
                        price=signal_data["price"],
                        confidence=signal_data.get("confidence"),
                        reasoning=signal_data.get("reasoning"),
                        executed=signal_data.get("executed", False),
                        created_at=signal_data["created_at"],
                    )
                    db.add(db_signal)
                db.commit()
            finally:
                db.close()
        finally:
            if backtest_id in running_backtests:
                del running_backtests[backtest_id]

    asyncio.run(_run())


@router.post(
    "/bots/{bot_id}/backtest",
    response_model=BacktestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_backtest(
    bot_id: str,
    config: BacktestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    settings = get_settings()
    backtest_id = str(uuid.uuid4())

    backtest_config = {
        "bot_id": bot_id,
        "token": config.token,
        "chain": config.chain,
        "timeframe": config.timeframe,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "strategy_config": bot.strategy_config,
        "ave_api_key": settings.AVE_API_KEY,
        "ave_api_plan": settings.AVE_API_PLAN,
        "initial_balance": 10000.0,
    }

    backtest = Backtest(
        id=backtest_id,
        bot_id=bot_id,
        started_at=datetime.utcnow(),
        status="running",
        config={
            "token": config.token,
            "chain": config.chain,
            "timeframe": config.timeframe,
            "start_date": config.start_date,
            "end_date": config.end_date,
        },
    )
    db.add(backtest)
    db.commit()
    db.refresh(backtest)

    db_url = str(settings.DATABASE_URL)
    background_tasks.add_task(
        run_backtest_sync, backtest_id, db_url, bot_id, backtest_config
    )

    return backtest


@router.get("/bots/{bot_id}/backtest/{run_id}", response_model=BacktestResponse)
def get_backtest(
    bot_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    backtest = (
        db.query(Backtest)
        .filter(Backtest.id == run_id, Backtest.bot_id == bot_id)
        .first()
    )
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found"
        )

    # Add progress from running engine if available
    if backtest.status == "running" and run_id in running_backtests:
        engine = running_backtests[run_id]
        backtest.progress = engine.progress
    
    return backtest


@router.get("/bots/{bot_id}/backtests", response_model=List[BacktestResponse])
def list_backtests(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    backtests = (
        db.query(Backtest)
        .filter(Backtest.bot_id == bot_id)
        .order_by(Backtest.started_at.desc())
        .all()
    )
    return backtests


@router.post("/bots/{bot_id}/backtest/{run_id}/stop")
def stop_backtest(
    bot_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )
    if bot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    backtest = (
        db.query(Backtest)
        .filter(Backtest.id == run_id, Backtest.bot_id == bot_id)
        .first()
    )
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found"
        )

    if run_id in running_backtests:
        engine = running_backtests[run_id]
        engine.running = False  # Direct sync access to running flag
        backtest.status = "stopped"
        backtest.ended_at = datetime.utcnow()
        db.commit()
    elif backtest.status == "running":
        # Engine already finished but status not updated
        backtest.status = "stopped"
        backtest.ended_at = datetime.utcnow()
        db.commit()

    return {"status": "stopping", "run_id": run_id}
