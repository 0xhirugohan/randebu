# AVE Claw Hackathon 2026 - Research Report

## 1. What is the AVE Claw Hackathon?

**Theme/Purpose:**
The AVE Claw Hackathon is a developer competition focused on building trading bots, analytics tools, and real-time monitoring applications using the AVE Cloud platform. Based on the hackathon site at `https://clawhackathon.aveai.trade/` (Vite-built), it appears to be centered around crypto/DEX trading automation and data analysis.

**Note:** The hackathon site is a client-side rendered SPA, so specific dates and prize amounts could not be extracted. You should visit the site directly or contact the organizers at `https://t.me/ave_ai_cloud` for official timeline details.

---

## 2. What is AVE Cloud Platform?

### Core Services

**A. Data API** (`https://data.ave-api.xyz` / `https://prod.ave-api.com`)
- Real-time and historical on-chain data
- Token pricing, transaction history, wallet info, Kline/candlestick data
- WebSocket streams for live price changes and transactions

**B. Trading API** (`https://bot-api.ave.ai`)
- **Chain Wallet API**: Self-custody trading where users control their private keys
- **Proxy Wallet (Bot Wallet) API**: Server-managed wallets for automated trading with TP/SL support
- Support for market orders, limit orders, take-profit, stop-loss, and trailing stop

**C. Authentication**
- API Key-based: `X-API-KEY` header required
- Proxy wallet uses HMAC signing with `AVE_SECRET_KEY`

### Supported Blockchains

| Chain | Data API | Chain-Wallet Trading | Proxy-Wallet Trading |
|-------|----------|---------------------|---------------------|
| BSC   | Yes      | Yes                 | Yes                 |
| Solana| Yes      | Yes                 | Yes                 |
| ETH   | Yes      | Yes                 | Yes                 |
| Base  | Yes      | Yes                 | Yes                 |

### Pricing Tiers

| Feature           | Free  | Level 1 | Level 2 | Enterprise |
|-------------------|-------|---------|---------|------------|
| Chain Wallet API  | Yes   | Yes     | Yes     | Yes        |
| Proxy Wallet API  | No    | Yes     | Yes     | Yes        |
| Write Req Rate    | 1 TPS | 5 TPS   | 20 TPS  | Unlimited  |
| Max Proxy Wallets | -     | 500     | 5000    | Unlimited  |

**Trading Fees:**
- Proxy Wallet API: 0.8% fee, 25% rebate
- Chain Wallet API: 0.6% fee, supports custom referral fees up to 10%

---

## 3. What Can Participants Build?

### Trading Bots
- **Market orders**: Buy/sell at current market prices
- **Limit orders**: Set specific buy/sell prices
- **Take-Profit/Stop-Loss**: Automated exit strategies
- **Trailing Stop**: Dynamic price-following exits
- **Multi-chain support**: BSC, Solana, ETH, Base DEXes

### Analytics Tools
- Token search and price lookup
- Transaction history analysis (swap txs, liquidity txs)
- Wallet PnL tracking
- Top 100 token holders analysis
- Risk/honeypot detection

### Real-Time Monitors
- WebSocket price change streams
- Live transaction feeds by pair or token
- Kline/candlestick data (intervals: 1m, 5m, 15m, 30m, 1h, etc.)
- Portfolio tracking

### Token Research Tools
- Trending tokens by chain
- Platform-based token filtering (meme, pump_in_hot, pump_out_hot, etc.)
- Token risk assessment
- Pair liquidity analysis

---

## 4. API Endpoints Summary

### Data REST API

| Endpoint | Description | Cost |
|----------|-------------|------|
| `GET /v2/tokens` | Search tokens by keyword | 5 CU |
| `GET /v2/tokens/{token-id}` | Token details + top 5 pairs | 5 CU |
| `POST /v2/tokens/price` | Batch token prices (up to 200) | 100 CU |
| `GET /v2/tokens/trending` | Trending tokens | 5 CU |
| `GET /v2/tokens/top100/{token-id}` | Top 100 token holders | 10 CU |
| `GET /v2/contracts/{token-id}` | Token risk info | 10 CU |
| `GET /v2/txs/swap/{pair-id}` | Swap tx history | 50 CU |
| `GET /v2/txs/liq/{pair-id}` | Liquidity change txs | 50 CU |
| `GET /v2/address/tx` | Wallet transaction history | 100 CU |
| `GET /v2/address/pnl` | Wallet PnL data | 5 CU |
| `GET /v2/address/walletinfo` | Wallet info (all tokens) | 5 CU |
| `GET /v2/address/walletinfo/tokens` | All tokens in wallet | 10 CU |
| `GET /v2/address/smart_wallet/list` | Smart wallet list (copy trading) | 5 CU |
| `GET /v2/klines/token/{token-id}` | Kline data by token | 10 CU |
| `GET /v2/klines/pair/{pair-id}` | Kline data by pair | 10 CU |
| `GET /v2/pairs/{pair-id}` | Pair details | 5 CU |
| `GET /v2/tokens/platform` | Tokens by launch platform | 10 CU |
| `GET /v2/tokens/main` | Main tokens on chain | 5 CU |

