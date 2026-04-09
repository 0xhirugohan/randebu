# Randebu Trading Bot - Product & Technical Audit Report

> **Date:** 2026-04-09  
> **Phase:** Phase 1 Implementation Complete - Pre-Testing Review  
> **Purpose:** Document current state, issues found, and recommendations for next steps

---

## 1. Product Overview

### 1.1 What is Randebu?

Randebu is an AI-powered trading bot platform where users create and manage automated trading strategies through natural language chat—similar to ChatGPT, but specialized for creating trading bots.

### 1.2 Core User Flow

```
User Registration → Create Bot → Chat with AI to Define Strategy 
    → Backtest Strategy → Simulate Trading → (Future) Live Trading
```

### 1.3 Phase 1 Scope

| Feature | Status |
|---------|--------|
| BNB Chain only | ✅ Intended (not yet enforced) |
| Backtest engine | ✅ Implemented |
| Simulation engine | ✅ Implemented |
| Natural language strategy parsing | ✅ Implemented |
| User authentication | ✅ Implemented |
| Multi-bot support (max 3) | ✅ Implemented |
| Dummy wallet (database record) | ✅ Implemented |

### 1.4 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Svelte 5 + TypeScript |
| Backend | Python FastAPI |
| AI Agent | CrewAI + MiniMax LLM |
| Database | SQLite |
| Trading Data | AVE Cloud API |

---

## 2. Critical Issues (Must Fix Before Testing)

These issues will cause complete pipeline failure if not addressed.

### 2.1 Database Tables Never Created

**Location:** `src/backend/app/main.py`, `src/backend/run.py`

**Problem:** The application starts but never creates the database tables. There is no:
- Alembic migration setup
- `Base.metadata.create_all()` call on startup
- Database initialization script

**Impact:** First database operation will fail with "table not found" error.

**Current State:**
```python
# core/database.py defines Base, but nothing calls:
# Base.metadata.create_all(engine)
```

**Fix Required:** Add database initialization on application startup.

---

### 2.2 Strategy Config Schema Mismatch

**Location:** Multiple files - see mapping below

**Problem:** The LLM outputs one schema format, but the backtest and simulation engines expect a completely different format. This is a **complete pipeline break** - strategies parsed by AI will never trigger any trades in backtesting.

#### Schema Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LLM OUTPUT (llm_connector.py) - What AI actually produces             │
├─────────────────────────────────────────────────────────────────────────┤
│ {                                                                       │
│   "type": "price_drop",                                                │
│   "params": {                                                          │
│     "token": "PEPE",                                                   │
│     "threshold_percent": 5                                             │
│   }                                                                    │
│ }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND VALIDATOR (crew.py - StrategyValidator.validate())             │
├─────────────────────────────────────────────────────────────────────────┤
│ # Validator expects params.threshold_percent - THIS WORKS              │
│ if "threshold_percent" not in params:                                  │
│     errors.append(f"Condition {i}: missing 'threshold_percent'")       │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ (But engines look for flat fields)
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKTEST ENGINE (services/backtest/engine.py - _check_condition())     │
├─────────────────────────────────────────────────────────────────────────┤
│ # What engine actually looks for:                                      │
│ threshold = condition.get("threshold", 0)    # ❌ Returns 0!          │
│ token = condition.get("token")                # ❌ Wrong path!         │
│ timeframe = condition.get("timeframe")        # ❌ Not in params!     │
│                                                                          │
│ # Result: Conditions NEVER trigger because field names don't match     │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ SIMULATE ENGINE (services/simulate/engine.py - _check_condition())    │
├─────────────────────────────────────────────────────────────────────────┤
│ # Same issue as backtest engine                                        │
│ threshold = condition.get("threshold", 0)    # ❌ Returns 0            │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND TYPES (src/frontend/src/lib/api/types.ts)                    │
├─────────────────────────────────────────────────────────────────────────┤
│ interface Condition {                                                  │
│   type: 'price_drop' | 'price_rise' | 'volume_spike' | 'price_level';│
│   token: string;                    # Flat - no params wrapper        │
│   threshold?: number;               # Not threshold_percent!          │
│   timeframe?: string;               # Exists here                    │
│ }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Field Mapping Table

