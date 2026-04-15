# Randebu

**Create Trading Bots Through Natural Conversation**

Randebu is a web-based platform that allows traders to create and manage automated trading bots through simple chat interactions. No coding required.

---

## The Problem

Trading bots like **OpenClaw** and similar platforms are powerful but come with a steep learning curve:

- Complex configuration files
- Requires understanding of trading strategies
- CLI-based interfaces
- Steep technical barrier for non-developers

## The Solution

Randebu lets you create trading bots by simply chatting:

> "Create a bot that buys PEPE when it drops 5% and sells when it profits 10%"

That's it. Randebu handles the rest.

---

## How It Works

1. **Chat** - Tell Randebu what you want in plain English
2. **Bot Created** - Randebu creates a configured trading bot
3. **Backtest** - Test your strategy with historical data
4. **Simulate** - Run a simulation with real-time data
5. **Deploy** - Activate your bot on the blockchain

---

## Built on AVE Cloud

Randebu is powered by **AVE Cloud Skills** - the same infrastructure used by professional trading teams.

### AVE Skills Currently Integrated

Randebu uses **AVE Cloud Skills** (the skill scripts from `ave-cloud-skill` repository) for data fetching:

| Skill Script | Command | Purpose | Line in agent.py |
|-------------|---------|---------|------------------|
| `ave_data_rest.py` | `trending` | Get trending tokens | 218 |
| `ave_data_rest.py` | `search` | Search tokens by keyword | 285 |
| `ave_data_rest.py` | `risk` | Honeypot/risk analysis | 367 |
| `ave_data_rest.py` | `token` | Get token details | 487 |
| `ave_data_rest.py` | `price` | Get token prices | 509 |

### AVE Integration Points

The AVE skills are called through `_call_ave_script()` in `agent.py`:

```python
# agent.py - Calling AVE skill scripts
def _call_ave_script(self, command: str, args: list) -> tuple[int, str]:
    ave_skill_path = os.path.join(
        repo_root, "ave-cloud-skill", "scripts", "ave_data_rest.py"
    )
    result = subprocess.run(
        ["python3", ave_skill_path, command] + args,
        ...
    )
```

### Direct API Usage (Not Skills)

These components use the AVE API directly (not through skills):
- `backtest/engine.py` - Uses `AveCloudClient.get_klines()` for historical kline data
- `simulate/engine.py` - Uses `AveCloudClient.get_klines()` for real-time kline data

---

## Further AVE Integration Opportunities

### 1. Trading Execution (Priority: High)
- **AVE Skills**: `trade-chain-wallet`, `trade-proxy-wallet`
- **Use**: Execute trades directly from the bot (market orders, limit orders, TP/SL)
- **Status**: Not yet integrated - this is the next major feature

### 2. Real-Time Alerts (Priority: Medium)
- **AVE Skills**: WebSocket streams (`data-wss`)
- **Use**: Notify users when price hits targets

### 3. Portfolio Tracking (Priority: Medium)
- **AVE API**: `address/walletinfo` endpoint
- **Use**: Show user's complete portfolio across chains

### 4. Advanced Risk Analysis (Priority: Low)
- **AVE Skills**: Extended token analysis
- **Use**: More detailed honeypot detection, liquidity analysis

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | SvelteKit, TypeScript |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| AI | MiniMax (extended thinking) |
| Trading Data | AVE Cloud API |

---

## Future Development Plan

### Phase 1: Core MVP (Current)
- [x] Chat-based bot creation
- [x] Strategy configuration via conversation
- [x] Backtest historical data
- [x] Simulation with real-time data
- [x] Bot management (create, list, set)

### Phase 2: Trading Execution
- [ ] AVE Trading API integration
- [ ] Chain wallet support
- [ ] Proxy wallet (bot-managed) support
- [ ] TP/SL automation

### Phase 3: Advanced Features
- [ ] Portfolio dashboard
- [ ] Multi-chain support (Solana, Base, ETH)
- [ ] Copy trading (follow other traders)
- [ ] Strategy marketplace

### Phase 4: Platform Growth
- [ ] Strategy templates
- [ ] Community strategies
- [ ] Premium features (for fees)

---

## Business Opportunity

### Target Market

1. **Retail Traders** - People who want to automate trading but can't code
2. **Crypto Enthusiasts** - Active traders looking for easier tools
3. **Small Funds** - Need automation without expensive developers

### Revenue Model

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 1 bot, 50 chats, basic features |
| Pro | $19/mo | Unlimited bots, backtests, simulations |
| Enterprise | Custom | API access, priority support, custom integrations |

### Competitive Advantage

- **No-code** - Unlike OpenClaw, 3Commas, Cryptohopper
- **Natural Language** - Describe strategy in plain English
- **AVE Integration** - Built on professional-grade infrastructure
- **Focused UX** - Simple, clean interface designed for beginners

### Market Size

- Crypto traders: 100M+ globally
- Trading bot market: $1.5B+ by 2027
- No-code platform market: Growing rapidly

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL

### Installation

```bash
# Clone the repo
git clone https://github.com/shoko/randebu.git
cd randebu

# Setup backend
cd src/backend
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
# Backend: uvicorn main:app
# Frontend: npm run dev
```

### Configuration

Required environment variables:
- `MINIMAX_API_KEY` - For AI chat
- `AVE_API_KEY` - For trading data
- `DATABASE_URL` - PostgreSQL connection

---

## Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

---

## License

MIT

---

## Links

- Website: [randebu.com](https://randebu.com)
- AVE Cloud: [cloud.ave.ai](https://cloud.ave.ai)
- Hackathon: [clawhackathon.aveai.trade](https://clawhackathon.aveai.trade)

---

*Built with ❤️ for traders, by traders*
