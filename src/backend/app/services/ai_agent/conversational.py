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
from ...db.models import Bot, Simulation


TOOL_REGISTRY = {
    "randebu": [
        {
            "name": "backtest",
            "description": "Run strategy backtest",
            "category": "Randebu Built-in",
            "command": "/backtest",
            "details": {
                "description": "Run a backtest to evaluate how the current trading strategy would have performed historically.",
                "usage": "/backtest [token_address] [--timeframe 1d|4h|1h|15m] [--start YYYY-MM-DD] [--end YYYY-MM-DD]",
                "example": "Run a backtest on PEPE for the last 30 days",
            },
        },
        {
            "name": "simulate",
            "description": "Start/stop simulation",
            "category": "Randebu Built-in",
            "command": "/simulate",
            "details": {
                "description": "Start or stop trading simulations that run on real-time klines.",
                "usage": "/simulate start|stop|status|results [token_address]",
                "example": "Start a simulation on PEPE",
            },
        },
        {
            "name": "strategy",
            "description": "View/update strategy",
            "category": "Randebu Built-in",
            "command": "/strategy",
            "details": {
                "description": "View your current trading strategy or update it with new parameters.",
                "usage": "Describe your strategy in plain English, e.g., 'Buy PEPE when price drops 5%'",
                "example": "Buy PEPE when it drops 10% within 1 hour",
            },
        },
    ],
    "ave": [
        {
            "name": "search",
            "description": "Token search",
            "category": "AVE Cloud Skills",
            "command": "/search",
            "details": {
                "description": "Find tokens by keyword, symbol, or contract address on BSC.",
                "usage": "search <keyword> [--chain bsc] [--limit 20]",
                "example": "search PEPE\nsearch 0x1234... --chain bsc",
            },
        },
        {
            "name": "trending",
            "description": "Popular tokens",
            "category": "AVE Cloud Skills",
            "command": "/trending",
            "details": {
                "description": "Get list of trending/popular tokens on BSC.",
                "usage": "trending [--chain bsc] [--limit 20]",
                "example": "trending --chain bsc\ntrending --limit 10",
            },
        },
        {
            "name": "risk",
            "description": "Honeypot detection",
            "category": "AVE Cloud Skills",
            "command": "/risk",
            "details": {
                "description": "Get risk analysis for a token contract including honeypot assessment.",
                "usage": "risk <token_address> [--chain bsc]",
                "example": "risk 0x6982508145454Ce125dDE157d8d64a26D53f60a2",
            },
        },
        {
            "name": "token",
            "description": "Token details",
            "category": "AVE Cloud Skills",
            "command": "/token",
            "details": {
                "description": "Get detailed information about a specific token including price, market cap, and pairs.",
                "usage": "token <address> [--chain bsc]",
                "example": "token 0x6982508145454Ce125dDE157d8d64a26D53f60a2",
            },
        },
        {
            "name": "price",
            "description": "Batch prices",
            "category": "AVE Cloud Skills",
            "command": "/price",
            "details": {
                "description": "Get current price(s) for multiple tokens.",
                "usage": "price <token_id>,<token_id>,... (e.g., PEPE-bsc,TRUMP-bsc)",
                "example": "price PEPE-bsc,TRUMP-bsc",
            },
        },
    ],
}


# Skill emojis mapping
SKILL_EMOJIS = {
    "backtest": "📊",
    "simulate": "🎮",
    "strategy": "📝",
    "search": "🔍",
    "trending": "📈",
    "risk": "📉",
    "token": "🪙",
    "price": "💰",
}


def get_tool_registry() -> Dict[str, Any]:
    """Return the tool registry for slash command help."""
    return TOOL_REGISTRY


def format_tools_list() -> str:
    """Format the tool registry as a help message."""
    message = "📋 Available Tools\n\n"

    for category in ["randebu", "ave"]:
        tools = TOOL_REGISTRY.get(category, [])
        if category == "randedu":
            message += "🤖 Randebu Built-in:\n"
        else:
            message += "☁️ AVE Cloud Skills:\n"

        for tool in tools:
            message += f"  • {tool['command']} - {tool['description']}\n"
        message += "\n"

    message = (
        message.rstrip() + "\n\nType /<tool-name> for detailed help on a specific tool."
    )
    return message


def format_skill_acknowledgment(tool_name: str, description: str) -> str:
    """Format a brief acknowledgment when a skill is activated."""
    emoji = SKILL_EMOJIS.get(tool_name.lower(), "✨")
    return f"{emoji} **{tool_name}** loaded. Ready for *{description}*, ask me away!"


def format_tool_help(tool_name: str) -> str:
    """Format detailed help for a specific tool."""
    tool_name = tool_name.lstrip("/")

    for category in ["randebu", "ave"]:
        for tool in TOOL_REGISTRY.get(category, []):
            if tool["name"].lower() == tool_name.lower():
                cat_label = (
                    "Randebu Built-in" if category == "randebu" else "AVE Cloud Skill"
                )
                details = tool["details"]
                message = (
                    f"🔍 {tool['command']} - {details['description']} ({cat_label})\n\n"
                )
                message += f"**Description:** {details['description']}\n"
                message += f"**Commands:**\n  {details['usage']}\n\n"
                message += f"**Example:**\n```\n{details['example']}\n```"
                return message

    return f"Tool '{tool_name}' not found. Type / to see all available tools."


