from typing import Optional, List, Dict, Any
import httpx
from crewai import LLM


class MiniMaxLLM(LLM):
    def __init__(self, api_key: str, model: str = "MiniMax-Text-01", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.minimax.chat/v1"

    def _call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return self._call(messages, **kwargs)


class MiniMaxConnector:
    def __init__(self, api_key: str, model: str = "MiniMax-Text-01"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict], **kwargs) -> str:
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", str(msg)),
                    }
                )
            else:
                formatted_messages.append({"role": "user", "content": str(msg)})

        llm = MiniMaxLLM(api_key=self.api_key, model=self.model)
        return llm.call(formatted_messages, **kwargs)

    def parse_strategy(
        self, user_message: str, conversation_history: list[dict] = None
    ) -> dict:
        system_prompt = """You are a trading strategy designer. Parse the user's natural language request into a JSON strategy_config object.

Supported conditions (MVP):
- price_drop: Token price drops by X% (requires: token, threshold_percent)
- price_rise: Token price rises by X% (requires: token, threshold_percent)
- volume_spike: Trading volume increases X% (requires: token, threshold_percent)
- price_level: Price crosses above/below X (requires: token, price, direction)

Output ONLY valid JSON with this schema:
{
    "conditions": [
        {
            "type": "price_drop|price_rise|volume_spike|price_level",
            "params": {
                "token": "TOKEN_SYMBOL",
                "threshold_percent": number,  // for price_drop, price_rise, volume_spike
                "price": number,              // for price_level
                "direction": "above|below"    // for price_level
            }
        }
    ],
    "actions": [
        {
            "type": "buy|sell|notify",
            "params": {}
        }
    ]
}

If the user wants a condition not in the supported list, ask for clarification.
"""

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history:
                messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )
        messages.append({"role": "user", "content": user_message})

        response = self.chat(messages)
        try:
            import json

            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {"error": "Failed to parse strategy", "raw_response": response}
