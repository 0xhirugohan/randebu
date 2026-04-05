# AVE Trading Bot - Implementation Plan

> **Project Overview:** An AI-powered trading bot platform where users create and manage trading bots through natural language chat, with backtesting and simulation capabilities.

---

## 1. Concept & Vision

### 1.1 What We're Building

A **prompt-driven AI trading bot platform** that democratizes agentic trading by letting anyone create automated trading strategies through conversation - no coding required.

**Core Promise:** "Create a trading bot by chatting with AI. Test it risk-free. Deploy when you're ready."

### 1.2 Target Audience

- People familiar with trading but not agentic/automated trading
- Want to learn agentic concepts without high barrier to entry
- Have money to trade but limited technical skills
- Age: Productive age (working adults)
- Tech-savvy: Low to moderate - can't run their own agent locally

### 1.3 Core Experience

**Chat-first interface** where users:
1. Describe trading strategies in natural language
2. AI interprets and creates bot configuration
3. User can modify by continuing the conversation
4. Run backtests to validate strategy
5. Run simulations to see real-time signals
6. Deploy to trade live (future phase)

**Multi-bot support:** Up to 3 bots per user, selectable in chat

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Svelte)                         │
│  - Chat interface (bot creation/modification)                 │
│  - Bot selector (max 3 bots)                               │
│  - Backtest results visualization                           │
│  - Simulation signals dashboard                             │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND (Python FastAPI)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Auth        │  │ Bot Config  │  │ User Management │   │
│  │ (JWT)       │  │ (CRUD)      │  │                 │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ AI Agent    │  │ Strategy    │  │ Execution       │   │
│  │ (CrewAI)    │  │ Compiler    │  │ Engine          │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │ Backtest    │  │ Simulate    │                         │
│  │ Engine      │  │ Engine      │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                         │
│  ┌─────────────────────┐  ┌────────────────────────────┐  │
│  │ SQLite              │  │ AVE Cloud APIs             │  │
│  │ - users             │  │ - Data API (klines, prices)│  │
│  │ - bots              │  │ - Trading API (chain wallet│  │
│  │ - signals           │  │ - Proxy wallet (Pro tier) │  │
│  │ - backtests         │  └────────────────────────────┘  │
│  │ - simulations       │  ┌────────────────────────────┐  │
│  └─────────────────────┘  │ MiniMax API               │  │
│                            │ (Anthropic format)       │  │
│                            └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Svelte + TypeScript | No Next.js, good DX, lightweight |
| **Backend** | Python FastAPI | Phase 1 - quick to prototype |
| **Backend (Phase 2)** | Bun/TypeScript | Performance, single language |
| **AI Agent** | CrewAI + MiniMax | Multi-agent orchestration |
| **LLM** | MiniMax (Anthropic format) | User has API key |
| **Database** | SQLite | File-based, simple for MVP |
| **Deployment** | Self-hosted (Debian) | User's server, subdomain |

---

## 4. Database Schema

### 4.1 Tables

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,           -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- bcrypt hashed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bots table (max 3 per user)
CREATE TABLE bots (
    id TEXT PRIMARY KEY,           -- UUID
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,              -- AI-generated description
    strategy_config JSON NOT NULL, -- The trading strategy
    llm_config JSON NOT NULL,     -- Model, temperature, etc.
    status TEXT DEFAULT 'draft',  -- draft, active, paused
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bot conversations (chat history)
CREATE TABLE bot_conversations (
    id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    role TEXT NOT NULL,            -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);

-- Backtest results
CREATE TABLE backtests (
    id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    status TEXT NOT NULL,          -- running, completed, failed
    config JSON NOT NULL,         -- Backtest parameters
    result JSON,                  -- Final results
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);

-- Simulation results
CREATE TABLE simulations (
    id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL,          -- running, stopped
    config JSON NOT NULL,          -- Simulation parameters
    signals JSON,                  -- Generated signals
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);

-- Signals log (for both backtest and simulate)
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    run_id TEXT NOT NULL,          -- backtest_id or simulation_id
    signal_type TEXT NOT NULL,     -- buy, sell, hold
    token TEXT NOT NULL,
    price REAL NOT NULL,
    confidence REAL,               -- AI confidence %
    reasoning TEXT,                -- Why this signal
    executed BOOLEAN DEFAULT FALSE, -- If actually executed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);
```

### 4.2 Indexes

```sql
CREATE INDEX idx_bots_user_id ON bots(user_id);
CREATE INDEX idx_conversations_bot_id ON bot_conversations(bot_id);
CREATE INDEX idx_backtests_bot_id ON backtests(bot_id);
CREATE INDEX idx_simulations_bot_id ON simulations(bot_id);
CREATE INDEX idx_signals_bot_id ON signals(bot_id);
CREATE INDEX idx_signals_run_id ON signals(run_id);
```

---

## 5. API Endpoints

### 5.1 Auth Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/logout` | Logout (invalidate token) |
| GET | `/api/auth/me` | Get current user |

### 5.2 Bot Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bots` | List user's bots (max 3) |
| POST | `/api/bots` | Create new bot |
| GET | `/api/bots/{id}` | Get bot details |
| PUT | `/api/bots/{id}` | Update bot |
| DELETE | `/api/bots/{id}` | Delete bot |
| POST | `/api/bots/{id}/chat` | Send message to bot |
| GET | `/api/bots/{id}/history` | Get chat history |

### 5.3 Backtest Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bots/{id}/backtest` | Start backtest |
| GET | `/api/bots/{id}/backtest/{run_id}` | Get backtest status/results |
| GET | `/api/bots/{id}/backtests` | List all backtests for bot |
| POST | `/api/bots/{id}/backtest/{run_id}/stop` | Stop running backtest |

### 5.4 Simulation Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bots/{id}/simulate` | Start simulation |
| GET | `/api/bots/{id}/simulate/{run_id}` | Get simulation status/signals |
| GET | `/api/bots/{id}/simulations` | List all simulations for bot |
| POST | `/api/bots/{id}/simulate/{run_id}/stop` | Stop simulation |

### 5.5 Config Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/chains` | Get supported chains |
| GET | `/api/config/tokens` | Get common tokens |

---

## 6. CrewAI Agent Design

### 6.1 Agent Roles

```python
# For parsing user intent → strategy config
trading_designer = Agent(
    role="Trading Strategy Designer",
    goal="Design clear, executable trading strategies from natural language",
    backstory="Expert in DeFi trading with deep knowledge of indicators, "
              "tokenomics, and market patterns. You specialize in translating "
              "user requirements into precise trading rules.",
)

# For validating strategy feasibility
strategy_validator = Agent(
    role="Strategy Validator",
    goal="Ensure strategies are realistic and well-formed",
    backstory="Risk management specialist who checks if strategies "
              "are implementable and identifies potential issues.",
)

# For generating explanations
strategy_explainer = Agent(
    role="Strategy Explainer",
    goal="Make complex strategies understandable",
    backstory="Education specialist who simplifies trading concepts "
              "for beginners without losing accuracy.",
)
```

### 6.2 Default Crew for Bot Chat

```python
trading_crew = Crew(
    agents=[trading_designer, strategy_validator, strategy_explainer],
    tasks=[understand_intent, validate_strategy, update_config, explain_changes],
    process=Process.sequential
)
```

### 6.3 Strategy Config Schema

```json
{
  "conditions": [
    {
      "type": "price_drop",
      "token": "PEPE",
      "chain": "bsc",
      "threshold": 5,
      "timeframe": "1h"
    }
  ],
  "actions": [
    {
      "type": "buy",
      "amount_percent": 10,
      "token": "PEPE"
    }
  ],
  "risk_management": {
    "stop_loss_percent": 3,
    "take_profit_percent": 10
  }
}
```

---

## 7. Backtest Engine

### 7.1 Algorithm

```
1. Parse strategy_config → conditions + actions
2. Fetch historical klines from AVE Cloud API
   - GET /v2/klines/token/{token-id} or /v2/klines/pair/{pair-id}
   - Time range: user-specified
3. For each time point in klines:
   a. Check if any condition is met
   b. If met → generate signal (buy/sell/hold)
   c. Simulate portfolio change
   d. Log signal to signals table
4. Calculate metrics:
   - Total return %
   - Win rate (% correct predictions)
   - Max drawdown
   - Sharpe ratio
   - Number of trades
5. Store results in backtests table
```

### 7.2 Backtest Response

```json
{
  "id": "backtest-uuid",
  "status": "completed",
  "duration_seconds": 45,
  "config": {
    "token": "PEPE-bsc",
    "timeframe": "1h",
    "start_date": "2024-01-01",
    "end_date": "2024-02-01"
  },
  "results": {
    "total_return": 15.4,
    "win_rate": 62.5,
    "total_trades": 24,
    "buy_signals": 12,
    "sell_signals": 12,
    "max_drawdown": 8.2,
    "sharpe_ratio": 1.45
  },
  "signals": [...]
}
```

---

## 8. Simulate Engine

### 8.1 Algorithm

```
1. Load bot's strategy_config
2. Start loop (user-initiated):
   a. Fetch current prices for relevant tokens
      - GET /v2/tokens/price (batch, up to 200)
   b. Check if any condition is met
   c. If met:
      - Generate signal with confidence score
      - Log to signals table
      - If auto_execute=true → call trading API
      - Else → notify user
   d. Wait N seconds (configurable, 60s default for free tier)
3. Stop when user stops or max_duration reached
```

### 8.2 User Notice

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Simulation Mode - Free Tier                            │
│                                                             │
│  Using REST polling (every 60s). For real-time signals,    │
│  consider upgrading to Pro tier for WebSocket streams.      │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Frontend Components

### 9.1 Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing or dashboard (if logged in) |
| `/login` | Login form |
| `/register` | Registration form |
| `/dashboard` | Main dashboard (list of bots) |
| `/bot/:id` | Bot chat interface |
| `/bot/:id/backtest` | Backtest results view |
| `/bot/:id/simulate` | Simulation monitor view |
| `/settings` | User settings, API keys |

### 9.2 Key Components

| Component | Purpose |
|-----------|---------|
| `ChatInterface` | Message input, AI responses, chat history |
| `BotCard` | Bot preview card for dashboard |
| `BotSelector` | Dropdown to select which bot to modify (max 3) |
| `StrategyPreview` | Shows parsed strategy config in readable format |
| `SignalChart` | Visual representation of signals over time |
| `BacktestChart` | Line chart of portfolio value over time |
| `ProUpgradeBanner` | Banner shown when feature requires Pro tier |
| `TokenPicker` | Search/select tokens for conditions |
| `ConditionBuilder` | UI for building price/volume conditions |

---

## 10. Tier Gating

| Feature | Free | Normal | Pro |
|---------|------|--------|-----|
| Bot creation (max 3) | ✅ | ✅ | ✅ |
| Chat interface | ✅ | ✅ | ✅ |
| Backtest | ✅ | ✅ | ✅ |
| Simulate (REST polling) | ✅ | ✅ | ✅ |
| Simulate (WebSocket) | ❌ | ❌ | ✅ |
| Chain Wallet trading | ✅ | ✅ | ✅ |
| Proxy Wallet trading | ❌ | ✅ | ✅ |
| Scheduled bot runs | ❌ | ❌ | ✅ |

---

## 11. Environment Configuration

### 11.1 Backend `.env`

```env
# Database
DATABASE_URL=sqlite:///./data/app.db

# Auth
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MiniMax
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_MODEL=MiniMax-Text-01

# AVE Cloud
AVE_API_KEY=your-ave-cloud-api-key
AVE_API_PLAN=free

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 11.2 Frontend `.env`

```env
VITE_API_URL=https://bot.yourdomain.com/api
VITE_WS_URL=wss://bot.yourdomain.com/ws
```

---

## 12. Project Structure

```
/home/shoko/repositories/randebu/
├── docs/
│   ├── ave-hackathon-research.md      # AVE Cloud research
│   ├── scripts/                       # AVE Cloud API scripts
│   │   ├── ave_data_rest.py
│   │   ├── ave_data_wss.py
│   │   ├── ave_trade_rest.py
│   │   └── requirements.txt
│   └── IMPLEMENTATION_PLAN.md         # This document
├── src/
│   ├── backend/                       # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── bots.py
│   │   │   │   ├── backtest.py
│   │   │   │   ├── simulate.py
│   │   │   │   └── config.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── database.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   └── schemas.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_agent/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── crew.py
│   │   │   │   │   └── llm_connector.py
│   │   │   │   ├── backtest/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── engine.py
│   │   │   │   └── simulate/
│   │   │   │       ├── __init__.py
│   │   │   │       └── engine.py
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   ├── run.py
│   │   └── setup.py
│   └── frontend/                      # Svelte frontend
│       ├── src/
│       │   ├── lib/
│       │   │   ├── components/
│       │   │   ├── stores/
│       │   │   └── api/
│       │   ├── routes/
│       │   └── app.html
│       ├── svelte.config.js
│       ├── package.json
│       └── vite.config.ts
└── README.md
```

---

## 13. Deployment

### 13.1 Prerequisites

- Debian server with 8GB RAM, 4 cores
- Python 3.10+
- Node.js 18+
- Nginx
- SSL certificate (Let's Encrypt)

### 13.2 Deployment Steps

```
1. Clone repo to server
   git clone https://github.com/your-repo/ave-trading-bot.git

2. Setup Python virtual environment
   cd ave-trading-bot/src/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. Setup SQLite database
   mkdir -p data

4. Configure Nginx (reverse proxy to localhost:8000)

5. Setup systemd service for auto-restart

6. Start backend service

7. Build frontend
   cd ../frontend
   npm install
   npm run build

8. Serve frontend via Nginx
```

---

## 14. Phase 1 Deliverables

| Deliverable | Status |
|-------------|--------|
| User auth (register, login, logout) | ☐ |
| Bot CRUD (max 3 per user) | ☐ |
| Chat interface with CrewAI | ☐ |
| Strategy parser (NL → config) | ☐ |
| Backtest engine + API | ☐ |
| Backtest results visualization | ☐ |
| Simulate engine + API | ☐ |
| Simulation signals dashboard | ☐ |
| AVE Cloud Data API integration | ☐ |
| AVE Cloud Trading API integration (Chain Wallet) | ☐ |
| Free tier detection + upsell messaging | ☐ |
| SQLite persistence | ☐ |
| Environment config via env vars | ☐ |
| Nginx deployment config | ☐ |
| Systemd service config | ☐ |
| Working deployment on subdomain | ☐ |

---

## 15. Phase 2 Considerations

| Feature | Notes |
|---------|-------|
| Proxy Wallet | Requires Normal+ tier |
| WebSocket streams | Requires Pro tier |
| Scheduled jobs | Need cron/background worker |
| Multiple coordinated bots | Portfolio management |
| Local agent runner | For advanced users |
| Bun/TypeScript backend | Migration from Python |

---

## 16. Open Questions

- [ ] Server SSH access details (to be provided later)
- [ ] Domain/subdomain DNS configuration (to be set up)
- [ ] MiniMax API key (provided via env var)
- [ ] AVE Cloud API key (provided via env var)

---

## 17. Appendix: Supported Conditions (MVP)

| Condition Type | Description | Parameters |
|----------------|-------------|-------------|
| `price_drop` | Token price drops by X% | threshold, timeframe |
| `price_rise` | Token price rises by X% | threshold, timeframe |
| `volume_spike` | Trading volume increases X% | threshold, timeframe |
| `price_level` | Price crosses above/below X | price, direction |

---

*Document Version: 1.0*  
*Created: 2026-04-05*