### WebSocket API (`wss://wss.ave-api.xyz`)

| Topic | Description |
|-------|-------------|
| `tx` | Real-time swap transactions by pair |
| `liq` | Liquidity changes by pair |
| `multi_tx` | All txs involving a token |
| `kline` | Real-time candlestick data |
| `price` | Price changes for multiple tokens/pairs |

### Trading API (Proxy Wallet)

- Market/Limit orders
- TP/SL/Trailing stop automation
- WebSocket order status updates (`wss://bot-api.ave.ai/thirdws?ave_access_key=...`)

---

## 5. Key Resources and Links

| Resource | URL |
|----------|-----|
| Hackathon Site | https://clawhackathon.aveai.trade/ |
| Registration/API Key | https://cloud.ave.ai/register |
| Bot API Docs | https://docs-bot-api.ave.ai/ |
| Data API Docs | https://ave-cloud.gitbook.io/data-api |
| GitHub (Skills) | https://github.com/AveCloud/ave-cloud-skill |
| Telegram Support | https://t.me/ave_ai_cloud |

### Python Skill Scripts

The `docs/scripts/` directory contains runnable Python scripts:

| Script | Purpose |
|--------|---------|
| `ave_data_rest.py` | Token search, prices, klines, holders, risk |
| `ave_data_wss.py` | Real-time WebSocket streams |
| `ave_trade_rest.py` | Chain & proxy wallet trading |

### Token Links Format
View tokens on AVE Pro: `https://pro.ave.ai/token/<token_address>-<chain>`
Example: `https://pro.ave.ai/token/0x1234...abcd-bsc`

---

## 6. Decision Guidance for Participants

**What to Build:**

1. **Trading Bot** - Use proxy wallet API for automated trading with TP/SL
2. **Analytics Dashboard** - Combine Data API + Trading API for comprehensive analysis
3. **Copy Trading System** - Track smart wallets via `/v2/address/smart_wallet/list` and mirror trades
4. **Token Scanner** - Use trending/risk APIs to find opportunities
5. **Real-time Alert System** - WebSocket streams for price/tx monitoring

**Required Tech:**
- Python (skill scripts provided)
- API integration via REST/WebSocket
- Multi-chain support (BSC/Solana/ETH/Base)

---

## 7. Extended API Documentation

### 7.1 Token ID Format

All token references use the format `<token_address>-<chain>`:

```
PEPE-bsc
0x6982508145454Ce325dDbE47a25d4ec3d2311933-bsc
6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN-solana
```

**Chain names:** `bsc`, `solana`, `eth`, `base`

### 7.2 Complete Request/Response Examples

#### Token Search

**Request:**
```bash
curl "https://prod.ave-api.com/v2/tokens?keyword=PEPE&chain=bsc&limit=10" \
  -H "X-API-KEY: your_api_key"
```

**Response:**
```json
{
  "status": 200,
  "msg": "success",
  "data": [
    {
      "name": "Pepe",
      "symbol": "PEPE",
      "chain": "bsc",
      "current_price_usd": "0.00001234",
      "market_cap": "1234567890",
      "tx_volume_u_24h": "50000000",
      "main_pair_tvl": "1000000",
      "logo_url": "https://..."
    }
  ]
}
```

#### Batch Token Price

**Request:**
```bash
curl -X POST "https://prod.ave-api.com/v2/tokens/price" \
  -H "X-API-KEY: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"token_ids": ["PEPE-bsc", "TRUMP-bsc", "0x55d398326f99059fF775485246999027B3197955-bsc"]}'
```

