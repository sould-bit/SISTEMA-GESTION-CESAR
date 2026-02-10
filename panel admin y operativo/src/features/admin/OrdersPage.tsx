import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { Order, OrderStatus } from './types';
import { OrderCard } from './components/OrderCard';
import { OrderListItem } from './components/OrderListItem';
import { OrderFilters } from './components/OrderFilters';
import { OrderDetailsModal } from './components/OrderDetailsModal';
import { PaymentModal } from './components/PaymentModal';

export const OrdersPage = () => {
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'board' | 'list'>('board');
    const [filter, setFilter] = useState<'all' | 'dine_in' | 'takeaway' | 'delivery'>('all');
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [isDetailsOpen, setIsDetailsOpen] = useState(false);
    const [isPaymentOpen, setIsPaymentOpen] = useState(false);
    const [, setTick] = useState(0);

    const queryClient = useQueryClient();

    // Force re-render every minute to update timers
    useEffect(() => {
        const timer = setInterval(() => setTick(t => t + 1), 60000);
        return () => clearInterval(timer);
    }, []);

    const { data: orders = [], isLoading } = useQuery({
        queryKey: ['activeOrders'],
        queryFn: async () => {
            const res = await api.get<Order[]>('/orders/', {
                params: {
                    status: 'pending,confirmed,preparing,ready,delivered'
                }
            });
            return res.data;
        },
        refetchInterval: 10000,
    });

    const statusMutation = useMutation({
        mutationFn: async ({ id, status }: { id: number, status: OrderStatus }) => {
            const res = await api.patch(`/orders/${id}/status`, { status });
            return res.data;
        },
        onMutate: async ({ id, status }) => {
            await queryClient.cancelQueries({ queryKey: ['activeOrders'] });
            const previousOrders = queryClient.getQueryData<Order[]>(['activeOrders']);

            if (previousOrders) {
                queryClient.setQueryData<Order[]>(['activeOrders'], (old) =>
                    old ? old.map(o => o.id === id ? { ...o, status } : o) : []
                );
            }
            return { previousOrders };
        },
        onError: (_err, _variables, context) => {
            if (context?.previousOrders) {
                queryClient.setQueryData(['activeOrders'], context.previousOrders);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
        }
    });

    const filteredOrders = orders.filter(o => {
        const typeMatch = filter === 'all' ? true : o.delivery_type === filter;

        // Calcular si está pagado
        const totalPaid = o.payments?.reduce((acc, p) => acc + (p.status === 'completed' ? Number(p.amount) : 0), 0) || 0;
        const isPaid = totalPaid >= o.total;

        // Si está entregado Y pagado, se considera finalizado y no se muestra en comandas activas
        if (o.status === 'delivered' && isPaid) return false;

        return typeMatch;
    });

    const counts = {
        all: filteredOrders.length,
        dine_in: filteredOrders.filter(o => o.delivery_type === 'dine_in').length,
        takeaway: filteredOrders.filter(o => o.delivery_type === 'takeaway').length,
        delivery: filteredOrders.filter(o => o.delivery_type === 'delivery').length,
    };

    const columns = [
        { id: 'pending', label: 'Pendientes', color: 'bg-status-alert', statuses: ['pending'] },
        { id: 'preparing', label: 'En Cocina', color: 'bg-accent-secondary', statuses: ['confirmed', 'preparing'] },
        { id: 'ready', label: 'Despacho', color: 'bg-status-success', statuses: ['ready'] },
        { id: 'unpaid', label: 'Por Cobrar', color: 'bg-accent-primary', statuses: ['delivered'] },
    ];

    const handleOpenDetails = (order: Order) => {
        setSelectedOrder(order);
        setIsDetailsOpen(true);
    };

    const handleOpenPayment = (order: Order) => {
        setSelectedOrder(order);
        setIsPaymentOpen(true);
    };

    if (isLoading && orders.length === 0) {
        return (
            <div className="p-8 flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-white font-bold animate-pulse">Cargando comandas...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] gap-6 overflow-hidden">
            {/* Header section */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 shrink-0 px-1">
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tight">Comandas Activas</h1>
                    <p className="text-text-muted text-sm font-medium">Panel de gestión operativa en tiempo real</p>
                </div>

                <div className="flex items-center gap-4">
                    <OrderFilters
                        currentFilter={filter}
                        onFilterChange={setFilter}
                        ordersCount={counts}
                    />

                    <div className="h-8 w-[1px] bg-border-dark hidden sm:block"></div>

                    <div className="flex bg-bg-deep rounded-xl p-1 border border-border-dark">
                        <button
                            onClick={() => setViewMode('board')}
                            className={`p-2 rounded-lg flex items-center transition-all ${viewMode === 'board' ? 'bg-accent-primary text-bg-deep' : 'text-text-muted hover:text-white'}`}
                        >
                            <span className="material-symbols-outlined">view_kanban</span>
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-2 rounded-lg flex items-center transition-all ${viewMode === 'list' ? 'bg-accent-primary text-bg-deep' : 'text-text-muted hover:text-white'}`}
                        >
                            <span className="material-symbols-outlined">view_list</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content Area: Board or List */}
            {viewMode === 'board' ? (
                /* Kanban Board Container */
                <div className="flex-1 overflow-x-auto min-h-0 custom-scrollbar-horizontal pb-4">
                    <div className="flex gap-6 min-w-[1200px] h-full px-1">
                        {columns.map(col => {
                            const colOrders = filteredOrders.filter(o => col.statuses.includes(o.status));
                            return (
                                <div key={col.id} className="flex-1 flex flex-col gap-4 bg-bg-dark/30 rounded-2xl p-2">
                                    <div className="flex items-center justify-between p-3 bg-card-dark rounded-xl border border-border-dark/60 shadow-lg">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2.5 h-2.5 rounded-full ${col.color} shadow-[0_0_8px] shadow-current`}></div>
                                            <span className="font-black text-xs text-white uppercase tracking-widest">{col.label}</span>
                                        </div>
                                        <span className="bg-bg-deep text-accent-primary text-[10px] font-black px-2.5 py-1 rounded-full border border-accent-primary/20">
                                            {colOrders.length}
                                        </span>
                                    </div>
                                    <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar pr-1 pb-4">
                                        {colOrders.map(order => (
                                            <OrderCard
                                                key={order.id}
                                                order={order}
                                                onViewDetail={handleOpenDetails}
                                                onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
                                                onOpenPayment={handleOpenPayment}
                                            />
                                        ))}
                                        {colOrders.length === 0 && (
                                            <div className="h-full flex flex-col items-center justify-center opacity-20 py-20 border-2 border-dashed border-border-dark rounded-3xl mt-2">
                                                <span className="material-symbols-outlined text-4xl mb-2">empty_dashboard</span>
                                                <p className="text-xs font-bold uppercase tracking-widest">Sin Pedidos</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ) : (
                /* List View Container */
                <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar pr-2 pb-4">
                    <div className="flex flex-col gap-4">
                        {filteredOrders.length > 0 ? (
                            filteredOrders.map(order => (
                                <OrderListItem
                                    key={order.id}
                                    order={order}
                                    onViewDetail={handleOpenDetails}
                                    onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
                                    onOpenPayment={handleOpenPayment}
                                />
                            ))
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center opacity-20 py-40 border-2 border-dashed border-border-dark rounded-3xl">
                                <span className="material-symbols-outlined text-6xl mb-4">empty_dashboard</span>
                                <h3 className="text-xl font-black uppercase tracking-widest text-white">No se encontraron pedidos</h3>
                                <p className="text-text-muted mt-2">Prueba cambiando los filtros o esperando nuevas comandas</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Modals */}
            <OrderDetailsModal
                isOpen={isDetailsOpen}
                onClose={() => setIsDetailsOpen(false)}
                order={selectedOrder}
                onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
                onOpenPayment={handleOpenPayment}
                onAddItems={(order) => {
                    navigate('/admin/orders/new', {
                        state: {
                            orderId: order.id,
                            branchId: order.branch_id,
                            deliveryType: order.delivery_type,
                            tableId: order.table_id
                        }
                    });
                }}
                onOrderUpdated={() => {
                    queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
                    // Also refresh selected order if needed, but invalidating activeOrders might re-render parent.
                    // However, selectedOrder is local state. We might need to close modal or update selectedOrder.
                    // For now, allow modal to stay open (it has "close" button).
                    // Actually, if we invalidate 'activeOrders', the 'orders' list updates.
                    // But 'selectedOrder' state is NOT automatically updated unless we sync it.
                    // If the modal shows stale data (e.g. cancellation_status still null), that's bad.
                    // We should probably close the modal or fetch the single order.
                    // The modal shows "Solicitud Enviada" badge if order.cancellation_status === 'pending'.
                    // We need 'selectedOrder' to update.
                    // Let's rely on the user closing the modal or implementing a refetch for selectedOrder.
                    // Simpler: Close the modal on update.
                    setIsDetailsOpen(false);
                }}
            />

            <PaymentModal
                isOpen={isPaymentOpen}
                onClose={() => setIsPaymentOpen(false)}
                order={selectedOrder}
            />
        </div>
    );
};
