"""
Conversational Trading Agent

This agent can:
1. Have normal conversations with users
2. Update trading strategies when user provides specific instructions

Uses MiniMax extended thinking API for proper thinking/reasoning separation.
"""

import json
import re
import requests
from typing import List, Optional, Dict, Any
from datetime import timedelta

from ...core.config import get_settings
from ...db.models import Bot


SYSTEM_PROMPT = """You are a helpful AI trading assistant named Randebu. You help users manage their trading bots.

IMPORTANT CHAIN LIMITATION:
- We ONLY support BSC (Binance Smart Chain) blockchain
- If user asks about any other chain (Solana, ETH, Base, etc.), respond with: "Currently we only support BSC (Binance Smart Chain). All trading strategies and token searches are performed on BSC."
- Never search or recommend tokens on other chains
- The search_tokens tool defaults to BSC, never change this

Your response must be valid JSON with exactly this structure:
{
  "thinking": "Your internal reasoning and analysis (what you're thinking about)",
  "response": "Your actual response to the user (be concise and helpful)",
  "strategy_update": null or {
    "conditions": [{"type": "price_drop" | "price_rise" | "volume_spike" | "price_level", "token": "TOKEN_SYMBOL", "token_address": null, "threshold": number, ...}],
    "actions": [{"type": "buy" | "sell" | "hold", "amount_percent": number, ...}],
    "risk_management": {"stop_loss_percent": number, "take_profit_percent": number}
  }
}

Guidelines:
- "thinking" should be detailed reasoning about the user's request
- "response" should be conversational and clear
- "strategy_update" should be populated ONLY when the user provides specific trading parameters (percentages, tokens, conditions, etc.)
- IMPORTANT: When a token is mentioned, set "token_address": null and ask user to confirm the token address before saving. Your response should say something like: "I need to confirm the token address. Could you provide the contract address for [TOKEN]?"
- If no strategy parameters are provided, set "strategy_update" to null
- Be friendly, concise, and helpful in your response

Example 1 (no strategy update):
User: "What can this bot do?"
{
  "thinking": "The user is asking about the bot's capabilities. I should explain the main features.",
  "response": "Randebu is your AI trading assistant! It can monitor cryptocurrency prices and execute trades based on your configured strategies. Tell me your trading parameters and I'll set them up for you.",
  "strategy_update": null
}

Example 2 (token needs confirmation):
User: "I want to buy PEPE when it drops 10%"
{
  "thinking": "User wants to buy PEPE. I need the token contract address to proceed. I should ask for confirmation.",
  "response": "I'd be happy to set up a buy order for PEPE! However, I need to confirm the token contract address. Could you provide the BSC contract address for PEPE? (It usually starts with 0x...)",
  "strategy_update": {
    "conditions": [{"type": "price_drop", "token": "PEPE", "token_address": null, "threshold": 10}],
    "actions": [{"type": "buy", "amount_percent": 100}],
    "risk_management": null
  }
}

Example 3 (with token address provided by user):
User: "Buy 0x6982508145454Ce125dDE157d8d64a26D53f60a2 when it drops 10%"
{
  "thinking": "User provided a contract address, I can use it directly.",
  "response": "Perfect! I've configured your strategy to buy the token when it drops 10%.",
  "strategy_update": {
    "conditions": [{"type": "price_drop", "token": "TOKEN", "token_address": "0x6982508145454Ce125dDE157d8d64a26D53f60a2", "threshold": 10}],
    "actions": [{"type": "buy", "amount_percent": 100}],
    "risk_management": null
  }
}"""


