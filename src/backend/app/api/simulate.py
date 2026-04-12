import uuid
import asyncio
import logging
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
from ..services.ave.client import AveCloudClient

logger = logging.getLogger(__name__)

router = APIRouter()

running_simulations: Dict[str, Any] = {}
executor = ThreadPoolExecutor(max_workers=4)


def run_simulation_sync(
    simulation_id: str, db_url: str, bot_id: str, config: Dict[str, Any]
):
    import asyncio
    import time
    from ..services.simulate.engine import SimulateEngine
    from ..core.database import SessionLocal

    async def _run():
        engine = SimulateEngine(config)
        engine.run_id = simulation_id
        running_simulations[simulation_id] = engine
        
        # Serialize signals for JSON storage (convert datetime to string)
        def serialize_signal(s):
            created = s.get("created_at")
            if hasattr(created, "isoformat"):
                created = created.isoformat()
            return {
                **s,
                "created_at": created
            }
        
        def save_progress():
            """Save current progress to database."""
            db = SessionLocal()
            try:
                simulation = (
                    db.query(Simulation).filter(Simulation.id == simulation_id).first()
                )
                if simulation:
                    simulation.status = engine.status
                    simulation.signals = [serialize_signal(s) for s in engine.signals]
                    simulation.klines = [
                        {"time": k.get("time"), "close": k.get("close")}
                        for k in engine.klines
                    ]
                    simulation.trade_log = engine.trade_log
                    db.commit()
            finally:
                db.close()
        
        async def run_with_progress_save():
            """Run simulation and save progress periodically."""
            last_save_time = time.time()
            save_interval = 5  # Save every 5 seconds
            
            while engine.running and engine.status == "running":
                await asyncio.sleep(1)  # Check every second
                
                current_time = time.time()
                if current_time - last_save_time >= save_interval:
                    save_progress()
                    last_save_time = current_time
            
            # Final save when done
            save_progress()
        
        try:
            # Run both simulation and progress saving concurrently
            await asyncio.gather(
                engine.run(),
                run_with_progress_save()
            )

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

    # Check if there's already a running simulation for this bot
    existing_simulation = (
        db.query(Simulation)
        .filter(Simulation.bot_id == bot_id, Simulation.status == "running")
        .first()
    )
    if existing_simulation:
        # Stop the existing simulation first
        if existing_simulation.id in running_simulations:
            running_simulations[existing_simulation.id].stop()
            del running_simulations[existing_simulation.id]
        existing_simulation.status = "stopped"
        db.commit()

    settings = get_settings()
    simulation_id = str(uuid.uuid4())
    
    # Create AVE client for klines fetching
    ave_client = AveCloudClient(
        api_key=settings.AVE_API_KEY,
        plan=settings.AVE_API_PLAN,
    )

    simulation_config = {
        "bot_id": bot_id,
        "token": config.token,
        "chain": config.chain,
        "kline_interval": config.kline_interval,
        "auto_execute": False,  # Always paper trade
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
            "kline_interval": config.kline_interval,
        },
        signals=[],
        klines=[],
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)

    # Fetch klines SYNCHRONOUSLY so user can see chart immediately
    try:
        token_id = f"{config.token}-{config.chain}"
        
        # Calculate time range (last 1 hour)
        import time
        end_time = int(time.time() * 1000)
        start_time = end_time - (60 * 60 * 1000)  # 1 hour ago
        
        klines_data = await ave_client.get_klines(
            token_id,
            interval=config.kline_interval,
            start_time=start_time,
            end_time=end_time,
            limit=500
        )
        klines_for_chart = [
            {"time": k.get("time"), "close": k.get("close")}
            for k in sorted(klines_data, key=lambda x: x.get("time", 0))
        ]
        # Update simulation with klines
        simulation.klines = klines_for_chart
        db.commit()
        db.refresh(simulation)
        logger.info(f"Fetched {len(klines_for_chart)} klines for simulation {simulation_id}")
    except Exception as e:
        logger.error(f"Failed to fetch klines: {e}")

    # Run simulation in background for signal processing
    background_tasks.add_task(
        run_simulation_sync, simulation_id, str(settings.DATABASE_URL), bot_id, simulation_config
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
            # Include klines from running engine for chart display
            if hasattr(engine, 'klines'):
                sim.klines = [{"time": k.get("time"), "close": k.get("close")} for k in engine.klines]

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

    # Always update status to stopped, even if engine is not in memory
    simulation.status = "stopped"
    
    # Try to stop the engine if it's still in memory
    if run_id in running_simulations:
        engine = running_simulations[run_id]
        engine.stop()
        del running_simulations[run_id]
    
    db.commit()

    return {"status": "stopped", "run_id": run_id}
