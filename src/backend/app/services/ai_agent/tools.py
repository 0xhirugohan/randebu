"""Tool registry and definitions for the conversational agent."""

from typing import Dict, Any, List

TOOL_REGISTRY: Dict[str, Any] = {
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
        {
            "name": "create_bot",
            "description": "Create a new trading bot",
            "category": "Randebu Built-in",
            "command": None,
            "details": {
                "description": "Create a new trading bot linked to the current conversation.",
                "usage": "create_bot <name> [--strategy <strategy_desc>]",
                "example": "create_bot MyBot --strategy Buy PEPE when it drops 5%",
            },
        },
        {
            "name": "list_bots",
            "description": "List your trading bots",
            "category": "Randebu Built-in",
            "command": None,
            "details": {
                "description": "List all trading bots you own.",
                "usage": "list_bots",
                "example": "list_bots",
            },
        },
        {
            "name": "set_bot",
            "description": "Set bot for this conversation",
            "category": "Randebu Built-in",
            "command": None,
            "details": {
                "description": "Associate a bot with the current conversation.",
                "usage": "set_bot <bot_id>",
                "example": "set_bot abc-123-def",
            },
        },
        {
            "name": "get_bot_info",
            "description": "Get current bot details",
            "category": "Randebu Built-in",
            "command": None,
            "details": {
                "description": "Get details of the current bot for display in the right pane.",
                "usage": "get_bot_info [bot_id]",
                "example": "get_bot_info abc-123-def",
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

SKILL_EMOJIS: Dict[str, str] = {
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


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Get tools filtered by category."""
    return TOOL_REGISTRY.get(category, [])


def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
    """Get a tool by its name."""
    for category in ["randebu", "ave"]:
        for tool in TOOL_REGISTRY.get(category, []):
            if tool["name"].lower() == tool_name.lower():
                return tool
    return None
