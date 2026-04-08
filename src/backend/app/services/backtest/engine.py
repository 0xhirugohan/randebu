import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from .ave_client import AveCloudClient


class BacktestEngine:
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
        self.initial_balance = config.get("initial_balance", 10000.0)
        self.current_balance = self.initial_balance
        self.position = 0.0
        self.position_token = ""
        self.trades: List[Dict[str, Any]] = []
        self.running = False

    async def run(self) -> Dict[str, Any]:
        self.running = True
        self.status = "running"
        started_at = datetime.utcnow()

        try:
            token = self.config.get("token", "")
            chain = self.config.get("chain", "bsc")
            timeframe = self.config.get("timeframe", "1h")
            start_date = self.config.get("start_date", "")
            end_date = self.config.get("end_date", "")

            token_id = (
                f"{token}-{chain}"
                if token and not token.endswith(f"-{chain}")
                else token
            )

            if not token_id or token_id == f"-{chain}":
                raise ValueError("Token ID is required")

            start_ts = None
            end_ts = None
            if start_date:
                start_ts = int(
                    datetime.fromisoformat(
                        start_date.replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )
            if end_date:
                end_ts = int(
                    datetime.fromisoformat(end_date.replace("Z", "+00:00")).timestamp()
                    * 1000
                )

            klines = await self.ave_client.get_klines(
                token_id=token_id,
                interval=timeframe,
                limit=1000,
                start_time=start_ts,
                end_time=end_ts,
            )

            if not klines:
                self.status = "failed"
                self.results = {"error": "No kline data available"}
                return self.results

            await self._process_klines(klines)
            self._calculate_metrics()
            self.status = "completed"

        except Exception as e:
            self.status = "failed"
            self.results = {"error": str(e)}

        ended_at = datetime.utcnow()
        self.results = self.results or {}
        self.results["started_at"] = started_at
        self.results["ended_at"] = ended_at
        self.results["duration_seconds"] = (ended_at - started_at).total_seconds()

        return self.results

    async def _process_klines(self, klines: List[Dict[str, Any]]):
        for i, kline in enumerate(klines):
            if not self.running:
                break

            price = float(kline.get("close", 0))
            if price <= 0:
                continue

            timestamp = kline.get("timestamp", 0)

            for condition in self.conditions:
                if self._check_condition(condition, klines, i, price):
                    await self._execute_actions(price, timestamp, condition)
                    break

    def _check_condition(
        self,
        condition: Dict[str, Any],
        klines: List[Dict[str, Any]],
        current_idx: int,
        current_price: float,
    ) -> bool:
        cond_type = condition.get("type", "")
        threshold = condition.get("threshold", 0)
        timeframe = condition.get("timeframe", "1h")
        price_level = condition.get("price")
        direction = condition.get("direction", "above")

        if cond_type == "price_drop":
            if current_idx == 0:
                return False
            prev_price = float(klines[current_idx - 1].get("close", 0))
            if prev_price <= 0:
                return False
            drop_pct = ((prev_price - current_price) / prev_price) * 100
            return drop_pct >= threshold

        elif cond_type == "price_rise":
            if current_idx == 0:
                return False
            prev_price = float(klines[current_idx - 1].get("close", 0))
            if prev_price <= 0:
                return False
            rise_pct = ((current_price - prev_price) / prev_price) * 100
            return rise_pct >= threshold

        elif cond_type == "volume_spike":
            if current_idx == 0:
                return False
            prev_volume = float(klines[current_idx - 1].get("volume", 0))
            current_volume = float(kline.get("volume", 0))
            if prev_volume <= 0:
                return False
            volume_increase = ((current_volume - prev_volume) / prev_volume) * 100
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
        token = matched_condition.get("token", self.config.get("token", ""))

        for action in self.actions:
            action_type = action.get("type", "")
            amount_percent = action.get("amount_percent", 10)
            amount = self.current_balance * (amount_percent / 100)

            if action_type == "buy" and self.current_balance >= amount:
                self.position += amount / price
                self.current_balance -= amount
                self.position_token = token
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
                self.signals.append(
                    {
                        "id": str(uuid.uuid4()),
                        "bot_id": self.bot_id,
                        "run_id": self.run_id,
                        "signal_type": "buy",
                        "token": token,
                        "price": price,
                        "confidence": 0.8,
                        "reasoning": f"Condition {matched_condition.get('type')} triggered buy",
                        "executed": False,
                        "created_at": datetime.utcnow(),
                    }
                )

            elif action_type == "sell" and self.position > 0:
                sell_amount = self.position * price
                self.current_balance += sell_amount
                self.trades.append(
                    {
                        "type": "sell",
                        "token": self.position_token,
                        "price": price,
                        "amount": sell_amount,
                        "quantity": self.position,
                        "timestamp": timestamp,
                    }
                )
                self.position = 0
                self.signals.append(
                    {
                        "id": str(uuid.uuid4()),
                        "bot_id": self.bot_id,
                        "run_id": self.run_id,
                        "signal_type": "sell",
                        "token": self.position_token,
                        "price": price,
                        "confidence": 0.8,
                        "reasoning": f"Condition {matched_condition.get('type')} triggered sell",
                        "executed": False,
                        "created_at": datetime.utcnow(),
                    }
                )

    def _calculate_metrics(self):
        final_balance = self.current_balance + (
            self.position * self.trades[-1]["price"]
            if self.trades and self.position > 0
            else 0
        )
        total_return = (
            (final_balance - self.initial_balance) / self.initial_balance
        ) * 100

        buy_trades = [t for t in self.trades if t["type"] == "buy"]
        sell_trades = [t for t in self.trades if t["type"] == "sell"]
        total_trades = len(buy_trades) + len(sell_trades)

        winning_trades = 0
        for i, trade in enumerate(sell_trades):
            if i < len(buy_trades):
                buy_price = buy_trades[i]["price"]
                sell_price = trade["price"]
                if sell_price > buy_price:
                    winning_trades += 1

        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        portfolio_values = []
        running_balance = self.initial_balance
        running_position = 0.0
        current_token = ""
        last_price = 0.0

        for trade in self.trades:
            if trade["type"] == "buy":
                running_position = trade["quantity"]
                running_balance = trade["amount"]
                current_token = trade["token"]
                last_price = trade["price"]
            else:
                running_balance = trade["amount"]
                running_position = 0
                last_price = trade["price"]

            portfolio_value = running_balance + (running_position * last_price)
            portfolio_values.append(portfolio_value)

        max_value = self.initial_balance
        max_drawdown = 0.0
        for value in portfolio_values:
            if value > max_value:
                max_value = value
            drawdown = ((max_value - value) / max_value) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        sharpe_ratio = 0.0
        if len(portfolio_values) > 1:
            returns = []
            for i in range(1, len(portfolio_values)):
                ret = (
                    portfolio_values[i] - portfolio_values[i - 1]
                ) / portfolio_values[i - 1]
                returns.append(ret)
            if returns:
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_dev = variance**0.5
                if std_dev > 0:
                    sharpe_ratio = avg_return / std_dev

        buy_signals = len(buy_trades)
        sell_signals = len(sell_trades)

        self.results = {
            "total_return": round(total_return, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": total_trades,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "final_balance": round(final_balance, 2),
            "signals": self.signals,
        }

    async def stop(self):
        self.running = False
        self.status = "stopped"
        self._calculate_metrics()

    def get_results(self) -> Dict[str, Any]:
        return {
            "id": self.run_id,
            "status": self.status,
            "results": self.results,
            "signals": self.signals,
        }
