# Open Issues

## Frontend

### Token Address Confirmation Dialog
- **Priority**: High
- **Status**: Open
- **Description**: When user configures a trading strategy via chat and mentions a token (e.g., "buy PEPE"), the AI asks for the token contract address. The frontend should show a confirmation dialog allowing user to:
  1. See the token the AI detected (PEPE)
  2. Enter/confirm the BSC contract address
  3. Save the strategy with the confirmed address

**Related Files**:
- Frontend: `src/frontend/src/routes/bot/[id]/+page.svelte`
- Backend: `src/backend/app/services/ai_agent/conversational.py`

**Acceptance Criteria**:
- [ ] Modal/dialog appears when AI detects a token without address
- [ ] User can enter the contract address (0x...)
- [ ] Strategy is saved only after user confirmation
- [ ] Clear error handling if address is invalid

---

## Backend

*No open backend issues*
