import { Navigate, Outlet } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../stores/store';
import { setAccessDenied } from '../stores/ui.slice';
import { useEffect } from 'react';
import { getPermissionLabel } from '../utils/permissions';

interface Props {
    requiredPermission?: string;
    allowedRoles?: string[];
}

export const PermissionGuard = ({ requiredPermission, allowedRoles }: Props) => {
    const { user } = useAppSelector(state => state.auth);
    const dispatch = useAppDispatch();

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

    // Handle Access Denied via Redux (Side Effect)
    useEffect(() => {
        if (!isAllowed) {
            dispatch(setAccessDenied({
                isOpen: true,
                isBlocking: true,
                requiredPermission: getPermissionLabel(requiredPermission),
                requiredPermissionCode: requiredPermission,
                actionName: "Acceso a sección protegida"
            }));
        } else {
            dispatch(setAccessDenied({ isOpen: false }));
        }

        return () => {
            dispatch(setAccessDenied({ isOpen: false }));
        };
    }, [isAllowed, dispatch, requiredPermission]);

    if (!isAllowed) {
        return null; // El overlay se maneja globalmente
    }

    return <Outlet />;
};
