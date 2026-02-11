import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../stores/store';
import { setCredentials } from '../../stores/auth.slice';
import { api } from '../../lib/api';

/**
 * Componente que inicializa y refresca la sesión del usuario al cargar la app.
 * Asegura que los permisos estén siempre actualizados con el backend.
 */
export const SessionInitializer = () => {
    const dispatch = useAppDispatch();
    const { token, isAuthenticated } = useAppSelector(state => state.auth);

    useEffect(() => {
        const refreshSession = async () => {
            if (!isAuthenticated || !token) return;

            try {
                // Obtener datos frescos del usuario y sus permisos
                const response = await api.get('/auth/me');

                dispatch(setCredentials({
                    token: token,
                    user: response.data
                }));

                console.log("✅ Sesión sincronizada con éxito");
            } catch (error) {
                console.error("❌ Error al sincronizar sesión:", error);
                // Si el error es 401, el interceptor de api.ts ya manejará el logout
            }
        };

        refreshSession();

        // Intervalo de refresco cada 5 minutos (opcional)
        const interval = setInterval(refreshSession, 1000 * 60 * 5);
        return () => clearInterval(interval);
    }, [dispatch, isAuthenticated, token]);

    return null; // Este componente no renderiza nada
};