# Tool definitions for the agent
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_tokens",
            "description": "Search for trending tokens on BSC blockchain. Use this when user asks for token recommendations, trending tokens, or wants to discover new tokens to trade. ALWAYS uses BSC chain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of tokens to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "Run a backtest to evaluate how the current trading strategy would have performed historically. Returns key metrics like ROI, win rate, max drawdown, etc. Use this when user asks to backtest, test strategy, or check historical performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "token_address": {
                        "type": "string",
                        "description": "The BSC contract address of the token to backtest (required)"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for klines: '1d' (1 day), '4h' (4 hours), '1h' (1 hour), '15m' (15 minutes)",
                        "default": "1d"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for backtest in YYYY-MM-DD format (e.g., '2024-01-01')"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for backtest in YYYY-MM-DD format (e.g., '2024-12-01')"
                    }
                },
                "required": ["token_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_simulation",
            "description": "Manage trading simulations: start, stop, or check status. Simulations run on real-time klines and show live portfolio updates. Use when user asks to run simulation, check simulation status, or stop simulation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "status", "results"],
                        "description": "Action to perform: 'start' (begin new simulation), 'stop' (stop running simulation), 'status' (check if simulation is running), 'results' (get results from current or latest simulation)"
                    },
                    "token_address": {
                        "type": "string",
                        "description": "Token contract address for simulation (required for 'start' action)"
                    },
                    "kline_interval": {
                        "type": "string",
                        "description": "Kline interval: '1m', '5m', '15m', '1h' (default: '1m')",
                        "default": "1m"
                    }
                },
                "required": ["action"]
            }
        }
    }
]

SYSTEM_PROMPT_WITH_TOOLS = SYSTEM_PROMPT + """

You have access to tools:
- search_tokens(chain, limit): Search for trending tokens on a blockchain. Use it when user asks for token recommendations or trending tokens.
- run_backtest(token_address, timeframe, start_date, end_date): Run a backtest on historical data. Returns performance metrics. Use when user asks to backtest or check historical performance.
- manage_simulation(action, token_address, kline_interval): Manage trading simulations. Actions: 'start' (begin new), 'stop' (stop running), 'status' (check if running), 'results' (get current/latest results).

When you want to use a tool, respond with:
{
  "thinking": "...",
  "response": "Running backtest...",
  "tool_call": {"name": "run_backtest", "arguments": {"token_address": "0x...", "timeframe": "1d", "start_date": "2024-01-01", "end_date": "2024-12-01"}}
}
"""


