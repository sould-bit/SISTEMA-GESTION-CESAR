import { Page, expect } from '@playwright/test';

export class OrderDetailsModal {
    constructor(private page: Page) { }

    // Locators
    private cancelRequestBtn = () => this.page.getByRole('button', { name: /solicitar cancelación/i });
    private denyCancelBtn = () => this.page.getByRole('button', { name: /rechazar/i });
    private approveCancelBtn = () => this.page.getByRole('button', { name: /aprobar/i });
    private reasonInput = () => this.page.getByPlaceholder(/cliente se retiró/i);
    private confirmRequestBtn = () => this.page.getByRole('button', { name: /confirmar solicitud/i });

    async requestCancellation(reason: string) {
        await this.cancelRequestBtn().click();
        await this.reasonInput().fill(reason);
        await this.confirmRequestBtn().click();
        // The modal might close or show an alert. In the implementation it shows alert and closes.
        // Handling the alert is handled by Playwright defaults or we can handle it explicitly.
    }

    async denyWithReason(reason: string) {
        // The frontend used window.prompt() for the denial reason
        this.page.once('dialog', async dialog => {
            await dialog.accept(reason);
        });
        await this.denyCancelBtn().click();
    }

    async approveCancellation() {
        // The frontend uses window.confirm() for approval
        this.page.once('dialog', async dialog => {
            await dialog.accept();
        });
        await this.approveCancelBtn().click();
    }

    async expectDenialReason(reason: string) {
        // Validar que el banner de rechazo contenga el texto
        const banner = this.page.locator('text=Cancelación Rechazada');
        await expect(banner).toBeVisible();
        await expect(this.page.locator(`text="${reason}"`)).toBeVisible();
    }

    async expectCancelled() {
        // If approved, the order status should change to CANCELLED in the header or the modal should reflect it.
        // In the implementation, handleProcessCancellation calls alert and onClose.
        // So we might need to check the table grid or reopen the modal.
        await expect(this.page.locator('text=Solicitud aprobada correctamente')).toBeVisible({ timeout: 5000 });
    }
}
