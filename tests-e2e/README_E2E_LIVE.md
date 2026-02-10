# E2E Tests on Live Environment

This configuration runs Playwright tests directly against your running local environment.

## Prerequisites

1. **Backend Running**: Must be accessible at `http://localhost:8000`.
2. **Frontend Running**: Must be accessible at `http://localhost:5173`.
3. **Database Data**:
    - For `10_cancellation_flow.spec.ts`:
        - Users `waiter@test.com` and `admin@test.com` (password `password123`) must exist.
        - An active order must exist on Table 1 (or the table selected in the test).

## Execution

Run the tests using the orchestrator (which now simply wraps Playwright):

```bash
npx tsx tests-e2e/start-e2e.ts
```

Or specific test:

```bash
npx tsx tests-e2e/start-e2e.ts tests-e2e/specs/10_cancellation_flow.spec.ts
```

**WARNING**: These tests execute actions on your LIVE database. They do NOT reset the database automatically.