class ConversationalAgent:
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", bot_id: str = None):
        self.api_key = api_key
        self.model = model
        self.bot_id = bot_id
        
        # Extended thinking endpoint
        self.thinking_endpoint = "https://api.minimax.io/v1/text/chatcompletion_v2"
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a user message and return a structured response.
        
        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages
            
        Returns:
            Dict with 'response', 'thinking', and 'strategy_updated'
        """
        try:
            # Build messages array with system prompt and conversation history
            messages = [{"role": "system", "content": SYSTEM_PROMPT_WITH_TOOLS}]
            
            # Add conversation history (last 10 messages)
            if conversation_history:
                for msg in conversation_history[-10:]:
                    role = "assistant" if msg.get("role") == "assistant" else "user"
                    messages.append({"role": role, "content": msg.get("content", "")})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Make API call to extended thinking endpoint
            resp = requests.post(
                self.thinking_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "thinking": {
                        "type": "human",
                        "budget_tokens": 1500
                    },
                    "tools": TOOLS
                }
            )
            
            result = resp.json()
            
            # Extract thinking from reasoning_content
            thinking = None
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    message = choice["message"]
                    thinking = message.get("reasoning_content")
                    
                    # Check for native function calls (tool_calls)
                    tool_calls = message.get("tool_calls", [])
                    if tool_calls:
                        for tool_call in tool_calls:
                            func = tool_call.get("function", {})
                            func_name = func.get("name", "")
                            args = json.loads(func.get("arguments", "{}"))
                            
                            if func_name == "search_tokens":
                                chain = "bsc"  # Always BSC
                                limit = args.get("limit", 10)
                                
                                # Execute the tool
                                from ..ave.client import AveCloudClient
                                from ...core.config import get_settings
                                settings = get_settings()
                                ave_client = AveCloudClient(
                                    api_key=settings.AVE_API_KEY,
                                    plan=settings.AVE_API_PLAN
                                )
                                import asyncio
                                tokens = asyncio.run(ave_client.get_tokens(chain=chain, limit=limit))
                                
                                if tokens:
                                    # Format tokens for response
                                    token_list = ""
                                    for t in tokens[:limit]:
                                        addr = t.get("token", "")
                                        symbol = t.get("symbol", "")
                                        name = t.get("name", "")
                                        price_change = t.get("token_price_change_24h", "N/A")
                                        token_list += f"- **{symbol}** ({name}): `{addr}` - 24h change: {price_change}%\n"
                                    
                                    response_text = f"Here are the trending tokens on {chain.upper()}:\n\n{token_list}\nWould you like me to set up a strategy for any of these?"
                                else:
                                    response_text = f"I couldn't find any trending tokens on {chain.upper()}. Try again later."
                                
                                # Return the tool result directly
                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True
                                }
                            
                            elif func_name == "run_backtest":
                                token_address = args.get("token_address")
                                timeframe = args.get("timeframe", "1d")
                                start_date = args.get("start_date")
                                end_date = args.get("end_date")
                                
                                # Execute backtest
                                backtest_result = self._execute_backtest(
                                    token_address=token_address,
                                    timeframe=timeframe,
                                    start_date=start_date,
                                    end_date=end_date
                                )
                                
                                return {
                                    "response": backtest_result,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True
                                }
                            
                            elif func_name == "manage_simulation":
                                action = args.get("action")
                                token_address = args.get("token_address")
                                kline_interval = args.get("kline_interval", "1m")
                                
                                # Execute simulation management
                                sim_result = self._manage_simulation(
                                    action=action,
                                    token_address=token_address,
                                    kline_interval=kline_interval
                                )
                                
                                return {
                                    "response": sim_result,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True
                                }
            
            # Get the main response content
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse JSON from the content
            thinking_field = None
            response_text = content
            strategy_update = None
            
            # Try to extract JSON from the content
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = None
            
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    thinking_field = parsed.get("thinking", "")
                    response_text = parsed.get("response", content)
                    strategy_update = parsed.get("strategy_update")
                    
                    # Handle tool call
                    tool_call = parsed.get("tool_call")
                    if tool_call and tool_call.get("name") == "search_tokens":
                        args = tool_call.get("arguments", {})
                        chain = args.get("chain", "bsc")
                        limit = args.get("limit", 10)
                        
                        # Execute the tool
                        from ..ave.client import AveCloudClient
                        from ...core.config import get_settings
                        settings = get_settings()
                        ave_client = AveCloudClient(
                            api_key=settings.AVE_API_KEY,
                            plan=settings.AVE_API_PLAN
                        )
                        import asyncio
                        tokens = asyncio.run(ave_client.get_tokens(chain=chain, limit=limit))
                        
                        if tokens:
                            # Format tokens for response
                            token_list = ""
                            for t in tokens[:limit]:
                                addr = t.get("token", "")
                                symbol = t.get("symbol", "")
                                name = t.get("name", "")
                                price_change = t.get("token_price_change_24h", "N/A")
                                token_list += f"- **{symbol}** ({name}): `{addr}` - 24h change: {price_change}%\n"
                            
                            response_text = f"Here are the trending tokens on {chain.upper()}:\n\n{token_list}\nWould you like me to set up a strategy for any of these?"
                        else:
                            response_text = f"I couldn't find any trending tokens on {chain.upper()}. Try again later."
                        
                        strategy_update = None
                        
                except json.JSONDecodeError:
                    pass  # Use defaults
            
            # Use the native thinking from API if available, otherwise use parsed thinking
            final_thinking = thinking or thinking_field
            
            # Check if token_address is missing in strategy_update
            strategy_needs_confirmation = False
            token_search_results = None
            
            if strategy_update:
                # Extract token name from conditions
                token_name = None
                for cond in strategy_update.get("conditions", []):
                    if not cond.get("token_address") and cond.get("token"):
                        token_name = cond.get("token")
                        strategy_needs_confirmation = True
                        break
                
                # Search for token if name is found
                if strategy_needs_confirmation and token_name:
                    try:
                        from ..ave.client import AveCloudClient
                        from ...core.config import get_settings
                        settings = get_settings()
                        ave_client = AveCloudClient(
                            api_key=settings.AVE_API_KEY,
                            plan=settings.AVE_API_PLAN
                        )
                        # Run async search in sync context
                        import asyncio
                        tokens = asyncio.run(ave_client.get_tokens(query=token_name, chain="bsc", limit=5))
                        if tokens:
                            token_search_results = [
                                {
                                    "symbol": t.get("symbol", ""),
                                    "name": t.get("name", ""),
                                    "address": t.get("token", ""),  # trending API uses "token" for contract address
                                    "chain": t.get("chain", "bsc")
                                }
                                for t in tokens
                            ]
                    except Exception as e:
                        print(f"Token search error: {e}")
            
            # Only update strategy if token_address is provided
            if strategy_update and strategy_needs_confirmation:
                # Don't auto-save - user needs to confirm token address
                # Return response but with strategy_update as None
                return {
                    "response": response_text,
                    "thinking": final_thinking,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": True,
                    "strategy_data": strategy_update,
                    "token_search_results": token_search_results,
                    "success": True
                }
            
            # Update strategy in database if provided
            if strategy_update and self.bot_id:
                self._update_strategy(strategy_update)
            
            return {
                "response": response_text,
                "thinking": final_thinking,
                "strategy_updated": strategy_update is not None,
                "strategy_needs_confirmation": False,
                "success": True
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "thinking": None,
                "strategy_updated": False,
                "success": False
            }
    
    def _execute_backtest(
        self,
        token_address: str,
        timeframe: str = "1d",
        start_date: str = None,
        end_date: str = None
    ) -> str:
        """Execute a backtest using the bot's current strategy."""
        try:
            import asyncio
            from ...core.database import get_db
            from ...db.models import Backtest
            from ...services.backtest.engine import BacktestEngine
            from ...core.config import get_settings
            from datetime import datetime
            import uuid
            
            settings = get_settings()
            db = next(get_db())
            
            # Get the bot
            bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
            if not bot:
                return "I couldn't find the bot. Please try again."
            
            # Default dates if not provided (last 30 days)
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Create backtest engine
            backtest_config = {
                "bot_id": self.bot_id,
                "token": token_address,
                "chain": "bsc",
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "strategy_config": bot.strategy_config,
                "ave_api_key": settings.AVE_API_KEY,
                "ave_api_plan": settings.AVE_API_PLAN,
                "initial_balance": 10000.0,
            }
            
            engine = BacktestEngine(backtest_config)
            results = asyncio.run(engine.run())
            
            # Format results for display
            if "error" in results:
                return f"Backtest failed: {results['error']}"
            
            total_return = results.get("total_return", 0)
            win_rate = results.get("win_rate", 0)
            total_trades = results.get("total_trades", 0)
            max_drawdown = results.get("max_drawdown", 0)
            sharpe_ratio = results.get("sharpe_ratio", 0)
            final_balance = results.get("final_balance", 10000)
            
            # Format return with emoji indicators
            return_emoji = "📈" if total_return >= 0 else "📉"
            return_str = f"+{total_return:.2f}%" if total_return >= 0 else f"{total_return:.2f}%"
            
            drawdown_emoji = "⚠️" if abs(max_drawdown) > 10 else "✅"
            
            response = f"""Here's the backtest result for {token_address}:

**Performance Summary**
{return_emoji} Total Return: {return_str}
💰 Final Balance: ${final_balance:,.2f}
📊 Total Trades: {total_trades}
🎯 Win Rate: {win_rate:.1f}%

**Risk Metrics**
{drawdown_emoji} Max Drawdown: {max_drawdown:.2f}%
📉 Sharpe Ratio: {sharpe_ratio:.2f}

**Period**: {start_date} to {end_date} ({timeframe})

Would you like me to adjust the strategy parameters based on these results?"""
            
            return response
            
        except Exception as e:
            return f"I encountered an error running the backtest: {str(e)}"
    
    def _manage_simulation(
        self,
        action: str,
        token_address: str = None,
        kline_interval: str = "1m"
    ) -> str:
        """Manage trading simulations: start, stop, status, or results."""
        try:
            import asyncio
            import threading
            import uuid
            from ...core.database import SessionLocal
            from ...db.models import Simulation
            from ...services.simulate.engine import SimulateEngine
            from ...core.config import get_settings
            from datetime import datetime
            
            db = SessionLocal()
            settings = get_settings()
            
            try:
                # Get the bot
                bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
                if not bot:
                    return "I couldn't find the bot. Please try again."
                
                if action == "start":
                    if not token_address:
                        return "I need a token address to start a simulation. Which token would you like to simulate?"
                    
                    # Check if there's already a running simulation
                    running_sim = db.query(Simulation).filter(
                        Simulation.bot_id == self.bot_id,
                        Simulation.status == "running"
                    ).first()
                    
                    if running_sim:
                        # Stop the existing one first
                        self._stop_simulation_db(running_sim.id)
                    
                    # Create new simulation
                    sim_id = str(uuid.uuid4())
                    simulation = Simulation(
                        id=sim_id,
                        bot_id=self.bot_id,
                        started_at=datetime.utcnow(),
                        status="running",
                        config={
                            "token": token_address,
                            "chain": "bsc",
                            "kline_interval": kline_interval
                        },
                        signals=[],
                        klines=[],
                        trade_log=[]
                    )
                    db.add(simulation)
                    db.commit()
                    
                    # Start the simulation in background
                    sim_config = {
                        "bot_id": self.bot_id,
                        "token": token_address,
                        "chain": "bsc",
                        "kline_interval": kline_interval,
                        "max_candles": 100,
                        "candle_delay": 30 if kline_interval == "1m" else 60,
                        "strategy_config": bot.strategy_config,
                        "ave_api_key": settings.AVE_API_KEY,
                        "ave_api_plan": settings.AVE_API_PLAN,
                        "initial_balance": 10000.0,
                    }
                    
                    # Run simulation in background thread
                    def run_sim():
                        asyncio.run(self._run_simulation_sync(sim_id, settings.DATABASE_URL, sim_config))
                    
                    thread = threading.Thread(target=run_sim)
                    thread.daemon = True
                    thread.start()
                    
                    return f"Started simulation on {token_address} using {kline_interval} klines. The simulation is running and will process up to 100 candles. Ask me for status or results anytime!"
                
                elif action == "stop":
                    # Find running simulation
                    running_sim = db.query(Simulation).filter(
                        Simulation.bot_id == self.bot_id,
                        Simulation.status == "running"
                    ).first()
                    
                    if not running_sim:
                        return "No simulation is currently running."
                    
                    self._stop_simulation_db(running_sim.id)
                    
                    # Get final results
                    portfolio = running_sim.portfolio or {}
                    current_balance = portfolio.get("current_balance", 10000)
                    initial_balance = portfolio.get("initial_balance", 10000)
                    pnl = current_balance - initial_balance
                    pnl_pct = (pnl / initial_balance) * 100 if initial_balance > 0 else 0
                    
                    return f"Simulation stopped!\n\nFinal Results:\n💰 Final Balance: ${current_balance:,.2f}\n📈 P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f} ({'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%)\n📊 Trades: {len(running_sim.trade_log or [])}"
                
                elif action == "status":
                    # Find running simulation
                    running_sim = db.query(Simulation).filter(
                        Simulation.bot_id == self.bot_id,
                        Simulation.status == "running"
                    ).first()
                    
                    if not running_sim:
                        return "No simulation is currently running."
                    
                    portfolio = running_sim.portfolio or {}
                    klines_count = len(running_sim.klines or [])
                    trade_count = len(running_sim.trade_log or [])
                    
                    status = f"**Simulation Status: Running**\n\n"
                    status += f"📊 Candles processed: ~{klines_count}\n"
                    status += f"📈 Trades executed: {trade_count}\n"
                    
                    if portfolio.get("position", 0) > 0:
                        status += f"💰 Position: {portfolio['position']:.4f} {portfolio.get('position_token', 'TOKEN')}\n"
                        status += f"💰 Cash: ${portfolio.get('current_balance', 0):,.2f}\n"
                    else:
                        status += f"💰 Cash: ${portfolio.get('current_balance', 10000):,.2f}\n"
                    
                    status += "\nAsk me to stop or get full results anytime!"
                    return status
                
                elif action == "results":
                    # Find running or most recent simulation
                    simulation = db.query(Simulation).filter(
                        Simulation.bot_id == self.bot_id
                    ).order_by(Simulation.started_at.desc()).first()
                    
                    if not simulation:
                        return "No simulation found. Start a simulation first!"
                    
                    portfolio = simulation.portfolio or {}
                    current_balance = portfolio.get("current_balance", 10000)
                    initial_balance = portfolio.get("initial_balance", 10000)
                    pnl = current_balance - initial_balance
                    pnl_pct = (pnl / initial_balance) * 100 if initial_balance > 0 else 0
                    trade_log = simulation.trade_log or []
                    
                    status_emoji = "🟢" if simulation.status == "running" else "⚪"
                    status_text = "Running" if simulation.status == "running" else "Completed/Stopped"
                    
                    results = f"**Simulation Results** {status_emoji} ({status_text})\n\n"
                    results += f"💰 Final Balance: ${current_balance:,.2f}\n"
                    results += f"📈 P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f} ({'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%)\n"
                    results += f"📊 Total Trades: {len(trade_log)}\n"
                    
                    if simulation.status == "running":
                        results += f"\n⏳ Simulation still running... (refresh for latest)"
                    
                    return results
                
                else:
                    return f"Unknown action: {action}. Use 'start', 'stop', 'status', or 'results'."
            
            finally:
                db.close()
        
        except Exception as e:
            return f"I encountered an error managing the simulation: {str(e)}"
    
    def _stop_simulation_db(self, simulation_id: str):
        """Stop a simulation in the database."""
        from ...core.database import SessionLocal
        db = SessionLocal()
        try:
            simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
            if simulation:
                simulation.status = "stopped"
                db.commit()
        finally:
            db.close()
    
    async def _run_simulation_sync(self, simulation_id: str, db_url: str, config: dict):
        """Run simulation synchronously in background."""
        from ...services.simulate.engine import SimulateEngine
        from ...core.database import SessionLocal
        
        async def _run():
            engine = SimulateEngine(config)
            engine.run_id = simulation_id
            
            def serialize_signal(s):
                created = s.get("created_at")
                if hasattr(created, "isoformat"):
                    created = created.isoformat()
                return {**s, "created_at": created}
            
            def save_progress():
                db = SessionLocal()
                try:
                    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
                    if sim:
                        sim.status = engine.status
                        sim.signals = [serialize_signal(s) for s in engine.signals]
                        sim.klines = [{"time": k.get("time"), "close": k.get("close")} for k in engine.klines]
                        sim.trade_log = engine.trade_log
                        sim.portfolio = {
                            "initial_balance": config.get("initial_balance", 10000),
                            "current_balance": engine.current_balance,
                            "position": engine.position,
                            "position_token": engine.position_token,
                            "entry_price": engine.entry_price,
                            "current_price": engine.last_close,
                        }
                        db.commit()
                finally:
                    db.close()
            
            try:
                await engine.run()
            finally:
                save_progress()
        
        asyncio.run(_run())
    
    def _update_strategy(self, strategy_update: Dict) -> bool:
        """Update the bot's strategy in the database."""
        try:
            from ...core.database import get_db
            
            db = next(get_db())
            bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
            if bot:
                bot.strategy_config = strategy_update
                db.commit()
                return True
        except Exception as e:
            print(f"Error updating strategy: {e}")
        return False


def get_conversational_agent(api_key: str = None, model: str = None, bot_id: str = None) -> ConversationalAgent:
    """Get or create a ConversationalAgent instance."""
    if api_key is None:
        settings = get_settings()
        api_key = settings.MINIMAX_API_KEY
    if model is None:
        settings = get_settings()
        model = settings.MINIMAX_MODEL
    
    return ConversationalAgent(api_key=api_key, model=model, bot_id=bot_id)
