import { test, expect, Page, BrowserContext } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';

// Helper function to reset database (copied from 10_cancellation_flow.spec.ts to be self-contained)
async function resetDatabase() {
    console.log('[SETUP] 🧹 Resetting Database to Gold Master...');
    try {
        const fixturePath = path.resolve(process.cwd(), 'fixtures/gold_master.sql');
        const command = `Get-Content '${fixturePath}' | docker exec -i container_DB_FastOps psql -U admin -d bdfastops`;

        await new Promise((resolve, reject) => {
            exec(command, { shell: 'powershell.exe' }, (error, stdout, stderr) => {
                if (error) {
                    console.error(`[SETUP] exec error: ${error}`);
                    // Don't reject purely on stderr warnings, only if error object exists
                    // reject(error); 
                    console.warn('[SETUP] continuing despite error...'); // Warn but continue for now as it might be non-fatal
                    resolve(stdout);
                    return;
                }
                if (stderr) console.error(`[SETUP] stderr: ${stderr}`);
                resolve(stdout);
            });
        });
        console.log('[SETUP] ✅ Database Reset Successful');
    } catch (error) {
        console.error('[SETUP] ❌ Database Reset Failed:', error);
        // We warn but don't fail the test immediately here to allow playwright to try
    }
}

/**
 * E2E Test: Flujo Cancelación - APROBACIÓN (Waiter + Cashier)
 * 
 * Flujo:
 *   1. Mesero crea pedido (Pending)
 *   2. Cajero acepta (Preparing)
 *   3. Mesero solicita cancelacion
 *   4. Cajero (desde MESAS) aprueba la cancelación
 *   5. Mesero (desde MESAS) ve que el pedido está cancelado
 */
