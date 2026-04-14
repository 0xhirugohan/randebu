"""MiniMax API client for the conversational agent."""

import requests
from typing import Dict, Any, Optional, List


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


class MiniMaxClient:
    """Client for MiniMax extended thinking API."""

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.minimax.io/v1/text/chatcompletion_v2"

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        thinking_budget: int = 1500,
    ) -> Dict[str, Any]:
        """Send a chat request to MiniMax API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        all_messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": self.model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking": {"type": "human", "budget_tokens": thinking_budget},
        }

        if tools:
            payload["tools"] = tools

        resp = requests.post(self.endpoint, headers=headers, json=payload)
        return resp.json() or {}

    def check_connection(self) -> bool:
        """Check if API is reachable."""
        try:
            resp = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False