def format_general_help() -> str:
    """Format general help about Randebu."""
    return """🤖 **Randebu - AI Trading Assistant**

Randebu is your AI trading assistant that helps you manage your trading bots on BSC (Binance Smart Chain).

**Getting Started:**
1. Create a bot on the dashboard
2. Describe your trading strategy in plain English
3. Run backtests to validate your strategy
4. Start simulations to see live trading

**Example Strategies:**
- "Buy PEPE when it drops 5%"
- "Sell if price rises 10% within 1 hour"
- "Buy when volume spikes by 200%"

**Slash Commands:**
- `/` - Show all available tools
- `/help` - Show this help message
- `/<tool-name>` - Get help on a specific tool

**Natural Language:**
You can also just describe what you want in natural language. For example:
- "What's the price of PEPE?"
- "Run a backtest on 0x... token"
- "Start a simulation on TRUMP"
"""


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
}"

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
            "description": "Search for tokens by keyword on BSC blockchain. Use this when user asks to search for a specific token or find tokens by name/symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Token symbol or name to search for (e.g., 'PEPE', 'BTC')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of tokens to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_token",
            "description": "Get detailed information about a specific token including price, market cap, and pairs. Use when user asks for token details or wants to find a specific token by contract address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Token contract address (e.g., '0x6982508145454Ce125dDE157d8d64a26D53f60a2')",
                    },
                    "chain": {
                        "type": "string",
                        "description": "Blockchain chain (default: bsc)",
                        "default": "bsc",
                    },
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Get current price(s) for tokens. Use when user asks for token price or wants to compare prices of multiple tokens.",
            "parameters": {
                "type": "object",
                "properties": {
                    "token_ids": {
                        "type": "string",
                        "description": "Comma-separated list of token IDs with chain suffix (e.g., 'PEPE-bsc,TRUMP-bsc')",
                    }
                },
                "required": ["token_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk",
            "description": "Get risk analysis for a token contract. Use when user asks about token risk, honeypot analysis, or safety assessment before trading.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Token contract address (e.g., '0x6982508145454Ce125dDE157d8d64a26D53f60a2')",
                    },
                    "chain": {
                        "type": "string",
                        "description": "Blockchain chain (default: bsc)",
                        "default": "bsc",
                    },
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending",
            "description": "Get trending tokens on a blockchain. Use when user asks what's trending, top tokens, or popular tokens right now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "description": "Blockchain chain (default: bsc)",
                        "default": "bsc",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of trending tokens to return (default: 10, max: 50)",
                        "default": 10,
                    },
                },
            },
        },
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
                        "description": "The BSC contract address of the token to backtest (required)",
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for klines: '1d' (1 day), '4h' (4 hours), '1h' (1 hour), '15m' (15 minutes)",
                        "default": "1d",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for backtest in YYYY-MM-DD format (e.g., '2024-01-01')",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for backtest in YYYY-MM-DD format (e.g., '2024-12-01')",
                    },
                },
                "required": ["token_address"],
            },
        },
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
                        "description": "Action to perform: 'start' (begin new simulation), 'stop' (stop running simulation), 'status' (check if simulation is running), 'results' (get results from current or latest simulation)",
                    },
                    "token_address": {
                        "type": "string",
                        "description": "Token contract address for simulation (required for 'start' action)",
                    },
                    "kline_interval": {
                        "type": "string",
                        "description": "Kline interval: '1m', '5m', '15m', '1h' (default: '1m')",
                        "default": "1m",
                    },
                },
                "required": ["action"],
            },
        },
    },
]

SYSTEM_PROMPT_WITH_TOOLS = (
    SYSTEM_PROMPT
    + """

You have access to tools:
- search_tokens(keyword, limit): Search for tokens by keyword. Use it when user asks to search for a token or find tokens by name/symbol.
- get_token(address, chain): Get detailed information about a specific token. Use when user asks for token details.
- get_price(token_ids): Get current price(s) for tokens. Use when user asks for token price.
- get_risk(address, chain): Get risk analysis for a token. Use when user asks about token safety or honeypot analysis.
- get_trending(chain, limit): Get trending tokens on a blockchain. Use when user asks what's trending, top tokens, or popular tokens.
- run_backtest(token_address, timeframe, start_date, end_date): Run a backtest on historical data. Returns performance metrics. Use when user asks to backtest or check historical performance.
- manage_simulation(action, token_address, kline_interval): Manage trading simulations. Actions: 'start' (begin new), 'stop' (stop running), 'status' (check if running), 'results' (get current/latest results).

When you want to use a tool, respond with:
{
  "thinking": "...",
  "response": "Running backtest...",
  "tool_call": {"name": "run_backtest", "arguments": {"token_address": "0x...", "timeframe": "1d", "start_date": "2024-01-01", "end_date": "2024-12-01"}}
}
"""
)