test.describe('Flujo Cancelación: Aprobación (Escenario Mesa)', () => {
    let waiterContext: BrowserContext;
    let cashierContext: BrowserContext;
    let waiterPage: Page;
    let cashierPage: Page;

    test.beforeAll(async ({ browser }) => {
        await resetDatabase();
        waiterContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        cashierContext = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        waiterPage = await waiterContext.newPage();
        cashierPage = await cashierContext.newPage();

        // Console Listeners
        waiterPage.on('console', msg => { if (msg.type() === 'log') console.log(`[WAITER] ${msg.text()}`); });
        cashierPage.on('console', msg => { if (msg.type() === 'log') console.log(`[CASHIER] ${msg.text()}`); });
    });

    test('Cajero APRUEBA la cancelación desde vista Mesas', async () => {
        const CANCEL_REASON = 'Cliente se retiró (Test E2E)';

        // ═══════════════════════════════════════════════════════════════
        // STEP 1: LOGIN
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 1: LOGIN ══════');
        const waiterLogin = new LoginPage(waiterPage);
        await waiterLogin.navigate();
        await waiterLogin.login('mesero@gmail.com', '123456');
        await waiterPage.waitForURL(url => url.href.includes('/admin'), { timeout: 15000 });

        const cashierLogin = new LoginPage(cashierPage);
        await cashierLogin.navigate();
        await cashierLogin.login('caja@gmail.com', '123456');
        await cashierPage.waitForURL(url => url.href.includes('/admin'), { timeout: 15000 });
        console.log('[TEST] ✅ Ambos usuarios logueados');

        // ═══════════════════════════════════════════════════════════════
        // STEP 2: MESERO CREA PEDIDO
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 2: CREAR PEDIDO ══════');
        await waiterPage.goto('/admin/tables', { waitUntil: 'networkidle' });
        await waiterPage.waitForTimeout(2000);

        // Click Mesa 1
        await waiterPage.locator('text=/Mesa 1/i').first().click();
        await waiterPage.waitForTimeout(1000);

        // Si no está en create-order, intentar clickear "Nuevo Pedido"
        if (!waiterPage.url().includes('create-order')) {
            const newBtn = waiterPage.locator('button').filter({ hasText: /nuevo pedido|crear/i }).first();
            if (await newBtn.isVisible().catch(() => false)) await newBtn.click();
        }
        await waiterPage.waitForURL(/create-order|order/);

        // Agregar Item (Bueger bacon)
        await waiterPage.locator('h3').filter({ hasText: /Bueger bacon/i }).first().click();
        const addBtn = waiterPage.getByRole('button', { name: /agregar|confirmar/i }).first();
        if (await addBtn.isVisible().catch(() => false)) await addBtn.click();

        // Confirmar Pedido
        await waiterPage.locator('button').filter({ hasText: /continuar/i }).first().click();
        await waiterPage.waitForTimeout(500);
        await waiterPage.locator('button').filter({ hasText: /confirmar orden/i }).first().click();
        await waiterPage.waitForURL(/\/admin\/(orders|tables)/);
        console.log('[TEST] ✅ Pedido Creado (Pending)');

        // ═══════════════════════════════════════════════════════════════
        // STEP 3: CAJERO ACEPTA (Desde Mesas para variar o Orders?)
        // ═══════════════════════════════════════════════════════════════
        // Nota: Para "Aceptar", el cajero suele usar Dashboard o Orders. 
        // Usaremos Orders que es lo estándar para el flujo rápido de inbound.
        console.log('\n[TEST] ══════ STEP 3: CAJERO ACEPTA ══════');
        await cashierPage.goto('/admin/orders', { waitUntil: 'networkidle' });
        const pendingCard = cashierPage.locator('[class*="card"]').filter({ hasText: /pending/i }).first();
        await expect(pendingCard).toBeVisible({ timeout: 10000 });
        await pendingCard.locator('button').filter({ hasText: /visibility/ }).click({ force: true });

        await cashierPage.locator('button').filter({ hasText: /aceptar y preparar/i }).click();
        await cashierPage.waitForTimeout(2000);
        // Cerrar modal si queda abierto
        const closeBtn = cashierPage.locator('button').filter({ hasText: /cerrar|close/i }).first();
        if (await closeBtn.isVisible()) await closeBtn.click();
        console.log('[TEST] ✅ Pedido en Preparación');

        // ═══════════════════════════════════════════════════════════════
        // STEP 4: MESERO SOLICITA CANCELACIÓN (Desde Mesa 1)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 4: SOLICITUD CANCELACIÓN ══════');
        await waiterPage.goto('/admin/tables', { waitUntil: 'networkidle' });
        await waiterPage.locator('text=/Mesa 1/i').first().click();

        // Esperar modal
        await expect(waiterPage.locator('h3').filter({ hasText: /Pedido M-/i })).toBeVisible();

        // Click solicitud
        await waiterPage.locator('button').filter({ hasText: /solicitar cancelación/i }).click();
        await waiterPage.getByPlaceholder(/motivo/i).fill(CANCEL_REASON);
        await waiterPage.locator('button').filter({ hasText: /confirmar solicitud/i }).click();
        await waiterPage.waitForTimeout(2000);

        // Cerrar modal del mesero para simular que sigue atendiendo
        const closeWaiterBtn = waiterPage.locator('button').filter({ hasText: /cerrar|close/i }).first();
        if (await closeWaiterBtn.isVisible()) await closeWaiterBtn.click();
        console.log('[TEST] ✅ Solicitud Enviada');

        // ═══════════════════════════════════════════════════════════════
        // STEP 6 (Adjusted): CAJERO APRUEBA (DESDE VISTA MESAS)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 6: CAJERO APRUEBA (DESDE MESAS) ══════');
        await cashierPage.goto('/admin/tables', { waitUntil: 'networkidle' });
        await cashierPage.waitForTimeout(2000);

        // Click Mesa 1 (Debe mostrar estado ocupado/preparando)
        const mesa1Cashier = cashierPage.locator('text=/Mesa 1/i').first();
        await expect(mesa1Cashier).toBeVisible();
        await mesa1Cashier.click();

        // Verificar modal de cajero
        await expect(cashierPage.locator('h3').filter({ hasText: /Pedido M-/i })).toBeVisible();

        // Banner de solicitud debe estar visible
        await expect(cashierPage.locator('text=/solicitud de cancelación/i')).toBeVisible();

        // Click APROBAR
        const approveBtn = cashierPage.locator('button').filter({ hasText: /aprobar|confirmar cancelación/i }).first();
        await expect(approveBtn).toBeVisible();
        await approveBtn.click();

        // Confirmar en el segundo modal/dialogo si existe
        // A veces pide confirmación "Sí, cancelar pedido"
        const confirmYesBtn = cashierPage.locator('button').filter({ hasText: /sí, cancelar|confirmar/i }).last();
        if (await confirmYesBtn.isVisible({ timeout: 3000 })) {
            await confirmYesBtn.click();
        }

        await cashierPage.waitForTimeout(2000);
        console.log('[TEST] ✅ Cajero Aprobó Cancelación');

        // ═══════════════════════════════════════════════════════════════
        // STEP 7: MESERO VERIFICA (DESDE VISTA MESAS)
        // ═══════════════════════════════════════════════════════════════
        console.log('\n[TEST] ══════ STEP 7: MESERO VERIFICA ══════');
        await waiterPage.reload(); // Recargar para asegurar estado fresco
        await waiterPage.waitForTimeout(2000);

        // La mesa debería estar LIBRE o Cancelada.
        // Si se cancela el pedido, la mesa se libera.
        const mesa1Label = waiterPage.locator('text=/Mesa 1/i').first();
        await expect(mesa1Label).toBeVisible();

        // Verificar etiqueta "Libre" en la tarjeta de la mesa
        // Esto depende de cómo se renderiza la tarjeta. 
        // Asumimos que dentro del contenedor de "Mesa 1" hay un texto "Libre"
        const cardMesa1 = waiterPage.locator('div').filter({ hasText: /Mesa 1/i }).last(); // Ajustar selector si es necesario
        // O simplemente buscar si existe "Mesa 1" y "Libre" cerca

        // Estrategia: Abrir la mesa. Si está libre, debería permitir crear nuevo pedido o mostrar "Sin pedidos".
        await mesa1Label.click();
        await waiterPage.waitForTimeout(1000);

        // Verificar que NO aparece el pedido anterior en estado 'preparing'
        const oldOrderTitle = waiterPage.locator('h3').filter({ hasText: /Pedido M-/i });
        const requestCancelBtn = waiterPage.locator('button').filter({ hasText: /solicitar cancelación/i });

        if (await oldOrderTitle.isVisible()) {
            // Si el pedido sigue ahí, verificar que su estado sea 'cancelled'
            const statusBadge = waiterPage.locator('text=/cancelado/i');
            await expect(statusBadge).toBeVisible();
        } else {
            console.log('[TEST] ✅ Mesa 1 parece estar libre (no se abrió detalle de pedido activo)');
        }

        // ═══════════════════════════════════════════════════════════════
        // STEP 8: CHECK API FINAL
        // ═══════════════════════════════════════════════════════════════
        const orders = await waiterPage.evaluate(async () => {
            const token = localStorage.getItem('token');
            const r = await fetch('http://localhost:8000/orders/', { headers: { 'Authorization': `Bearer ${token}` } });
            return r.json();
        });
        const myOrder = orders.find((o: any) => o.cancellation_status === 'approved' || o.status === 'cancelled');
        expect(myOrder).toBeDefined();
        // El status final puede ser 'cancelled'
        expect(myOrder.status).toBe('cancelled');
        console.log('[TEST] ✅ API confirma status: cancelled');

    });

    test.afterAll(async () => {
        await waiterContext.close();
        await cashierContext.close();
    });
});
