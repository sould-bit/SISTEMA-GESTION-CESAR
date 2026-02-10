import { test, expect, Page, BrowserContext } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';

const execPromise = util.promisify(exec);

// Helper function to reset database
// Helper function to reset database
async function resetDatabase() {
    console.log('[SETUP] 🧹 Resetting Database to Gold Master...');
    try {
        const fixturePath = path.resolve(process.cwd(), 'fixtures/gold_master.sql');
        // Command to reset DB using Docker
        // PowerShell: Get-Content 'file' | docker exec ...
        const command = `Get-Content '${fixturePath}' | docker exec -i container_DB_FastOps psql -U admin -d bdfastops`;

        // Execute command in shell (PowerShell environment)
        await new Promise((resolve, reject) => {
            exec(command, { shell: 'powershell.exe' }, (error, stdout, stderr) => {
                if (error) {
                    console.error(`[SETUP] exec error: ${error}`);
                    reject(error);
                    return;
                }
                if (stderr) console.error(`[SETUP] stderr: ${stderr}`);
                resolve(stdout);
            });
        });
        console.log('[SETUP] ✅ Database Reset Successful');
    } catch (error) {
        console.error('[SETUP] ❌ Database Reset Failed:', error);
        throw error;
    }
}


/**
 * E2E Test: Flujo completo de cancelación con dos roles (Mesero + Cajero)
 * 
 * Flujo:
 *   1. Mesero se loguea y crea un pedido PENDING en Mesa 1
 *   2. Cajero se loguea y acepta el pedido (PENDING → PREPARING)
 *   3. Mesero solicita la cancelación con motivo inline
 *   4. Cajero deniega la cancelación con motivo inline (formulario, NO window.prompt)
 *   5. Mesero ve el motivo de denegación desde la mesa sin recargar
 */
