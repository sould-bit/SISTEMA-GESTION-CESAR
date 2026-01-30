import { Navigate, Outlet } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../stores/store';
import { setAccessDenied } from '../stores/ui.slice';
import { useEffect } from 'react';

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

    // Handle Access Denied via Redux (Side Effect)
    useEffect(() => {
        if (!isAllowed) {
            dispatch(setAccessDenied({ isOpen: true, isBlocking: true }));
        } else {
            // Ensure we clear the state if we are allowed (e.g. navigation change)
            // But be careful not to clear it if it was set by API error?
            // Actually, if we are in a Guarded Route and we are allowed, we shouldn't implicitly clear it 
            // unless we want to "reset" the view. 
            // Ideally, navigation clears it.
            dispatch(setAccessDenied({ isOpen: false }));
        }

        // Cleanup on unmount seems risky if we navigate away? 
        return () => {
            dispatch(setAccessDenied({ isOpen: false }));
        };
    }, [isAllowed, dispatch, requiredPermission]);

    if (!isAllowed) {
        // Render nothing, MainLayout will handle the overlay via Redux
        return null;
    }

    return <Outlet />;
};
