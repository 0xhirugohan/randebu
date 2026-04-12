import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import sys
sys.path.insert(0, 'src/backend')

from app.services.simulate.engine import SimulateEngine


class MockAveClient:
    """Mock AVE client for testing."""
    
    def __init__(self, klines_data=None):
        self.klines_data = klines_data or []
    
    async def get_klines(self, token_id, interval="1m", limit=100, start_time=None, end_time=None):
        return self.klines_data


def create_engine(config_override=None, klines_data=None):
    """Create a test engine with mock client."""
    config = {
        "bot_id": "test-bot",
        "token": "0x1234567890123456789012345678901234567890",
        "chain": "bsc",
        "kline_interval": "1m",
        "max_candles": 10,  # Small number for fast tests
        "candle_delay": 0,  # No delay in tests
        "auto_execute": False,
        "strategy_config": {
            "conditions": [
                {"type": "price_drop", "threshold": 5, "token": "TEST", "token_address": "0x1234"}
            ],
            "actions": [
                {"type": "buy", "amount_percent": 10}
            ],
            "risk_management": {
                "stop_loss_percent": 5,
                "take_profit_percent": 10
            }
        },
        "ave_api_key": "test",
        "ave_api_plan": "free",
    }
    if config_override:
        config.update(config_override)
    
    engine = SimulateEngine(config)
    engine.ave_client = MockAveClient(klines_data)
    return engine


