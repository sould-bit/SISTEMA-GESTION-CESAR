import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';

import { GenesisPage } from '../features/genesis/GenesisPage';
import { MainLayout } from '../components/layout/MainLayout';
import { ErrorPage } from '../components/ErrorPage';
import { ProtectedRoute } from './ProtectedRoute';
import { PermissionGuard } from './PermissionGuard';
import { DashboardPage } from '../features/admin/DashboardPage';
import { InventoryPage } from '../features/admin/InventoryPage';
import { OrdersPage } from '../features/admin/OrdersPage';
import { CreateOrderPage } from '../features/admin/CreateOrderPage';
import { TablesPage } from '../features/tables/TablesPage';

// Kitchen Module (V4.1 - Recetas Vivas)
import { IngredientManager, RecipesPage, MenuMatrix, RecipeManagerV2 } from '../features/kitchen';
import { IngredientHistoryPage } from '../features/kitchen/pages/IngredientHistoryPage';
import { UnifiedSetupPage } from '../features/setup/UnifiedSetupPage';
import { StaffPage } from '../features/staff/StaffPage';
import { BranchesPage } from '../features/branches/BranchesPage';

export const router = createBrowserRouter([
    {
        path: '/',
        element: <div className="min-h-screen bg-bg-deep text-white"><Outlet /></div>,
        errorElement: <ErrorPage />,
        children: [
            {
                index: true,
                element: <Navigate to="/login" replace />,
            },
            {
                path: 'login',
                element: <LoginPage />,
            },

            {
                path: 'genesis',
                element: <GenesisPage />
            },
            {
                path: 'admin',
                element: <ProtectedRoute />,
                children: [
                    {
                        element: <MainLayout />,
                        children: [
                            {
                                index: true,
                                element: <Navigate to="/admin/dashboard" replace />
                            },
                            {
                                path: 'dashboard',
                                element: <DashboardPage />
                            },
                            {
                                path: 'inventory',
                                element: <PermissionGuard requiredPermission="inventory.read" />,
                                children: [
                                    { index: true, element: <InventoryPage /> }
                                ]
                            },
                            {
                                path: 'tables',
                                element: <PermissionGuard requiredPermission="orders.read" />,
                                children: [
                                    { index: true, element: <TablesPage /> }
                                ]
                            },
                            {
                                path: 'orders',
                                element: <PermissionGuard requiredPermission="orders.read" />,
                                children: [
                                    { index: true, element: <OrdersPage /> },
                                    { path: 'new', element: <CreateOrderPage /> }
                                ]
                            },
                            {
                                path: 'setup',
                                element: <PermissionGuard requiredPermission="settings.read" />,
                                children: [
                                    { index: true, element: <UnifiedSetupPage /> }
                                ]
                            },
                            {
                                path: 'staff',
                                element: <PermissionGuard requiredPermission="users.read" />,
                                children: [
                                    { index: true, element: <StaffPage /> }
                                ]
                            },
                            {
                                path: 'branches',
                                element: <PermissionGuard requiredPermission="branches.read" />,
                                children: [
                                    { index: true, element: <BranchesPage /> }
                                ]
                            }
                        ]
                    }
                ]
            },

            // Kitchen Routes (V4.1 - Cocina & Menú)
            {
                path: 'kitchen',
                element: <ProtectedRoute />,
                children: [
                    {
                        element: <MainLayout />,
                        children: [
                            {
                                index: true,
                                element: <Navigate to="/kitchen/ingredients" replace />
                            },
                            {
                                path: 'ingredients',
                                element: <IngredientManager />
                            },
                            {
                                path: 'ingredients/:id/history',
                                element: <IngredientHistoryPage />
                            },
                            {
                                path: 'recipes',
                                element: <RecipesPage />
                            },
                            {
                                path: 'recipes-v2',
                                element: <RecipeManagerV2 />
                            },
                            {
                                path: 'menu-engineering',
                                element: <MenuMatrix />
                            },


                        ]
                    }
                ]
            }
        ]
    }
]);