**Response:**
```json
{
  "status": 200,
  "msg": "success",
  "data": {
    "PEPE-bsc": {
      "price": "0.00001234",
      "price_24h_change": "5.67",
      "updated_at": 1756888200
    },
    "TRUMP-bsc": {
      "price": "4.56",
      "price_24h_change": "-2.34",
      "updated_at": 1756888200
    }
  }
}
```

#### Wallet PnL

**Request:**
```bash
curl "https://prod.ave-api.com/v2/address/pnl?wallet_address=0xd9c500dff816a1da21a48a732d3498bf09dc9aeb&chain=bsc&token_address=0x55d398326f99059fF775485246999027B3197955" \
  -H "X-API-KEY: your_api_key"
```

**Response:**
```json
{
  "status": 200,
  "msg": "success",
  "data": {
    "wallet_address": "0xd9c500dff816a1da21a48a732d3498bf09dc9aeb",
    "token_address": "0x55d398326f99059fF775485246999027B3197955",
    "total_profit": "123.45",
    "total_profit_rate": "0.15",
    "buy_amount": "10000",
    "sell_amount": "10123.45",
    "avg_buy_price": "1.0",
    "avg_sell_price": "1.0123"
  }
}
```

### 7.3 Error Codes

#### HTTP Status Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid parameters, malformed JSON |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | API key expired, plan limits reached |
| 429 | Rate Limited | TPS exceeded |
| 500 | Server Error | Internal error, try again later |

#### Business Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 1001 | General failure |
| 1011 | System error |
| 1021 | Signature verification failed |
| 1022 | API frozen, contact support |
| 1023 | Request expired (timestamp out of range) |
| 2001 | Request parameter error |
| 3001 | Transaction send failed |
| 3011 | Transaction record not found |
| 3021 | Order cancellation failed |
| 3101 | User does not exist |
| 3102 | User assets don't belong to this organization |
| 3103 | User asset account disabled |
| 3104 | No proxy wallet permission, upgrade plan required |

### 7.4 CU (Compute Unit) Cost Optimization

Each API call costs CU. Strategies to minimize usage:

| Strategy | Example |
|----------|---------|
| Use `/v2/tokens/price` batch (100 CU) vs individual calls | Batch up to 200 tokens in one call |
| Cache trending/risk data | Risk info changes slowly, cache for 5-10 min |
| Use filters | Add `tvl_min`, `tx_24h_volume_min` to price queries |
| Prefer search over detailed token | `/v2/tokens` (5 CU) vs `/v2/tokens/{id}` (5 CU) |

### 7.5 Pagination

Endpoints that return lists support pagination:

| Parameter | For |
|-----------|-----|
| `page_size` | Results per page (max varies) |
| `current_page` | Page number (0-indexed) |
| `last_id` | Cursor for next page (from previous response) |

Example pagination flow:
```python
# Get first page
result = get_trending_tokens(chain="bsc", page=0, page_size=50)
next_page = result["next_page"]  # Use this for next request

# For wallet PnL with cursor
result = get_wallet_pnl(wallet, chain, token)
if result.get("has_more"):
    next_result = get_wallet_pnl(wallet, chain, token, last_id=result["last_id"])
```

---

## 8. Working Code Examples

### 8.1 Setup

```bash
cd /home/shoko/repositories/randebu
pip install -r docs/scripts/requirements.txt

export AVE_API_KEY=your_api_key_here
export API_PLAN=free  # or normal, pro
```

### 8.2 Data REST API Examples

```bash
# Token search
python3 docs/scripts/ave_data_rest.py search --keyword PEPE --chain bsc

# Batch price (up to 200 tokens)
python3 docs/scripts/ave_data_rest.py price --token-ids "PEPE-bsc,TRUMP-bsc,SOL-bsc"

# Trending tokens
python3 docs/scripts/ave_data_rest.py trending --chain bsc --page-size 20

# Token details + top pairs
python3 docs/scripts/ave_data_rest.py token --token-id "PEPE-bsc"

# Risk assessment
python3 docs/scripts/ave_data_rest.py risk --token-id "PEPE-bsc"

# Top 100 holders
python3 docs/scripts/ave_data_rest.py holders --token-id "PEPE-bsc" --limit 50

# Kline data (1h intervals)
python3 docs/scripts/ave_data_rest.py klines --token-id "PEPE-bsc" --interval 1h --limit 100

# Wallet PnL
python3 docs/scripts/ave_data_rest.py wallet-pnl \
  --wallet 0xd9c500dff816a1da21a48a732d3498bf09dc9aeb \
  --chain bsc --token 0x55d398326f99059fF775485246999027B3197955

# Smart wallets (for copy trading)
python3 docs/scripts/ave_data_rest.py smart-wallets --chain bsc --sort total_profit
```