class TestSimulateEngine:
    """Unit tests for SimulateEngine."""
    
    # ==================== Kline Fetching Tests ====================
    
    @pytest.mark.asyncio
    async def test_fetches_klines_on_start(self):
        """Engine should fetch klines when run is called."""
        klines = [
            {"time": 1000, "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000},
            {"time": 2000, "open": 102, "high": 107, "low": 100, "close": 104, "volume": 1100},
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        assert engine.status == "completed"
        assert results["candles_processed"] == 2
    
    @pytest.mark.asyncio
    async def test_handles_no_klines_data(self):
        """Engine should handle empty klines gracefully."""
        engine = create_engine(klines_data=[])
        engine.running = True
        
        results = await engine.run()
        
        assert engine.status == "failed"
        assert "error" in results
        assert "No kline data" in results["error"]
    
    # ==================== Price Drop Condition Tests ====================
    
    @pytest.mark.asyncio
    async def test_price_drop_condition_triggers_buy(self):
        """Price drop >= threshold should trigger BUY signal."""
        # Price drops from 100 to 90 (10% drop) - should trigger 5% threshold
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # 10% drop
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        assert results["total_signals"] >= 1
        buy_signals = [s for s in engine.signals if s["signal_type"] == "buy"]
        assert len(buy_signals) >= 1
        assert buy_signals[0]["price"] == 90.0
    
    @pytest.mark.asyncio
    async def test_price_drop_below_threshold_no_signal(self):
        """Price drop < threshold should NOT trigger signal."""
        # Price drops from 100 to 98 (2% drop) - below 5% threshold
        klines = [
            {"time": 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 97, "close": 98, "volume": 1000},  # 2% drop
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        assert results["total_signals"] == 0
    
    # ==================== Risk Management Tests ====================
    
    @pytest.mark.asyncio
    async def test_stop_loss_triggers_after_buy(self):
        """Stop loss should trigger SELL after price drops below threshold."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # BUY triggered @ 90
            {"time": 3000, "open": 90, "high": 91, "low": 84, "close": 85, "volume": 1300},  # Stop loss @ 85.5 (90 * 0.95)
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        buy_signals = [s for s in engine.signals if s["signal_type"] == "buy"]
        sell_signals = [s for s in engine.signals if s["signal_type"] == "sell"]
        
        assert len(buy_signals) >= 1, "Should have at least one BUY signal"
        assert len(sell_signals) >= 1, "Stop loss should trigger SELL"
        assert "stop_loss" in sell_signals[0]["reasoning"]
    
    @pytest.mark.asyncio
    async def test_take_profit_triggers_after_buy(self):
        """Take profit should trigger SELL after price rises above threshold."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # BUY triggered @ 90
            {"time": 3000, "open": 90, "high": 101, "low": 89, "close": 100, "volume": 1300},  # TP @ 99 (90 * 1.10)
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        buy_signals = [s for s in engine.signals if s["signal_type"] == "buy"]
        sell_signals = [s for s in engine.signals if s["signal_type"] == "sell"]
        
        assert len(buy_signals) >= 1, "Should have at least one BUY signal"
        assert len(sell_signals) >= 1, "Take profit should trigger SELL"
        assert "take_profit" in sell_signals[0]["reasoning"]
    
    # ==================== Multiple Conditions Tests ====================
    
    @pytest.mark.asyncio
    async def test_no_buy_if_already_in_position(self):
        """Should not trigger another BUY if already holding position."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # BUY triggered
            {"time": 3000, "open": 90, "high": 91, "low": 85, "close": 86, "volume": 1300},  # Another drop but already in position
            {"time": 4000, "open": 86, "high": 87, "low": 81, "close": 82, "volume": 1400},  # Another drop
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        buy_signals = [s for s in engine.signals if s["signal_type"] == "buy"]
        
        # Should only have 1 buy, not multiple
        assert len(buy_signals) == 1, "Should only have one BUY signal"
    
    @pytest.mark.asyncio
    async def test_can_buy_again_after_sell(self):
        """Should be able to BUY again after position is closed by risk management."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            # First trade
            {"time": 2000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # BUY @ 90
            {"time": 3000, "open": 90, "high": 91, "low": 84, "close": 85, "volume": 1300},  # STOP LOSS @ 85.5
            # Second trade
            {"time": 4000, "open": 85, "high": 86, "low": 79, "close": 80, "volume": 1400},  # BUY @ 80 (after position closed)
            {"time": 5000, "open": 80, "high": 89, "low": 79, "close": 88, "volume": 1500},  # TP @ 88
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        buy_signals = [s for s in engine.signals if s["signal_type"] == "buy"]
        sell_signals = [s for s in engine.signals if s["signal_type"] == "sell"]
        
        assert len(buy_signals) == 2, "Should have two BUY signals"
        assert len(sell_signals) == 2, "Should have two SELL signals"
    
    # ==================== Edge Cases ====================
    
    @pytest.mark.asyncio
    async def test_handles_zero_price(self):
        """Should skip processing for candles with zero price but still count them."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0},  # Skipped in processing
            {"time": 3000, "open": 100, "high": 101, "low": 89, "close": 90, "volume": 1200},  # This should work
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        results = await engine.run()
        
        # All 3 candles counted, but only 2 valid for condition checking
        assert results["candles_processed"] == 3
        # Only 1 signal (the valid candle that dropped 10%)
        assert results["total_signals"] == 1
    
    @pytest.mark.asyncio
    async def test_max_candles_limit(self):
        """Should respect max_candles limit."""
        klines = [
            {"time": i * 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}
            for i in range(1, 201)  # 200 candles
        ]
        engine = create_engine(klines_data=klines, config_override={"max_candles": 50})
        engine.running = True
        
        results = await engine.run()
        
        assert results["candles_processed"] == 50
    
    @pytest.mark.asyncio
    async def test_stop_interrupts_processing(self):
        """Should stop processing when stop() is called."""
        klines = [
            {"time": i * 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}
            for i in range(1, 101)
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        engine.run_id = "test"
        
        # Stop after a few candles
        async def stop_after_delay():
            await asyncio.sleep(0.1)
            engine.stop()
        
        await asyncio.gather(engine.run(), stop_after_delay())
        
        assert engine.status == "stopped"
        # Should have processed some candles before stopping
        assert engine.last_processed_time is not None
    
    # ==================== Price Movement Display Tests ====================
    
    @pytest.mark.asyncio
    async def test_records_all_processed_prices(self):
        """Should track last processed time for display purposes."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 101, "low": 99, "close": 101, "volume": 1100},
            {"time": 3000, "open": 101, "high": 103, "low": 100, "close": 102, "volume": 1200},
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        await engine.run()
        
        # Should have tracked the last candle's time
        assert engine.last_processed_time == 3000
    
    @pytest.mark.asyncio
    async def test_tracks_price_changes(self):
        """Should track price changes for potential chart display."""
        klines = [
            {"time": 1000, "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"time": 2000, "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1100},
        ]
        engine = create_engine(klines_data=klines)
        engine.running = True
        
        await engine.run()
        
        # Last close should be the last candle's close
        assert engine.last_close == 104.0

    # ==================== Integration Tests ====================
    
    @pytest.mark.asyncio
    async def test_full_simulation_workflow_generates_signals_and_trades(self):
        """
        Full integration test: provides klines with clear price movements
        and verifies signals and trade_log are populated.
        
        This test ensures the simulation is working by:
        1. Creating klines with obvious price movements (drops > 0.1%)
        2. Using a very low threshold (0.1%)
        3. Verifying signals are generated
        4. Verifying trade_log is populated
        5. Verifying we have buy/sell actions
        """
        # Create klines with clear price drops and rises
        klines = [
            {"time": 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},  # Flat
            {"time": 2000, "open": 100, "high": 101, "low": 99.9, "close": 99.95, "volume": 1000},  # 0.05% drop
            {"time": 3000, "open": 99.95, "high": 100, "low": 99.5, "close": 99.5, "volume": 1000},  # 0.45% drop
            {"time": 4000, "open": 99.5, "high": 100, "low": 99, "close": 99.2, "volume": 1000},   # 0.30% drop
            {"time": 5000, "open": 99.2, "high": 100, "low": 98, "close": 98.5, "volume": 1000},   # 0.71% drop
            {"time": 6000, "open": 98.5, "high": 99, "low": 98, "close": 98.8, "volume": 1000},    # 0.30% rise
            {"time": 7000, "open": 98.8, "high": 99, "low": 98, "close": 98.3, "volume": 1000},   # 0.51% drop
            {"time": 8000, "open": 98.3, "high": 99, "low": 97, "close": 97.5, "volume": 1000},   # 0.81% drop
            {"time": 9000, "open": 97.5, "high": 98, "low": 96, "close": 96.5, "volume": 1000},   # 1.03% drop
        ]
        
        # Use very low threshold to ensure signals are generated
        config_override = {
            "max_candles": 100,
            "strategy_config": {
                "conditions": [
                    {"type": "price_drop", "threshold": 0.1, "token": "TEST", "token_address": "0x1234"}
                ],
                "actions": [
                    {"type": "buy", "amount_percent": 10}
                ],
                "risk_management": {
                    "stop_loss_percent": 5,
                    "take_profit_percent": 5
                }
            }
        }
        
        engine = create_engine(config_override=config_override, klines_data=klines)
        engine.running = True
        engine.run_id = "integration-test"
        
        results = await engine.run()
        
        # Verify results
        print(f"\n=== Integration Test Results ===")
        print(f"Status: {engine.status}")
        print(f"Candles processed: {results.get('candles_processed')}")
        print(f"Signals count: {len(engine.signals)}")
        print(f"Trade log count: {len(engine.trade_log)}")
        
        # ASSERTIONS - These should NEVER fail if simulation is working
        assert engine.status == "completed", "Simulation should complete successfully"
        assert results.get("candles_processed") == len(klines), f"Should process all {len(klines)} candles"
        
        # Critical: signals should NOT be empty
        assert len(engine.signals) > 0, "SIGNALS SHOULD NOT BE EMPTY! Simulation is not generating signals."
        print(f"Signals: {[s['signal_type'] for s in engine.signals]}")
        
        # Critical: trade_log should NOT be empty
        assert len(engine.trade_log) > 0, "TRADE_LOG SHOULD NOT BE EMPTY! No activity logged."
        print(f"Trade log: {[t['action'] for t in engine.trade_log]}")
        
        # Should have at least one BUY signal
        buy_signals = [s for s in engine.signals if s['signal_type'] == 'buy']
        assert len(buy_signals) > 0, "Should have at least one BUY signal"
        print(f"Buy signals: {len(buy_signals)}")
        
        # Verify trade_log has BUY action
        buy_trades = [t for t in engine.trade_log if t['action'] == 'buy']
        assert len(buy_trades) > 0, "Trade log should contain BUY actions"
        
        # Verify results contain the data
        assert "signals" in results, "Results should contain signals"
        assert "trade_log" in results, "Results should contain trade_log"
        
        print("\n=== Integration Test PASSED ===")
        print(f"Simulation working correctly!")
        print(f"Generated {len(engine.signals)} signals and {len(engine.trade_log)} trade log entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
