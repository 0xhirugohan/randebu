from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..db.schemas import BacktestCreate, BacktestResponse

router = APIRouter()


@router.post("/bots/{bot_id}/backtest", response_model=BacktestResponse)
def start_backtest(bot_id: str, config: BacktestCreate, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/bots/{bot_id}/backtest/{run_id}", response_model=BacktestResponse)
def get_backtest(bot_id: str, run_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/bots/{bot_id}/backtests", response_model=List[BacktestResponse])
def list_backtests(bot_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/bots/{bot_id}/backtest/{run_id}/stop")
def stop_backtest(bot_id: str, run_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
