import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import { MainLayout } from '../components/layout/MainLayout';
import { ErrorPage } from '../components/ErrorPage';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardPage } from '../features/admin/DashboardPage';

export const router = createBrowserRouter([
    {
        path: '/',
        element: <div className="min-h-screen bg-asphalt text-white"><Outlet /></div>,
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
                path: 'register',
                element: <RegisterPage />
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
                                path: 'products',
                                element: <div>Products CRUD</div>
                            },
                            {
                                path: 'dashboard',
                                element: <DashboardPage />
                            }
                        ]
                    }
                ]
            }
        ]
    }
]);