### 8.3 WebSocket Examples

```bash
# Requires API_PLAN=pro

# Subscribe to swap transactions by pair
python3 docs/scripts/ave_data_wss.py subscribe-tx \
  --pair Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE \
  --chain solana

# Subscribe to all txs involving a token
python3 docs/scripts/ave_data_wss.py subscribe-multi-tx \
  --token 0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c \
  --chain bsc

# Subscribe to liquidity changes
python3 docs/scripts/ave_data_wss.py subscribe-liq \
  --pair Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE \
  --chain solana

# Subscribe to price changes
python3 docs/scripts/ave_data_wss.py subscribe-price \
  --pairs "PEPE-bsc,TRUMP-bsc,SOL-bsc"

# Subscribe to kline data
python3 docs/scripts/ave_data_wss.py subscribe-kline \
  --token "PEPE-bsc" --interval 1m

# Interactive REPL mode
python3 docs/scripts/ave_data_wss.py wss-repl
# Then type commands like:
#   subscribe tx <pair_address> <chain>
#   subscribe price PEPE-bsc,TRUMP-bsc
#   list
#   quit
```

### 8.4 Trading Examples

```bash
# Chain Wallet (self-custody) - Free tier OK
# Dry-run quote
python3 docs/scripts/ave_trade_rest.py chain-quote \
  --chain bsc \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy

# Actual swap (requires signing keys configured)
python3 docs/scripts/ave_trade_rest.py chain-swap \
  --chain bsc \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy

# Proxy Wallet (server-managed) - Requires normal/pro tier
export AVE_SECRET_KEY=your_secret_key_here

# Dry-run quote
python3 docs/scripts/ave_trade_rest.py proxy-quote \
  --chain bsc \
  --proxy-wallet 0x... \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy

# Market order with TP/SL
python3 docs/scripts/ave_trade_rest.py proxy-market \
  --chain bsc \
  --proxy-wallet 0x... \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy \
  --tp-price 35.0 --sl-price 30.0

# Limit order
python3 docs/scripts/ave_trade_rest.py proxy-limit \
  --chain bsc \
  --proxy-wallet 0x... \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy --price 35.5

# Get open orders
python3 docs/scripts/ave_trade_rest.py proxy-orders \
  --chain bsc --proxy-wallet 0x...

# Cancel order
python3 docs/scripts/ave_trade_rest.py proxy-cancel \
  --chain bsc --order-id xxx

# Create proxy wallet
python3 docs/scripts/ave_trade_rest.py create-proxy-wallet --chain bsc

# List proxy wallets
python3 docs/scripts/ave_trade_rest.py list-proxy-wallets --chain bsc
```

---

## 9. Security Guide

### 9.1 API Key Management

| Do | Don't |
|----|-------|
| Store in environment variables | Commit to git |
| Use `.env` file (add to `.gitignore`) | Share in Slack/Discord |
| Rotate keys periodically | Use in client-side code |
| Regenerate if compromised | Log API keys in errors |

```bash
# .env file (NEVER commit this)
AVE_API_KEY=your_api_key_here
AVE_SECRET_KEY=your_secret_key_here
AVE_EVM_PRIVATE_KEY=your_private_key_here
```

### 9.2 HMAC Signing for Proxy Wallet

Proxy wallet requests require HMAC-SHA256 signature:

```python
import hashlib
import hmac
import json
import time

def generate_signature(secret_key: str, timestamp: str, body: str = "") -> str:
    message = timestamp + body
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

# Usage
timestamp = str(int(time.time() * 1000))
body = json.dumps({"chain": "bsc", "proxy_wallet": "0x..."}, separators=(",", ":"))
signature = generate_signature(AVE_SECRET_KEY, timestamp, body)

headers = {
    "X-API-KEY": API_KEY,
    "X-Signature": signature,
    "X-Timestamp": timestamp,
    "Content-Type": "application/json"
}
```

### 9.3 Chain Wallet Private Key Protection

| Option | Security Level | Use Case |
|--------|---------------|----------|
| Hardware wallet | Highest | Production trading |
| Encrypted keystore | High | Development |
| Mnemonic (never raw key) | Medium | Quick testing |
| Raw private key in env | Low | Temporary only |

