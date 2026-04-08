from typing import Optional


class LLMConnector:
    def __init__(self, api_key: str, model: str = "MiniMax-Text-01"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict], **kwargs):
        raise NotImplementedError("LLM integration not yet implemented")

    def parse_strategy(self, user_message: str) -> dict:
        raise NotImplementedError("Strategy parsing not yet implemented")
