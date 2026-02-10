import { test, expect } from '@playwright/test';

test('Minimal test', async ({ page }) => {
    console.log('Minimal test running');
    await page.goto('about:blank');
    expect(1).toBe(1);
});
