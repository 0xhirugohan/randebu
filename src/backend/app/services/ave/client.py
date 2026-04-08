import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class AveCloudClient:
    DATA_API_URL = "https://prod.ave-api.com"
    TRADING_API_URL = "https://bot-api.ave.ai"

    def __init__(self, api_key: str, plan: str = "free"):
        self.api_key = api_key
        self.plan = plan

    def _data_headers(self) -> Dict[str, str]:
        return {"X-API-KEY": self.api_key}

    def _trading_headers(self) -> Dict[str, str]:
        return {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    async def get_tokens(
        self,
        query: Optional[str] = None,
        chain: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/tokens"
        params = {"limit": limit}
        if query:
            params["query"] = query
        if chain:
            params["chain"] = chain

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self._data_headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", [])
            raise Exception(f"Failed to fetch tokens: {data}")

    async def get_batch_prices(self, token_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/tokens/price"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._data_headers(),
                json={"token_ids": token_ids},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", {})
            return {}

    async def get_token_details(self, token_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/tokens/{token_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._data_headers(), timeout=30.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data")
            return None

    async def get_klines(
        self,
        token_id: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/klines/token/{token_id}"
        params = {"interval": interval, "limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self._data_headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", [])
            raise Exception(f"Failed to fetch klines: {data}")

    async def get_trending_tokens(
        self, chain: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/tokens/trending"
        params = {"limit": limit}
        if chain:
            params["chain"] = chain

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self._data_headers(), params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data", [])
            raise Exception(f"Failed to fetch trending tokens: {data}")

    async def get_token_risk(self, contract_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.DATA_API_URL}/v2/contracts/{contract_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._data_headers(), timeout=30.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data")
            return None

    async def get_chain_quote(
        self,
        chain: str,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.TRADING_API_URL}/v1/chain/quote"
        payload = {
            "chain": chain,
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "slippage": slippage,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self._trading_headers(), json=payload, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data")
            return None

    async def get_chain_swap(
        self,
        chain: str,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 0.5,
        wallet_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.TRADING_API_URL}/v1/chain/swap"
        payload = {
            "chain": chain,
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "slippage": slippage,
        }
        if wallet_address:
            payload["wallet_address"] = wallet_address
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self._trading_headers(), json=payload, timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200:
                return data.get("data")
            return None


def check_tier_access(user_tier: str, feature: str) -> tuple[bool, Optional[str]]:
    tier_access = {
        "free": {
            "data_rest": True,
            "websocket": False,
            "chain_wallet": True,
            "proxy_wallet": False,
        },
        "normal": {
            "data_rest": True,
            "websocket": False,
            "chain_wallet": True,
            "proxy_wallet": True,
        },
        "pro": {
            "data_rest": True,
            "websocket": True,
            "chain_wallet": True,
            "proxy_wallet": True,
        },
    }

    if user_tier not in tier_access:
        user_tier = "free"

    access = tier_access[user_tier]
    if access.get(feature):
        return True, None

    upsell_messages = {
        "websocket": "Upgrade to Pro plan to access WebSocket streaming data. Visit your account settings.",
        "proxy_wallet": "Upgrade to Normal or Pro plan to access Proxy Wallet functionality. Visit your account settings.",
    }

    return False, upsell_messages.get(
        feature, "Upgrade your plan to access this feature."
    )
