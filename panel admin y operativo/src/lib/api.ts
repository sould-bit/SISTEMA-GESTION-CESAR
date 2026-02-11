import axios from 'axios';
import { API_URL } from '../config/env';
import { store } from '../stores/store';
import { logout } from '../stores/auth.slice';
import { setAccessDenied } from '../stores/ui.slice';
import { getPermissionLabel } from '../utils/permissions';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = store.getState().auth.token;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

/**
 * Analiza el error 403 para extraer información del permiso faltante y la acción.
 */
const parseAccessDeniedError = (error: any) => {
    const config = error.config;
    const responseData = error.response?.data;
    const detail = responseData?.detail || '';

    let permissionCode = 'unknown';
    let action = 'Realizar esta operación';

    // 1. Intentar extraer el código del permiso desde el detalle del backend
    // Formato esperado: "Permiso denegado: se requiere 'permission.code'"
    const match = detail.match(/'([^']+)'/);
    if (match && match[1]) {
        permissionCode = match[1];
    }

    // 2. Determinar la acción basada en URL si no se puede inferir del error
    const url = config.url || '';
    const method = config.method?.toUpperCase() || '';

    if (url.includes('/orders')) {
        if (url.includes('/status')) action = 'Actualizar estado de pedido';
        else if (url.includes('/cancel')) action = 'Gestionar cancelación';
        else if (method === 'POST') action = 'Crear un nuevo pedido';
        else action = 'Operar con pedidos';
    } else if (url.includes('/branches')) {
        action = 'Gestionar sucursales';
    } else if (url.includes('/users') || url.includes('/staff')) {
        action = 'Gestionar personal / usuarios';
    } else if (url.includes('/cash')) {
        action = 'Operaciones de caja';
    } else if (url.includes('/products')) {
        action = 'Gestionar productos';
    }

    return {
        action,
        permissionCode,
        permissionLabel: getPermissionLabel(permissionCode)
    };
};

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            if (error.response.status === 401) {
                store.dispatch(logout());
                window.location.href = '/login';
            } else if (error.response.status === 403) {
                const info = parseAccessDeniedError(error);
                const currentState = store.getState().ui;

                console.warn(`⛔ 403 Forbidden: ${info.action}. Requerido: ${info.permissionLabel} (${info.permissionCode})`);

                // No re-abrir si ya hay un error bloqueante o si es la misma información
                if (!currentState.accessDenied || currentState.requiredPermissionCode !== info.permissionCode) {
                    store.dispatch(setAccessDenied({
                        isOpen: true,
                        isBlocking: false,
                        actionName: info.action,
                        requiredPermission: info.permissionLabel,
                        requiredPermissionCode: info.permissionCode !== 'unknown' ? info.permissionCode : undefined
                    }));
                }
            }
        }
        return Promise.reject(error);
    }
);
