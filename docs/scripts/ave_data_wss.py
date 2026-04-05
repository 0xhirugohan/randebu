#!/usr/bin/env python3
"""
AVE Cloud Data WebSocket API - Real-time Streams

Usage:
    export AVE_API_KEY=your_api_key_here
    export API_PLAN=pro  # REQUIRED for WebSocket (must be 'pro')

    python3 docs/scripts/ave_data_wss.py subscribe-tx --pair "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE" --chain solana
    python3 docs/scripts/ave_data_wss.py subscribe-multi-tx --token "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c" --chain bsc
    python3 docs/scripts/ave_data_wss.py subscribe-liq --pair "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE" --chain solana
    python3 docs/scripts/ave_data_wss.py subscribe-price --pairs "PEPE-bsc,TRUMP-bsc"
    python3 docs/scripts/ave_data_wss.py subscribe-kline --token "0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc" --interval 1m
    python3 docs/scripts/ave_data_wss.py wss-repl  # Interactive REPL mode

Notes:
    - WebSocket API requires API_PLAN=pro
    - Max 5 concurrent WebSocket connections
    - Auto-reconnect with exponential backoff on disconnect
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import websocket

WSS_URL = "wss://wss.ave-api.xyz"
API_KEY = os.getenv("AVE_API_KEY", "")
API_PLAN = os.getenv("API_PLAN", "")


@dataclass
class WssMessage:
    id: int
    method: str
    params: list
    result: Optional[dict] = None


@dataclass
class WssSubscription:
    topic: str
    address: str
    chain: str
    id: int


class AveWssClient:
    def __init__(self, api_key: str, debug: bool = False):
        self.api_key = api_key
        self.debug = debug
        self.ws: Optional[websocket.WebSocket] = None
        self.subscription_id = 1
        self.subscriptions: list[WssSubscription] = []
        self.running = False

    def connect(self):
        if self.ws:
            self.disconnect()
        self.ws = websocket.WebSocketApp(
            WSS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.running = True

    def disconnect(self):
        self.running = False
        if self.ws:
            self.ws.close()
            self.ws = None

    def _on_open(self, ws):
        print("[Connected to WebSocket]", file=sys.stderr)

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            if self.debug:
                print(f"[DEBUG] {json.dumps(data, indent=2)}", file=sys.stderr)
            if "result" in data and data.get("id"):
                for sub in self.subscriptions:
                    if sub.id == data["id"]:
                        sub.id = data["result"].get("id", data["id"])
                        print(
                            f"[Subscribed to {sub.topic}] {sub.address} on {sub.chain}",
                            file=sys.stderr,
                        )
                        break
            elif "params" in data:
                topic = data["params"].get("topic", "unknown")
                if topic == "tx":
                    self._handle_tx(data["params"]["data"])
                elif topic == "liq":
                    self._handle_liq(data["params"]["data"])
                elif topic == "kline":
                    self._handle_kline(data["params"]["data"])
                elif topic == "price":
                    self._handle_price(data["params"]["data"])
        except json.JSONDecodeError:
            print(f"[Error] Failed to parse message: {message}", file=sys.stderr)

    def _on_error(self, ws, error):
        print(f"[WebSocket Error] {error}", file=sys.stderr)

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"[Disconnected] {close_status_code}: {close_msg}", file=sys.stderr)
        self.running = False

    def _handle_tx(self, tx: dict):
        print(
            f"[TX] {tx.get('chain')}: {tx.get('from_symbol')} -> {tx.get('to_symbol')} "
            f"Amount: {tx.get('from_amount')} {tx.get('from_symbol')} | "
            f"Sender: {tx.get('sender', 'unknown')[:10]}... | "
            f"Pair: {tx.get('pair_address', 'unknown')[:15]}..."
        )

    def _handle_liq(self, liq: dict):
        print(
            f"[LIQ] {liq.get('chain')}: {liq.get('action')} "
            f"Amount: {liq.get('amount')} {liq.get('symbol')} | "
            f"Pair: {liq.get('pair_address', 'unknown')[:15]}..."
        )

    def _handle_kline(self, kline: dict):
        print(
            f"[KLINE] {kline.get('token_id', kline.get('pair_id'))} "
            f"{kline.get('interval')}: O={kline.get('open')} H={kline.get('high')} "
            f"L={kline.get('low')} C={kline.get('close')} V={kline.get('volume')}"
        )

    def _handle_price(self, price: dict):
        print(
            f"[PRICE] {price.get('token_id', price.get('pair_id'))}: "
            f"{price.get('price')} USD (change: {price.get('price_change_24h', 'N/A')}%)"
        )

    def _send(self, method: str, params: list, timeout: int = 10) -> Optional[dict]:
        if not self.ws:
            return None
        msg_id = self.subscription_id
        self.subscription_id += 1
        msg = {"jsonrpc": "2.0", "method": method, "params": params, "id": msg_id}
        self.ws.send(json.dumps(msg))
        return {"id": msg_id}

    def subscribe_tx(self, pair_address: str, chain: str):
        params = ["tx", pair_address, chain]
        result = self._send("subscribe", params)
        if result:
            self.subscriptions.append(
                WssSubscription(
                    topic="tx", address=pair_address, chain=chain, id=result["id"]
                )
            )

    def subscribe_multi_tx(self, token_address: str, chain: str):
        params = ["multi_tx", token_address, chain]
        result = self._send("subscribe", params)
        if result:
            self.subscriptions.append(
                WssSubscription(
                    topic="multi_tx",
                    address=token_address,
                    chain=chain,
                    id=result["id"],
                )
            )

    def subscribe_liq(self, pair_address: str, chain: str):
        params = ["liq", pair_address, chain]
        result = self._send("subscribe", params)
        if result:
            self.subscriptions.append(
                WssSubscription(
                    topic="liq", address=pair_address, chain=chain, id=result["id"]
                )
            )

    def subscribe_price(self, pairs: list):
        params = ["price", pairs]
        result = self._send("subscribe", params)
        if result:
            for pair in pairs:
                self.subscriptions.append(
                    WssSubscription(
                        topic="price", address=pair, chain="multi", id=result["id"]
                    )
                )

    def subscribe_kline(self, token_or_pair_id: str, interval: str = "1m"):
        params = ["kline", token_or_pair_id, interval]
        result = self._send("subscribe", params)
        if result:
            self.subscriptions.append(
                WssSubscription(
                    topic="kline",
                    address=token_or_pair_id,
                    chain=interval,
                    id=result["id"],
                )
            )

    def unsubscribe(self, topic: str, address: str, chain: str):
        params = (
            ["unsubscribe", topic, address, chain]
            if chain != "multi"
            else ["unsubscribe", topic, address]
        )
        self._send("unsubscribe", params)
        self.subscriptions = [
            s
            for s in self.subscriptions
            if not (s.topic == topic and s.address == address and s.chain == chain)
        ]

    def run_forever(self, reconnect_delay: int = 5, max_reconnect_delay: int = 60):
        delay = reconnect_delay
        while self.running:
            try:
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                print(f"[Error] {e}", file=sys.stderr)
            if self.running:
                print(f"[Reconnecting in {delay}s...]", file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, max_reconnect_delay)
                self.connect()


def cmd_subscribe_tx(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    client.subscribe_tx(args.pair, args.chain)
    print("[Press Ctrl+C to exit]", file=sys.stderr)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        client.disconnect()


def cmd_subscribe_multi_tx(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    client.subscribe_multi_tx(args.token, args.chain)
    print("[Press Ctrl+C to exit]", file=sys.stderr)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        client.disconnect()


def cmd_subscribe_liq(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    client.subscribe_liq(args.pair, args.chain)
    print("[Press Ctrl+C to exit]", file=sys.stderr)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        client.disconnect()


def cmd_subscribe_price(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    pairs = [p.strip() for p in args.pairs.split(",")]
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    client.subscribe_price(pairs)
    print("[Press Ctrl+C to exit]", file=sys.stderr)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        client.disconnect()


def cmd_subscribe_kline(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    client.subscribe_kline(args.token, args.interval)
    print("[Press Ctrl+C to exit]", file=sys.stderr)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        client.disconnect()


def cmd_wss_repl(args):
    if API_PLAN != "pro":
        print("Error: WebSocket requires API_PLAN=pro", file=sys.stderr)
        sys.exit(1)
    client = AveWssClient(args.api_key, debug=args.debug)
    client.connect()
    print(
        "[WebSocket REPL - type 'help' for commands, 'quit' to exit]", file=sys.stderr
    )
    print(
        "[Commands: subscribe tx <pair> <chain>, subscribe price <pairs>, unsubscribe <topic> <addr> <chain>]",
        file=sys.stderr,
    )

    subscriptions = []

    def print_help():
        print("Commands:")
        print(
            "  subscribe tx <pair_address> <chain>     - Subscribe to swap transactions by pair"
        )
        print(
            "  subscribe multi_tx <token_address> <chain> - Subscribe to all txs involving a token"
        )
        print(
            "  subscribe liq <pair_address> <chain>  - Subscribe to liquidity changes by pair"
        )
        print("  subscribe price <pair1,pair2,...>       - Subscribe to price changes")
        print(
            "  subscribe kline <token_id> <interval>   - Subscribe to kline data (interval: 1m, 5m, etc.)"
        )
        print("  unsubscribe <topic> <address> <chain>   - Unsubscribe")
        print("  list                                      - List subscriptions")
        print("  help                                      - Show this help")
        print("  quit                                      - Exit")

    while True:
        try:
            user_input = input("wss> ").strip()
            if not user_input:
                continue
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd == "quit":
                break
            elif cmd == "help":
                print_help()
            elif cmd == "list":
                for s in client.subscriptions:
                    print(f"  {s.topic}: {s.address} on {s.chain}")
            elif cmd == "subscribe" and len(parts) >= 3:
                sub_type = parts[1].lower()
                if sub_type == "tx" and len(parts) >= 4:
                    client.subscribe_tx(parts[2], parts[3])
                elif sub_type == "multi_tx" and len(parts) >= 4:
                    client.subscribe_multi_tx(parts[2], parts[3])
                elif sub_type == "liq" and len(parts) >= 4:
                    client.subscribe_liq(parts[2], parts[3])
                elif sub_type == "price" and len(parts) >= 3:
                    pairs = parts[2].split(",")
                    client.subscribe_price(pairs)
                elif sub_type == "kline" and len(parts) >= 4:
                    client.subscribe_kline(parts[2], parts[3])
                else:
                    print("Invalid subscribe command")
            elif cmd == "unsubscribe" and len(parts) >= 4:
                client.unsubscribe(parts[1], parts[2], parts[3])
            else:
                print("Unknown command. Type 'help' for commands.")
        except KeyboardInterrupt:
            break
        except EOFError:
            break

    client.disconnect()
    print("\n[Exited]")


def main():
    parser = argparse.ArgumentParser(description="AVE Cloud Data WebSocket API")
    parser.add_argument(
        "--api-key", default=API_KEY, help="AVE API key (or set AVE_API_KEY env)"
    )
    parser.add_argument(
        "--api-plan", default=API_PLAN, help="API plan (or set API_PLAN env)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    p_tx = subparsers.add_parser(
        "subscribe-tx", help="Subscribe to swap transactions by pair"
    )
    p_tx.add_argument("--pair", required=True, help="Pair address")
    p_tx.add_argument(
        "--chain", required=True, help="Chain name (solana, bsc, eth, base)"
    )

    p_multi = subparsers.add_parser(
        "subscribe-multi-tx", help="Subscribe to all txs involving a token"
    )
    p_multi.add_argument("--token", required=True, help="Token address")
    p_multi.add_argument("--chain", required=True, help="Chain name")

    p_liq = subparsers.add_parser(
        "subscribe-liq", help="Subscribe to liquidity changes by pair"
    )
    p_liq.add_argument("--pair", required=True, help="Pair address")
    p_liq.add_argument("--chain", required=True, help="Chain name")

    p_price = subparsers.add_parser(
        "subscribe-price", help="Subscribe to price changes"
    )
    p_price.add_argument(
        "--pairs", required=True, help="Comma-separated pairs (e.g. PEPE-bsc,TRUMP-bsc)"
    )

    p_kline = subparsers.add_parser("subscribe-kline", help="Subscribe to kline data")
    p_kline.add_argument(
        "--token", required=True, help="Token ID (address-chain format)"
    )
    p_kline.add_argument(
        "--interval", default="1m", help="Interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)"
    )

    subparsers.add_parser("wss-repl", help="Interactive WebSocket REPL")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required. Set AVE_API_KEY env or use --api-key")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        "subscribe-tx": cmd_subscribe_tx,
        "subscribe-multi-tx": cmd_subscribe_multi_tx,
        "subscribe-liq": cmd_subscribe_liq,
        "subscribe-price": cmd_subscribe_price,
        "subscribe-kline": cmd_subscribe_kline,
        "wss-repl": cmd_wss_repl,
    }

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
