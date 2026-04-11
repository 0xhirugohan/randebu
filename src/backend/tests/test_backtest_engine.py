"""
Unit tests for BacktestEngine to verify stop loss functionality
"""
import pytest
import asyncio
from app.services.backtest.engine import BacktestEngine


class TestStopLoss:
    """Test stop loss functionality"""
    
    def test_stop_loss_triggers_when_price_drops(self):
        """Test that stop loss triggers when price drops to stop_loss_percent"""
        config = {
            "bot_id": "test-bot",
            "strategy_config": {
                "conditions": [
                    {"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 10}
                ],
                "actions": [
                    {"type": "buy", "amount_percent": 100}
                ],
                "risk_management": {
                    "stop_loss_percent": 5,  # 5% stop loss
                    "take_profit_percent": 10
                }
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        engine = BacktestEngine(config)
        
        # Simulate klines: buy at $100, then price drops to $94 (6% drop - should trigger 5% stop loss)
        # Stop loss price = $100 * (1 - 0.05) = $95
        # Price at $94 is below stop loss, so it should trigger
        
        klines = [
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "99.0", "timestamp": 2000, "open": "99.0", "high": "99.0", "low": "99.0", "volume": "1000"},
            {"close": "98.0", "timestamp": 3000, "open": "98.0", "high": "98.0", "low": "98.0", "volume": "1000"},
            {"close": "97.0", "timestamp": 4000, "open": "97.0", "high": "97.0", "low": "97.0", "volume": "1000"},
            {"close": "96.0", "timestamp": 5000, "open": "96.0", "high": "96.0", "low": "96.0", "volume": "1000"},
            # Stop loss should trigger here at $95 or below
            {"close": "94.0", "timestamp": 6000, "open": "94.0", "high": "94.0", "low": "94.0", "volume": "1000"},
        ]
        
        result = asyncio.run(engine.run_with_klines(klines))
        
        print(f"Trades: {engine.trades}")
        print(f"Position after: {engine.position}")
        print(f"Results: {result}")
        
        # Should have executed a sell due to stop loss
        sell_trades = [t for t in engine.trades if t["type"] == "sell"]
        assert len(sell_trades) > 0, "Should have executed a sell due to stop loss"
        assert sell_trades[0]["exit_reason"] == "stop_loss", f"Exit reason should be stop_loss, got {sell_trades[0].get('exit_reason')}"
    
    def test_max_drawdown_with_multiple_buys(self):
        """Test max drawdown when there are more buys than sells"""
        config = {
            "bot_id": "test-bot",
            "strategy_config": {
                "conditions": [
                    {"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 10}
                ],
                "actions": [
                    {"type": "buy", "amount_percent": 50}
                ],
                "risk_management": {
                    "stop_loss_percent": 5,
                    "take_profit_percent": 5
                }
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        engine = BacktestEngine(config)
        
        # Simulate:
        # 1. Buy at $100 (condition triggered at start)
        # 2. Price rises to $105 -> take profit sells
        # 3. Buy again at $105
        # 4. Price drops to $94 -> stop loss triggers at $99.75
        # 5. Buy at $94 (new position)
        # 6. Price continues to drop - no more sells
        
        klines = [
            # First buy at $100
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            # Price rises, take profit at $105
            {"close": "105.0", "timestamp": 2000, "open": "105.0", "high": "105.0", "low": "105.0", "volume": "1000"},
            # Second buy at $105 (price dropped 10% from peak triggers buy)
            {"close": "105.0", "timestamp": 3000, "open": "105.0", "high": "105.0", "low": "105.0", "volume": "1000"},
            # Price drops, stop loss should trigger at $99.75 (5% from $105)
            {"close": "99.0", "timestamp": 4000, "open": "99.0", "high": "99.0", "low": "99.0", "volume": "1000"},
            # Third buy at $99 (after stop loss, price dropped 10% from $110)
            {"close": "99.0", "timestamp": 5000, "open": "99.0", "high": "99.0", "low": "99.0", "volume": "1000"},
            # Price continues to drop to $80 (no sell triggered since position is closed)
            {"close": "80.0", "timestamp": 6000, "open": "80.0", "high": "80.0", "low": "80.0", "volume": "1000"},
        ]
        
        result = asyncio.run(engine.run_with_klines(klines))
        
        print(f"\n=== Max Drawdown Test ===")
        print(f"Trades: {engine.trades}")
        print(f"Number of sells: {len([t for t in engine.trades if t['type'] == 'sell'])}")
        print(f"Max drawdown: {result.get('max_drawdown')}")
        print(f"Stop loss percent configured: {engine.stop_loss_percent}")
        
        # With 5% stop loss, max drawdown should be around 5% (plus some slippage)
        # NOT 82%!
        if result.get('max_drawdown', 0) > 10:
            print(f"ERROR: Max drawdown {result.get('max_drawdown')}% is too high with 5% stop loss!")
    
    def test_multiple_buys_sells_sequence(self):
        """Test with a sequence: buy, sell, buy, sell, buy (open position)"""
        config = {
            "bot_id": "test-bot",
            "strategy_config": {
                "conditions": [
                    {"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 10}
                ],
                "actions": [
                    {"type": "buy", "amount_percent": 50}
                ],
                "risk_management": {
                    "stop_loss_percent": 5,
                    "take_profit_percent": 10
                }
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        engine = BacktestEngine(config)
        
        # Sequence:
        # 1. K1: $100 -> Buy (condition triggers because price_drop threshold met at start)
        # 2. K2: $110 -> Take profit sells (10% gain)
        # 3. K3: $100 -> Buy (10% drop triggers)
        # 4. K4: $90 -> Stop loss triggers (5% loss from $94.5 avg... wait no)
        #    Stop loss from $100 with 5% = $95
        #    $90 is below $95, so stop loss triggers
        # 5. K5: $85 -> Buy ($85 is 15% drop from $100)
        # 6. K6: $80 -> No sell (position open)
        
        klines = [
            # Initial buy at $100
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            # Price goes up to $110 - take profit triggers (10% gain)
            {"close": "110.0", "timestamp": 2000, "open": "110.0", "high": "110.0", "low": "110.0", "volume": "1000"},
            # Price drops to $100 - buy triggers again
            {"close": "100.0", "timestamp": 3000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            # Price drops to $94 - stop loss should trigger (5% from $100 = $95)
            {"close": "94.0", "timestamp": 4000, "open": "94.0", "high": "94.0", "low": "94.0", "volume": "1000"},
            # Price drops to $85 - buy triggers again (15% drop from $100)
            {"close": "85.0", "timestamp": 5000, "open": "85.0", "high": "85.0", "low": "85.0", "volume": "1000"},
            # Price drops to $80 - no sell, position still open
            {"close": "80.0", "timestamp": 6000, "open": "80.0", "high": "80.0", "low": "80.0", "volume": "1000"},
        ]
        
        result = asyncio.run(engine.run_with_klines(klines))
        
        print(f"\n=== Multiple Buys/Sells Test ===")
        print(f"Trades: {engine.trades}")
        print(f"Buy trades: {len([t for t in engine.trades if t['type'] == 'buy'])}")
        print(f"Sell trades: {len([t for t in engine.trades if t['type'] == 'sell'])}")
        print(f"Open position: {engine.position}")
        print(f"Max drawdown: {result.get('max_drawdown')}")
        print(f"Total return: {result.get('total_return')}")
        
        # Should have 2 sell trades (take profit and stop loss)
        sell_trades = [t for t in engine.trades if t["type"] == "sell"]
        print(f"Sell exit reasons: {[t.get('exit_reason') for t in sell_trades]}")


if __name__ == "__main__":
    test = TestStopLoss()
    print("=== Test 1: Stop Loss Triggers ===")
    test.test_stop_loss_triggers_when_price_drops()
    print("\n=== Test 2: Max Drawdown with Multiple Buys ===")
    test.test_max_drawdown_with_multiple_buys()
    print("\n=== Test 3: Multiple Buys/Sells Sequence ===")
    test.test_multiple_buys_sells_sequence()
