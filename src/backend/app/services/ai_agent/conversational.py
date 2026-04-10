"""
Conversational Trading Agent

This agent can:
1. Have normal conversations with users
2. Update trading strategies when user provides specific instructions

Uses CrewAI's tool-calling capabilities for structured updates.
"""

from typing import List, Optional, Dict, Any
from crewai import Agent, LLM
from crewai.tools import tool
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...db.models import Bot


# Tool definitions
@tool
def get_current_strategy(bot_id: str) -> str:
    """Get the current trading strategy configuration for a bot.
    
    Use this tool to check the current strategy before making changes.
    
    Args:
        bot_id: The ID of the bot to get strategy for
        
    Returns:
        JSON string with current strategy configuration
    """
    from ...core.database import get_db
    from ...db.models import Bot
    
    db = next(get_db())
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        return '{"error": "Bot not found"}'
    return str(bot.strategy_config)


@tool
def update_trading_strategy(
    bot_id: str,
    conditions: List[Dict],
    actions: List[Dict],
    risk_management: Optional[Dict] = None
) -> str:
    """Update the trading strategy configuration for a bot.
    
    Call this tool when the user provides specific trading parameters like:
    - Buy/sell conditions (price drops, price rises, etc.)
    - Take profit percentages
    - Stop loss percentages
    
    Args:
        bot_id: The ID of the bot to update
        conditions: List of trigger conditions (e.g., [{"type": "price_drop", "token": "PEPE", "threshold": 5}])
        actions: List of actions to take (e.g., [{"type": "buy", "amount_percent": 50}])
        risk_management: Optional risk settings (e.g., {"stop_loss_percent": 10, "take_profit_percent": 50})
        
    Returns:
        Confirmation message with updated strategy
    """
    from ...core.database import get_db
    from ...db.models import Bot
    
    db = next(get_db())
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        return '{"error": "Bot not found"}'
    
    new_config = {
        "conditions": conditions,
        "actions": actions,
    }
    if risk_management:
        new_config["risk_management"] = risk_management
    
    bot.strategy_config = new_config
    db.commit()
    
    return f'Successfully updated trading strategy. New config: {new_config}'


SYSTEM_PROMPT = """You are a helpful AI trading assistant. You can:

1. Have normal conversations - answer questions about trading, tokens, strategies, etc.
2. Help users configure their trading bots when they provide specific parameters

When a user asks general questions, just answer conversationally.
When a user provides specific trading parameters (like percentages, tokens, conditions), 
use the update_trading_strategy tool to save their configuration.

Example conversations:
- User: "What is this?" → Answer conversationally about the trading bot platform
- User: "I want take profit at 200%" → Use update_trading_strategy with that parameter
- User: "Alert me when PEPE drops 5%" → Use update_trading_strategy with that condition

Be friendly, helpful, and clear in your responses."""


class ConversationalAgent:
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", bot_id: str = None):
        self.api_key = api_key
        self.model = model
        self.bot_id = bot_id
        self.llm = LLM(
            model=model,
            api_key=api_key,
            api_base="https://api.minimax.io/v1"
        )
        
        # Create agent with tools
        self.agent = Agent(
            role="Trading Assistant",
            goal="Help users with trading strategies and general questions",
            backstory=SYSTEM_PROMPT,
            tools=[get_current_strategy, update_trading_strategy],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a user message and return a response.
        
        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages
            
        Returns:
            Dict with 'response' (the assistant's reply), 'thinking' (reasoning), and 'strategy_updated' (bool)
        """
        # Execute agent using kickoff
        try:
            result = self.agent.kickoff(user_message)
            
            # Try to extract thinking from result if available
            thinking = None
            if hasattr(result, 'thinking') and result.thinking:
                thinking = result.thinking
            elif isinstance(result, dict) and 'thinking' in result:
                thinking = result.get('thinking')
            
            # The actual response
            result_str = str(result) if not isinstance(result, str) else result
            
            # Check if strategy was updated
            strategy_updated = "update_trading_strategy" in result_str or \
                             "Successfully updated" in result_str
            
            return {
                "response": result_str,
                "thinking": thinking,
                "strategy_updated": strategy_updated,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "thinking": None,
                "strategy_updated": False,
                "success": False
            }


def get_conversational_agent(api_key: str = None, model: str = None, bot_id: str = None) -> ConversationalAgent:
    """Get or create a ConversationalAgent instance."""
    if api_key is None:
        settings = get_settings()
        api_key = settings.MINIMAX_API_KEY
    if model is None:
        settings = get_settings()
        model = settings.MINIMAX_MODEL
    
    return ConversationalAgent(api_key=api_key, model=model, bot_id=bot_id)
