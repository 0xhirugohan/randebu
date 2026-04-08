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
from ..db.schemas import SimulationCreate, SimulationResponse
from ..db.models import Bot, Simulation, Signal, User

router = APIRouter()

running_simulations: Dict[str, Any] = {}
executor = ThreadPoolExecutor(max_workers=4)


def run_simulation_sync(
    simulation_id: str, db_url: str, bot_id: str, config: Dict[str, Any]
):
    import asyncio
    from ..services.simulate.engine import SimulateEngine
    from ..core.database import SessionLocal

    async def _run():
        engine = SimulateEngine(config)
        engine.run_id = simulation_id
        running_simulations[simulation_id] = engine
        try:
            results = await engine.run()
            db = SessionLocal()
            try:
                simulation = (
                    db.query(Simulation).filter(Simulation.id == simulation_id).first()
                )
                if simulation:
                    simulation.status = engine.status
                    simulation.signals = engine.signals
                    db.commit()

                for signal in engine.signals:
                    db_signal = Signal(
                        id=signal["id"],
                        bot_id=signal["bot_id"],
                        run_id=signal["run_id"],
                        signal_type=signal["signal_type"],
                        token=signal["token"],
                        price=signal["price"],
                        confidence=signal.get("confidence"),
                        reasoning=signal.get("reasoning"),
                        executed=signal.get("executed", False),
                        created_at=signal["created_at"],
                    )
                    db.add(db_signal)
                db.commit()
            finally:
                db.close()
        finally:
            if simulation_id in running_simulations:
                del running_simulations[simulation_id]

    asyncio.run(_run())


@router.post(
    "/bots/{bot_id}/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_simulation(
    bot_id: str,
    config: SimulationCreate,
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
    simulation_id = str(uuid.uuid4())

    check_interval = config.check_interval
    if settings.AVE_API_PLAN != "pro" and check_interval < 60:
        check_interval = 60

    simulation_config = {
        "bot_id": bot_id,
        "token": config.token,
        "chain": config.chain,
        "duration_seconds": config.duration_seconds,
        "check_interval": check_interval,
        "auto_execute": config.auto_execute,
        "strategy_config": bot.strategy_config,
        "ave_api_key": settings.AVE_API_KEY,
        "ave_api_plan": settings.AVE_API_PLAN,
    }

    simulation = Simulation(
        id=simulation_id,
        bot_id=bot_id,
        started_at=datetime.utcnow(),
        status="running",
        config={
            "token": config.token,
            "chain": config.chain,
            "duration_seconds": config.duration_seconds,
            "check_interval": check_interval,
            "auto_execute": config.auto_execute,
        },
        signals=[],
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)

    db_url = str(settings.DATABASE_URL)
    background_tasks.add_task(
        run_simulation_sync, simulation_id, db_url, bot_id, simulation_config
    )

    return simulation


@router.get("/bots/{bot_id}/simulate/{run_id}", response_model=SimulationResponse)
def get_simulation(
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

    simulation = (
        db.query(Simulation)
        .filter(Simulation.id == run_id, Simulation.bot_id == bot_id)
        .first()
    )
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found"
        )

    if run_id in running_simulations:
        engine = running_simulations[run_id]
        simulation.signals = engine.get_signals()

    return simulation


@router.get("/bots/{bot_id}/simulations", response_model=List[SimulationResponse])
def list_simulations(
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

    simulations = (
        db.query(Simulation)
        .filter(Simulation.bot_id == bot_id)
        .order_by(Simulation.started_at.desc())
        .all()
    )

    for sim in simulations:
        if sim.id in running_simulations:
            engine = running_simulations[sim.id]
            sim.signals = engine.get_signals()

    return simulations


@router.post("/bots/{bot_id}/simulate/{run_id}/stop")
def stop_simulation(
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

    simulation = (
        db.query(Simulation)
        .filter(Simulation.id == run_id, Simulation.bot_id == bot_id)
        .first()
    )
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found"
        )

    if run_id in running_simulations:
        engine = running_simulations[run_id]
        asyncio.create_task(engine.stop())
        simulation.status = "stopped"
        db.commit()

    return {"status": "stopping", "run_id": run_id}