| Component | Token Field | Threshold Field | Timeframe Field |
|-----------|-----------|-----------------|-----------------|
| LLM Output | `params.token` | `params.threshold_percent` | N/A |
| Validator | `params.token` | `params.threshold_percent` | N/A |
| Backtest Engine | `token` | `threshold` | `timeframe` |
| Simulate Engine | `token` | `threshold` | `timeframe` |
| Frontend Types | `token` | `threshold` | `timeframe` |

**Fix Required:** Normalize to ONE consistent schema across the entire pipeline. Recommended: Use the flat structure (token, threshold, timeframe) as it's simpler and already used by engines and frontend.

---

### 2.3 Bot Creation Will Fail

**Location:** 
- `src/backend/app/db/schemas.py` (BotCreate)
- `src/frontend/src/lib/api/client.ts` (bots.create)

**Problem:**

| Issue | Details |
|-------|---------|
| Backend requires | `strategy_config: dict` (REQUIRED) |
| Backend requires | `llm_config: dict` (REQUIRED) |
| Frontend sends | Only `name` and optional `description` |

**Impact:** Users cannot create bots through the frontend - API will return validation error.

**Fix Required:** Either:
1. Make `strategy_config` and `llm_config` optional in backend with default values
2. OR update frontend to send default config values

---

### 2.4 Config Endpoints Return Empty Data

**Location:** `src/backend/app/api/config.py`

```python
@router.get("/chains")
def get_chains():
    return {"chains": []}  # ❌ Always empty

@router.get("/tokens")
def get_tokens():
    return {"tokens": []}  # ❌ Always empty
```

**Impact:** Frontend cannot populate dropdowns for chain/token selection.

**Fix Required:** Return BSC (BNB Chain) as the only supported chain in Phase 1, and query AVE API for available tokens.

---

## 3. Major Issues

### 3.1 Risk Management Not Implemented

**Location:** 
- `src/backend/app/db/models.py` (schema supports it)
- `src/backend/app/services/backtest/engine.py`
- `src/backend/app/services/simulate/engine.py`

**Problem:** The database schema and frontend UI support `risk_management` configuration:
```typescript
interface RiskManagement {
    stop_loss_percent?: number;
    take_profit_percent?: number;
}
```

However, neither the backtest nor simulation engines actually check or use stop-loss/take-profit logic during trade execution. The config is saved but ignored.

**Fix Required:** Implement actual stop-loss and take-profit checks in both engines.

---

### 3.2 Duplicate AveCloudClient Implementations

**Location:**
- `src/backend/app/services/ave/client.py`
- `src/backend/app/services/backtest/ave_client.py`

**Problem:** Two different AveCloudClient classes with different methods:

| `services/ave/client.py` | `services/backtest/ave_client.py` |
|--------------------------|-----------------------------------|
| `get_tokens()` | ❌ Missing |
| `get_batch_prices()` | ✅ `get_batch_prices()` |
| `get_token_details()` | ❌ Missing |
| `get_klines()` | ✅ `get_klines()` |
| `get_trending_tokens()` | ❌ Missing |
| `get_token_risk()` | ❌ Missing |
| `get_chain_quote()` | ❌ Missing |
| `get_chain_swap()` | ❌ Missing |
| ❌ Missing | `get_token_price()` |

Additionally, the simulate engine imports from the wrong location:
```python
# services/simulate/engine.py
from ..backtest.ave_client import AveCloudClient  # ❌ Wrong import
```

**Fix Required:** Consolidate into ONE AveCloudClient class.

---

### 3.3 Silent Error Handling in Simulation

**Location:** `src/backend/app/services/simulate/engine.py`