class ConversationalAgent:
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", bot_id: str = None):
        self.api_key = api_key
        self.model = model
        self.bot_id = bot_id

        # Extended thinking endpoint
        self.thinking_endpoint = "https://api.minimax.io/v1/text/chatcompletion_v2"

        # Track pending command after acknowledgment
        self.pending_command = None

    def _handle_slash_command(self, user_message: str) -> Dict[str, Any]:
        """Handle slash command help requests.

        Args:
            user_message: The slash command message (e.g., '/', '/help', '/search')

        Returns:
            Dict with 'response', 'thinking', and other fields
        """
        cmd = user_message.strip().lower()

        if cmd == "/":
            return {
                "response": format_tools_list(),
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }
        elif cmd == "/help":
            return {
                "response": format_general_help(),
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }
        elif cmd.startswith("/"):
            # Check if it's a known skill (only look at first word after /)
            parts = cmd[1:].split()
            tool_name = parts[0].lower() if parts else ""
            has_args = len(parts) > 1

            for category in ["randebu", "ave"]:
                for tool in TOOL_REGISTRY.get(category, []):
                    if tool["name"].lower() == tool_name:
                        # Special handling for /strategy - fetch current strategy from DB
                        if tool_name == "strategy" and not has_args:
                            return self._get_strategy_response()
                        # Special handling for /trending - execute trending directly
                        if tool_name == "trending" and not has_args:
                            return self._execute_trending()
                        # Special handling for /backtest - execute directly
                        if tool_name == "backtest" and not has_args:
                            return self._execute_backtest_direct()
                        # Special handling for /simulate - execute directly
                        if tool_name == "simulate" and not has_args:
                            return self._execute_simulate_direct()
                        # For commands that need params (/search, /risk, /token, /price)
                        # execute immediately if args provided, otherwise set pending
                        if not has_args:
                            # Set pending command for next message
                            self.pending_command = tool_name
                            return {
                                "response": format_skill_acknowledgment(
                                    tool["name"], tool["description"]
                                ),
                                "thinking": None,
                                "strategy_updated": False,
                                "strategy_needs_confirmation": False,
                                "success": True,
                            }
                        return None  # Has args - let AI handle it

            # Unknown skill
            return {
                "response": f"Unknown command '{tool_name}'. Type / to see available tools.",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        return {
            "response": "Unknown command. Type / for available tools or /help for general help.",
            "thinking": None,
            "strategy_updated": False,
            "strategy_needs_confirmation": False,
            "success": True,
        }

    def _get_strategy_response(self) -> Dict[str, Any]:
        """Fetch and format the current strategy from the database."""
        if not self.bot_id:
            return {
                "response": "No bot selected. Please select a bot first.",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        try:
            from ...core.database import get_db
            db = next(get_db())
            try:
                bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
                if not bot:
                    return {
                        "response": "Bot not found.",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }

                strategy_config = bot.strategy_config
                if not strategy_config:
                    return {
                        "response": "📝 **Your Current Strategy**\n\nNo strategy has been configured yet. Tell me what trading strategy you'd like to use, and I'll set it up for you!\n\nExample: \"Buy PEPE when it drops 5%\"",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }

                # Format the strategy nicely
                conditions = strategy_config.get("conditions", [])
                actions = strategy_config.get("actions", [])
                risk = strategy_config.get("risk_management", {})

                response = "📝 **Your Current Strategy**\n\n"

                # Format conditions
                if conditions:
                    response += "**Conditions:**\n"
                    for cond in conditions:
                        cond_type = cond.get("type", "unknown")
                        token = cond.get("token", "")
                        threshold = cond.get("threshold", 0)
                        timeframe = cond.get("timeframe", "")
                        if cond_type == "price_drop":
                            response += f"- Buy when {token} drops {threshold}%"
                        elif cond_type == "price_rise":
                            response += f"- Sell when {token} rises {threshold}%"
                        elif cond_type == "volume_spike":
                            response += f"- Buy when volume spikes {threshold}%"
                        elif cond_type == "price_level":
                            response += f"- Buy/sell at price level {threshold}"
                        else:
                            response += f"- {cond_type}: {token} {threshold}"
                        if timeframe:
                            response += f" within {timeframe}"
                        response += "\n"
                    response += "\n"

                # Format actions
                if actions:
                    response += "**Actions:**\n"
                    for action in actions:
                        action_type = action.get("type", "unknown")
                        amount = action.get("amount_percent", 0)
                        response += f"- {action_type.capitalize()} {amount}% of balance\n"
                    response += "\n"

                # Format risk management
                if risk:
                    response += "**Risk Management:**\n"
                    stop_loss = risk.get("stop_loss_percent", 0)
                    take_profit = risk.get("take_profit_percent", 0)
                    if stop_loss:
                        response += f"- Stop loss: {stop_loss}%\n"
                    if take_profit:
                        response += f"- Take profit: {take_profit}%\n"

                response += "\nWould you like to modify this strategy?"

                return {
                    "response": response,
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
            finally:
                db.close()
        except Exception as e:
            return {
                "response": f"Error fetching strategy: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_trending(self) -> Dict[str, Any]:
        """Execute the trending tokens command and return results."""
        try:
            code, output = self._call_ave_script(
                "trending",
                ["--chain", "bsc", "--page-size", "10"],
            )
            if code == 0:
                try:
                    data = json.loads(output)
                    # Handle both dict with 'tokens' key and direct list
                    data_field = data.get("data", [])
                    if isinstance(data_field, list):
                        tokens = data_field
                    else:
                        tokens = data_field.get("tokens", [])
                    if tokens:
                        token_list = ""
                        for t in tokens[:10]:
                            addr = t.get("token", "")
                            symbol = t.get("symbol", "")
                            name = t.get("name", "")
                            price_change = t.get("token_price_change_24h", "N/A")
                            mc = t.get("market_cap", "N/A")
                            try:
                                mc_str = f"${float(mc):,.0f}"
                            except (ValueError, TypeError):
                                mc_str = str(mc)
                            token_list += f"- **{symbol}** ({name}): `{addr}` - MC: {mc_str} - 24h: {price_change}%\n"
                        return {
                            "response": f"📈 **Trending Tokens on BSC:**\n\n{token_list}\nWould you like me to set up a strategy for any of these?",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                    else:
                        return {
                            "response": "No trending tokens found on BSC right now. Try again later!",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                except json.JSONDecodeError:
                    return {
                        "response": f"Failed to parse trending data: {output[:200]}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
            else:
                return {
                    "response": f"Failed to get trending tokens: {output}",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
        except Exception as e:
            return {
                "response": f"Error getting trending tokens: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_search(self, keyword: str) -> Dict[str, Any]:
        """Execute search with the given keyword."""
        try:
            code, output = self._call_ave_script(
                "search",
                ["--keyword", keyword.strip(), "--chain", "bsc", "--limit", "10"],
            )
            if code == 0:
                try:
                    data = json.loads(output)
                    # Handle both dict with 'tokens' key and direct list
                    data_field = data.get("data", [])
                    if isinstance(data_field, list):
                        tokens = data_field
                    else:
                        tokens = data_field.get("tokens", [])
                    if tokens:
                        token_list = ""
                        for t in tokens[:10]:
                            addr = t.get("token", "")
                            symbol = t.get("symbol", "")
                            name = t.get("name", "")
                            price_change = t.get("token_price_change_24h", "N/A")
                            mc = t.get("market_cap", "N/A")
                            try:
                                mc_str = f"${float(mc):,.0f}"
                            except (ValueError, TypeError):
                                mc_str = str(mc)
                            token_list += f"- **{symbol}** ({name}): `{addr}` - MC: {mc_str} - 24h: {price_change}%\n"
                        return {
                            "response": f"🔍 **Search Results for '{keyword}':**\n\n{token_list}\nWould you like me to set up a strategy for any of these?",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                    else:
                        return {
                            "response": f"No tokens found for '{keyword}'. Try a different keyword.",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                except json.JSONDecodeError:
                    return {
                        "response": f"Failed to parse search results: {output[:200]}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
            else:
                return {
                    "response": f"Failed to search tokens: {output}",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
        except Exception as e:
            return {
                "response": f"Error searching tokens: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_risk(self, address: str) -> Dict[str, Any]:
        """Execute risk analysis for the given token address."""
        try:
            code, output = self._call_ave_script(
                "risk",
                ["--address", address.strip(), "--chain", "bsc"],
            )
            if code == 0:
                try:
                    data = json.loads(output)
                    data_field = data.get("data")
                    risk_data = data_field if isinstance(data_field, dict) else {}
                    if risk_data:
                        is_honeypot = risk_data.get("is_honeypot", "unknown")
                        buy_tax = risk_data.get("buy_tax", 0)
                        sell_tax = risk_data.get("sell_tax", 0)
                        status = risk_data.get("status", "unknown")
                        # Convert is_honeypot to string
                        if isinstance(is_honeypot, bool):
                            is_honeypot_str = str(is_honeypot).lower()
                        elif isinstance(is_honeypot, int):
                            is_honeypot_str = "true" if is_honeypot == 1 else "false" if is_honeypot == 0 else "unknown"
                        else:
                            is_honeypot_str = str(is_honeypot).lower() if is_honeypot else "unknown"
                        # Convert tax values
                        try:
                            buy_tax_val = float(buy_tax) if buy_tax not in (None, "N/A") else 0
                        except (ValueError, TypeError):
                            buy_tax_val = 0
                        try:
                            sell_tax_val = float(sell_tax) if sell_tax not in (None, "N/A") else 0
                        except (ValueError, TypeError):
                            sell_tax_val = 0
                        risk_text = f"🛡️ **Risk Analysis for `{address}`**\n\n"
                        risk_text += f"- Status: {status}\n"
                        risk_text += f"- Honeypot: {is_honeypot_str}\n"
                        risk_text += f"- Buy Tax: {buy_tax}%\n"
                        risk_text += f"- Sell Tax: {sell_tax}%\n"
                        if is_honeypot_str == "true":
                            risk_text += "\n⚠️ **Warning: This token appears to be a honeypot. Do not buy!**"
                        elif buy_tax_val > 10 or sell_tax_val > 10:
                            risk_text += "\n⚠️ **Warning: High tax detected. Trade with caution!**"
                        else:
                            risk_text += "\n✅ This token appears safe to trade."
                        return {
                            "response": risk_text,
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                    else:
                        return {
                            "response": f"No risk data available for `{address}`",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                except json.JSONDecodeError:
                    return {
                        "response": f"Failed to parse risk data: {output[:200]}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
            else:
                return {
                    "response": f"Failed to get risk data: {output}",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
        except Exception as e:
            return {
                "response": f"Error getting risk data: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_token(self, address: str) -> Dict[str, Any]:
        """Execute token details for the given address."""
        try:
            code, output = self._call_ave_script(
                "token",
                ["--address", address.strip(), "--chain", "bsc"],
            )
            if code == 0:
                try:
                    data = json.loads(output)
                    data_field = data.get("data")
                    token_data = data_field if isinstance(data_field, dict) else {}
                    token_info = token_data.get("token", token_data)
                    symbol = token_info.get("symbol") or token_data.get("symbol")
                    name = token_info.get("name") or token_data.get("name")
                    if not symbol or symbol == "N/A" or not name or name == "N/A":
                        return {
                            "response": f"Token not found for `{address}`.",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                    price = token_info.get("current_price_usd") or token_info.get("price_usd") or token_info.get("price") or token_data.get("price") or "N/A"
                    mc = token_info.get("market_cap") or token_info.get("fdv") or token_data.get("market_cap") or "N/A"
                    vol = token_info.get("tx_volume_u_24h") or token_info.get("volume_24h") or token_data.get("volume_24h") or "N/A"
                    pairs = token_info.get("top_pairs") or token_data.get("top_pairs") or []
                    pairs_text = ""
                    if pairs:
                        pairs_text = "\n**Top Pairs:**\n"
                        for p in pairs[:3]:
                            liq = p.get('liquidity', 'N/A')
                            try:
                                liq_str = f"${float(liq):,.0f}" if liq and liq != "N/A" else liq
                            except (ValueError, TypeError):
                                liq_str = str(liq)
                            pairs_text += f"- {p.get('pair', 'N/A')}: {liq_str} liquidity\n"
                    try:
                        mc_str = f"${float(mc):,.0f}" if mc != "N/A" else mc
                    except (ValueError, TypeError):
                        mc_str = str(mc)
                    try:
                        vol_str = f"${float(vol):,.0f}" if vol != "N/A" else vol
                    except (ValueError, TypeError):
                        vol_str = str(vol)
                    return {
                        "response": f"🪙 **{symbol}** ({name})\n\nPrice: ${price}\nMarket Cap: {mc_str}\n24h Volume: {vol_str}{pairs_text}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
                except json.JSONDecodeError:
                    return {
                        "response": f"Failed to parse token data: {output[:200]}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
            else:
                return {
                    "response": f"Failed to get token details: {output}",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
        except Exception as e:
            return {
                "response": f"Error getting token details: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_price(self, token_ids: str) -> Dict[str, Any]:
        """Execute price lookup for the given token IDs."""
        try:
            tokens_list = token_ids.replace(",", " ").split()
            if not tokens_list:
                return {
                    "response": "No token IDs provided. Please provide token IDs like 'PEPE-bsc TRUMP-bsc'",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
            code, output = self._call_ave_script(
                "price",
                ["--tokens"] + tokens_list,
            )
            if code == 0:
                try:
                    data = json.loads(output)
                    prices = data.get("data", {})
                    if not isinstance(prices, dict):
                        prices = {}
                    if prices:
                        price_text = "💰 **Token Prices:**\n"
                        for token_id, price_data in prices.items():
                            price = price_data.get("price", "N/A") if isinstance(price_data, dict) else "N/A"
                            change_24h = price_data.get("token_price_change_24h", "N/A") if isinstance(price_data, dict) else "N/A"
                            price_text += f"- {token_id}: ${price} (24h: {change_24h}%)\n"
                        return {
                            "response": price_text,
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                    else:
                        return {
                            "response": "No price data available.",
                            "thinking": None,
                            "strategy_updated": False,
                            "strategy_needs_confirmation": False,
                            "success": True,
                        }
                except json.JSONDecodeError:
                    return {
                        "response": f"Failed to parse price data: {output[:200]}",
                        "thinking": None,
                        "strategy_updated": False,
                        "strategy_needs_confirmation": False,
                        "success": True,
                    }
            else:
                return {
                    "response": f"Failed to get prices: {output}",
                    "thinking": None,
                    "strategy_updated": False,
                    "strategy_needs_confirmation": False,
                    "success": True,
                }
        except Exception as e:
            return {
                "response": f"Error getting prices: {str(e)}",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

    def _execute_backtest_direct(self, message: str) -> Dict[str, Any]:
        """Execute backtest directly using token from strategy or message."""
        # Extract token address from message if provided
        parts = message.split()
        token_address = None
        timeframe = "1d"
        start_date = None
        end_date = None

        # Parse arguments from message
        for i, part in enumerate(parts[1:], 1):  # Skip /backtest
            if part.startswith("0x") and len(part) > 20:
                token_address = part
            elif part in ["1d", "4h", "1h", "15m"]:
                timeframe = part
            elif part.startswith("20") and len(part) == 10:
                if not start_date:
                    start_date = part
                else:
                    end_date = part

        # If no token address in message, try to get from strategy
        if not token_address and self.bot_id:
            try:
                from ...core.database import get_db
                db = next(get_db())
                try:
                    bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
                    if bot and bot.strategy_config:
                        conditions = bot.strategy_config.get("conditions", [])
                        for cond in conditions:
                            addr = cond.get("token_address")
                            if addr:
                                token_address = addr
                                break
                finally:
                    db.close()
            except Exception:
                pass

        if not token_address:
            return {
                "response": "📊 **Backtest**\n\nI need a token address to run a backtest. Please provide:\n- Token contract address (e.g., `0x...`)\n- Timeframe (1d, 4h, 1h, 15m) - default is 1d\n- Start and end dates (YYYY-MM-DD) - optional, defaults to last 30 days",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        # Execute backtest
        result = self._execute_backtest(
            token_address=token_address,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "response": result,
            "thinking": None,
            "strategy_updated": False,
            "strategy_needs_confirmation": False,
            "success": True,
        }

    def _execute_simulate_direct(self, message: str) -> Dict[str, Any]:
        """Execute simulate directly using token from strategy or message."""
        # Extract parameters from message
        parts = message.split()
        action = None
        token_address = None
        kline_interval = "1m"

        # Parse arguments from message
        for i, part in enumerate(parts[1:], 1):  # Skip /simulate
            if part in ["start", "stop", "status", "results"]:
                action = part
            elif part.startswith("0x") and len(part) > 20:
                token_address = part
            elif part in ["1m", "5m", "15m", "1h", "4h"]:
                kline_interval = part

        # If no token in message and action is start, try to get from strategy
        if not token_address and self.bot_id and action == "start":
            try:
                from ...core.database import get_db
                db = next(get_db())
                try:
                    bot = db.query(Bot).filter(Bot.id == self.bot_id).first()
                    if bot and bot.strategy_config:
                        conditions = bot.strategy_config.get("conditions", [])
                        for cond in conditions:
                            addr = cond.get("token_address")
                            if addr:
                                token_address = addr
                                break
                finally:
                    db.close()
            except Exception:
                pass

        if action == "start" and not token_address:
            return {
                "response": "🎮 **Simulation**\n\nI need a token address to start a simulation. Please provide:\n- Token contract address (e.g., `0x...`)\n- Kline interval (1m, 5m, 15m, 1h, 4h) - default is 1m",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        if not action:
            return {
                "response": "🎮 **Simulation**\n\nPlease specify an action:\n- `/simulate start [token_address]` - Start new simulation\n- `/simulate stop` - Stop running simulation\n- `/simulate status` - Check simulation status\n- `/simulate results` - Get simulation results",
                "thinking": None,
                "strategy_updated": False,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        # Execute simulation
        result = self._manage_simulation(
            action=action,
            token_address=token_address,
            kline_interval=kline_interval,
        )
        return {
            "response": result,
            "thinking": None,
            "strategy_updated": False,
            "strategy_needs_confirmation": False,
            "success": True,
        }

    def chat(
        self, user_message: str, conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """Process a user message and return a structured response.

        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages

        Returns:
            Dict with 'response', 'thinking', and 'strategy_updated'
        """
        try:
            # Handle slash commands
            if user_message.startswith("/"):
                result = self._handle_slash_command(user_message)
                # If None returned, it means a skill was recognized but has args - let AI handle it
                if result is not None:
                    return result

            # Check if there's a pending command from previous message
            if self.pending_command:
                pending = self.pending_command
                self.pending_command = None  # Clear pending

                # Auto-execute the pending command with user's message as param
                if pending == "search":
                    return self._execute_search(user_message)
                elif pending == "risk":
                    return self._execute_risk(user_message)
                elif pending == "token":
                    return self._execute_token(user_message)
                elif pending == "price":
                    return self._execute_price(user_message)

            # Check for backtest/simulate with args in message
            if user_message.startswith("/backtest"):
                return self._execute_backtest_direct(user_message)
            elif user_message.startswith("/simulate"):
                return self._execute_simulate_direct(user_message)

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
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "thinking": {"type": "human", "budget_tokens": 1500},
                    "tools": TOOLS,
                },
            )

            result = resp.json() or {}

            # Extract thinking from reasoning_content
            thinking = None
            if result.get("choices") and len(result.get("choices", [])) > 0:
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
                                keyword = args.get("keyword", "")
                                limit = args.get("limit", 10)

                                code, output = self._call_ave_script(
                                    "search",
                                    [
                                        "--keyword",
                                        keyword,
                                        "--chain",
                                        "bsc",
                                        "--limit",
                                        str(limit),
                                    ],
                                )
                                if code == 0:
                                    try:
                                        data = json.loads(output)
                                        # Handle both dict with 'tokens' key and direct list
                                        data_field = data.get("data", [])
                                        if isinstance(data_field, list):
                                            tokens = data_field
                                        else:
                                            tokens = data_field.get("tokens", [])
                                        if tokens:
                                            token_list = ""
                                            for t in tokens[:limit]:
                                                addr = t.get("token", "")
                                                symbol = t.get("symbol", "")
                                                name = t.get("name", "")
                                                price_change = t.get(
                                                    "token_price_change_24h", "N/A"
                                                )
                                                mc = t.get("market_cap", "N/A")
                                                try:
                                                    mc_str = f"${float(mc):,.0f}"
                                                except (ValueError, TypeError):
                                                    mc_str = str(mc)
                                                token_list += f"- **{symbol}** ({name}): `{addr}` - MC: {mc_str} - 24h: {price_change}%\n"
                                            response_text = f"Here are the search results for '{keyword}' on BSC:\n\n{token_list}\nWould you like me to set up a strategy for any of these?"
                                        else:
                                            response_text = f"No tokens found for '{keyword}'. Try a different keyword."
                                    except json.JSONDecodeError:
                                        response_text = (
                                            f"Failed to parse search results."
                                        )
                                else:
                                    response_text = f"Failed to search tokens: {output}"

                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

                            elif func_name == "get_token":
                                address = args.get("address", "")
                                chain = args.get("chain", "bsc")

                                code, output = self._call_ave_script(
                                    "token", ["--address", address, "--chain", chain]
                                )
                                if code == 0:
                                    try:
                                        data = json.loads(output)
                                        data_field = data.get("data")
                                        # Handle both dict and list responses
                                        token_data = data_field if isinstance(data_field, dict) else {}
                                        # Token details may be nested in 'token' key
                                        token_info = token_data.get("token", token_data)
                                        # Check if token has valid symbol/name (not None, not 'N/A')
                                        symbol = token_info.get("symbol") or token_data.get("symbol")
                                        name = token_info.get("name") or token_data.get("name")
                                        if not symbol or symbol == "N/A" or not name or name == "N/A":
                                            response_text = f"Token not found for {address}. Raw response: {output[:500]}"
                                        else:
                                            # Try different price field names
                                            price = (token_info.get("current_price_usd") 
                                                     or token_info.get("price_usd") 
                                                     or token_info.get("price") 
                                                     or token_data.get("price") 
                                                     or "N/A")
                                            mc = (token_info.get("market_cap") 
                                                  or token_info.get("fdv") 
                                                  or token_data.get("market_cap") 
                                                  or "N/A")
                                            vol = (token_info.get("tx_volume_u_24h") 
                                                   or token_info.get("volume_24h") 
                                                   or token_data.get("volume_24h") 
                                                   or "N/A")
                                            pairs = token_info.get("top_pairs") or token_data.get("top_pairs") or []
                                            pairs_text = ""
                                            if pairs:
                                                pairs_text = "\n**Top Pairs:**\n"
                                                for p in pairs[:3]:
                                                    liq = p.get('liquidity', 'N/A')
                                                    try:
                                                        liq_str = f"${float(liq):,.0f}"
                                                    except (ValueError, TypeError):
                                                        liq_str = str(liq)
                                                    pairs_text += f"- {p.get('pair', 'N/A')}: {liq_str} liquidity\n"
                                            try:
                                                mc_str = f"${float(mc):,.0f}" if mc != "N/A" else "N/A"
                                            except (ValueError, TypeError):
                                                mc_str = str(mc)
                                            try:
                                                vol_str = f"${float(vol):,.0f}" if vol != "N/A" else "N/A"
                                            except (ValueError, TypeError):
                                                vol_str = str(vol)
                                            response_text = f"**{symbol}** ({name})\n\nPrice: ${price}\nMarket Cap: {mc_str}\n24h Volume: {vol_str}{pairs_text}"
                                    except json.JSONDecodeError:
                                        response_text = "Failed to parse token data."
                                else:
                                    response_text = (
                                        f"Failed to get token details: {output}"
                                    )

                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

                            elif func_name == "get_price":
                                token_ids = args.get("token_ids", "")

                                tokens_list = token_ids.replace(",", " ").split()
                                if not tokens_list:
                                    response_text = "No token IDs provided."
                                else:
                                    code, output = self._call_ave_script(
                                        "price", ["--tokens"] + tokens_list
                                    )
                                    if code == 0:
                                        try:
                                            data = json.loads(output)
                                            prices = data.get("data", {})
                                            # Ensure prices is a dict
                                            if not isinstance(prices, dict):
                                                prices = {}
                                            if prices:
                                                price_text = "**Token Prices:**\n"
                                                for (
                                                    token_id,
                                                    price_data,
                                                ) in prices.items():
                                                    price = price_data.get(
                                                        "price", "N/A"
                                                    )
                                                    change_24h = price_data.get(
                                                        "token_price_change_24h", "N/A"
                                                    )
                                                    price_text += f"- {token_id}: ${price} (24h: {change_24h}%)\n"
                                                response_text = price_text
                                            else:
                                                response_text = (
                                                    "No price data available."
                                                )
                                        except json.JSONDecodeError:
                                            response_text = (
                                                "Failed to parse price data."
                                            )
                                    else:
                                        response_text = (
                                            f"Failed to get prices: {output}"
                                        )

                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

                            elif func_name == "get_risk":
                                address = args.get("address", "")
                                chain = args.get("chain", "bsc")

                                code, output = self._call_ave_script(
                                    "risk", ["--address", address, "--chain", chain]
                                )
                                if code == 0:
                                    try:
                                        data = json.loads(output)
                                        data_field = data.get("data")
                                        # Handle both dict and list responses
                                        risk_data = data_field if isinstance(data_field, dict) else {}
                                        if risk_data:
                                            is_honeypot = risk_data.get(
                                                "is_honeypot", "unknown"
                                            )
                                            buy_tax = risk_data.get("buy_tax", 0)
                                            sell_tax = risk_data.get("sell_tax", 0)
                                            status = risk_data.get("status", "unknown")
                                            # Convert is_honeypot to string for comparison
                                            if isinstance(is_honeypot, bool):
                                                is_honeypot_str = str(is_honeypot).lower()
                                            elif isinstance(is_honeypot, int):
                                                if is_honeypot == 1:
                                                    is_honeypot_str = "true"
                                                elif is_honeypot == 0:
                                                    is_honeypot_str = "false"
                                                else:
                                                    is_honeypot_str = "unknown"  # -1 or other means couldn't determine
                                            else:
                                                is_honeypot_str = str(is_honeypot).lower() if is_honeypot else "unknown"
                                            
                                            # Format honeypot display value
                                            if is_honeypot_str == "unknown":
                                                honeypot_display = "Unknown (could not determine)"
                                            else:
                                                honeypot_display = is_honeypot_str
                                            # Convert tax values to float for comparison
                                            try:
                                                buy_tax_val = float(buy_tax) if buy_tax not in (None, "N/A") else 0
                                            except (ValueError, TypeError):
                                                buy_tax_val = 0
                                            try:
                                                sell_tax_val = float(sell_tax) if sell_tax not in (None, "N/A") else 0
                                            except (ValueError, TypeError):
                                                sell_tax_val = 0
                                            risk_text = (
                                                f"**Risk Analysis for {address}**\n\n"
                                            )
                                            risk_text += f"- Status: {status}\n"
                                            risk_text += f"- Honeypot: {honeypot_display}\n"
                                            risk_text += f"- Buy Tax: {buy_tax}%\n"
                                            risk_text += f"- Sell Tax: {sell_tax}%\n"
                                            if is_honeypot_str == "true":
                                                risk_text += "\n⚠️ **Warning: This token appears to be a honeypot. Do not buy!**"
                                            elif buy_tax_val > 10 or sell_tax_val > 10:
                                                risk_text += "\n⚠️ **Warning: High tax detected. Trade with caution!**"
                                            else:
                                                risk_text += "\n✅ This token appears safe to trade."
                                            response_text = risk_text
                                        else:
                                            response_text = (
                                                f"No risk data available for {address}"
                                            )
                                    except json.JSONDecodeError:
                                        response_text = "Failed to parse risk data."
                                else:
                                    response_text = f"Failed to get risk data: {output}"

                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

                            elif func_name == "get_trending":
                                chain = args.get("chain", "bsc")
                                limit = args.get("limit", 10)

                                code, output = self._call_ave_script(
                                    "trending",
                                    ["--chain", chain, "--page-size", str(min(limit, 50))],
                                )
                                if code == 0:
                                    try:
                                        data = json.loads(output)
                                        data_field = data.get("data")
                                        # Handle both dict and list responses
                                        tokens = data_field if isinstance(data_field, list) else data_field.get("tokens", [])
                                        if tokens:
                                            token_list = ""
                                            for t in tokens[:limit]:
                                                addr = t.get("token", "")
                                                symbol = t.get("symbol", "")
                                                name = t.get("name", "")
                                                price_change = t.get("token_price_change_24h", "N/A")
                                                mc = t.get("market_cap", "N/A")
                                                try:
                                                    mc_str = f"${float(mc):,.0f}"
                                                except (ValueError, TypeError):
                                                    mc_str = str(mc)
                                                token_list += f"- **{symbol}** ({name}): `{addr}` - MC: {mc_str} - 24h: {price_change}%\n"
                                            response_text = f"🔥 Trending tokens on {chain.upper()}:\n\n{token_list}\nWould you like me to set up a strategy for any of these?"
                                        else:
                                            response_text = f"No trending tokens found on {chain.upper()}."
                                    except json.JSONDecodeError:
                                        response_text = "Failed to parse trending data."
                                else:
                                    response_text = f"Failed to get trending tokens: {output}"

                                return {
                                    "response": response_text,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
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
                                    end_date=end_date,
                                )

                                return {
                                    "response": backtest_result,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

                            elif func_name == "manage_simulation":
                                action = args.get("action")
                                token_address = args.get("token_address")
                                kline_interval = args.get("kline_interval", "1m")

                                # Execute simulation management
                                sim_result = self._manage_simulation(
                                    action=action,
                                    token_address=token_address,
                                    kline_interval=kline_interval,
                                )

                                return {
                                    "response": sim_result,
                                    "thinking": thinking,
                                    "strategy_updated": False,
                                    "strategy_needs_confirmation": False,
                                    "success": True,
                                }

            # Get the main response content
            content = (
                result.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            # Parse JSON from the content
            thinking_field = None
            response_text = content
            strategy_update = None

            # Try to extract JSON from the content
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
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
                        keyword = args.get("keyword", "")
                        limit = args.get("limit", 10)

                        # Execute the tool using ave-cloud-skill CLI
                        code, output = self._call_ave_script(
                            "search",
                            [
                                "--keyword",
                                keyword,
                                "--chain",
                                "bsc",
                                "--limit",
                                str(limit),
                            ],
                        )
                        if code == 0:
                            try:
                                data = json.loads(output)
                                # Handle both dict with 'tokens' key and direct list
                                data_field = data.get("data", [])
                                if isinstance(data_field, list):
                                    tokens = data_field
                                else:
                                    tokens = data_field.get("tokens", [])
                                if tokens:
                                    token_list = ""
                                    for t in tokens[:limit]:
                                        addr = t.get("token", "")
                                        symbol = t.get("symbol", "")
                                        name = t.get("name", "")
                                        price_change = t.get(
                                            "token_price_change_24h", "N/A"
                                        )
                                        mc = t.get("market_cap", "N/A")
                                        try:
                                            mc_str = f"${float(mc):,.0f}"
                                        except (ValueError, TypeError):
                                            mc_str = str(mc)
                                        token_list += f"- **{symbol}** ({name}): `{addr}` - MC: {mc_str} - 24h: {price_change}%\n"
                                    response_text = f"Here are the search results for '{keyword}' on BSC:\n\n{token_list}\nWould you like me to set up a strategy for any of these?"
                                else:
                                    response_text = f"No tokens found for '{keyword}'. Try a different keyword."
                            except json.JSONDecodeError:
                                response_text = "Failed to parse search results."
                        else:
                            response_text = f"Failed to search tokens: {output}"

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
                for cond in (strategy_update.get("conditions") or []):
                    if not cond.get("token_address") and cond.get("token"):
                        token_name = cond.get("token")
                        strategy_needs_confirmation = True
                        break

                # Search for token if name is found
                if strategy_needs_confirmation and token_name:
                    try:
                        code, output = self._call_ave_script(
                            "search",
                            ["--keyword", token_name, "--chain", "bsc", "--limit", "5"],
                        )
                        if code == 0:
                            data = json.loads(output)
                            # Handle both dict with 'tokens' key and direct list
                            data_field = data.get("data", [])
                            if isinstance(data_field, list):
                                tokens = data_field
                            else:
                                tokens = data_field.get("tokens", [])
                            if tokens:
                                token_search_results = [
                                    {
                                        "symbol": t.get("symbol", ""),
                                        "name": t.get("name", ""),
                                        "address": t.get("token", ""),
                                        "chain": t.get("chain", "bsc"),
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
                    "success": True,
                }

            # Update strategy in database if provided
            if strategy_update and self.bot_id:
                self._update_strategy(strategy_update)

            return {
                "response": response_text,
                "thinking": final_thinking,
                "strategy_updated": strategy_update is not None,
                "strategy_needs_confirmation": False,
                "success": True,
            }

        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "thinking": None,
                "strategy_updated": False,
                "success": False,
            }

    def _execute_backtest(
        self,
        token_address: str,
        timeframe: str = "1d",
        start_date: str = None,
        end_date: str = None,
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
            return_str = (
                f"+{total_return:.2f}%" if total_return >= 0 else f"{total_return:.2f}%"
            )

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
        self, action: str, token_address: str = None, kline_interval: str = "1m"
    ) -> str:
        """Manage trading simulations: start, stop, status, or results."""
        try:
            import asyncio
            import threading
            import uuid
            from ...core.database import SessionLocal
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
                    running_sim = (
                        db.query(Simulation)
                        .filter(
                            Simulation.bot_id == self.bot_id,
                            Simulation.status == "running",
                        )
                        .first()
                    )

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
                            "kline_interval": kline_interval,
                        },
                        signals=[],
                        klines=[],
                        trade_log=[],
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
                        asyncio.run(
                            self._run_simulation_sync(
                                sim_id, settings.DATABASE_URL, sim_config
                            )
                        )

                    thread = threading.Thread(target=run_sim)
                    thread.daemon = True
                    thread.start()

                    return f"Started simulation on {token_address} using {kline_interval} klines. The simulation is running and will process up to 100 candles. Ask me for status or results anytime!"

                elif action == "stop":
                    # Find running simulation
                    running_sim = (
                        db.query(Simulation)
                        .filter(
                            Simulation.bot_id == self.bot_id,
                            Simulation.status == "running",
                        )
                        .first()
                    )

                    if not running_sim:
                        return "No simulation is currently running."

                    self._stop_simulation_db(running_sim.id)

                    # Get final results
                    portfolio = running_sim.portfolio or {}
                    current_balance = portfolio.get("current_balance", 10000)
                    initial_balance = portfolio.get("initial_balance", 10000)
                    pnl = current_balance - initial_balance
                    pnl_pct = (
                        (pnl / initial_balance) * 100 if initial_balance > 0 else 0
                    )

                    return f"Simulation stopped!\n\nFinal Results:\n💰 Final Balance: ${current_balance:,.2f}\n📈 P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f} ({'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%)\n📊 Trades: {len(running_sim.trade_log or [])}"

                elif action == "status":
                    # Find running simulation
                    running_sim = (
                        db.query(Simulation)
                        .filter(
                            Simulation.bot_id == self.bot_id,
                            Simulation.status == "running",
                        )
                        .first()
                    )

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
                        status += (
                            f"💰 Cash: ${portfolio.get('current_balance', 0):,.2f}\n"
                        )
                    else:
                        status += f"💰 Cash: ${portfolio.get('current_balance', 10000):,.2f}\n"

                    status += "\nAsk me to stop or get full results anytime!"
                    return status

                elif action == "results":
                    # Find running or most recent simulation
                    simulation = (
                        db.query(Simulation)
                        .filter(Simulation.bot_id == self.bot_id)
                        .order_by(Simulation.started_at.desc())
                        .first()
                    )

                    if not simulation:
                        return "No simulation found. Start a simulation first!"

                    portfolio = simulation.portfolio or {}
                    current_balance = portfolio.get("current_balance", 10000)
                    initial_balance = portfolio.get("initial_balance", 10000)
                    pnl = current_balance - initial_balance
                    pnl_pct = (
                        (pnl / initial_balance) * 100 if initial_balance > 0 else 0
                    )
                    trade_log = simulation.trade_log or []

                    status_emoji = "🟢" if simulation.status == "running" else "⚪"
                    status_text = (
                        "Running"
                        if simulation.status == "running"
                        else "Completed/Stopped"
                    )

                    results = (
                        f"**Simulation Results** {status_emoji} ({status_text})\n\n"
                    )
                    results += f"💰 Final Balance: ${current_balance:,.2f}\n"
                    results += f"📈 P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f} ({'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%)\n"
                    results += f"📊 Total Trades: {len(trade_log)}\n"

                    if simulation.status == "running":
                        results += (
                            f"\n⏳ Simulation still running... (refresh for latest)"
                        )

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
            simulation = (
                db.query(Simulation).filter(Simulation.id == simulation_id).first()
            )
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
                    sim = (
                        db.query(Simulation)
                        .filter(Simulation.id == simulation_id)
                        .first()
                    )
                    if sim:
                        sim.status = engine.status
                        sim.signals = [serialize_signal(s) for s in engine.signals]
                        sim.klines = [
                            {"time": k.get("time"), "close": k.get("close")}
                            for k in engine.klines
                        ]
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

    def _call_ave_script(self, command: str, args: list) -> tuple[int, str]:
        """Call an ave-cloud-skill CLI script and return (status_code, stdout)."""
        import json
        import os
        import subprocess
        from ...core.config import get_settings

        settings = get_settings()
        repo_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        )
        ave_skill_path = os.path.join(
            repo_root, "ave-cloud-skill", "scripts", "ave_data_rest.py"
        )

        env = os.environ.copy()
        env["AVE_API_KEY"] = settings.AVE_API_KEY
        env["API_PLAN"] = settings.AVE_API_PLAN
        env["AVE_USE_DOCKER"] = "false"

        try:
            result = subprocess.run(
                ["python3", ave_skill_path, command] + args,
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            # Include stderr in output for debugging
            output = result.stdout
            if result.returncode != 0 and result.stderr:
                output = f"{output}\n{result.stderr}".strip()
            return result.returncode, output
        except subprocess.TimeoutExpired:
            return 1, "Error: Command timed out"
        except Exception as e:
            return 1, f"Error: {str(e)}"


def get_conversational_agent(
    api_key: str = None, model: str = None, bot_id: str = None
) -> ConversationalAgent:
    """Get or create a ConversationalAgent instance."""
    if api_key is None:
        settings = get_settings()
        api_key = settings.MINIMAX_API_KEY
    if model is None:
        settings = get_settings()
        model = settings.MINIMAX_MODEL

    return ConversationalAgent(api_key=api_key, model=model, bot_id=bot_id)
