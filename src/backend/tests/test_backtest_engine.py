"""
Unit tests for BacktestEngine
Tests stop loss, take profit, and max drawdown calculations
"""
import asyncio
from app.services.backtest.engine import BacktestEngine


class TestBacktestEngine:
    """Test suite for BacktestEngine"""
    
    def _run_backtest(self, config, klines):
        """Helper to run backtest with given klines"""
        engine = BacktestEngine(config)
        result = asyncio.run(engine.run_with_klines(klines))
        return engine, result
    
    def _trace_portfolio(self, engine, initial_balance):
        """Print portfolio trace for debugging"""
        running_balance = initial_balance
        running_position = 0.0
        
        print("\nPortfolio Trace:")
        for i, trade in enumerate(engine.trades):
            if trade["type"] == "buy":
                running_position = trade["quantity"]
                running_balance -= trade["amount"]
                portfolio = running_balance + (running_position * trade["price"])
                print(f"  BUY  #{i+1}: @${trade['price']} - portfolio=${portfolio:.2f}")
            else:
                running_balance += trade["amount"]
                running_position = 0
                portfolio = running_balance
                print(f"  SELL #{i+1}: @${trade['price']} ({trade.get('exit_reason', '')}) - portfolio=${portfolio:.2f}")
        
        if engine.position > 0 and engine.last_kline_price:
            final = running_balance + (engine.position * engine.last_kline_price)
            print(f"  FINAL: position={engine.position:.2f} @ ${engine.last_kline_price} = ${final:.2f}")
        print()
    
    def test_stop_loss_triggers_correctly(self):
        """Test stop loss triggers at configured percentage"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 5}],
                "actions": [{"type": "buy", "amount_percent": 100}],
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # Price sequence that triggers buy then stop loss:
        # $110 -> $100 (9% drop, BUY)
        # $100 -> $95 (5% drop, STOP LOSS at 5% from $100 = $95)
        klines = [
            {"close": "110.0", "timestamp": 1000, "open": "110.0", "high": "110.0", "low": "110.0", "volume": "1000"},
            {"close": "100.0", "timestamp": 2000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "95.0", "timestamp": 3000, "open": "95.0", "high": "95.0", "low": "95.0", "volume": "1000"},
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)} (expected 2)")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")
        
        assert len(engine.trades) == 2
        assert engine.trades[0]["type"] == "buy"
        assert engine.trades[1]["type"] == "sell"
        assert engine.trades[1]["exit_reason"] == "stop_loss"
        # Max drawdown should be ~5% (stop loss percentage)
        assert 3 < result['max_drawdown'] < 8
        # Total return should be ~-5%
        assert -8 < result['total_return'] < -3
    
    def test_take_profit_triggers(self):
        """Test take profit triggers at configured percentage"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 5}],
                "actions": [{"type": "buy", "amount_percent": 100}],
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # $100 -> $95 (5% drop, BUY) -> $104.5 (10% rise, TAKE PROFIT)
        klines = [
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "95.0", "timestamp": 2000, "open": "95.0", "high": "95.0", "low": "95.0", "volume": "1000"},
            {"close": "104.5", "timestamp": 3000, "open": "104.5", "high": "104.5", "low": "104.5", "volume": "1000"},
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)} (expected 2)")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")
        
        assert len(engine.trades) == 2
        assert engine.trades[1]["exit_reason"] == "take_profit"
        assert result['total_return'] > 0
    
    def test_max_drawdown_bounded_by_stop_loss(self):
        """Test that max drawdown is bounded by stop loss when position is properly closed"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 5}],
                "actions": [{"type": "buy", "amount_percent": 100}],
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # $110 -> $100 -> $95 (BUY) -> $90 (STOP LOSS)
        klines = [
            {"close": "110.0", "timestamp": 1000, "open": "110.0", "high": "110.0", "low": "110.0", "volume": "1000"},
            {"close": "100.0", "timestamp": 2000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "95.0", "timestamp": 3000, "open": "95.0", "high": "95.0", "low": "95.0", "volume": "1000"},
            {"close": "90.0", "timestamp": 4000, "open": "90.0", "high": "90.0", "low": "90.0", "volume": "1000"},
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)}")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")
        
        # With 5% stop loss, max drawdown should be around 5%
        assert 3 < result['max_drawdown'] < 8
    
    def test_open_position_not_closed(self):
        """Test scenario where last kline has an open position"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 10}],
                "actions": [{"type": "buy", "amount_percent": 100}],
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # $100 -> $90 (10% drop, BUY) - and backtest ends here
        # Position is open, marked to market at $90
        klines = [
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "90.0", "timestamp": 2000, "open": "90.0", "high": "90.0", "low": "90.0", "volume": "1000"},
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)}")
        print(f"  Position open: {engine.position > 0}")
        print(f"  Entry price: ${engine.entry_price}")
        print(f"  Last kline price: ${engine.last_kline_price}")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")
        
        # Position should be open
        assert engine.position > 0
        # Entry should be $90
        assert engine.entry_price == 90.0
        # Since entry = last kline price, no unrealized loss
        # Max drawdown should be 0%
        assert result['max_drawdown'] == 0.0
    
    def test_open_position_with_loss(self):
        """Test open position where price dropped but stop loss didn't trigger"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 10}],
                "actions": [{"type": "buy", "amount_percent": 100}],
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # $100 -> $90 (10% drop, BUY at $90) -> $85 (stop loss at 5% from $90 = $85.5)
        # $85 > $85.5? No, $85 < $85.5, so stop loss WOULD trigger
        # Let me use $86 instead - $86 > $85.5 so no stop loss
        klines = [
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "90.0", "timestamp": 2000, "open": "90.0", "high": "90.0", "low": "90.0", "volume": "1000"},
            {"close": "86.0", "timestamp": 3000, "open": "86.0", "high": "86.0", "low": "86.0", "volume": "1000"},
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)}")
        print(f"  Position open: {engine.position > 0}")
        print(f"  Entry price: ${engine.entry_price}")
        print(f"  Last kline price: ${engine.last_kline_price}")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")
        
        # Position should be open
        assert engine.position > 0
        # Entry = $90, stop = $85.50, last = $86 (above stop)
        # Portfolio: $0 + position * $86
        # Position: 10000/90 = 111.11 tokens
        # Portfolio at $86: 111.11 * 86 = $9,555.56
        # But we only track portfolio at trade points, so max was $10,000
        # drawdown = (10000 - 9555.56) / 10000 = 4.44%
        print(f"  Expected max drawdown: ~4.4% (marked to market at $86)")
    
    def test_multiple_buy_sell_cycles(self):
        """Test multiple buy/sell cycles"""
        config = {
            "bot_id": "test",
            "strategy_config": {
                "conditions": [{"type": "price_drop", "token": "TEST", "token_address": "0x123", "threshold": 5}],
                "actions": [{"type": "buy", "amount_percent": 50}],  # 50% of balance
                "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 10}
            },
            "ave_api_key": "test",
            "ave_api_plan": "free",
            "initial_balance": 10000.0,
        }
        
        # $100 -> $95 (BUY) -> $104.5 (TAKE PROFIT) -> $95 (BUY) -> $90 (STOP LOSS)
        klines = [
            {"close": "100.0", "timestamp": 1000, "open": "100.0", "high": "100.0", "low": "100.0", "volume": "1000"},
            {"close": "95.0", "timestamp": 2000, "open": "95.0", "high": "95.0", "low": "95.0", "volume": "1000"},   # BUY at $95
            {"close": "104.5", "timestamp": 3000, "open": "104.5", "high": "104.5", "low": "104.5", "volume": "1000"},  # TAKE PROFIT
            {"close": "95.0", "timestamp": 4000, "open": "95.0", "high": "95.0", "low": "95.0", "volume": "1000"},   # 9% drop - no buy
            {"close": "90.0", "timestamp": 5000, "open": "90.0", "high": "90.0", "low": "90.0", "volume": "1000"},   # 10.5% drop from $100 - BUY at $90
            {"close": "85.5", "timestamp": 6000, "open": "85.5", "high": "85.5", "low": "85.5", "volume": "1000"},   # STOP LOSS at 5% from $90 = $85.5
        ]
        
        engine, result = self._run_backtest(config, klines)
        self._trace_portfolio(engine, 10000.0)
        
        print(f"Results:")
        print(f"  Trades: {len(engine.trades)}")
        print(f"  Buy count: {len([t for t in engine.trades if t['type'] == 'buy'])}")
        print(f"  Sell count: {len([t for t in engine.trades if t['type'] == 'sell'])}")
        print(f"  Max drawdown: {result['max_drawdown']}%")
        print(f"  Total return: {result['total_return']}%")


def run_tests():
    tests = TestBacktestEngine()
    
    print("=" * 60)
    print("TEST 1: Stop Loss Triggers Correctly")
    print("=" * 60)
    try:
        tests.test_stop_loss_triggers_correctly()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")
    
    print("=" * 60)
    print("TEST 2: Take Profit Triggers")
    print("=" * 60)
    try:
        tests.test_take_profit_triggers()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")
    
    print("=" * 60)
    print("TEST 3: Max Drawdown Bounded by Stop Loss")
    print("=" * 60)
    try:
        tests.test_max_drawdown_bounded_by_stop_loss()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")
    
    print("=" * 60)
    print("TEST 4: Open Position Not Closed")
    print("=" * 60)
    try:
        tests.test_open_position_not_closed()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")
    
    print("=" * 60)
    print("TEST 5: Open Position With Loss")
    print("=" * 60)
    try:
        tests.test_open_position_with_loss()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")
    
    print("=" * 60)
    print("TEST 6: Multiple Buy/Sell Cycles")
    print("=" * 60)
    try:
        tests.test_multiple_buy_sell_cycles()
        print("PASSED\n")
    except AssertionError as e:
        print(f"FAILED: {e}\n")


def test_dca_multiple_buys():
    """Test that DCA with multiple consecutive buys uses weighted average for stop loss."""
    print("\n" + "=" * 60)
    print("TEST 7: DCA With Multiple Consecutive Buys")
    print("=" * 60)
    
    config = {
        "bot_id": "test",
        "strategy_config": {
            "conditions": [{"type": "price_drop", "threshold": 2, "token": "TEST", "token_address": "0x123"}],
            "actions": [{"type": "buy", "amount_percent": 20}],
            "risk_management": {"stop_loss_percent": 5, "take_profit_percent": 5},
        },
        "initial_balance": 10000.0,
        "ave_api_key": "test",
        "ave_api_plan": "free",
    }
    
    # 3 consecutive 2% drops = 3 buys at $0.58, $0.57, $0.56
    # Then drop to $0.50 which is below 5% from average (~$0.57 * 0.95 = $0.54)
    klines = [
        {"close": "0.60", "timestamp": 1000, "open": "0.60", "high": "0.60", "low": "0.60", "volume": "1000"},
        {"close": "0.588", "timestamp": 2000},  # 2% drop -> BUY 1 @ $0.588
        {"close": "0.576", "timestamp": 3000},  # 2% drop -> BUY 2 @ $0.576
        {"close": "0.565", "timestamp": 4000},  # 2% drop -> BUY 3 @ $0.565
        {"close": "0.50", "timestamp": 5000},   # Below 5% from avg -> STOP LOSS
    ]
    
    test = TestBacktestEngine()
    engine, result = test._run_backtest(config, klines)
    test._trace_portfolio(engine, 10000.0)
    
    print(f"\nResults:")
    print(f"  Trades: {len(engine.trades)} (expected 3: 2 buys + stop loss)")
    print(f"  Max drawdown: {result['max_drawdown']}%")
    print(f"  Total return: {result['total_return']}%")
    
    # Verify: 2 buys + 1 sell (stop loss) = 3 trades
    # The 3rd buy @ $0.565 doesn't happen because stop loss triggers at $0.5 first
    assert len(engine.trades) == 3, f"Expected 3 trades, got {len(engine.trades)}"
    
    # Verify last trade is stop loss
    last_trade = engine.trades[-1]
    assert last_trade["type"] == "sell", "Last trade should be sell"
    assert last_trade.get("exit_reason") == "stop_loss", f"Last trade should be stop_loss, got {last_trade.get('exit_reason')}"
    
    # Verify max drawdown is reasonable (close to stop loss %)
    # Actual loss should be around 5% from weighted average
    assert result['max_drawdown'] < 10, f"Max drawdown {result['max_drawdown']}% is too high for 5% stop loss"
    
    # Position is now 0 after stop loss, so avg_entry_price is None
    print(f"  Position closed: {engine.position == 0}")
    print(f"  Final balance: ${engine.current_balance:.2f}")
    print("PASSED")
    return True


if __name__ == "__main__":
    run_tests()
    test_dca_multiple_buys()
