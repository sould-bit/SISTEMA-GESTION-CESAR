import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/stores/store';

export const ProtectedRoute = () => {
    const { isAuthenticated, token } = useAppSelector((state) => state.auth);
    const location = useLocation();

    // Verificación básica: Si no hay token o flag isAuthenticated es falso
    if (!isAuthenticated || !token) {
        // Redirigir al login, guardando la ubicación intentada para volver después
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <Outlet />;
};
