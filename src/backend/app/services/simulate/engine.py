import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..backtest.ave_client import AveCloudClient


class SimulateEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.run_id = str(uuid.uuid4())
        self.status = "pending"
        self.results: Optional[Dict[str, Any]] = None
        self.signals: List[Dict[str, Any]] = []
        self.ave_client = AveCloudClient(
            api_key=config.get("ave_api_key", ""),
            plan=config.get("ave_api_plan", "free"),
        )
        self.bot_id = config.get("bot_id")
        self.strategy_config = config.get("strategy_config", {})
        self.conditions = self.strategy_config.get("conditions", [])
        self.actions = self.strategy_config.get("actions", [])
        self.check_interval = config.get("check_interval", 60)
        self.duration_seconds = config.get("duration_seconds", 3600)
        self.auto_execute = config.get("auto_execute", False)
        self.token = config.get("token", "")
        self.chain = config.get("chain", "bsc")
        self.running = False
        self.started_at: Optional[datetime] = None
        self.last_price: Optional[float] = None
        self.last_volume: Optional[float] = None

    async def run(self) -> Dict[str, Any]:
        self.running = True
        self.status = "running"
        self.started_at = datetime.utcnow()

        token_id = (
            f"{self.token}-{self.chain}"
            if self.token and not self.token.endswith(f"-{self.chain}")
            else self.token
        )

        if not token_id or token_id == f"-{self.chain}":
            self.status = "failed"
            self.results = {"error": "Token ID is required"}
            return self.results

        end_time = datetime.utcnow().timestamp() + self.duration_seconds

        try:
            while self.running and datetime.utcnow().timestamp() < end_time:
                try:
                    price_data = await self.ave_client.get_token_price(token_id)
                    if price_data:
                        current_price = float(price_data.get("price", 0))
                        current_volume = float(price_data.get("volume", 0))

                        if current_price > 0:
                            await self._check_conditions(
                                current_price, current_volume, price_data
                            )

                        self.last_price = current_price
                        self.last_volume = current_volume

                except Exception as e:
                    pass

                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)

            if self.running:
                self.status = "completed"
            else:
                self.status = "stopped"

        except Exception as e:
            self.status = "failed"
            self.results = {"error": str(e)}

        self.results = self.results or {}
        self.results["total_signals"] = len(self.signals)
        self.results["signals"] = self.signals
        self.results["started_at"] = self.started_at
        self.results["ended_at"] = datetime.utcnow()

        return self.results

    async def _check_conditions(
        self, current_price: float, current_volume: float, price_data: Dict[str, Any]
    ):
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        for condition in self.conditions:
            if self._check_condition(condition, current_price, current_volume):
                await self._execute_actions(current_price, timestamp, condition)
                break

    def _check_condition(
        self,
        condition: Dict[str, Any],
        current_price: float,
        current_volume: float,
    ) -> bool:
        cond_type = condition.get("type", "")
        threshold = condition.get("threshold", 0)
        price_level = condition.get("price")
        direction = condition.get("direction", "above")

        if cond_type == "price_drop":
            if self.last_price is None or self.last_price <= 0:
                return False
            drop_pct = ((self.last_price - current_price) / self.last_price) * 100
            return drop_pct >= threshold

        elif cond_type == "price_rise":
            if self.last_price is None or self.last_price <= 0:
                return False
            rise_pct = ((current_price - self.last_price) / self.last_price) * 100
            return rise_pct >= threshold

        elif cond_type == "volume_spike":
            if self.last_volume is None or self.last_volume <= 0:
                return False
            volume_increase = (
                (current_volume - self.last_volume) / self.last_volume
            ) * 100
            return volume_increase >= threshold

        elif cond_type == "price_level":
            if price_level is None:
                return False
            if direction == "above":
                return current_price > price_level
            else:
                return current_price < price_level

        return False

    async def _execute_actions(
        self, price: float, timestamp: int, matched_condition: Dict[str, Any]
    ):
        token = matched_condition.get("token", self.token)
        reasoning = f"Condition {matched_condition.get('type')} triggered"

        signal = {
            "id": str(uuid.uuid4()),
            "bot_id": self.bot_id,
            "run_id": self.run_id,
            "signal_type": "signal",
            "token": token,
            "price": price,
            "confidence": 0.8,
            "reasoning": reasoning,
            "executed": self.auto_execute,
            "created_at": datetime.utcnow(),
        }

        self.signals.append(signal)

    async def stop(self):
        self.running = False
        self.status = "stopped"

    def get_results(self) -> Dict[str, Any]:
        return {
            "id": self.run_id,
            "status": self.status,
            "results": self.results,
            "signals": self.signals,
        }

    def get_signals(self) -> List[Dict[str, Any]]:
        return self.signals