```python
try:
    # ... API calls ...
except Exception as e:
    pass  # ❌ Silently swallows ALL errors!
```

**Impact:** If AVE API fails or returns bad data, the simulation continues silently with no logging or user feedback.

**Fix Required:** Add proper error logging and user-facing error messages.

---

### 3.4 No Chain Validation for Phase 1

**Problem:** You mentioned limiting to BNB Chain only for Phase 1, but:
- No backend validation enforces this
- Users can specify any chain in backtest/simulate config
- The config endpoints return empty arrays

**Fix Required:** Add chain validation that only allows "bsc" for Phase 1.

---

### 3.5 In-Memory Token Blacklist

**Location:** `src/backend/app/api/auth.py`

```python
TOKEN_BLACKLIST = set()  # ❌ In-memory only
```

**Problems:**
- Resets when server restarts
- Doesn't work with multiple workers/processes
- Logout doesn't truly invalidate tokens in production

**Fix Required:** Use Redis or database-backed token blacklist for production.

---

### 3.6 Conversation History Not Passed to Crew

**Location:** `src/backend/app/api/bots.py`

```python
history_for_crew = conversation_history[-10:]  # Gets history
crew = get_trading_crew()                      # ❌ Doesn't pass history!
result = crew.chat(user_message, history_for_crew)
```

The history is fetched but not actually used by the agent - each chat starts fresh.

**Fix Required:** Pass conversation history to the crew agent.

---

### 3.7 No Rate Limiting Applied

**Location:** `src/backend/app/main.py`

```python
app.state.limiter = limiter  # Set up but not used on most endpoints
```

The rate limiter is initialized but only applied to the login endpoint. Other endpoints have no protection.

**Fix Required:** Apply rate limiting to sensitive endpoints.

---

### 3.8 CORS Wide Open

**Location:** `src/backend/app/main.py`

```python
allow_origins=["*"]  # ❌ Should be restricted to frontend domain
```

**Fix Required:** Limit CORS to the frontend domain in production.

---

### 3.9 No WebSocket for Real-Time Updates

**Problem:** Users must poll the API to see:
- Backtest progress
- Simulation signals (new signals only appear on refresh)

**Impact:** Poor UX during long-running operations.

**Fix Required:** Add WebSocket support for real-time updates (Phase 2 or later).

---

## 4. Minor Issues

### 4.1 Unused Dependencies

**Location:** `src/backend/requirements.txt`

```python
anthropic>=0.18.0  # Included but project uses MiniMax
```

**Fix Required:** Remove unused dependency.

---

### 4.2 Missing .env Example

**Problem:** No `.env.example` file to guide deployment.

**Fix Required:** Create `.env.example` with all required variables documented.

---

### 4.3 No Input Sanitization

User-provided data (bot names, chat messages) isn't sanitized before storage or display.

**Fix Required:** Add input validation and sanitization.

---

### 4.4 Inconsistent Error Responses

Some endpoints return `{"detail": "..."}` (FastAPI default), others return custom error shapes.

**Fix Required:** Standardize error response format.

---

### 4.5 No Integration Tests

No tests that verify the full pipeline (chat → config → backtest).

**Fix Required:** Add integration tests.

---

## 5. Missing Documentation Files

The following should be created:

1. **`.env.example`** - All environment variables with descriptions
2. **`docs/STRATEGY_SCHEMA.md`** - Single source of truth for strategy config schema
3. **`docs/API_SCHEMA.md`** - API contract documentation
4. **`init_db.py`** - Database initialization script

---

## 6. Recommendations Summary

