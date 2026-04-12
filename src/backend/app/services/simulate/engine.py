import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..ave.client import AveCloudClient

logger = logging.getLogger(__name__)


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
        
        # Kline-based settings
        self.kline_interval = config.get("kline_interval", "1m")
        self.max_candles = config.get("max_candles", 500)  # Limit candles to process
        
        self.auto_execute = config.get("auto_execute", False)
        self.token = config.get("token", "")
        self.chain = config.get("chain", "bsc")
        self.running = False
        self.started_at: Optional[datetime] = None
        
        # Price tracking (for conditions)
        self.last_close: Optional[float] = None
        self.last_volume: Optional[float] = None
        
        # Position tracking (for risk management)
        self.position: float = 0.0
        self.position_token: str = ""
        self.entry_price: Optional[float] = None
        self.entry_time: Optional[int] = None
        
        # Portfolio
        self.current_balance: float = config.get("initial_balance", 10000.0)
        self.trades: List[Dict[str, Any]] = []
        
        # Error tracking
        self.errors: List[str] = []
        
        # Kline data
        self.klines: List[Dict[str, Any]] = []
        self.last_processed_time: Optional[int] = None

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

        try:
            # Step 1: Fetch klines (only once for simulation)
            self.klines = await self._fetch_klines(token_id)
            
            if not self.klines:
                self.status = "failed"
                self.results = {"error": "No kline data available"}
                return self.results
            
            logger.info(f"Fetched {len(self.klines)} klines for {token_id}")
            
            # Step 2: Process candles (with limit)
            candles_processed = 0
            for candle in self.klines:
                if not self.running:
                    break
                if candles_processed >= self.max_candles:
                    logger.info(f"Reached max candles limit ({self.max_candles})")
                    break
                
                candle_time = int(candle.get("time", 0))
                
                # Get OHLCV data from candle
                close_price = float(candle.get("close", 0))
                volume = float(candle.get("volume", 0))
                
                if close_price > 0:
                    # Process candle
                    await self._process_candle(close_price, volume, candle_time)
                    
                    # Update last close for next iteration
                    self.last_close = close_price
                    self.last_volume = volume
                    
                    # Track last processed time
                    self.last_processed_time = candle_time
                
                candles_processed += 1
            
            self.status = "completed"

        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.status = "failed"
            self.results = {"error": str(e)}
            self.errors.append(str(e))

        self.results = self.results or {}
        self.results["total_signals"] = len(self.signals)
        self.results["total_trades"] = len(self.trades)
        self.results["total_errors"] = len(self.errors)
        self.results["errors"] = self.errors
        self.results["signals"] = self.signals
        self.results["candles_processed"] = candles_processed if self.running else 0
        self.results["klines"] = self.klines  # Include klines for chart display
        self.results["started_at"] = self.started_at
        self.results["ended_at"] = datetime.utcnow()

        return self.results

    async def _fetch_klines(
        self, 
        token_id: str, 
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetch klines from AVE API."""
        try:
            klines = await self.ave_client.get_klines(
                token_id,
                interval=self.kline_interval,
                limit=limit
            )
            
            # Sort by time ascending (oldest first)
            klines = sorted(klines, key=lambda x: x.get("time", 0))
            return klines
            
        except Exception as e:
            logger.warning(f"Failed to fetch klines for {token_id}: {e}")
            self.errors.append(f"Kline fetch failed: {str(e)}")
            return []

    async def _process_candle(
        self, 
        close_price: float, 
        volume: float, 
        timestamp: int
    ):
        """Process a single candle - check conditions and risk management."""
        
        # Check risk management first (for open positions)
        if self.position > 0 and self.entry_price is not None:
            exit_info = self._check_risk_management(close_price, timestamp)
            if exit_info:
                await self._execute_risk_exit(close_price, timestamp, exit_info)
                return  # Skip condition check if we just exited

        # Check conditions (only if no open position)
        if self.position == 0:
            for condition in self.conditions:
                if self._check_condition(condition, close_price, volume):
                    await self._execute_actions(close_price, timestamp, condition)
                    break

    def _check_risk_management(
        self, current_price: float, timestamp: int
    ) -> Optional[Dict[str, Any]]:
        """Check if stop loss or take profit is triggered."""
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
        """Execute stop loss or take profit."""
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
        """Check if a condition is met based on price movement."""
        cond_type = condition.get("type", "")
        threshold = condition.get("threshold", 0)

        if cond_type == "price_drop":
            # Price dropped by threshold % from last close
            if self.last_close is None or self.last_close <= 0:
                return False
            drop_pct = ((self.last_close - current_price) / self.last_close) * 100
            return drop_pct >= threshold

        elif cond_type == "price_rise":
            # Price rose by threshold % from last close
            if self.last_close is None or self.last_close <= 0:
                return False
            rise_pct = ((current_price - self.last_close) / self.last_close) * 100
            return rise_pct >= threshold

        elif cond_type == "volume_spike":
            # Volume increased significantly
            if self.last_volume is None or self.last_volume <= 0:
                return False
            volume_increase = ((current_volume - self.last_volume) / self.last_volume) * 100
            return volume_increase >= threshold

        elif cond_type == "price_level":
            price_level = condition.get("price")
            direction = condition.get("direction", "above")
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
        """Execute buy/sell actions based on matched condition."""
        token = matched_condition.get("token", self.token)
        reasoning = f"Condition {matched_condition.get('type')} triggered"

        for action in self.actions:
            action_type = action.get("type", "")
            if action_type == "buy":
                amount_percent = action.get("amount_percent", 10)
                amount = self.current_balance * (amount_percent / 100)
                quantity = amount / price
                
                self.position += quantity
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
                        "quantity": quantity,
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

    def stop(self):
        """Stop the simulation."""
        self.running = False
        self.status = "stopped"

    def get_results(self) -> Dict[str, Any]:
        """Get simulation results."""
        return {
            "id": self.run_id,
            "status": self.status,
            "results": self.results,
            "signals": self.signals,
        }

    def get_signals(self) -> List[Dict[str, Any]]:
        """Get current signals."""
        return self.signals