```bash
# Use hardware wallet or encrypted key
# NEVER do this:
AVE_EVM_PRIVATE_KEY=0x1234567890abcdef...

# DO this instead:
# Import from encrypted keystore or hardware wallet
```

### 9.4 Webhook/Callback Verification

If implementing webhooks for order updates:

```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### 9.5 Security Checklist

- [ ] API key stored in environment variable, not code
- [ ] `.env` in `.gitignore`
- [ ] Proxy wallet HMAC signing implemented correctly
- [ ] Private keys never logged or error messages
- [ ] HTTPS only (all AVE Cloud endpoints use HTTPS)
- [ ] Timestamp validation (requests expire after ~30s)
- [ ] Input validation on all user-provided addresses/tokens

---

## 10. Testing Strategies

### 10.1 Dry-Run / Quote Mode

Always test with quotes first:

```bash
# Chain wallet quote (no actual trade)
python3 docs/scripts/ave_trade_rest.py chain-quote \
  --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy

# Proxy wallet quote (no actual trade)
python3 docs/scripts/ave_trade_rest.py proxy-quote \
  --chain bsc --proxy-wallet 0x... \
  --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy
```

### 10.2 Paper Trading Pattern

```python
import os

class PaperTradingBot:
    def __init__(self):
        self.mode = os.getenv("TRADING_MODE", "paper")  # paper or live

    def execute_trade(self, order):
        if self.mode == "paper":
            print(f"[PAPER] Would execute: {order}")
            return {"status": "paper", "order_id": "paper_123"}
        else:
            return self.live_execute(order)
```

### 10.3 Testnet Considerations

> **Important:** AVE Cloud **does not support testnet chains**. All API endpoints connect to production/mainnet:
> - Data API: `https://prod.ave-api.com`
> - Trading API: `https://bot-api.ave.ai`
> - WebSocket: `wss://wss.ave-api.xyz`
>
> The testnet resources below are general blockchain testnets - they are **not** AVE Cloud testnets.

| Chain | Testnet | Faucet |
|-------|---------|--------|
| BSC | https://testnet.bscscan.com | https://testnet.bnb.org |
| Solana | https://api.devnet.solana.com | https://faucet.solana.com |
| ETH | Sepolia testnet | https://sepoliafaucet.com |
| Base | Base Sepolia | https://www.coinbase.com/faucets |

**Safe testing without real money:**
- Use **quote/dry-run mode** - All trading endpoints have a `quote` operation that simulates trades without execution
- Execute with **minimal amounts** - Use tiny amounts (e.g., $1-10) to verify flows
- **Contact AVE support** at `https://t.me/ave_ai_cloud` to ask about sandbox options

### 10.4 Mocking API Responses

```python
import pytest
from unittest.mock import Mock, patch

def test_token_search():
    mock_response = {
        "status": 200,
        "data": [{"symbol": "PEPE", "chain": "bsc", "current_price_usd": "0.00001"}]
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(json=lambda: mock_response, status_code=200)

        result = search_tokens("PEPE", "bsc")
        assert result["data"][0]["symbol"] == "PEPE"
```

### 10.5 Testing WebSocket Reconnection

```python
def test_reconnect():
    client = AveWssClient(API_KEY)
    client.connect()

    # Simulate disconnect
    client.ws.close()

    # Should auto-reconnect
    assert client.running
    time.sleep(6)  # Wait for reconnect
    assert client.ws is not None
```

---

## 11. Troubleshooting Guide

### 11.1 Common Errors and Fixes

| Error | HTTP Code | Business Code | Cause | Solution |
|-------|-----------|--------------|-------|---------|
| 401 Unauthorized | 401 | - | Invalid/missing API key | Regenerate at cloud.ave.ai |
| 403 Forbidden | 403 | 1022 | API key expired | Renew key or contact support |
| 403 Forbidden | 403 | 3104 | Free tier accessing proxy wallet | Upgrade to Level 1+ |
| 429 Rate Limited | 429 | - | TPS exceeded | Add delay, implement backoff |
| 3001 Send TX Failed | 200 | 3001 | Insufficient gas or wallet balance | Check RPC, fund wallet |
| 1021 Signature Failed | 200 | 1021 | HMAC signature incorrect | Check timestamp and signing logic |
| 2001 Parameter Error | 200 | 2001 | Invalid request parameters | Check API docs for required fields |

