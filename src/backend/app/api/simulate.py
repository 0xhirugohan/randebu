from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..db.schemas import SimulationCreate, SimulationResponse

router = APIRouter()


@router.post("/bots/{bot_id}/simulate", response_model=SimulationResponse)
def start_simulation(
    bot_id: str, config: SimulationCreate, db: Session = Depends(get_db)
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/bots/{bot_id}/simulate/{run_id}", response_model=SimulationResponse)
def get_simulation(bot_id: str, run_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.get("/bots/{bot_id}/simulations", response_model=List[SimulationResponse])
def list_simulations(bot_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )


@router.post("/bots/{bot_id}/simulate/{run_id}/stop")
def stop_simulation(bot_id: str, run_id: str, db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented"
    )
