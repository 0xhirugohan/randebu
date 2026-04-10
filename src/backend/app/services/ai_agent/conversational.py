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

from ...core.config import get_settings
from ...db.models import Bot


SYSTEM_PROMPT = """You are a helpful AI trading assistant named Randebu. You help users manage their trading bots.

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
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
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
                    }
                }
            )
            
            result = resp.json()
            
            # Extract thinking from reasoning_content
            thinking = None
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    thinking = choice["message"].get("reasoning_content")
            
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
                                    "address": t.get("id") or t.get("contract_address", ""),
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
