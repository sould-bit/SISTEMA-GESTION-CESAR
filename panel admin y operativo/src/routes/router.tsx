import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';

import { GenesisPage } from '../features/genesis/GenesisPage';
import { MainLayout } from '../components/layout/MainLayout';
import { ErrorPage } from '../components/ErrorPage';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardPage } from '../features/admin/DashboardPage';
import { InventoryPage } from '../features/admin/InventoryPage';
import { OrdersPage } from '../features/admin/OrdersPage';

// Kitchen Module (V4.1 - Recetas Vivas)
import { IngredientManager, RecipesPage, MenuMatrix } from '../features/kitchen';

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
                                element: <InventoryPage />
                            },
                            {
                                path: 'orders',
                                element: <OrdersPage />
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
                                path: 'recipes',
                                element: <RecipesPage />
                            },
                            {
                                path: 'menu-engineering',
                                element: <MenuMatrix />
                            }
                        ]
                    }
                ]
            }
        ]
    }
]);
