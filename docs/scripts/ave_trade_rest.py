#!/usr/bin/env python3
"""
AVE Cloud Trading REST API - Chain Wallet & Proxy Wallet Trading

Usage:
    # Environment setup
    export AVE_API_KEY=your_api_key_here
    export API_PLAN=free  # free for chain-wallet, normal/pro for proxy-wallet
    export AVE_SECRET_KEY=your_secret_key_here  # For proxy wallet HMAC signing

    # Chain Wallet (Self-custody) - Free tier OK
    python3 docs/scripts/ave_trade_rest.py chain-quote --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --in-amount 10000000 --swap-type buy
    python3 docs/scripts/ave_trade_rest.py chain-swap --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --in-amount 10000000 --swap-type buy

    # Proxy Wallet (Server-managed) - Requires normal/pro tier
    python3 docs/scripts/ave_trade_rest.py proxy-quote --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --in-amount 10000000 --swap-type buy
    python3 docs/scripts/ave_trade_rest.py proxy-market --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --in-amount 10000000 --swap-type buy
    python3 docs/scripts/ave_trade_rest.py proxy-limit --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c --in-amount 10000000 --swap-type buy --price 35.5
    python3 docs/scripts/ave_trade_rest.py proxy-orders --chain bsc
    python3 docs/scripts/ave_trade_rest.py proxy-cancel --chain bsc --order-id xxx

    # Wallet Management
    python3 docs/scripts/ave_trade_rest.py create-proxy-wallet --chain bsc
    python3 docs/scripts/ave_trade_rest.py list-proxy-wallets --chain bsc

Notes:
    - Chain Wallet: Requires API_PLAN=free or higher
    - Proxy Wallet: Requires API_PLAN=normal or pro
    - All amount fields use string format to avoid floating point precision issues
    - Proxy wallet uses HMAC-SHA256 signing with AVE_SECRET_KEY
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests

CHAIN_WALLET_URL = "https://bot-api.ave.ai"
PROXY_WALLET_URL = "https://bot-api.ave.ai"
API_KEY = os.getenv("AVE_API_KEY", "")
API_PLAN = os.getenv("API_PLAN", "free")
SECRET_KEY = os.getenv("AVE_SECRET_KEY", "")
EVM_PRIVATE_KEY = os.getenv("AVE_EVM_PRIVATE_KEY", "")
SOLANA_PRIVATE_KEY = os.getenv("AVE_SOLANA_PRIVATE_KEY", "")


@dataclass
class TradeResponse:
    status: int
    data: Optional[dict] = None
    error: Optional[str] = None
    business_code: Optional[int] = None


def make_headers(signed: bool = False):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    }
    return headers


def make_proxy_headers(timestamp: str, signature: str):
    return {
        "X-API-KEY": API_KEY,
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json",
    }


def generate_hmac_signature(timestamp: str, body: str = "") -> str:
    message = timestamp + body
    signature = hmac.new(
        SECRET_KEY.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return signature


def handle_response(response: requests.Response) -> TradeResponse:
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200 or data.get("status") == 200:
            return TradeResponse(status=200, data=data)
        else:
            return TradeResponse(
                status=data.get("code", response.status_code),
                data=data,
                error=data.get("msg", "Unknown error"),
                business_code=data.get("code"),
            )
    elif response.status_code == 401:
        return TradeResponse(
            status=401, error="Unauthorized - invalid or missing API key"
        )
    elif response.status_code == 403:
        return TradeResponse(
            status=403,
            error="Forbidden - API key expired, plan limits, or insufficient permissions",
        )
    elif response.status_code == 429:
        return TradeResponse(status=429, error="Rate limited - TPS exceeded")
    else:
        try:
            data = response.json()
            return TradeResponse(
                status=response.status_code,
                data=data,
                error=data.get("msg", response.text),
                business_code=data.get("code"),
            )
        except json.JSONDecodeError:
            return TradeResponse(status=response.status_code, error=response.text)


def chain_quote(
    chain: str,
    in_token: str,
    out_token: str,
    in_amount: str,
    swap_type: str,
    slippage: float = 0.5,
) -> TradeResponse:
    endpoint = f"{CHAIN_WALLET_URL}/v1/chain/quote"
    data = {
        "chain": chain,
        "in_token": in_token,
        "out_token": out_token,
        "in_amount": in_amount,
        "swap_type": swap_type,
        "slippage": slippage,
    }
    response = requests.post(endpoint, headers=make_headers(), json=data)
    return handle_response(response)


def chain_swap(
    chain: str,
    in_token: str,
    out_token: str,
    in_amount: str,
    swap_type: str,
    slippage: float = 0.5,
    recipient: Optional[str] = None,
) -> TradeResponse:
    endpoint = f"{CHAIN_WALLET_URL}/v1/chain/swap"
    data = {
        "chain": chain,
        "in_token": in_token,
        "out_token": out_token,
        "in_amount": in_amount,
        "swap_type": swap_type,
        "slippage": slippage,
    }
    if recipient:
        data["recipient"] = recipient
    response = requests.post(endpoint, headers=make_headers(), json=data)
    return handle_response(response)


def proxy_quote(
    chain: str,
    proxy_wallet: str,
    in_token: str,
    out_token: str,
    in_amount: str,
    swap_type: str,
) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    body = json.dumps(
        {
            "chain": chain,
            "proxy_wallet": proxy_wallet,
            "in_token": in_token,
            "out_token": out_token,
            "in_amount": in_amount,
            "swap_type": swap_type,
        },
        separators=(",", ":"),
    )
    signature = generate_hmac_signature(timestamp, body)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/quote"
    response = requests.post(endpoint, headers=headers, json=json.loads(body))
    return handle_response(response)


def proxy_market_order(
    chain: str,
    proxy_wallet: str,
    in_token: str,
    out_token: str,
    in_amount: str,
    swap_type: str,
    tp_price: Optional[str] = None,
    sl_price: Optional[str] = None,
    trailing_stop: Optional[dict] = None,
) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    data = {
        "chain": chain,
        "proxy_wallet": proxy_wallet,
        "in_token": in_token,
        "out_token": out_token,
        "in_amount": in_amount,
        "swap_type": swap_type,
        "order_type": "market",
    }
    if tp_price:
        data["tp_price"] = tp_price
    if sl_price:
        data["sl_price"] = sl_price
    if trailing_stop:
        data["trailing_stop"] = trailing_stop
    body = json.dumps(data, separators=(",", ":"))
    signature = generate_hmac_signature(timestamp, body)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/market_order"
    response = requests.post(endpoint, headers=headers, json=data)
    return handle_response(response)


def proxy_limit_order(
    chain: str,
    proxy_wallet: str,
    in_token: str,
    out_token: str,
    in_amount: str,
    swap_type: str,
    price: str,
    tp_price: Optional[str] = None,
    sl_price: Optional[str] = None,
) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    data = {
        "chain": chain,
        "proxy_wallet": proxy_wallet,
        "in_token": in_token,
        "out_token": out_token,
        "in_amount": in_amount,
        "swap_type": swap_type,
        "price": price,
        "order_type": "limit",
    }
    if tp_price:
        data["tp_price"] = tp_price
    if sl_price:
        data["sl_price"] = sl_price
    body = json.dumps(data, separators=(",", ":"))
    signature = generate_hmac_signature(timestamp, body)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/limit_order"
    response = requests.post(endpoint, headers=headers, json=data)
    return handle_response(response)


def proxy_cancel_order(chain: str, order_id: str) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    data = {"chain": chain, "order_id": order_id}
    body = json.dumps(data, separators=(",", ":"))
    signature = generate_hmac_signature(timestamp, body)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/cancel_order"
    response = requests.post(endpoint, headers=headers, json=data)
    return handle_response(response)


def proxy_get_orders(
    chain: str, proxy_wallet: str, order_type: Optional[str] = None
) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    params = {"chain": chain, "proxy_wallet": proxy_wallet}
    if order_type:
        params["order_type"] = order_type
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = generate_hmac_signature(timestamp, query_string)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/orders"
    response = requests.get(endpoint, headers=headers, params=params)
    return handle_response(response)


def proxy_get_order_history(chain: str, proxy_wallet: str) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    params = {"chain": chain, "proxy_wallet": proxy_wallet}
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = generate_hmac_signature(timestamp, query_string)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/order_history"
    response = requests.get(endpoint, headers=headers, params=params)
    return handle_response(response)


def create_proxy_wallet(chain: str) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    data = {"chain": chain}
    body = json.dumps(data, separators=(",", ":"))
    signature = generate_hmac_signature(timestamp, body)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/create_proxy_wallet"
    response = requests.post(endpoint, headers=headers, json=data)
    return handle_response(response)


def list_proxy_wallets(chain: str) -> TradeResponse:
    timestamp = str(int(time.time() * 1000))
    params = {"chain": chain}
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = generate_hmac_signature(timestamp, query_string)
    headers = make_proxy_headers(timestamp, signature)
    endpoint = f"{PROXY_WALLET_URL}/v1/proxy_wallets"
    response = requests.get(endpoint, headers=headers, params=params)
    return handle_response(response)


def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)


def print_trade_response(result: TradeResponse, success_msg: str = "Success"):
    if result.error:
        print(f"Error ({result.business_code or result.status}): {result.error}")
        if result.data:
            print(format_json(result.data))
        sys.exit(1)
    else:
        print(f"{success_msg}")
        if result.data:
            print(format_json(result.data))


def cmd_chain_quote(args):
    result = chain_quote(
        chain=args.chain,
        in_token=args.in_token,
        out_token=args.out_token,
        in_amount=args.in_amount,
        swap_type=args.swap_type,
        slippage=args.slippage,
    )
    print_trade_response(result, "Quote retrieved (dry-run - no actual trade)")


def cmd_chain_swap(args):
    result = chain_swap(
        chain=args.chain,
        in_token=args.in_token,
        out_token=args.out_token,
        in_amount=args.in_amount,
        swap_type=args.swap_type,
        slippage=args.slippage,
        recipient=args.recipient,
    )
    print_trade_response(result, "Swap executed!")


def cmd_proxy_quote(args):
    result = proxy_quote(
        chain=args.chain,
        proxy_wallet=args.proxy_wallet,
        in_token=args.in_token,
        out_token=args.out_token,
        in_amount=args.in_amount,
        swap_type=args.swap_type,
    )
    print_trade_response(result, "Quote retrieved (dry-run - no actual trade)")


def cmd_proxy_market(args):
    result = proxy_market_order(
        chain=args.chain,
        proxy_wallet=args.proxy_wallet,
        in_token=args.in_token,
        out_token=args.out_token,
        in_amount=args.in_amount,
        swap_type=args.swap_type,
        tp_price=args.tp_price,
        sl_price=args.sl_price,
    )
    print_trade_response(result, "Market order submitted!")


def cmd_proxy_limit(args):
    result = proxy_limit_order(
        chain=args.chain,
        proxy_wallet=args.proxy_wallet,
        in_token=args.in_token,
        out_token=args.out_token,
        in_amount=args.in_amount,
        swap_type=args.swap_type,
        price=args.price,
        tp_price=args.tp_price,
        sl_price=args.sl_price,
    )
    print_trade_response(result, "Limit order submitted!")


def cmd_proxy_cancel(args):
    result = proxy_cancel_order(args.chain, args.order_id)
    print_trade_response(result, "Order cancelled!")


def cmd_proxy_orders(args):
    result = proxy_get_orders(args.chain, args.proxy_wallet, args.order_type)
    print_trade_response(result)


def cmd_proxy_history(args):
    result = proxy_get_order_history(args.chain, args.proxy_wallet)
    print_trade_response(result)


def cmd_create_proxy_wallet(args):
    result = create_proxy_wallet(args.chain)
    print_trade_response(result, "Proxy wallet created!")


def cmd_list_proxy_wallets(args):
    result = list_proxy_wallets(args.chain)
    print_trade_response(result)


def main():
    parser = argparse.ArgumentParser(description="AVE Cloud Trading REST API")
    parser.add_argument(
        "--api-key", default=API_KEY, help="AVE API key (or set AVE_API_KEY env)"
    )
    parser.add_argument(
        "--api-plan", default=API_PLAN, help="API plan (or set API_PLAN env)"
    )
    parser.add_argument(
        "--secret-key",
        default=SECRET_KEY,
        help="AVE SECRET_KEY for HMAC signing (or set AVE_SECRET_KEY env)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_cquote = subparsers.add_parser(
        "chain-quote", help="Chain wallet - get swap quote (dry-run)"
    )
    p_cquote.add_argument(
        "--chain", required=True, help="Chain name (bsc, solana, eth, base)"
    )
    p_cquote.add_argument("--in-token", required=True, help="Input token address")
    p_cquote.add_argument("--out-token", required=True, help="Output token address")
    p_cquote.add_argument(
        "--in-amount", required=True, help="Input amount (use string format)"
    )
    p_cquote.add_argument("--swap-type", required=True, help="Swap type (buy or sell)")
    p_cquote.add_argument(
        "--slippage", type=float, default=0.5, help="Slippage tolerance (default: 0.5)"
    )

    p_cswap = subparsers.add_parser("chain-swap", help="Chain wallet - execute swap")
    p_cswap.add_argument("--chain", required=True, help="Chain name")
    p_cswap.add_argument("--in-token", required=True, help="Input token address")
    p_cswap.add_argument("--out-token", required=True, help="Output token address")
    p_cswap.add_argument("--in-amount", required=True, help="Input amount")
    p_cswap.add_argument("--swap-type", required=True, help="Swap type (buy or sell)")
    p_cswap.add_argument(
        "--slippage", type=float, default=0.5, help="Slippage tolerance"
    )
    p_cswap.add_argument("--recipient", help="Optional recipient address")

    p_pquote = subparsers.add_parser(
        "proxy-quote", help="Proxy wallet - get swap quote (dry-run)"
    )
    p_pquote.add_argument("--chain", required=True, help="Chain name")
    p_pquote.add_argument("--proxy-wallet", required=True, help="Proxy wallet address")
    p_pquote.add_argument("--in-token", required=True, help="Input token address")
    p_pquote.add_argument("--out-token", required=True, help="Output token address")
    p_pquote.add_argument("--in-amount", required=True, help="Input amount")
    p_pquote.add_argument("--swap-type", required=True, help="Swap type (buy or sell)")

    p_pmarket = subparsers.add_parser(
        "proxy-market", help="Proxy wallet - submit market order"
    )
    p_pmarket.add_argument("--chain", required=True, help="Chain name")
    p_pmarket.add_argument("--proxy-wallet", required=True, help="Proxy wallet address")
    p_pmarket.add_argument("--in-token", required=True, help="Input token address")
    p_pmarket.add_argument("--out-token", required=True, help="Output token address")
    p_pmarket.add_argument("--in-amount", required=True, help="Input amount")
    p_pmarket.add_argument("--swap-type", required=True, help="Swap type (buy or sell)")
    p_pmarket.add_argument("--tp-price", help="Take-profit price")
    p_pmarket.add_argument("--sl-price", help="Stop-loss price")

    p_plimit = subparsers.add_parser(
        "proxy-limit", help="Proxy wallet - submit limit order"
    )
    p_plimit.add_argument("--chain", required=True, help="Chain name")
    p_plimit.add_argument("--proxy-wallet", required=True, help="Proxy wallet address")
    p_plimit.add_argument("--in-token", required=True, help="Input token address")
    p_plimit.add_argument("--out-token", required=True, help="Output token address")
    p_plimit.add_argument("--in-amount", required=True, help="Input amount")
    p_plimit.add_argument("--swap-type", required=True, help="Swap type (buy or sell)")
    p_plimit.add_argument("--price", required=True, help="Limit price")
    p_plimit.add_argument("--tp-price", help="Take-profit price")
    p_plimit.add_argument("--sl-price", help="Stop-loss price")

    p_cancel = subparsers.add_parser("proxy-cancel", help="Proxy wallet - cancel order")
    p_cancel.add_argument("--chain", required=True, help="Chain name")
    p_cancel.add_argument("--order-id", required=True, help="Order ID to cancel")

    p_orders = subparsers.add_parser(
        "proxy-orders", help="Proxy wallet - get open orders"
    )
    p_orders.add_argument("--chain", required=True, help="Chain name")
    p_orders.add_argument("--proxy-wallet", required=True, help="Proxy wallet address")
    p_orders.add_argument("--order-type", help="Filter by order type (market/limit)")

    p_history = subparsers.add_parser(
        "proxy-history", help="Proxy wallet - get order history"
    )
    p_history.add_argument("--chain", required=True, help="Chain name")
    p_history.add_argument("--proxy-wallet", required=True, help="Proxy wallet address")

    p_create = subparsers.add_parser(
        "create-proxy-wallet", help="Create a new proxy wallet"
    )
    p_create.add_argument("--chain", required=True, help="Chain name")

    p_list = subparsers.add_parser("list-proxy-wallets", help="List proxy wallets")
    p_list.add_argument("--chain", required=True, help="Chain name")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required. Set AVE_API_KEY env or use --api-key")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "chain-quote": cmd_chain_quote,
        "chain-swap": cmd_chain_swap,
        "proxy-quote": cmd_proxy_quote,
        "proxy-market": cmd_proxy_market,
        "proxy-limit": cmd_proxy_limit,
        "proxy-cancel": cmd_proxy_cancel,
        "proxy-orders": cmd_proxy_orders,
        "proxy-history": cmd_proxy_history,
        "create-proxy-wallet": cmd_create_proxy_wallet,
        "list-proxy-wallets": cmd_list_proxy_wallets,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
