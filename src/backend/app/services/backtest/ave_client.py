import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class AveCloudClient:
    BASE_URL = "https://prod.ave-api.com"

    def __init__(self, api_key: str, plan: str = "free"):
        self.api_key = api_key
        self.plan = plan

    def _headers(self) -> Dict[str, str]:
        return {"X-API-KEY": self.api_key}

    async def get_klines(
        self,
        token_id: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/v2/klines/token/{token_id}"
        params = {"interval": interval, "limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self._headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", [])
            raise Exception(f"Failed to fetch klines: {data}")

    async def get_token_price(self, token_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/v2/tokens/price"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={"token_ids": [token_id]},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                prices = data.get("data", {})
                return prices.get(token_id)
            return None

    async def get_batch_prices(self, token_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        url = f"{self.BASE_URL}/v2/tokens/price"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={"token_ids": token_ids},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", {})
            return {}
