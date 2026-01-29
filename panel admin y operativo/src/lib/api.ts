import axios from 'axios';
import { API_URL } from '../config/env';
import { store } from '../stores/store';
import { logout } from '../stores/auth.slice';

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

import { setAccessDenied } from '../stores/ui.slice';

// ... existing code ...

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            if (error.response.status === 401) {
                store.dispatch(logout());
                window.location.href = '/login';
            } else if (error.response.status === 403) {
                console.warn("⛔ 403 Forbidden detected. Dispatching Access Denied...");
                // Bloqueo global de UI cuando se detecta falta de permisos
                store.dispatch(setAccessDenied(true));
            }
        }
        return Promise.reject(error);
    }
);
