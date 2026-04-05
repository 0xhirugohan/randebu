#!/usr/bin/env python3
"""
AVE Cloud Data REST API - Token Search, Prices, Klines, Holders, Risk

Usage:
    export AVE_API_KEY=your_api_key_here
    export API_PLAN=free  # free, normal, pro

    python3 docs/scripts/ave_data_rest.py search --keyword PEPE
    python3 docs/scripts/ave_data_rest.py price --token-ids "PEPE-bsc,TRUMP-bsc"
    python3 docs/scripts/ave_data_rest.py trending --chain bsc
    python3 docs/scripts/ave_data_rest.py token --token-id "0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc"
    python3 docs/scripts/ave_data_rest.py risk --token-id "0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc"
    python3 docs/scripts/ave_data_rest.py holders --token-id "0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc"
    python3 docs/scripts/ave_data_rest.py klines --token-id "0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc"
    python3 docs/scripts/ave_data_rest.py pairs --pair-id "0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae-bsc"
    python3 docs/scripts/ave_data_rest.py wallet-pnl --wallet "0xd9c500dff816a1da21a48a732d3498bf09dc9aeb" --chain bsc --token "0x55d398326f99059fF775485246999027B3197955"
    python3 docs/scripts/ave_data_rest.py wallet-info --wallet "0xd9c500dff816a1da21a48a732d3498bf09dc9aeb" --chain bsc
    python3 docs/scripts/ave_data_rest.py smart-wallets --chain bsc
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

import requests

BASE_URL = "https://prod.ave-api.com"
API_KEY = os.getenv("AVE_API_KEY", "")
API_PLAN = os.getenv("API_PLAN", "free")

CU_COSTS = {
    "search": 5,
    "price": 100,
    "trending": 5,
    "token": 5,
    "risk": 10,
    "holders": 10,
    "klines_token": 10,
    "klines_pair": 10,
    "pairs": 5,
    "wallet_pnl": 5,
    "wallet_info": 5,
    "wallet_tokens": 10,
    "smart_wallet": 5,
}

TIER_LIMITS = {
    "free": {"tps": 1, "data_wss": False, "proxy_wallet": False},
    "normal": {"tps": 5, "data_wss": False, "proxy_wallet": True},
    "pro": {"tps": 20, "data_wss": True, "proxy_wallet": True},
}


@dataclass
class ApiResponse:
    status: int
    data: Optional[dict] = None
    error: Optional[str] = None


def make_headers():
    return {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    }


def handle_response(response: requests.Response) -> ApiResponse:
    if response.status_code == 200:
        return ApiResponse(status=200, data=response.json())
    elif response.status_code == 401:
        return ApiResponse(
            status=401, error="Unauthorized - invalid or missing API key"
        )
    elif response.status_code == 403:
        return ApiResponse(
            status=403, error="Forbidden - API key expired or plan limits reached"
        )
    elif response.status_code == 429:
        return ApiResponse(status=429, error="Rate limited - TPS exceeded")
    else:
        return ApiResponse(status=response.status_code, error=response.text)


def search_tokens(
    keyword: str, chain: Optional[str] = None, limit: int = 100
) -> ApiResponse:
    params = {"keyword": keyword, "limit": limit}
    if chain:
        params["chain"] = chain
    response = requests.get(
        f"{BASE_URL}/v2/tokens", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_token_price(token_ids: list) -> ApiResponse:
    data = {"token_ids": token_ids}
    response = requests.post(
        f"{BASE_URL}/v2/tokens/price", headers=make_headers(), json=data
    )
    return handle_response(response)


def get_trending_tokens(chain: str, page: int = 0, page_size: int = 50) -> ApiResponse:
    params = {"chain": chain, "current_page": page, "page_size": page_size}
    response = requests.get(
        f"{BASE_URL}/v2/tokens/trending", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_token_detail(token_id: str) -> ApiResponse:
    response = requests.get(f"{BASE_URL}/v2/tokens/{token_id}", headers=make_headers())
    return handle_response(response)


def get_token_risk(token_id: str) -> ApiResponse:
    response = requests.get(
        f"{BASE_URL}/v2/contracts/{token_id}", headers=make_headers()
    )
    return handle_response(response)


def get_top_holders(token_id: str, limit: int = 100) -> ApiResponse:
    params = {"limit": limit} if limit != 100 else {}
    response = requests.get(
        f"{BASE_URL}/v2/tokens/top100/{token_id}", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_klines_by_token(
    token_id: str, interval: str = "1h", limit: int = 100
) -> ApiResponse:
    params = {"interval": interval, "limit": limit}
    response = requests.get(
        f"{BASE_URL}/v2/klines/token/{token_id}", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_klines_by_pair(
    pair_id: str, interval: str = "1h", limit: int = 100
) -> ApiResponse:
    params = {"interval": interval, "limit": limit}
    response = requests.get(
        f"{BASE_URL}/v2/klines/pair/{pair_id}", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_pair_detail(pair_id: str) -> ApiResponse:
    response = requests.get(f"{BASE_URL}/v2/pairs/{pair_id}", headers=make_headers())
    return handle_response(response)


def get_wallet_pnl(
    wallet_address: str,
    chain: str,
    token_address: str,
    from_time: Optional[int] = None,
    to_time: Optional[int] = None,
) -> ApiResponse:
    params = {
        "wallet_address": wallet_address,
        "chain": chain,
        "token_address": token_address,
    }
    if from_time:
        params["from_time"] = from_time
    if to_time:
        params["to_time"] = to_time
    response = requests.get(
        f"{BASE_URL}/v2/address/pnl", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_wallet_info(wallet_address: str, chain: str) -> ApiResponse:
    params = {"wallet_address": wallet_address, "chain": chain}
    response = requests.get(
        f"{BASE_URL}/v2/address/walletinfo", headers=make_headers(), params=params
    )
    return handle_response(response)


def get_wallet_tokens(
    wallet_address: str,
    chain: str,
    sort: str = "last_txn_time",
    sort_dir: str = "desc",
    hide_sold: int = 0,
    hide_small: int = 0,
) -> ApiResponse:
    params = {
        "wallet_address": wallet_address,
        "chain": chain,
        "sort": sort,
        "sort_dir": sort_dir,
        "hide_sold": hide_sold,
        "hide_small": hide_small,
    }
    response = requests.get(
        f"{BASE_URL}/v2/address/walletinfo/tokens",
        headers=make_headers(),
        params=params,
    )
    return handle_response(response)


def get_smart_wallets(
    chain: str, sort: str = "total_profit", sort_dir: str = "desc"
) -> ApiResponse:
    params = {"chain": chain, "sort": sort, "sort_dir": sort_dir}
    response = requests.get(
        f"{BASE_URL}/v2/address/smart_wallet/list",
        headers=make_headers(),
        params=params,
    )
    return handle_response(response)


def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)


def print_cu_warning(operation: str):
    cu_cost = CU_COSTS.get(operation, "unknown")
    print(f"[CU Cost: {cu_cost}]", file=sys.stderr)


def cmd_search(args):
    result = search_tokens(args.keyword, args.chain, args.limit)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("search")
    print(format_json(result.data))


def cmd_price(args):
    token_ids = [t.strip() for t in args.token_ids.split(",")]
    result = get_token_price(token_ids)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("price")
    print(format_json(result.data))


def cmd_trending(args):
    result = get_trending_tokens(args.chain, args.page, args.page_size)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("trending")
    print(format_json(result.data))


def cmd_token(args):
    result = get_token_detail(args.token_id)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("token")
    print(format_json(result.data))


def cmd_risk(args):
    result = get_token_risk(args.token_id)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("risk")
    print(format_json(result.data))


def cmd_holders(args):
    result = get_top_holders(args.token_id, args.limit)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("holders")
    print(format_json(result.data))


def cmd_klines(args):
    if args.pair_id:
        result = get_klines_by_pair(args.pair_id, args.interval, args.limit)
        print_cu_warning("klines_pair")
    else:
        result = get_klines_by_token(args.token_id, args.interval, args.limit)
        print_cu_warning("klines_token")
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print(format_json(result.data))


def cmd_pairs(args):
    result = get_pair_detail(args.pair_id)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("pairs")
    print(format_json(result.data))


def cmd_wallet_pnl(args):
    result = get_wallet_pnl(
        args.wallet, args.chain, args.token, args.from_time, args.to_time
    )
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("wallet_pnl")
    print(format_json(result.data))


def cmd_wallet_info(args):
    result = get_wallet_info(args.wallet, args.chain)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("wallet_info")
    print(format_json(result.data))


def cmd_wallet_tokens(args):
    result = get_wallet_tokens(
        args.wallet,
        args.chain,
        args.sort,
        args.sort_dir,
        args.hide_sold,
        args.hide_small,
    )
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("wallet_tokens")
    print(format_json(result.data))


def cmd_smart_wallets(args):
    result = get_smart_wallets(args.chain, args.sort, args.sort_dir)
    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)
    print_cu_warning("smart_wallet")
    print(format_json(result.data))


def main():
    parser = argparse.ArgumentParser(description="AVE Cloud Data REST API")
    parser.add_argument(
        "--api-key", default=API_KEY, help="AVE API key (or set AVE_API_KEY env)"
    )
    parser.add_argument(
        "--api-plan",
        default=API_PLAN,
        choices=["free", "normal", "pro"],
        help="API plan",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_search = subparsers.add_parser("search", help="Search tokens by keyword")
    p_search.add_argument("--keyword", required=True, help="Token symbol or address")
    p_search.add_argument("--chain", help="Chain name (bsc, solana, eth, base)")
    p_search.add_argument(
        "--limit", type=int, default=100, help="Number of results (max 300)"
    )

    p_price = subparsers.add_parser("price", help="Get batch token prices")
    p_price.add_argument(
        "--token-ids",
        required=True,
        help="Comma-separated token IDs (e.g. PEPE-bsc,TRUMP-bsc)",
    )

    p_trending = subparsers.add_parser("trending", help="Get trending tokens")
    p_trending.add_argument("--chain", required=True, help="Chain name")
    p_trending.add_argument("--page", type=int, default=0, help="Page number")
    p_trending.add_argument(
        "--page-size", type=int, default=50, help="Results per page (max 100)"
    )

    p_token = subparsers.add_parser("token", help="Get token details and top pairs")
    p_token.add_argument(
        "--token-id", required=True, help="Token ID (address-chain format)"
    )

    p_risk = subparsers.add_parser("risk", help="Get token risk information")
    p_risk.add_argument(
        "--token-id", required=True, help="Token ID (address-chain format)"
    )

    p_holders = subparsers.add_parser("holders", help="Get top 100 token holders")
    p_holders.add_argument(
        "--token-id", required=True, help="Token ID (address-chain format)"
    )
    p_holders.add_argument(
        "--limit", type=int, default=100, help="Number of holders (max 100)"
    )

    p_klines = subparsers.add_parser("klines", help="Get kline/candlestick data")
    p_klines.add_argument("--token-id", help="Token ID (use OR --pair-id)")
    p_klines.add_argument("--pair-id", help="Pair ID (use OR --token-id)")
    p_klines.add_argument(
        "--interval", default="1h", help="Interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)"
    )
    p_klines.add_argument("--limit", type=int, default=100, help="Number of klines")

    p_pairs = subparsers.add_parser("pairs", help="Get pair details")
    p_pairs.add_argument(
        "--pair-id", required=True, help="Pair ID (address-chain format)"
    )

    p_wallet_pnl = subparsers.add_parser(
        "wallet-pnl", help="Get wallet PnL for a token"
    )
    p_wallet_pnl.add_argument("--wallet", required=True, help="Wallet address")
    p_wallet_pnl.add_argument("--chain", required=True, help="Chain name")
    p_wallet_pnl.add_argument("--token", required=True, help="Token address")
    p_wallet_pnl.add_argument(
        "--from-time", type=int, help="Unix epoch seconds (earliest 15 days ago)"
    )
    p_wallet_pnl.add_argument("--to-time", type=int, help="Unix epoch seconds")

    p_wallet_info = subparsers.add_parser(
        "wallet-info", help="Get wallet info (all tokens on chain)"
    )
    p_wallet_info.add_argument("--wallet", required=True, help="Wallet address")
    p_wallet_info.add_argument("--chain", required=True, help="Chain name")

    p_wallet_tokens = subparsers.add_parser(
        "wallet-tokens", help="Get all tokens holding in wallet"
    )
    p_wallet_tokens.add_argument("--wallet", required=True, help="Wallet address")
    p_wallet_tokens.add_argument("--chain", required=True, help="Chain name")
    p_wallet_tokens.add_argument("--sort", default="last_txn_time", help="Sort field")
    p_wallet_tokens.add_argument(
        "--sort-dir", default="desc", help="Sort direction (desc/asc)"
    )
    p_wallet_tokens.add_argument(
        "--hide-sold", type=int, default=0, help="Hide sold tokens (0/1)"
    )
    p_wallet_tokens.add_argument(
        "--hide-small", type=int, default=0, help="Hide small balances (0/1)"
    )

    p_smart = subparsers.add_parser(
        "smart-wallets", help="Get smart wallet list (for copy trading)"
    )
    p_smart.add_argument("--chain", required=True, help="Chain name")
    p_smart.add_argument("--sort", default="total_profit", help="Sort field")
    p_smart.add_argument("--sort-dir", default="desc", help="Sort direction (desc/asc)")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required. Set AVE_API_KEY env or use --api-key")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "search": cmd_search,
        "price": cmd_price,
        "trending": cmd_trending,
        "token": cmd_token,
        "risk": cmd_risk,
        "holders": cmd_holders,
        "klines": cmd_klines,
        "pairs": cmd_pairs,
        "wallet-pnl": cmd_wallet_pnl,
        "wallet-info": cmd_wallet_info,
        "wallet-tokens": cmd_wallet_tokens,
        "smart-wallets": cmd_smart_wallets,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
