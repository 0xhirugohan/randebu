from typing import List, Optional, Dict, Any
from crewai import Agent, Task, Crew
from .llm_connector import MiniMaxConnector, MiniMaxLLM
from ...core.config import get_settings


class StrategyValidator:
    SUPPORTED_CONDITIONS = ["price_drop", "price_rise", "volume_spike", "price_level"]
    SUPPORTED_ACTIONS = ["buy", "sell", "notify"]

    def validate(self, strategy_config: dict) -> tuple[bool, list[str]]:
        errors = []

        if "conditions" not in strategy_config:
            errors.append("Missing 'conditions' in strategy config")
            return False, errors

        if not isinstance(strategy_config["conditions"], list):
            errors.append("'conditions' must be a list")
            return False, errors

        if len(strategy_config["conditions"]) == 0:
            errors.append("At least one condition is required")
            return False, errors

        for i, condition in enumerate(strategy_config["conditions"]):
            if "type" not in condition:
                errors.append(f"Condition {i}: missing 'type'")
                continue

            cond_type = condition.get("type")
            if cond_type not in self.SUPPORTED_CONDITIONS:
                errors.append(f"Condition {i}: unsupported type '{cond_type}'")
                continue

            if cond_type in ["price_drop", "price_rise", "volume_spike"]:
                if "token" not in condition:
                    errors.append(f"Condition {i}: missing 'token'")
                if "threshold" not in condition:
                    errors.append(f"Condition {i}: missing 'threshold'")
                elif not isinstance(condition["threshold"], (int, float)):
                    errors.append(f"Condition {i}: 'threshold' must be a number")
                elif condition["threshold"] <= 0:
                    errors.append(f"Condition {i}: 'threshold' must be positive")

            elif cond_type == "price_level":
                if "token" not in condition:
                    errors.append(f"Condition {i}: missing 'token'")
                if "price" not in condition:
                    errors.append(f"Condition {i}: missing 'price'")
                if "direction" not in condition:
                    errors.append(f"Condition {i}: missing 'direction'")
                elif condition["direction"] not in ["above", "below"]:
                    errors.append(
                        f"Condition {i}: direction must be 'above' or 'below'"
                    )

        if "actions" in strategy_config:
            if not isinstance(strategy_config["actions"], list):
                errors.append("'actions' must be a list")
            else:
                for i, action in enumerate(strategy_config["actions"]):
                    if "type" not in action:
                        errors.append(f"Action {i}: missing 'type'")
                    elif action["type"] not in self.SUPPORTED_ACTIONS:
                        errors.append(
                            f"Action {i}: unsupported type '{action['type']}'"
                        )

        return len(errors) == 0, errors


class StrategyExplainer:
    def explain(self, strategy_config: dict) -> str:
        explanations = []

        if "conditions" in strategy_config:
            cond_list = strategy_config["conditions"]
            if cond_list:
                explanations.append("This strategy will trigger when:")
                for cond in cond_list:
                    cond_type = cond.get("type")
                    token = cond.get("token", "the token")

                    if cond_type == "price_drop":
                        pct = cond.get("threshold", 0)
                        explanations.append(f"  - {token} price drops by {pct}%")
                    elif cond_type == "price_rise":
                        pct = cond.get("threshold", 0)
                        explanations.append(f"  - {token} price rises by {pct}%")
                    elif cond_type == "volume_spike":
                        pct = cond.get("threshold", 0)
                        explanations.append(
                            f"  - {token} trading volume increases by {pct}%"
                        )
                    elif cond_type == "price_level":
                        price = cond.get("price", 0)
                        direction = cond.get("direction", "unknown")
                        explanations.append(
                            f"  - {token} price crosses {direction} ${price}"
                        )

        if "actions" in strategy_config:
            actions = strategy_config.get("actions", [])
            if actions:
                explanations.append("\nWhen triggered, the strategy will:")
                for action in actions:
                    action_type = action.get("type")
                    if action_type == "buy":
                        explanations.append("  - Buy the token")
                    elif action_type == "sell":
                        explanations.append("  - Sell the token")
                    elif action_type == "notify":
                        explanations.append("  - Send a notification")

        if not explanations:
            explanations.append("Strategy configuration is empty or invalid.")

        return "\n".join(explanations)