### 11.2 WebSocket Troubleshooting

**Connection refused:**
```bash
# Verify API plan is pro
echo $API_PLAN  # Should be "pro"
```

**Not receiving messages:**
```python
# Enable debug mode
client = AveWssClient(api_key, debug=True)
```

**Auto-reconnect not working:**
```python
# Manual reconnect
client.disconnect()
time.sleep(5)
client.connect()
```

### 11.3 Rate Limit Handling

```python
import time
import requests

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        result = func()
        if result.status_code != 429:
            return result
        wait_time = 2 ** attempt  # Exponential backoff
        print(f"Rate limited, waiting {wait_time}s...")
        time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### 11.4 Debugging Tips

1. **Check headers:**
   ```python
   print(headers)  # Verify X-API-KEY is present
   ```

2. **Verify token ID format:**
   ```python
   # Correct
   "PEPE-bsc"
   "0x1234...-eth"

   # Wrong
   "PEPE"  # Missing chain
   "bsc:0x1234..."  # Wrong separator
   ```

3. **Check timestamp for HMAC:**
   ```python
   # Timestamp must be milliseconds
   timestamp = str(int(time.time() * 1000))
   ```

4. **Amount format:**
   ```python
   # Use string to avoid floating point precision issues
   "10000000"  # Correct
   10000000    # Also works
   10.0        # WRONG - precision loss
   ```

---

## 12. Competitive Analysis

### 12.1 AVE Cloud vs Alternatives

| Feature | AVE Cloud | DexScreener | Moralis | CoinGecko |
|---------|-----------|-------------|---------|-----------|
| Multi-chain support | 4 chains | 20+ chains | 10+ chains | 100+ chains |
| Trading API | ✅ Chain + Proxy wallet | ❌ | ✅ ETH/ERC-20 only | ❌ |
| WebSocket streams | ✅ (pro tier) | ✅ Free | ✅ Paid only | ❌ |
| TP/SL automation | ✅ Proxy wallet | ❌ | ❌ | ❌ |
| Copy trading support | ✅ Smart wallet list | ❌ | ✅ | ❌ |
| Self-custody option | ✅ Chain wallet | ❌ | ❌ | ❌ |
| CU-based pricing | ✅ | Free | Free tier limited | Free tier limited |
| Risk/honeypot detection | ✅ Built-in | Limited | ✅ | ✅ |
| API documentation | Chinese-focused | Basic | Comprehensive | Comprehensive |
| Community size | Very small (3 stars) | Large | Large | Very large |

### 12.2 Unique Selling Points of AVE Cloud

1. **TP/SL Automation** - Built into proxy wallet, no need to monitor
2. **Dual Wallet Options** - Self-custody (chain) or managed (proxy)
3. **Copy Trading Infrastructure** - Smart wallet tracking API built-in
4. **All-in-one** - Data + Trading in single platform
5. **Low fees** - 0.6% chain, 0.8% proxy with rebates

### 12.3 Weaknesses

1. **Small community** - Only 3 GitHub stars, limited tutorials
2. **Documentation** - Primarily Chinese, limited English examples
3. **New platform** - Early stage, potential instability
4. **Feature locks** - WebSocket requires pro tier
5. **Solana complexity** - Priority fees not well documented

### 12.4 When to Use Alternatives

| Use Case | Alternative |
|----------|-------------|
| Multi-chain analytics only | DexScreener API |
| ERC-20 trading on ETH | Moralis |
| Historical price data | CoinGecko API |
| Advanced charting | TradingView API |
| Social sentiment | LunarCrush |

### 12.5 AVE Cloud Best Fit

- **Hackathon projects** focused on automated trading with TP/SL
- **Copy trading bots** leveraging smart wallet tracking
- **Multi-chain trading bots** needing unified API
- **Real-time monitoring dashboards** with WebSocket feeds

---

## 13. AVE Cloud Agent Skills - User Insights

**GitHub Activity:**
- `ave-cloud-skill`: 3 stars, 46 commits (very early stage)
- `ave-cloud-mcp`: 0 stars, just created (1 commit)

### Most Used/Popular Features
1. **Token Research & Due Diligence** (`ave-data-rest`)
   - Token search, price lookup, risk/honeypot detection
   - Trending token discovery
   - Most featured in documentation

2. **Proxy Wallet Trading** (`ave-trade-proxy-wallet`)
   - Market/limit orders with TP/SL
   - Easier UX than self-custody
   - Well-documented

3. **Live Price Monitoring** (`ave-data-wss`)
   - Real-time WebSocket streams
   - Multiple token tracking

### Least Used/Niche Features
1. **Self-custody Chain-Wallet Trading** (`ave-trade-chain-wallet`)
   - Requires private key/mnemonic management
   - Complex RPC setup
   - Lower priority in routing

2. **External Signer Workflows**
   - Hardware wallet integration
   - Multi-sig support

3. **Solana-specific trading** - Less documented, priority fee complexity

### User Pain Points
- API tier confusion (features locked behind paid tiers)
- Multiple environment variables needed
- WSS connection limit (5 concurrent)
- No community tutorials or reviews found

### Community Presence
- Telegram: @aveai_english, @aveai_community_cn
- Discord: discord.gg/Z2RmAzF2
- No YouTube tutorials, blog posts, or external reviews yet

**Bottom line:** The skills system is very new (3 stars), primarily used for token research and proxy wallet trading. The self-custody chain-wallet is the least used due to complexity.

---

## Appendix: Quick Reference

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `AVE_API_KEY` | All scripts | API key from cloud.ave.ai |
| `API_PLAN` | WSS, Proxy trading | free, normal, or pro |
| `AVE_SECRET_KEY` | Proxy wallet | HMAC signing secret |
| `AVE_EVM_PRIVATE_KEY` | Chain wallet (optional) | Hex private key for BSC/ETH/Base |
| `AVE_SOLANA_PRIVATE_KEY` | Chain wallet (optional) | Base58 private key for Solana |
| `AVE_MNEMONIC` | Chain wallet (optional) | BIP39 mnemonic |

### Script Quick Reference

```bash
# Data REST
python3 docs/scripts/ave_data_rest.py search --keyword <keyword>
python3 docs/scripts/ave_data_rest.py price --token-ids <comma-separated>
python3 docs/scripts/ave_data_rest.py trending --chain <chain>
python3 docs/scripts/ave_data_rest.py token --token-id <id>
python3 docs/scripts/ave_data_rest.py risk --token-id <id>
python3 docs/scripts/ave_data_rest.py holders --token-id <id>
python3 docs/scripts/ave_data_rest.py klines --token-id <id>
python3 docs/scripts/ave_data_rest.py wallet-pnl --wallet <addr> --chain <chain> --token <addr>
python3 docs/scripts/ave_data_rest.py wallet-info --wallet <addr> --chain <chain>
python3 docs/scripts/ave_data_rest.py smart-wallets --chain <chain>

