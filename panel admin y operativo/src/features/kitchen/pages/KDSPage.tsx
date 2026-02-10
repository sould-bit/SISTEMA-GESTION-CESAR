import { useEffect, useState } from 'react';
import { useSocket } from '../../../components/SocketProvider';
import { api } from '../../../lib/api';
import { Order } from '../../admin/types';
import { KitchenOrderCard } from '../components/KitchenOrderCard';
import { UtensilsCrossed, Wifi, WifiOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const KDSPage = () => {
    const { socket, isConnected } = useSocket();
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'pending' | 'preparing' | 'ready'>('all');

    const fetchActiveOrders = async () => {
        try {
            // Fetch only active statuses (Including confirmed which is the step before preparing)
            const response = await api.get('/orders?status=pending,confirmed,preparing,ready&limit=50');
            if (Array.isArray(response.data)) {
                setOrders(response.data);
            } else {
                console.error('Invalid orders response format:', response.data);
                setOrders([]);
            }
        } catch (error) {
            console.error('Error fetching orders:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchActiveOrders();

        if (socket) {
            const handleNewOrder = (newOrder: Order) => {
                setOrders(prev => {
                    // Avoid duplicates
                    if (prev.find(o => o.id === newOrder.id)) return prev;
                    return [...prev, newOrder];
                });
                // Optional: Play sound
            };

            const handleStatusUpdate = (updatedOrder: { order_id: number; status: string }) => {
                setOrders(prev => {
                    // If status is final/delivered, remove it (or keep it if you want history)
                    if (['delivered', 'cancelled'].includes(updatedOrder.status)) {
                        return prev.filter(o => o.id !== updatedOrder.order_id);
                    }

                    return prev.map(o =>
                        o.id === updatedOrder.order_id
                            ? { ...o, status: updatedOrder.status as any }
                            : o
                    );
                });
            };

            const handleCancellationRequest = (data: { order_id: number; reason: string }) => {
                setOrders(prev => prev.map(o =>
                    o.id === data.order_id
                        ? { ...o, cancellation_status: 'pending', cancellation_reason: data.reason }
                        : o
                ));
            };

            socket.on('kitchen:new_order', handleNewOrder);
            socket.on('order:created', handleNewOrder); // Fallback if kitchen specific event fails
            socket.on('order:status', handleStatusUpdate);
            socket.on('order:cancellation_requested', handleCancellationRequest);

            return () => {
                socket.off('kitchen:new_order', handleNewOrder);
                socket.off('order:created', handleNewOrder);
                socket.off('order:status', handleStatusUpdate);
                socket.off('order:cancellation_requested', handleCancellationRequest);
            };
        }
    }, [socket]);

    const filteredOrders = orders.filter(o => {
        if (filter === 'all') return true;
        return o.status === filter;
    }).sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    return (
        <div className="min-h-screen bg-bg-deep p-6">
            {/* Header */}
            <header className="mb-8 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-primary text-white shadow-lg shadow-accent-primary/20">
                        <UtensilsCrossed size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Monitor de Cocina</h1>
                        <p className="text-sm text-text-secondary">
                            {orders.length} pedidos activos
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Connection Status */}
                    <div className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold ${isConnected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                        {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                        {isConnected ? 'CONECTADO' : 'DESCONECTADO'}
                    </div>

                    {/* Filters */}
                    <div className="flex rounded-lg bg-bg-card p-1 border border-white/5">
                        {(['all', 'pending', 'preparing', 'ready'] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${filter === f
                                    ? 'bg-accent-primary text-white shadow-md'
                                    : 'text-text-secondary hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                {f === 'all' ? 'Todos' : f.charAt(0).toUpperCase() + f.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            {/* Grid */}
            {loading ? (
                <div className="flex h-64 items-center justify-center text-text-secondary">
                    Cargando pedidos...
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    <AnimatePresence mode='popLayout'>
                        {filteredOrders.map((order) => (
                            <motion.div
                                key={order.id}
                                layout
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                transition={{ duration: 0.2 }}
                            >
                                <KitchenOrderCard order={order} />
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {filteredOrders.length === 0 && (
                        <div className="col-span-full flex flex-col items-center justify-center py-20 text-text-muted opacity-50">
                            <UtensilsCrossed size={48} className="mb-4" />
                            <p className="text-lg">No hay pedidos pendientes</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