def create_trading_designer_agent(
    api_key: str, model: str = "MiniMax-M2.7"
) -> Agent:
    connector = MiniMaxConnector(api_key=api_key, model=model)

    system_prompt = """You are a Trading Strategy Designer AI. Your role is to parse user requests 
    for trading strategies into structured JSON configuration.

    Supported conditions (MVP):
    - price_drop: Triggers when a token's price drops by a specified percentage
    - price_rise: Triggers when a token's price rises by a specified percentage
    - volume_spike: Triggers when trading volume increases by a specified percentage
    - price_level: Triggers when price crosses above or below a specified level

    Always ask clarifying questions if the user's request is ambiguous.
    Output strategy_config in valid JSON format only when you have all required information.
    """

    return Agent(
        role="Trading Strategy Designer",
        goal="Convert natural language trading requests into precise strategy configurations",
        backstory=system_prompt,
        llm=MiniMaxLLM(api_key=api_key, model=model),
        verbose=True,
    )


def create_strategy_validator_agent(
    api_key: str, model: str = "MiniMax-M2.7"
) -> Agent:
    return Agent(
        role="Strategy Validator",
        goal="Validate trading strategy configurations for feasibility and identify potential issues",
        backstory="""You are a meticulous strategy validator with expertise in trading systems.
        You check that all required parameters are present, values are reasonable, and the 
        strategy makes logical sense. You never approve strategies with missing or invalid data.""",
        llm=MiniMaxLLM(api_key=api_key, model=model),
        verbose=True,
    )


def create_strategy_explainer_agent(
    api_key: str, model: str = "MiniMax-M2.7"
) -> Agent:
    return Agent(
        role="Strategy Explainer",
        goal="Generate clear, user-friendly explanations of trading strategies",
        backstory="""You are a patient trading strategy explainer. You translate complex 
        strategy configurations into easy-to-understand language. You help users understand 
        exactly what their strategies will do when triggered.""",
        llm=MiniMaxLLM(api_key=api_key, model=model),
        verbose=True,
    )


class TradingCrew:
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
        self.api_key = api_key
        self.model = model
        self.validator = StrategyValidator()
        self.explainer = StrategyExplainer()
        self.connector = MiniMaxConnector(api_key=api_key, model=model)

    def parse_strategy(
        self, user_message: str, conversation_history: list[dict] = None
    ) -> dict:
        strategy_config = self.connector.parse_strategy(
            user_message, conversation_history
        )

        if "error" in strategy_config:
            return strategy_config

        is_valid, errors = self.validator.validate(strategy_config)
        if not is_valid:
            return {
                "error": "Strategy validation failed",
                "validation_errors": errors,
                "partial_config": strategy_config,
            }

        return strategy_config

    def explain_strategy(self, strategy_config: dict) -> str:
        return self.explainer.explain(strategy_config)

    def chat(self, user_message: str, conversation_history: list[dict] = None) -> dict:
        strategy_config = self.parse_strategy(user_message, conversation_history)

        if "error" in strategy_config:
            explanation = f"I had trouble understanding your strategy: {strategy_config.get('error', 'Unknown error')}"
            if "validation_errors" in strategy_config:
                explanation += "\n\nValidation issues:"
                for err in strategy_config["validation_errors"]:
                    explanation += f"\n  - {err}"
            return {
                "response": explanation,
                "strategy_config": strategy_config.get("partial_config"),
                "success": False,
            }

        explanation = self.explain_strategy(strategy_config)
        return {
            "response": f"I've configured your strategy:\n\n{explanation}",
            "strategy_config": strategy_config,
            "success": True,
        }


def get_trading_crew(
    api_key: Optional[str] = None, model: Optional[str] = None
) -> TradingCrew:
    if api_key is None:
        settings = get_settings()
        api_key = settings.MINIMAX_API_KEY
    if model is None:
        settings = get_settings()
        model = settings.MINIMAX_MODEL

    return TradingCrew(api_key=api_key, model=model)