# Data WebSocket
python3 docs/scripts/ave_data_wss.py subscribe-tx --pair <addr> --chain <chain>
python3 docs/scripts/ave_data_wss.py subscribe-multi-tx --token <addr> --chain <chain>
python3 docs/scripts/ave_data_wss.py subscribe-price --pairs <comma-separated>
python3 docs/scripts/ave_data_wss.py wss-repl

# Trading REST
python3 docs/scripts/ave_trade_rest.py chain-quote --chain <chain> --in-token <addr> --out-token <addr> --in-amount <amount> --swap-type <buy|sell>
python3 docs/scripts/ave_trade_rest.py chain-swap ...
python3 docs/scripts/ave_trade_rest.py proxy-quote ...
python3 docs/scripts/ave_trade_rest.py proxy-market ... [--tp-price <p>] [--sl-price <p>]
python3 docs/scripts/ave_trade_rest.py proxy-limit ... --price <p>
python3 docs/scripts/ave_trade_rest.py proxy-orders --chain <chain> --proxy-wallet <addr>
python3 docs/scripts/ave_trade_rest.py proxy-cancel --chain <chain> --order-id <id>
python3 docs/scripts/ave_trade_rest.py create-proxy-wallet --chain <chain>
python3 docs/scripts/ave_trade_rest.py list-proxy-wallets --chain <chain>
```

### Common Token Addresses (BSC Mainnet)

| Token | Address |
|-------|---------|
| BNB | (native) |
| USDT | 0x55d398326f99059fF775485246999027B3197955 |
| BUSD | 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 |
| BTCB | 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c |
| ETH | 0x2170Ed0880ac9A755fd29C2681C0DBeD5aF88B2c |

### Common Token Addresses (Solana)

| Token | Address |
|-------|---------|
| SOL | So11111111111111111111111111111111111111112 |
| USDC | EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v |
| USDT | Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB |
