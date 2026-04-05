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
| `GET /v2/tokens/price` | Batch token prices (up to 200) | 100 CU |
| `GET /v2/tokens/trending` | Trending tokens | 5 CU |
| `GET /v2/tokens/top100/{token-id}` | Top 100 token holders | 10 CU |
| `GET /v2/contracts/{token-id}` | Token risk info | 10 CU |
| `GET /v2/txs/swap/{pair-id}` | Swap tx history | 50 CU |
| `GET /v2/txs/liq/{pair-id}` | Liquidity change txs | 50 CU |
| `GET /v2/address/tx` | Wallet transaction history | 100 CU |
| `GET /v2/address/pnl` | Wallet PnL data | 5 CU |
| `GET /v2/address/walletinfo` | Wallet info (all tokens) | 5 CU |
| `GET /v2/klines/token/{token-id}` | Kline data by token | 10 CU |
| `GET /v2/klines/pair/{pair-id}` | Kline data by pair | 10 CU |

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

### Python Skill Scripts (GitHub)

The `ave-cloud-skill` repo provides Python scripts:

| Script | Purpose |
|--------|---------|
| `ave_data_rest.py` | Token search, prices, klines, holders, risk |
| `ave_data_wss.py` | Real-time WebSocket streams |
| `ave_trade_rest.py` | Chain & proxy wallet trading |
| `ave_trade_wss.py` | Proxy wallet WebSocket updates |

### Quick Start Example

```bash
# Build Docker image
docker build -f scripts/Dockerfile.txt -t ave-cloud .

# Token search
docker run --rm \
  -e AVE_API_KEY=your_api_key \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_rest.py search --keyword PEPE

# Live price watch
docker run --rm -it \
  -e AVE_API_KEY=your_api_key \
  -e API_PLAN=pro \
  --entrypoint python3 \
  ave-cloud scripts/ave_data_wss.py wss-repl

# Dry-run trade preview
docker run --rm \
  -e AVE_API_KEY=your_api_key \
  -e API_PLAN=free \
  --entrypoint python3 \
  ave-cloud scripts/ave_trade_rest.py quote \
  --chain bsc --in-token 0x55d398326f99059fF775485246999027B3197955 \
  --out-token 0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c \
  --in-amount 10000000 --swap-type buy
```

### Token Links Format
View tokens on AVE Pro: `https://pro.ave.ai/token/<token_address>-<chain>`
Example: `https://pro.ave.ai/token/0x1234...abcd-bsc`

---

## Decision Guidance for Participants

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

## 6. AVE Cloud Agent Skills - User Insights

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