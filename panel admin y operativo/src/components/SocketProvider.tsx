import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { Socket } from 'socket.io-client';
import { useQueryClient } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { RootState } from '../stores/store';
import { getSocket, disconnectSocket } from '../lib/socket';

// Types for order events
interface OrderCreatedEvent {
    id: number;
    order_number: string;
    table_id?: number;
    delivery_type: string;
    status: string;
    total: number;
    items?: Array<{ product_name: string; quantity: number }>;
}

interface OrderStatusEvent {
    order_id: number;
    status: string;
}

interface Notification {
    id: string;
    type: 'order_created' | 'order_status' | 'cancellation_requested';
    title: string;
    message: string;
    orderId?: number;
    timestamp: Date;
}

interface SocketContextValue {
    socket: Socket | null;
    isConnected: boolean;
    notifications: Notification[];
    clearNotification: (id: string) => void;
    clearAllNotifications: () => void;
}

const SocketContext = createContext<SocketContextValue | null>(null);

export const useSocket = () => {
    const context = useContext(SocketContext);
    if (!context) {
        throw new Error('useSocket must be used within a SocketProvider');
    }
    return context;
};

interface SocketProviderProps {
    children: ReactNode;
}

export const SocketProvider = ({ children }: SocketProviderProps) => {
    const [socket, setSocket] = useState<Socket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);

    const token = useSelector((state: RootState) => state.auth.token);
    const queryClient = useQueryClient();

    const clearNotification = useCallback((id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    const clearAllNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
        const newNotification: Notification = {
            ...notification,
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date(),
        };
        setNotifications(prev => [newNotification, ...prev].slice(0, 10)); // Keep max 10

        // Play notification sound
        try {
            const audio = new Audio('/notification.mp3');
            audio.volume = 0.5;
            audio.play().catch(() => {/* Ignore autoplay restrictions */ });
        } catch {
            /* Audio not supported */
        }
    }, []);

    useEffect(() => {
        if (!token) {
            disconnectSocket();
            setSocket(null);
            setIsConnected(false);
            return;
        }

        const socketInstance = getSocket(token);
        setSocket(socketInstance);

        const handleConnect = () => {
            console.log('✅ Socket connected');
            setIsConnected(true);
        };

        const handleDisconnect = () => {
            console.log('❌ Socket disconnected');
            setIsConnected(false);
        };

        const handleOrderCreated = (data: OrderCreatedEvent) => {
            console.log('📦 New order received:', data);

            // Invalidate queries to refresh data
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            queryClient.invalidateQueries({ queryKey: ['tables'] });

            // Add notification
            const tableInfo = data.table_id ? `Mesa ${data.table_id}` : data.delivery_type;
            addNotification({
                type: 'order_created',
                title: '🆕 Nuevo Pedido',
                message: `${data.order_number} - ${tableInfo} - $${data.total.toLocaleString()}`,
                orderId: data.id,
            });
        };

        const handleOrderStatus = (data: OrderStatusEvent) => {
            console.log('📋 Order status changed:', data);

            // Invalidate queries
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            queryClient.invalidateQueries({ queryKey: ['tables'] });
            queryClient.invalidateQueries({ queryKey: ['tableOrders'] });

            // Notify if order is ready
            if (data.status === 'ready') {
                addNotification({
                    type: 'order_status',
                    title: '✅ ¡Pedido Listo!',
                    message: `El pedido #${data.order_id} ya está cocinado y listo para entregar.`,
                    orderId: data.order_id,
                });
            }
        };

        const handleCancellationRequested = (data: { order_id: number; order_number: string; reason: string }) => {
            console.log('🚫 Cancellation request received:', data);

            // Invalidate queries to refresh orders
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });

            // Add prominent notification
            addNotification({
                type: 'cancellation_requested',
                title: '⚠️ Solicitud de Cancelación',
                message: `Pedido ${data.order_number}: "${data.reason || 'Sin motivo'}"`,
                orderId: data.order_id,
            });
        };

        const handleCancellationDenied = (data: { order_id: number; order_number: string; denial_reason: string }) => {
            console.log('❌ Cancellation denied:', data);

            // Invalidate queries to refresh orders
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            queryClient.invalidateQueries({ queryKey: ['tables'] });
            queryClient.invalidateQueries({ queryKey: ['tableOrders'] });

            // Notify waiter that their request was denied
            addNotification({
                type: 'order_status',
                title: '❌ Cancelación Rechazada',
                message: `Pedido ${data.order_number}: "${data.denial_reason || 'Sin motivo'}"`,
                orderId: data.order_id,
            });
        };

        const handleCancellationApproved = (data: { order_id: number; order_number: string }) => {
            console.log('✅ Cancellation approved:', data);

            // Invalidate queries to refresh orders
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            queryClient.invalidateQueries({ queryKey: ['tables'] });
            queryClient.invalidateQueries({ queryKey: ['tableOrders'] });

            // Notify waiter
            addNotification({
                type: 'order_status',
                title: '✅ Cancelación Aprobada',
                message: `El pedido ${data.order_number} ha sido cancelado exitosamente.`,
                orderId: data.order_id,
            });
        };

        socketInstance.on('connect', handleConnect);
        socketInstance.on('disconnect', handleDisconnect);
        socketInstance.on('order:created', handleOrderCreated);
        socketInstance.on('order:status', handleOrderStatus);
        socketInstance.on('order:cancellation_requested', handleCancellationRequested);
        socketInstance.on('order:cancellation_denied', handleCancellationDenied);
        socketInstance.on('order:cancellation_approved', handleCancellationApproved);

        // Check if already connected
        if (socketInstance.connected) {
            setIsConnected(true);
        }

        return () => {
            socketInstance.off('connect', handleConnect);
            socketInstance.off('disconnect', handleDisconnect);
            socketInstance.off('order:created', handleOrderCreated);
            socketInstance.off('order:status', handleOrderStatus);
            socketInstance.off('order:cancellation_requested', handleCancellationRequested);
            socketInstance.off('order:cancellation_denied', handleCancellationDenied);
            socketInstance.off('order:cancellation_approved', handleCancellationApproved);
        };
    }, [token, queryClient, addNotification]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnectSocket();
        };
    }, []);

    return (
        <SocketContext.Provider value={{
            socket,
            isConnected,
            notifications,
            clearNotification,
            clearAllNotifications,
        }}>
            {children}
        </SocketContext.Provider>
    );
};