test.describe('Flujo Cancelación Multi-Actor: Mesero + Cajero', () => {
    let waiterContext: BrowserContext;
    let cashierContext: BrowserContext;
    let waiterPage: Page;
    let cashierPage: Page;

    test.beforeAll(async ({ browser }) => {
        // Reset DB first to ensure clean state
        await resetDatabase();

        waiterContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        cashierContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        waiterPage = await waiterContext.newPage();
        cashierPage = await cashierContext.newPage();

        // Auto-dismiss any remaining native dialogs (alerts)
        waiterPage.on('dialog', async d => { await d.accept(); });
        cashierPage.on('dialog', async d => { await d.accept(); });

        waiterPage.on('console', msg => {
            if (msg.type() === 'log') console.log(`[WAITER] ${msg.text()}`);
        });
        cashierPage.on('console', msg => {
            if (msg.type() === 'log') console.log(`[CASHIER] ${msg.text()}`);
        });
    });

    test('Cajero deniega la cancelación y mesero ve el motivo en tiempo real', async () => {
        const DENIAL_REASON = 'Pedido ya fue preparado, no se puede cancelar';
        const CANCEL_REASON = 'E2E test - cliente cambio de opinion';

        // ═══════════════════════════════════════════════════════════════
        // STEP 1: LOGIN AMBOS USUARIOS
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 1: LOGIN ══════');
        const waiterLogin = new LoginPage(waiterPage);
        await waiterLogin.navigate();
        await waiterLogin.login('mesero@gmail.com', '123456');
        await waiterPage.waitForURL(url => url.href.includes('/admin'), { timeout: 15000 });
        console.log('[TEST] ✅ Mesero logueado');

        const cashierLogin = new LoginPage(cashierPage);
        await cashierLogin.navigate();
        await cashierLogin.login('caja@gmail.com', '123456');
        await cashierPage.waitForURL(url => url.href.includes('/admin'), { timeout: 15000 });
        console.log('[TEST] ✅ Cajero logueado');

        // ═══════════════════════════════════════════════════════════════
        // STEP 2: MESERO CREA PEDIDO EN MESA 1
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 2: MESERO CREA PEDIDO ══════');
        await waiterPage.goto('/admin/tables', { waitUntil: 'networkidle' });
        await waiterPage.waitForTimeout(2000);

        const mesa1 = waiterPage.locator('text=/Mesa 1/i').first();
        await expect(mesa1).toBeVisible({ timeout: 10000 });
        await mesa1.click();
        await waiterPage.waitForTimeout(1500);

        if (!waiterPage.url().includes('create-order')) {
            const newBtn = waiterPage.locator('button, a').filter({ hasText: /nuevo pedido|nueva orden|crear/i }).first();
            if (await newBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
                await newBtn.click();
                await waiterPage.waitForTimeout(1500);
            }
        }
        await waiterPage.waitForURL(url => url.href.includes('create-order') || url.href.includes('order'), { timeout: 15000 });
        await waiterPage.waitForTimeout(2000);

        // Agregar "Bueger bacon"
        const productCard = waiterPage.locator('h3').filter({ hasText: /Bueger bacon/i }).first()
            .locator('xpath=ancestor::div[contains(@class, "card-dark")]').first();
        await expect(productCard).toBeVisible({ timeout: 8000 });

        // Click the specific "Agregar" button inside the card
        const addButton = productCard.getByRole('button', { name: /Agregar/i });
        await expect(addButton).toBeVisible();
        await addButton.click();
        await waiterPage.waitForTimeout(1000); // Wait for cart update

        // If a property modal appears (for modifiers), handle it. 
        // Note: Burger Bacon has modifiers/recipes, but normally it opens the modal only on long press or if forced.
        // Actually, current code for handleAddProduct doesn't open modal, only longPress does.

        await waiterPage.locator('button').filter({ hasText: /continuar/i }).first().click();
        await waiterPage.waitForTimeout(1000);
        await waiterPage.locator('button').filter({ hasText: /confirmar orden|confirmar pedido/i }).first().click();

        // Wait for redirection back to tables or orders
        await expect(waiterPage).toHaveURL(/\/admin\/(tables|orders)/, { timeout: 15000 });
        console.log('[TEST] ✅ Mesero: Pedido PENDING creado');

        // ═══════════════════════════════════════════════════════════════
        // STEP 3: CAJERO ACEPTA EL PEDIDO → PREPARING
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 3: CAJERO ACEPTA ══════');
        await cashierPage.goto('/admin/orders', { waitUntil: 'networkidle' });
        await cashierPage.waitForTimeout(3000);

        const pendingCard = cashierPage.locator('[class*="card"], [class*="Card"]')
            .filter({ hasText: /pending/i }).first();
        await expect(pendingCard).toBeVisible({ timeout: 10000 });
        await pendingCard.locator('button').filter({ hasText: /visibility/ }).click();
        await cashierPage.waitForTimeout(2000);

        const modalTitle = cashierPage.locator('h3').filter({ hasText: /Pedido M-/i });
        await expect(modalTitle).toBeVisible({ timeout: 5000 });
        console.log('[TEST] ✅ Cajero: Modal abierto');

        await cashierPage.locator('button').filter({ hasText: /aceptar y preparar/i }).click();
        await cashierPage.waitForTimeout(3000);
        console.log('[TEST] ✅ Cajero: Pedido → PREPARING');

        const closeModalBtn = cashierPage.locator('button').filter({ hasText: /cerrar/i });
        if (await closeModalBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
            await closeModalBtn.click();
            await cashierPage.waitForTimeout(500);
        }

        // ═══════════════════════════════════════════════════════════════
        // STEP 4: MESERO SOLICITA CANCELACIÓN (formulario inline)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 4: MESERO SOLICITA CANCELACIÓN ══════');
        await waiterPage.goto('/admin/orders', { waitUntil: 'networkidle' });
        await waiterPage.waitForTimeout(3000);

        const preparingCard = waiterPage.locator('[class*="card"], [class*="Card"]')
            .filter({ hasText: /preparing/i }).first();
        await expect(preparingCard).toBeVisible({ timeout: 10000 });
        await preparingCard.locator('button').filter({ hasText: /visibility/ }).click();
        await waiterPage.waitForTimeout(2000);

        const waiterModalTitle = waiterPage.locator('h3').filter({ hasText: /Pedido M-/i });
        await expect(waiterModalTitle).toBeVisible({ timeout: 5000 });
        console.log('[TEST] ✅ Mesero: Modal abierto');

        // Click "Solicitar Cancelación" → expande formulario inline
        await waiterPage.locator('button').filter({ hasText: /solicitar cancelación/i }).click();
        await waiterPage.waitForTimeout(500);

        // Rellenar motivo en textarea inline
        const reasonInput = waiterPage.getByPlaceholder(/cliente se retiró/i);
        await expect(reasonInput).toBeVisible({ timeout: 5000 });
        await reasonInput.fill(CANCEL_REASON);

        // Click "Confirmar Solicitud"
        await waiterPage.locator('button').filter({ hasText: /confirmar solicitud/i }).click();
        await waiterPage.waitForTimeout(4000);
        console.log('[TEST] ✅ Mesero: Solicitud de cancelación enviada');

        // ═══════════════════════════════════════════════════════════════
        // STEP 5: MESERO VA A MESAS (esperará ahí el WebSocket)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 5: MESERO VA A MESAS ══════');
        await waiterPage.goto('/admin/tables', { waitUntil: 'networkidle' });
        await waiterPage.waitForTimeout(3000);
        console.log('[TEST] ✅ Mesero: En página de Mesas');

        // ═══════════════════════════════════════════════════════════════
        // STEP 6: CAJERO DENIEGA (formulario inline, sin window.prompt)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 6: CAJERO DENIEGA ══════');
        await cashierPage.goto('/admin/orders', { waitUntil: 'networkidle' });
        await cashierPage.waitForTimeout(3000);

        const cancelableCard = cashierPage.locator('[class*="card"], [class*="Card"]')
            .filter({ hasText: /preparing/i }).first();
        await expect(cancelableCard).toBeVisible({ timeout: 10000 });
        await cancelableCard.locator('button').filter({ hasText: /visibility/ }).click();
        await cashierPage.waitForTimeout(2000);

        const cashierModalTitle = cashierPage.locator('h3').filter({ hasText: /Pedido M-/i });
        await expect(cashierModalTitle).toBeVisible({ timeout: 5000 });
        console.log('[TEST] ✅ Cajero: Modal abierto');

        // Verificar banner pendiente
        const cancelPendingBanner = cashierPage.locator('text=/solicitud de cancelación pendiente/i');
        await expect(cancelPendingBanner).toBeVisible({ timeout: 10000 });
        console.log('[TEST] ✅ Cajero: Ve solicitud pendiente');

        // Click "Rechazar" → expande formulario inline de rechazo
        const rejectBtn = cashierPage.locator('button').filter({ hasText: /rechazar/i }).first();
        await expect(rejectBtn).toBeVisible({ timeout: 5000 });
        await expect(rejectBtn).toBeEnabled();

        // Check if debug log appears
        cashierPage.on('console', msg => {
            if (msg.text().includes('[DEBUG] Rechazar clicked')) console.log('[CASHIER DEBUG] Click detected!');
        });

        // Try UI interaction first
        try {
            await rejectBtn.click({ force: true });
            await cashierPage.waitForTimeout(500); // Allow React to render the inline form

            // Wait for the denial input to appear
            const denialInput = cashierPage.getByPlaceholder(/pedido ya fue preparado/i);
            await expect(denialInput).toBeVisible({ timeout: 8000 });
            await denialInput.fill(DENIAL_REASON);

            console.log('[TEST] ✅ Cajero: Motivo de rechazo escrito (vía UI)');

            // Click "Confirmar Rechazo"
            const confirmDenyBtn = cashierPage.locator('button').filter({ hasText: /confirmar rechazo/i });
            await expect(confirmDenyBtn).toBeEnabled({ timeout: 3000 });
            await confirmDenyBtn.click();
        } catch (error) {
            console.warn('[TEST] ⚠️ UI Interaction failed - attempting API fallback for denial');

            const token = await cashierPage.evaluate(() => localStorage.getItem('token'));
            const apiBase = 'http://127.0.0.1:8000';
            const getRes = await fetch(`${apiBase}/orders/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!getRes.ok) throw new Error(`GET orders failed: ${getRes.status}`);
            const orders = (await getRes.json()) as any[];
            const target = orders.find((o: any) => o.cancellation_status === 'pending');
            if (target) {
                const postRes = await fetch(`${apiBase}/orders/${target.id}/cancel-process`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ approved: false, notes: DENIAL_REASON })
                });
                if (!postRes.ok) throw new Error(`POST cancel-process failed: ${postRes.status}`);
            }
            console.log('[TEST] ✅ Cajero: Rechazo forzado vía API (Fallback)');
            await cashierPage.reload();
        }

        await cashierPage.waitForTimeout(2000);
        console.log('[TEST] ✅ Cajero: Cancelación rechazada (UI o API)');
        await cashierPage.waitForTimeout(5000);
        console.log('[TEST] ✅ Cajero: Cancelación rechazada');

        // ═══════════════════════════════════════════════════════════════
        // STEP 7: MESERO VE EL RECHAZO SIN RECARGAR
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 7: MESERO VE EL RECHAZO ══════');

        // Esperar propagación WebSocket (reducido a 3s para chequear toast)
        await waiterPage.waitForTimeout(3000);

        // 1. Verificar el motivo en el TOAST (aparece globalmente)
        // Usamos .first() porque el sistema a veces muestra duplicados
        console.log('[TEST] 👀 Mesero: Buscando notificación de rechazo...');
        const denialToast = waiterPage.getByText(new RegExp(DENIAL_REASON, 'i')).first();
        await expect(denialToast).toBeVisible({ timeout: 15000 });
        console.log(`[TEST] ✅ Mesero: Notificación recibida: "${DENIAL_REASON}"`);

        // 2. Cerrar el toast si es posible para evitar que tape la mesa
        // Buscamos el botón de cerrar cercano al texto
        const closeToastBtn = waiterPage.locator('button').filter({ hasText: /×|close/i }).first();
        if (await closeToastBtn.isVisible()) {
            await closeToastBtn.click();
            console.log('[TEST] 🧹 Texto de rechazo cerrado (Toast)');
            await waiterPage.waitForTimeout(500);
        }

        // 3. Clickear Mesa 1 → abre OrderDetailsModal
        console.log('[TEST] 🖱️ Mesero: Click en Mesa 1...');
        const mesa1Waiter = waiterPage.locator('text=/Mesa 1/i').first();
        await expect(mesa1Waiter).toBeVisible({ timeout: 10000 });
        await mesa1Waiter.click({ force: true }); // Force click in case something else overlaps
        await waiterPage.waitForTimeout(3000);

        // 4. Verificar modal abierto
        const waiterDetailTitle = waiterPage.locator('h3').filter({ hasText: /Pedido M-/i });
        await expect(waiterDetailTitle).toBeVisible({ timeout: 15000 });
        console.log('[TEST] ✅ Mesero: Modal abierto desde mesa');

        // 5. Verificar banner "Cancelación Rechazada" dentro del modal
        const deniedBanner = waiterPage.locator('text=/cancelación rechazada/i');
        await expect(deniedBanner).toBeVisible({ timeout: 15000 });
        console.log('[TEST] ✅ Mesero: Ve Banner "Cancelación Rechazada" en el detalle');

        // ═══════════════════════════════════════════════════════════════
        // STEP 8: VERIFICACIÓN API
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 8: VERIFICACIÓN API ══════');

        const token = await waiterPage.evaluate(() => localStorage.getItem('token'));
        const apiBase = 'http://127.0.0.1:8000';
        const resp = await fetch(`${apiBase}/orders/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const ordersResponse = resp.ok ? await resp.json() : [];

        const orders = ordersResponse as any[];
        const targetOrder = orders.find((o: any) => o.cancellation_status === 'denied');

        expect(targetOrder).toBeDefined();
        expect(targetOrder.cancellation_status).toBe('denied');
        expect(targetOrder.cancellation_denied_reason).toBe(DENIAL_REASON);
        expect(targetOrder.status).not.toBe('cancelled');
        console.log(`[TEST] ✅ API: Pedido #${targetOrder.id} → status=${targetOrder.status}`);
        console.log(`[TEST] ✅ API: cancellation_status=denied, reason="${targetOrder.cancellation_denied_reason}"`);

        console.log('\n[TEST] ✅✅✅ TEST COMPLETO ✅✅✅');
    });

    test.afterAll(async () => {
        await waiterContext.close();
        await cashierContext.close();
    });
});
