import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Escenario: Verificación de Privilegios de Mesero', () => {
    let adminContext: any;
    let waiterContext: any;
    let adminPage: any;
    let waiterPage: any;

    let adminToken: string;
    let branchId: number;

    // Credentials provided by user
    const adminEmail = 'kate@gmail.com';
    const adminPassword = '123456';
    const waiterEmail = 'mesero@gmail.com';
    const waiterPassword = '123456';

    let serverRoleId: string;
    let ordersUpdatePermId: string;
    let productDetails: any;
    let tableId: number;

    // Unique identifier for this test run resources
    const timestamp = Date.now();
    const tableNumber = Math.floor(timestamp % 10000); // Ensure int for table_number

    test.beforeAll(async ({ request }) => {
        console.log('🔹 Starting Setup with Existing Users');

        // 1. Login as Admin to get Token & Context
        const loginRes = await request.post('http://127.0.0.1:8000/auth/login', {
            data: {
                email: adminEmail,
                password: adminPassword
            }
        });

        if (!loginRes.ok()) {
            const errorText = await loginRes.text();
            console.error(`Login Failed: ${errorText}`);
            throw new Error(`Admin login failed: ${errorText}`);
        }
        const loginData = await loginRes.json();
        if (!loginData.token) {
            throw new Error(`Login failed (no token): ${JSON.stringify(loginData)}`);
        }
        adminToken = loginData.token.access_token;

        // Fetch User Info to get branch_id
        const meRes = await request.get('http://127.0.0.1:8000/auth/me', {
            headers: { Authorization: `Bearer ${adminToken}` }
        });
        expect(meRes.ok(), `Failed to fetch /auth/me: ${await meRes.text()}`).toBeTruthy();
        const meData = await meRes.json();
        branchId = meData.branch_id;
        console.log(`✅ Admin logged in. Branch ID: ${branchId}`);

        // 2. Get Roles and Permissions IDs
        const rolesRes = await request.get('http://127.0.0.1:8000/rbac/roles/', {
            headers: { Authorization: `Bearer ${adminToken}` }
        });
        expect(rolesRes.ok()).toBeTruthy();
        const roles = await rolesRes.json();
        const meseroRole = roles.find((r: any) => r.code === 'server');
        expect(meseroRole, 'Server role not found').toBeDefined();
        serverRoleId = meseroRole.id;

        const permsRes = await request.get('http://127.0.0.1:8000/rbac/permissions', {
            headers: { Authorization: `Bearer ${adminToken}` }
        });
        expect(permsRes.ok()).toBeTruthy();
        const perms = await permsRes.json();
        const updateOrderPerm = perms.find((p: any) => p.code === 'orders.update');
        expect(updateOrderPerm, 'orders.update permission not found').toBeDefined();
        ordersUpdatePermId = updateOrderPerm.id;

        // 3. Ensure Waiter does NOT have the permission initially
        // We accept failure here (404) if the permission doesn't exist on the role
        await request.delete(`http://127.0.0.1:8000/rbac/roles/${serverRoleId}/permissions/${ordersUpdatePermId}`, {
            headers: { Authorization: `Bearer ${adminToken}` }
        }).catch(() => { });

        // 4. Create Test Resources (Category, Product, Table, Order)

        // 4a. Category
        const catRes = await request.post('http://127.0.0.1:8000/categories/', {
            headers: { Authorization: `Bearer ${adminToken}` },
            data: { name: `Cat ${timestamp}`, description: 'Test', is_active: true }
        });
        expect(catRes.ok()).toBeTruthy();
        const category = await catRes.json();

        // 4b. Product
        const prodRes = await request.post('http://127.0.0.1:8000/products/', {
            headers: { Authorization: `Bearer ${adminToken}` },
            data: {
                name: `Prod ${timestamp}`,
                price: 150,
                category_id: category.id,
                description: 'Test Item',
                is_active: true,
                stock: 100
            }
        });
        expect(prodRes.ok()).toBeTruthy();
        productDetails = await prodRes.json();

        // 4c. Table
        const tableRes = await request.post('http://127.0.0.1:8000/tables', {
            headers: { Authorization: `Bearer ${adminToken}` },
            data: {
                table_number: tableNumber,
                seat_count: 2,
                branch_id: branchId
            }
        });
        if (!tableRes.ok()) {
            console.error(`Table creation failed: ${await tableRes.text()}`);
        }
        expect(tableRes.ok()).toBeTruthy();
        const tableData = await tableRes.json();
        tableId = tableData.id;

        // 4d. Order
        const orderRes = await request.post('http://127.0.0.1:8000/orders', {
            headers: { Authorization: `Bearer ${adminToken}` },
            data: {
                branch_id: branchId,
                table_id: tableId,
                items: [
                    { product_id: productDetails.id, quantity: 1, notes: 'Test Note' }
                ],
                customer_notes: 'Permission Test'
            }
        });
        if (!orderRes.ok()) {
            const errorBody = await orderRes.text();
            console.error(`Order creation failed: ${errorBody}`);
            throw new Error(`Critical Setup Error: Cannot create order for test. ${errorBody}`);
        }
        expect(orderRes.ok()).toBeTruthy();
        console.log(`✅ Setup Complete. Order created on Table ${tableNumber}`);
    });

    test.beforeEach(async ({ browser }) => {
        waiterContext = await browser.newContext();
        waiterPage = await waiterContext.newPage();
    });

    test.afterEach(async () => {
        await waiterContext.close();
    });

    test('Mesero debe ver botones solo cuando tiene permisos', async ({ request }) => {
        // --- 1. Login Mesero ---
        const loginWaiter = new LoginPage(waiterPage);
        await loginWaiter.navigate();
        await loginWaiter.login(waiterEmail, waiterPassword);

        // Esperar dashboard
        await expect(waiterPage.getByText('Módulos')).toBeVisible();

        // --- 2. Navegar a Mesas ---
        await waiterPage.getByRole('link', { name: 'Mesas' }).click();
        await waiterPage.waitForLoadState('networkidle');

        // CHECK: Is the waiter actually authorized?
        const isUnauthorized = await waiterPage.getByText(/No autorizado|Permiso denegado|No tienes permiso|Acceso Denegado/i).isVisible();
        if (isUnauthorized) {
            throw new Error(`ERROR CRÍTICO: El mesero (${waiterEmail}) no puede entrar a la pantalla de Mesas (No autorizado). Revisa los permisos de RBAC para el rol correspondientes. Puede ser tables.read u orders.read.`);
        }

        await expect(waiterPage).toHaveURL(/.*tables/);

        // --- 3. Seleccionar la Mesa ---
        // Verify the table exists and click it
        const tableLocator = waiterPage.locator('div').filter({ hasText: new RegExp(`^Mesa ${tableNumber}$`, 'i') }).first();
        // Fallback for different UI (e.g. just text)
        await expect(waiterPage.getByText(`Mesa ${tableNumber}`)).toBeVisible();
        await waiterPage.getByText(`Mesa ${tableNumber}`).click();

        // --- 4. VERIFICAR: Botón "Aceptar" NO debe estar visible (Revoked in beforeAll) ---
        // The button we are looking for is likely "Aceptar" or a checkmark for the order item or the order itself
        const acceptButton = waiterPage.getByRole('button', { name: 'Aceptar' });

        await expect(acceptButton).toBeHidden();
        console.log('✅ Button matches NO PERMISSION state');

        // --- 5. ADMIN otorga permiso ---
        console.log('🔹 Admin granting permission...');
        const grantRes = await request.put(`http://127.0.0.1:8000/rbac/roles/${serverRoleId}/permissions/${ordersUpdatePermId}`, {
            headers: { Authorization: `Bearer ${adminToken}` }
        });
        expect(grantRes.ok(), 'Failed to grant permission').toBeTruthy();

        // --- 6. Reload y Verificar ---
        console.log('🔹 Reloading waiter view...');
        await waiterPage.reload();

        // Re-navigate if needed
        if (!waiterPage.url().includes('tables')) {
            await waiterPage.getByRole('link', { name: 'Mesas' }).click();
        }
        await waiterPage.getByText(`Mesa ${tableNumber}`).click();

        // --- 7. VERIFICAR: Botón "Aceptar" DEBE estar visible ---
        await expect(acceptButton).toBeVisible();
        console.log('✅ Button matches GRANTED PERMISSION state');
    });
});
