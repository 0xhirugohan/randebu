import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..ave.client import AveCloudClient


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
        self.risk_management = self.strategy_config.get("risk_management", {})
        self.stop_loss_percent = self.risk_management.get("stop_loss_percent")
        self.take_profit_percent = self.risk_management.get("take_profit_percent")
        self.check_interval = config.get("check_interval", 60)
        self.duration_seconds = config.get("duration_seconds", 3600)
        self.auto_execute = config.get("auto_execute", False)
        self.token = config.get("token", "")
        self.chain = config.get("chain", "bsc")
        self.running = False
        self.started_at: Optional[datetime] = None
        self.last_price: Optional[float] = None
        self.last_volume: Optional[float] = None
        self.position: float = 0.0
        self.position_token: str = ""
        self.entry_price: Optional[float] = None
        self.entry_time: Optional[int] = None
        self.current_balance: float = config.get("initial_balance", 10000.0)
        self.trades: List[Dict[str, Any]] = []

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

        if self.position > 0 and self.entry_price is not None:
            exit_info = self._check_risk_management(current_price, timestamp)
            if exit_info:
                await self._execute_risk_exit(current_price, timestamp, exit_info)
                return

        for condition in self.conditions:
            if self._check_condition(condition, current_price, current_volume):
                await self._execute_actions(current_price, timestamp, condition)
                break

    def _check_risk_management(
        self, current_price: float, timestamp: int
    ) -> Optional[Dict[str, Any]]:
        if self.position <= 0 or self.entry_price is None:
            return None

        if self.stop_loss_percent is not None:
            stop_loss_price = self.entry_price * (1 - self.stop_loss_percent / 100)
            if current_price <= stop_loss_price:
                return {"reason": "stop_loss", "price": stop_loss_price}

        if self.take_profit_percent is not None:
            take_profit_price = self.entry_price * (1 + self.take_profit_percent / 100)
            if current_price >= take_profit_price:
                return {"reason": "take_profit", "price": take_profit_price}

        return None

    async def _execute_risk_exit(
        self, price: float, timestamp: int, exit_info: Dict[str, Any]
    ):
        if self.position <= 0:
            return

        reason = exit_info["reason"]
        self.trades.append(
            {
                "type": "sell",
                "token": self.position_token,
                "price": price,
                "quantity": self.position,
                "timestamp": timestamp,
                "exit_reason": reason,
            }
        )
        self.signals.append(
            {
                "id": str(uuid.uuid4()),
                "bot_id": self.bot_id,
                "run_id": self.run_id,
                "signal_type": "sell",
                "token": self.position_token,
                "price": price,
                "confidence": 1.0,
                "reasoning": f"Risk management triggered {reason}",
                "executed": self.auto_execute,
                "created_at": datetime.utcnow(),
            }
        )
        self.position = 0
        self.entry_price = None
        self.entry_time = None

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

        for action in self.actions:
            action_type = action.get("type", "")
            if action_type == "buy":
                amount_percent = action.get("amount_percent", 10)
                amount = self.current_balance * (amount_percent / 100)
                self.position += amount / price
                self.position_token = token
                self.entry_price = price
                self.entry_time = timestamp
                self.current_balance -= amount
                self.trades.append(
                    {
                        "type": "buy",
                        "token": token,
                        "price": price,
                        "amount": amount,
                        "quantity": amount / price,
                        "timestamp": timestamp,
                    }
                )

            signal = {
                "id": str(uuid.uuid4()),
                "bot_id": self.bot_id,
                "run_id": self.run_id,
                "signal_type": action_type,
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