### Priority Matrix

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| **P0** | Database tables not created | Small | App crashes on startup |
| **P0** | Bot creation fails | Small | Users can't create bots |
| **P0** | Strategy schema mismatch | Medium | Backtesting completely broken |
| **P0** | Config endpoints empty | Small | No chain/token selection |
| **P1** | Risk management not implemented | Medium | No stop-loss/take-profit |
| **P1** | Chain validation missing | Small | Can use non-BSC chains |
| **P1** | Silent error handling | Small | Hard to debug issues |
| **P2** | Duplicate AveCloudClient | Medium | Maintenance burden |
| **P2** | CORS restricted | Small | Security hardening |
| **P2** | Token blacklist (production) | Medium | Security |
| **P2** | Rate limiting | Medium | DoS protection |
| **P3** | WebSocket support | Large | UX improvement |
| **P3** | Integration tests | Medium | Code quality |

---

## 7. AVE Cloud Integration Notes

### Rate Limit Strategy

| Tier | TPS | Recommended Approach |
|------|-----|---------------------|
| Free | 1 | Aggressive caching, batch requests |
| Normal | 5 | Moderate caching |
| Pro | 20 | Minimal caching |

### Caching Recommendations

1. **Token prices:** Cache for 30-60 seconds
2. **Trending tokens:** Cache for 5-10 minutes
3. **Token details:** Cache for 5-10 minutes
4. **Risk assessments:** Cache for 15-30 minutes

### No Testnet Warning

AVE Cloud has **no testnet**. All API calls use real money:
- Use quote/dry-run mode for testing
- Start with minimal amounts ($1-10)
- Contact AVE support about sandbox options

---

## 8. Next Steps

### Immediate (Before Testing)

1. Add database initialization to startup
2. Fix bot creation (frontend or backend)
3. **Normalize strategy schema** - Choose flat structure, update all components
4. Populate config endpoints with BSC + default tokens
5. Add BSC-only chain validation

### Short Term

6. Implement risk management (stop-loss/take-profit)
7. Consolidate AveCloudClient
8. Add proper error handling
9. Create .env.example
10. Add input sanitization

### Medium Term

11. Add WebSocket for real-time updates
12. Implement production token blacklist (Redis)
13. Apply rate limiting
14. Restrict CORS
15. Add integration tests

---

## 9. Files Reference

### Key Backend Files

| File | Purpose |
|------|---------|
| `src/backend/app/main.py` | FastAPI app initialization |
| `src/backend/app/api/bots.py` | Bot CRUD + chat endpoint |
| `src/backend/app/api/backtest.py` | Backtest API |
| `src/backend/app/api/simulate.py` | Simulation API |
| `src/backend/app/api/ave.py` | AVE Cloud proxy endpoints |
| `src/backend/app/api/config.py` | Config endpoints |
| `src/backend/app/db/schemas.py` | Pydantic schemas |
| `src/backend/app/db/models.py` | SQLAlchemy models |
| `src/backend/app/services/ai_agent/crew.py` | CrewAI agents |
| `src/backend/app/services/ai_agent/llm_connector.py` | MiniMax LLM |
| `src/backend/app/services/backtest/engine.py` | Backtest logic |
| `src/backend/app/services/simulate/engine.py` | Simulation logic |
| `src/backend/app/services/ave/client.py` | AVE Cloud client |

### Key Frontend Files

| File | Purpose |
|------|---------|
| `src/frontend/src/lib/api/client.ts` | API client |
| `src/frontend/src/lib/api/types.ts` | TypeScript types |
| `src/frontend/src/routes/bot/[id]/+page.svelte` | Bot chat page |
| `src/frontend/src/routes/bot/[id]/backtest/+page.svelte` | Backtest page |
| `src/frontend/src/routes/bot/[id]/simulate/+page.svelte` | Simulation page |
| `src/frontend/src/lib/components/ChatInterface.svelte` | Chat UI |
| `src/frontend/src/lib/components/StrategyPreview.svelte` | Strategy display |

---

## 10. Audit Complete

This audit was conducted by reviewing:
- All source code in `src/backend/` and `src/frontend/`
- Documentation in `docs/`
- Database models and schemas
- API endpoints and their implementations

The product has a **solid architectural foundation** and addresses a real market need. The core issues are manageable - primarily schema standardization and missing initialization code.

---

*End of Audit Report*
