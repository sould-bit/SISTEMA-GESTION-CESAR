import { Page, expect } from '@playwright/test';

export class LoginPage {
    constructor(private page: Page) { }

    async navigate() {
        await this.page.goto('/');
    }

    async login(email: string, password: string) {
        console.log(`[LOGIN] Attempting login for ${email}...`);

        // Wait for elements to be ready
        await this.page.waitForSelector('#email', { state: 'visible' });

        await this.page.fill('#email', email);
        await this.page.fill('#password', password);

        await Promise.all([
            this.page.click('button[type="submit"]'),
            // Wait for response or navigation
        ]);

        console.log(`[LOGIN] Clicked submit for ${email}. Waiting for transition...`);

        const companySelector = this.page.getByText(/Elige tu destino/i);
        const errorMessage = this.page.locator('.text-status-alert'); // Based on LoginPage.tsx

        try {
            await Promise.race([
                this.page.waitForURL(url => !url.href.includes('login'), { timeout: 15000 }),
                companySelector.waitFor({ state: 'visible', timeout: 5000 }),
                errorMessage.waitFor({ state: 'visible', timeout: 5000 })
            ]);

            if (await errorMessage.isVisible()) {
                const text = await errorMessage.innerText();
                console.error(`[LOGIN ERROR] Backend rejected ${email}: ${text}`);
                throw new Error(`Login failed for ${email}: ${text}`);
            }

            if (await companySelector.isVisible()) {
                console.log(`[LOGIN] Multi-tenant detected for ${email}. Selecting first company.`);
                // Click the first option button
                await this.page.locator('button').filter({ hasText: /.*/ }).nth(0).click();
                await this.page.waitForURL(url => !url.href.includes('login'), { timeout: 15000 });
            }
        } catch (error) {
            console.error(`[LOGIN FATAL] failed for ${email}:`, error);
            // Take diagnostic screenshot if possible? (Playwright does this on failure usually)
            throw error;
        }

        await expect(this.page).not.toHaveURL(/.*login/);
        console.log(`[LOGIN] Successful for ${email}`);
    }
}
