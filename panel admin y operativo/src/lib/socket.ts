import { io, Socket } from 'socket.io-client';
import { WS_URL } from '../config/env';

let socket: Socket | null = null;

/**
 * Get or create a Socket.IO connection.
 * @param token JWT access token for authentication
 */
export const getSocket = (token: string): Socket => {
    if (!socket) {
        socket = io(WS_URL, {
            auth: { token },
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        socket.on('connect', () => {
            console.log('🔌 WebSocket connected:', socket?.id);
        });

        socket.on('disconnect', (reason) => {
            console.log('🔌 WebSocket disconnected:', reason);
        });

        socket.on('connect_error', (error) => {
            console.error('🔌 WebSocket connection error:', error.message);
        });
    }
    return socket;
};

/**
 * Disconnect and cleanup the socket instance.
 */
export const disconnectSocket = (): void => {
    if (socket) {
        socket.disconnect();
        socket = null;
        console.log('🔌 WebSocket disconnected and cleaned up');
    }
};

/**
 * Check if socket is currently connected.
 */
export const isSocketConnected = (): boolean => {
    return socket?.connected ?? false;
};
