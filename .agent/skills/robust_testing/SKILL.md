---
name: Robust Testing
description: Standards and best practices for writing reliable, flake-free E2E tests with Playwright.
---

# Robust Testing Guidelines

## 1. Avoid Static Waits (`waitForTimeout`)
Never use `page.waitForTimeout(5000)` unless absolutely necessary for debugging.
Instead, use **auto-retrying assertions** or explicit waits for state:
- **Bad:** `await page.waitForTimeout(5000);`
- **Good:** `await expect(page.locator('.my-element')).toBeVisible({ timeout: 10000 });`
- **Good:** `await page.waitForURL(/\/dashboard/);`
- **Good:** `await page.waitForResponse(resp => resp.url().includes('/api/orders') && resp.status() === 200);`

## 2. Dynamic Data Cleanup
Tests must be self-contained or explicitly clean up their data.
- **Ideally:** Reset DB to a known state before/after suites (using `tests-e2e/fixtures/gold_master.sql`).
- **Alternatively:** Create unique data per test (e.g., `const user = "user_${Date.now()}@test.com"`) to avoid collisions.

## 3. Selectors Best Practices
Prioritize user-facing attributes over CSS classes:
1. `page.getByRole('button', { name: /submit/i })`
2. `page.getByLabel('Email')`
3. `page.getByPlaceholder('Enter your name')`
4. `page.getByText('Welcome')`
5. **Avoid:** `page.locator('div > div:nth-child(3) > span')` (Brittle!)
6. **Acceptable:** `page.locator('[data-testid="submit-btn"]')`

## 4. Visual Debugging & Tracing
Enable tracing in `playwright.config.ts` to debug failures easily:
```ts
use: {
  trace: 'on-first-retry',
  video: 'retain-on-failure',
  screenshot: 'only-on-failure',
}
```

## 5. Handling Network Requests
Don't just wait for UI; wait for the underlying network request to complete:
```ts
// Start waiting for response BEFORE clicking
const responsePromise = page.waitForResponse(resp => resp.url().includes('/api/login') && resp.status() === 200);
await page.getByRole('button', { name: /login/i }).click();
await responsePromise; // Wait for the promise to resolve
```

## 6. Authentication State
Re-use authentication state via `storageState` to speed up tests, instead of logging in via UI every time (unless testing the login flow itself).

## 7. Mobile & Responsive Testing
Ensure tests run on mobile viewports if the app is responsive.
```ts
test.use({ viewport: { width: 375, height: 667 } });
```
