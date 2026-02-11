
import { test, expect, request } from '@playwright/test';

test.describe('Order Permissions Check KDS', () => {

    let viewerUser: any;
    let serverUser: any;
    let testOrder: any;

    const generateRandomString = (length = 6) => Math.random().toString(36).substring(2, 2 + length);

    test.beforeAll(async ({ }) => {
        const apiContext = await request.newContext({ baseURL: 'http://127.0.0.1:8001' });

        // 1. Register New Company (Fresh Admin)
        const slug = `test-perm-${generateRandomString()}`;
        const adminEmail = `admin-${slug}@test.com`;
        const adminPass = 'password123';

        console.log(`🚀 Registering new company: ${slug}`);
        const regPayload = {
            company_name: `Test Company ${slug}`,
            company_slug: slug,
            owner_name: 'Admin Test',
            username: `admin_${slug}`,
            owner_email: adminEmail,
            password: adminPass,
            plan: 'free'
        };

        const regRes = await apiContext.post('/auth/register', { data: regPayload });
        if (!regRes.ok()) {
            console.error('Registration failed:', await regRes.text());
            throw new Error('Registration failed');
        }
        const regData = await regRes.json();
        const authToken = regData.access_token;
        console.log('✅ Registered & Logged in as Admin');

        const adminContext = await request.newContext({
            baseURL: 'http://127.0.0.1:8001',
            extraHTTPHeaders: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        // 2. Fetch Permissions to get IDs
        const permsRes = await adminContext.get('/rbac/permissions');
        if (!permsRes.ok()) {
            throw new Error(`Failed to fetch permissions: ${await permsRes.text()}`);
        }
        const permissionsList = await permsRes.json();
        const getPermissionId = (code: string) => {
            const p = permissionsList.find((perm: any) => perm.code === code);
            if (!p) throw new Error(`Permission code not found: ${code}`);
            return p.id;
        };

        // 3. Create Test Roles
        // Viewer Role: No orders.update (Only read)
        const viewerRolePayload = {
            name: 'Test Viewer',
            code: 'test_viewer',
            description: 'Viewer for testing',
            permission_ids: [
                getPermissionId('orders.read'),
                getPermissionId('products.read')
            ]
        };
        const viewerRoleRes = await adminContext.post('/rbac/roles/', { data: viewerRolePayload });
        if (!viewerRoleRes.ok()) throw new Error(`Failed to create viewer role: ${await viewerRoleRes.text()}`);
        const viewerRole = await viewerRoleRes.json();

        // Server Role: Has orders.update
        const serverRolePayload = {
            name: 'Test Server',
            code: 'test_server',
            description: 'Server for testing',
            permission_ids: [
                getPermissionId('orders.read'),
                getPermissionId('orders.update'),
                getPermissionId('products.read')
            ]
        };
        const serverRoleRes = await adminContext.post('/rbac/roles/', { data: serverRolePayload });
        if (!serverRoleRes.ok()) throw new Error(`Failed to create server role: ${await serverRoleRes.text()}`);
        const serverRole = await serverRoleRes.json();

        // 4. Get Branch
        const branchesRes = await adminContext.get('/branches/');
        const branches = await branchesRes.json();
        const mainBranch = branches[0];

        // 5. Create Users
        const vRes = await adminContext.post('/users/', {
            data: {
                email: `viewer-${slug}@test.com`,
                username: `viewer-${slug}`,
                password: 'password123',
                full_name: 'Viewer Test',
                role_id: viewerRole.id,
                branch_id: mainBranch.id,
                is_active: true
            }
        });
        if (!vRes.ok()) throw new Error(`Failed to create viewer user: ${await vRes.text()}`);
        viewerUser = await vRes.json();
        viewerUser.password = 'password123';

        const sRes = await adminContext.post('/users/', {
            data: {
                email: `server-${slug}@test.com`,
                username: `server-${slug}`,
                password: 'password123',
                full_name: 'Server Test',
                role_id: serverRole.id,
                branch_id: mainBranch.id,
                is_active: true
            }
        });
        if (!sRes.ok()) throw new Error(`Failed to create server user: ${await sRes.text()}`);
        serverUser = await sRes.json();
        serverUser.password = 'password123';

        // 6. Create Product & Order
        const catsRes = await adminContext.get('/categories/');
        let cats = await catsRes.json();
        let categoryId;
        if (cats.length > 0) categoryId = cats[0].id;
        else {
            const cRes = await adminContext.post('/categories/', { data: { name: 'Test Cat', is_active: true } });
            categoryId = (await cRes.json()).id;
        }

        const prodRes = await adminContext.post('/products/', {
            data: {
                name: `Burger ${slug}`,
                price: 100,
                category_id: categoryId,
                is_active: true
            }
        });
        const product = await prodRes.json();

        const orderPayload = {
            branch_id: mainBranch.id,
            customer_count: 1,
            delivery_type: 'dine_in',
            items: [{ product_id: product.id, quantity: 1 }]
        };
        const orderRes = await adminContext.post('/orders/', { data: orderPayload });
        testOrder = await orderRes.json();
        console.log('✅ Created Test Order:', testOrder.order_number);
    });

    test('Viewer Role (No orders.update) cannot see action buttons on KDS', async ({ page }) => {
        if (!viewerUser) test.skip();

        await page.goto('/login');
        await page.getByPlaceholder('Usuario').fill(viewerUser.username);
        await page.getByPlaceholder('Contraseña').fill(viewerUser.password);
        await page.getByRole('button', { name: /Iniciar Sesión|Login/i }).click();

        // Wait for redirect and navigate to KDS
        await page.waitForURL(/\/admin|\/kitchen/);
        await page.goto('/kitchen/display');

        // Locate the order card
        const orderCard = page.locator(`text=#${testOrder.order_number.slice(-4)}`).locator('..').locator('..').locator('..').locator('..');
        // Better locator strategy: find the container that has the order number

        // Wait for orders to load
        await expect(page.getByText(`#${testOrder.order_number.slice(-4)}`)).toBeVisible({ timeout: 10000 });

        // Filter valid card
        const card = page.locator('.bg-bg-card').filter({ hasText: `#${testOrder.order_number.slice(-4)}` }).first();
        await expect(card).toBeVisible();

        // Verify buttons are HIDDEN
        // "Confirmar Pedido" appears for pending orders if user has permission
        await expect(card.getByRole('button', { name: /Confirmar Pedido/i })).toBeHidden();
        await expect(card.getByRole('button', { name: /Empezar Preparación/i })).toBeHidden();
        await expect(card.getByRole('button', { name: /Pedido Listo/i })).toBeHidden();
    });

    test('Server Role (Has orders.update) CAN see action buttons on KDS', async ({ page }) => {
        if (!serverUser) test.skip();

        await page.goto('/login');
        await page.getByPlaceholder('Usuario').fill(serverUser.username);
        await page.getByPlaceholder('Contraseña').fill(serverUser.password);
        await page.getByRole('button', { name: /Iniciar Sesión|Login/i }).click();

        await page.waitForURL(/\/admin|\/kitchen/);
        await page.goto('/kitchen/display');

        await expect(page.getByText(`#${testOrder.order_number.slice(-4)}`)).toBeVisible({ timeout: 10000 });
        const card = page.locator('.bg-bg-card').filter({ hasText: `#${testOrder.order_number.slice(-4)}` }).first();
        await expect(card).toBeVisible();

        // Verify "Confirmar Pedido" IS VISIBLE (since order is pending)
        await expect(card.getByRole('button', { name: /Confirmar Pedido/i })).toBeVisible();
    });

});
