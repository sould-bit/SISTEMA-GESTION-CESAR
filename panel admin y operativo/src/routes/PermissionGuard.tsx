import { Navigate, Outlet } from 'react-router-dom';
import { useAppSelector } from '../stores/store';
import { AccessDenied } from '../features/shared/AccessDenied';

interface Props {
    requiredPermission?: string;
    allowedRoles?: string[];
}

export const PermissionGuard = ({ requiredPermission, allowedRoles }: Props) => {
    const { user } = useAppSelector(state => state.auth);

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // 1. Admin Bypass - Admins can access everything
    if (user.role_code === 'admin' || user.role === 'admin') {
        return <Outlet />;
    }

    let isAllowed = true;

    // 2. Check Required Permission
    if (requiredPermission) {
        // If user has no permissions array or doesn't have the specific permission
        if (!user.permissions?.includes(requiredPermission)) {
            isAllowed = false;
        }
    }

    // 3. Check Allowed Roles
    if (allowedRoles && allowedRoles.length > 0) {
        const userRole = user.role_code || user.role;
        if (!allowedRoles.includes(userRole)) {
            isAllowed = false;
        }
    }

    // 4. Default Allow (if no props)
    // If neither prop is passed, we assume the route is just authenticated (Protected)
    // which is already handled by user check above.

    if (!isAllowed) {
        return <AccessDenied isBlocking={true} />;
    }

    return <Outlet />;
};
