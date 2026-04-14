"""Help formatters for slash commands and tool documentation."""

from typing import Optional
from .tools import get_tool_registry, SKILL_EMOJIS


def format_tools_list() -> str:
    """Format the tool registry as a help message."""
    message = "📋 Available Tools\n\n"

    for category in ["randebu", "ave"]:
        tools = get_tool_registry().get(category, [])
        if category == "randebu":
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
        for tool in get_tool_registry().get(category, []):
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
