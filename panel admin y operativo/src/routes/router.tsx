import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';

// Layout & Core
import { MainLayout } from '../components/layout/MainLayout';
import { ErrorPage } from '../components/ErrorPage';
import { ProtectedRoute } from './ProtectedRoute';
import { PermissionGuard } from './PermissionGuard';

// Loading Component
const PageLoader = () => (
    <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4">
            <div className="size-10 border-4 border-accent-primary/20 border-t-accent-primary rounded-full animate-spin"></div>
            <p className="text-xs font-bold text-accent-primary uppercase tracking-widest animate-pulse">Cargando módulo...</p>
        </div>
    </div>
);

// Lazy Loaded Features
const LoginPage = lazy(() => import('../features/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const GenesisPage = lazy(() => import('../features/genesis/GenesisPage').then(m => ({ default: m.GenesisPage })));
const DashboardPage = lazy(() => import('../features/admin/DashboardPage').then(m => ({ default: m.DashboardPage })));
const InventoryPage = lazy(() => import('../features/admin/InventoryPage').then(m => ({ default: m.InventoryPage })));
const OrdersPage = lazy(() => import('../features/admin/OrdersPage').then(m => ({ default: m.OrdersPage })));
const CreateOrderPage = lazy(() => import('../features/admin/CreateOrderPage').then(m => ({ default: m.CreateOrderPage })));
const TablesPage = lazy(() => import('../features/tables/TablesPage').then(m => ({ default: m.TablesPage })));
const StaffPage = lazy(() => import('../features/staff/StaffPage').then(m => ({ default: m.StaffPage })));
const BranchesPage = lazy(() => import('../features/branches/BranchesPage').then(m => ({ default: m.BranchesPage })));
const UnifiedSetupPage = lazy(() => import('../features/setup/UnifiedSetupPage').then(m => ({ default: m.UnifiedSetupPage })));

// Kitchen Module
const IngredientManager = lazy(() => import('../features/kitchen').then(m => ({ default: m.IngredientManager })));
const RecipesPage = lazy(() => import('../features/kitchen').then(m => ({ default: m.RecipesPage })));
const MenuMatrix = lazy(() => import('../features/kitchen').then(m => ({ default: m.MenuMatrix })));
const RecipeManagerV2 = lazy(() => import('../features/kitchen').then(m => ({ default: m.RecipeManagerV2 })));
const IngredientHistoryPage = lazy(() => import('../features/kitchen/pages/IngredientHistoryPage').then(m => ({ default: m.IngredientHistoryPage })));

const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
    <Suspense fallback={<PageLoader />}>
        {children}
    </Suspense>
);

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
                element: <SuspenseWrapper><LoginPage /></SuspenseWrapper>,
            },
            {
                path: 'genesis',
                element: <SuspenseWrapper><GenesisPage /></SuspenseWrapper>
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
                                element: <SuspenseWrapper><DashboardPage /></SuspenseWrapper>
                            },
                            {
                                path: 'inventory',
                                element: <PermissionGuard requiredPermission="inventory.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><InventoryPage /></SuspenseWrapper> }
                                ]
                            },
                            {
                                path: 'tables',
                                element: <PermissionGuard requiredPermission="orders.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><TablesPage /></SuspenseWrapper> }
                                ]
                            },
                            {
                                path: 'orders',
                                element: <PermissionGuard requiredPermission="orders.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><OrdersPage /></SuspenseWrapper> },
                                    { path: 'new', element: <SuspenseWrapper><CreateOrderPage /></SuspenseWrapper> }
                                ]
                            },
                            {
                                path: 'setup',
                                element: <PermissionGuard requiredPermission="settings.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><UnifiedSetupPage /></SuspenseWrapper> }
                                ]
                            },
                            {
                                path: 'staff',
                                element: <PermissionGuard requiredPermission="users.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><StaffPage /></SuspenseWrapper> }
                                ]
                            },
                            {
                                path: 'branches',
                                element: <PermissionGuard requiredPermission="branches.read" />,
                                children: [
                                    { index: true, element: <SuspenseWrapper><BranchesPage /></SuspenseWrapper> }
                                ]
                            }
                        ]
                    }
                ]
            },
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
                                element: <SuspenseWrapper><IngredientManager /></SuspenseWrapper>
                            },
                            {
                                path: 'ingredients/:id/history',
                                element: <SuspenseWrapper><IngredientHistoryPage /></SuspenseWrapper>
                            },
                            {
                                path: 'recipes',
                                element: <SuspenseWrapper><RecipesPage /></SuspenseWrapper>
                            },
                            {
                                path: 'recipes-v2',
                                element: <SuspenseWrapper><RecipeManagerV2 /></SuspenseWrapper>
                            },
                            {
                                path: 'menu-engineering',
                                element: <SuspenseWrapper><MenuMatrix /></SuspenseWrapper>
                            },
                        ]
                    }
                ]
            }
        ]
    }
]);
