
import { test, expect, request } from '@playwright/test';
import { resetDatabase } from '../utils/db/reset';

test.describe('Genesis Protocol (Registration & Seeding)', () => {

    test.beforeAll(async () => {
        console.log('⚠️ Running against Live Environment. NO RESET performed.');
    });

    test('should register company and seed operational data', async ({ page }) => {
        // --- PART 1: GENESIS REGISTRATION ---

        await page.goto('/genesis');

        // Step 1: Foundation
        await expect(page.getByRole('heading', { name: 'Fundación' })).toBeVisible();
        await page.getByPlaceholder('Ej. Corporación Stark').fill('FastFood Demo');
        await page.getByPlaceholder('Ej. 900.123.456-7').fill('900.123.456-7');
        await page.getByPlaceholder('Ej. Tony Stark').fill('Juan Admin');
        await page.getByPlaceholder('Ej. +57 300 123 4567').fill('+573001234567');
        await page.getByRole('button', { name: 'Establecer Cimientos' }).click();

        // Step 2: Territory
        await expect(page.getByRole('heading', { name: 'Nexo Territorial' })).toBeVisible();
        await page.getByPlaceholder('Ej. Sede Central - Norte').fill('Sede Principal');
        await page.getByPlaceholder('Ej. Av. Principal #123').fill('Calle 123 #45-67');
        await page.getByRole('button', { name: 'Establecer Base' }).click();

        // Step 3: Auth
        await expect(page.getByRole('heading', { name: 'Credenciales de Acceso' })).toBeVisible();
        await expect(page.getByPlaceholder('Ej. Tony Stark')).toHaveValue('Juan Admin');

        const adminEmail = 'admin@fastfood.com';
        const adminPass = 'password123';
        const companySlug = 'fastfood-demo';

        await page.getByPlaceholder('Ej. ironman').fill('admin_fastfood');
        await page.getByPlaceholder('admin@imperio.com').fill(adminEmail);
        await page.getByPlaceholder('••••••••').fill(adminPass);

        // Intercept registration to get token
        const registerPromise = page.waitForResponse(resp => resp.url().includes('/auth/register') && resp.status() === 200);
        await page.getByRole('button', { name: 'Registrar' }).click();

        const registerResponse = await registerPromise;
        const registerData = await registerResponse.json();
        console.log('⚠️ DEBUG REGISTER RESPONSE:', JSON.stringify(registerData, null, 2));
        const authToken = registerData.access_token;
        expect(authToken, `Token missing. Response: ${JSON.stringify(registerData)}`).toBeTruthy();

        console.log('✅ Registration Successful. Token acquired.');

        // Wait for redirection
        await expect(page).toHaveURL(/\/admin\/staff/);


        // --- PART 2: DATA SEEDING VIA API ---
        console.log('🌱 Seeding Operational Data via API...');

        // Create API Context
        const api = await request.newContext({
            baseURL: 'http://127.0.0.1:8001',
            extraHTTPHeaders: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        // 1. Get Roles & Branch IDs
        const rolesRes = await api.get('/roles/');
        expect(rolesRes.ok()).toBeTruthy();
        const roles = await rolesRes.json();
        const waiterRole = roles.find((r: any) => r.code === 'waiter');
        const kitchenRole = roles.find((r: any) => r.code === 'kitchen');

        const branchesRes = await api.get('/branches/');
        expect(branchesRes.ok()).toBeTruthy();
        const branches = await branchesRes.json();
        const mainBranch = branches[0]; // The one created during genesis

        console.log(`   - Roles & Branch loaded (Branch ID: ${mainBranch.id})`);

        // 2. Create Users (Waiter & Kitchen)
        const waiterUser = {
            email: 'waiter@test.com',
            username: 'waiter_test',
            password: 'password123',
            full_name: 'Waiter Test',
            role_id: waiterRole.id,
            branch_id: mainBranch.id,
            is_active: true
        };
        await api.post('/users/', { data: waiterUser });

        const kitchenUser = {
            email: 'kitchen@test.com',
            username: 'kitchen_test',
            password: 'password123',
            full_name: 'Kitchen Test',
            role_id: kitchenRole.id,
            branch_id: mainBranch.id,
            is_active: true
        };
        await api.post('/users/', { data: kitchenUser });
        console.log('   - Users created (waiter & kitchen)');

        // 3. Create Categories
        const catRes = await api.post('/products/categories/', {
            data: { name: 'Hamburguesas', description: 'Best burgers' }
        });
        const category = await catRes.json();

        // 4. Create Product
        const prodRes = await api.post('/products/', {
            data: {
                name: 'Hamburguesa Clásica',
                description: 'Carne 150g',
                price: 15.00,
                category_id: category.id,
                tax_rate: 0,
                is_active: true,
                type: 'finished'
            }
        });
        const product = await prodRes.json();
        console.log('   - Product created');

        // 5. Create Tables
        const tableRes = await api.post('/tables/', {
            data: {
                table_number: 1,
                capacity: 4,
                location: 'Main Hall',
                branch_id: mainBranch.id
            }
        });
        const table = await tableRes.json();

        // 6. Create Demo Order (Confirmed)
        // We need to login as Waiter to create order? Or Admin can do it?
        // Admin has 'orders.create' permission, so they can do it.
        const orderRes = await api.post('/orders/', {
            data: {
                branch_id: mainBranch.id,
                table_id: table.id,
                customer_count: 2,
                items: [
                    { product_id: product.id, quantity: 2, notes: 'Sin cebolla' }
                ]
            }
        });
        const order = await orderRes.json();

        // Confirm Order to make it available for cancellation flow
        // The API likely has a status update endpoint
        await api.patch(`/orders/${order.id}/status`, {
            data: { status: 'confirmed' }
        });

        console.log(`   - Order ${order.order_number} created & confirmed`);
        console.log('✅ Data Seeding Complete');
    });

});
