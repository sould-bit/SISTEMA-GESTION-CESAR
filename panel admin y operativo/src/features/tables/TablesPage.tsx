import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table } from './tables.service';
import { OrderDetailsModal } from '../admin/components/OrderDetailsModal';
import { PaymentModal } from '../admin/components/PaymentModal';
import { useQueryClient } from '@tanstack/react-query';
import { useSocket } from '../../components/SocketProvider';
import { useTableOrders } from './useTableOrders';
import { TableCard } from './TableCard';
import { useMachine } from '@xstate/react';
import { tablesMachine } from './tables.machine';

export const TablesPage = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const { socket } = useSocket();

    const [state, send] = useMachine(tablesMachine);
    const { tables, tableOrders, activeTab, selectedOrder } = state.context;

    const [setupCount, setSetupCount] = useState(10);
    const [isPaymentOpen, setIsPaymentOpen] = useState(false);

    // Fetch active orders for all tables via query (we still use this for the Record of orders)
    const { data: updatedTableOrders = {}, refetch: refetchOrders } = useTableOrders(state.context.branchId);

    // Initial fetch handled by machine, but we sync the orders record
    useEffect(() => {
        send({ type: 'REFRESH_ORDERS', tableOrders: updatedTableOrders });
    }, [updatedTableOrders, send]);

    // Listen for real-time order events and send FETCH to machine
    useEffect(() => {
        if (!socket) return;

        const handleOrderEvent = () => {
            console.log('🔄 Machine fetching due to socket event');
            send({ type: 'FETCH' });
            refetchOrders();
        };

        socket.on('order:created', handleOrderEvent);
        socket.on('order:status', handleOrderEvent);

        return () => {
            socket.off('order:created', handleOrderEvent);
            socket.off('order:status', handleOrderEvent);
        };
    }, [socket, send, refetchOrders]);

    // React to machine transitions for navigation
    useEffect(() => {
        if (state.matches('redirectingToNewOrder')) {
            // In XState v5, the event that triggered the current state is not on state.event 
            // We can handle this logic inside the handleTableClick before sending the event
            // or use a more robust approach. For now, we'll keep it simple.
        }
    }, [state.value, navigate]);

    const handleSetup = () => {
        send({ type: 'SETUP_TABLES', count: setupCount });
    };

    const handleTableClick = (table: Table) => {
        if (table.status === 'available' && !tableOrders[table.id]) {
            navigate('/admin/orders/new', {
                state: {
                    tableId: table.id,
                    tableNumber: table.table_number,
                    branchId: table.branch_id,
                    deliveryType: 'dine_in'
                }
            });
            return;
        }
        send({ type: 'SELECT_TABLE', table, tableOrders });
    };

    const handleNewOrder = (type: 'takeaway' | 'delivery') => {
        const targetBranchId = state.context.branchId || 1;
        navigate('/admin/orders/new', {
            state: {
                branchId: targetBranchId,
                deliveryType: type
            }
        });
    };

    if (state.matches('loading')) return <div className="p-8 text-white">Cargando sala...</div>;

    // View: Setup (only if in tables mode and no tables found)
    const showSetup = activeTab === 'tables' && tables.length === 0 && state.matches('idle');

    if (showSetup || state.matches('settingUp')) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8">
                <div className="bg-card-dark p-8 rounded-2xl border border-border-dark max-w-md w-full text-center">
                    <div className="size-16 bg-accent-primary/10 rounded-full flex items-center justify-center text-accent-primary mx-auto mb-6">
                        <span className="material-symbols-outlined text-3xl">table_restaurant</span>
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Configuración Inicial</h2>
                    <p className="text-text-muted mb-6">
                        No hay mesas configuradas. ¿Cuántas mesas deseas habilitar?
                    </p>
                    <div className="flex gap-4 mb-6">
                        <input
                            type="number"
                            min="1"
                            max="50"
                            value={setupCount}
                            onChange={(e) => setSetupCount(Number(e.target.value))}
                            className="w-full bg-input-bg border border-input-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-accent-primary"
                        />
                    </div>
                    <button
                        onClick={handleSetup}
                        className="w-full bg-accent-primary hover:bg-accent-primary/90 text-white font-bold py-3 rounded-lg transition-all"
                    >
                        Generar Mesas
                    </button>
                    {/* Allow skipping setup to go to other tabs */}
                    <button
                        onClick={() => send({ type: 'SET_TAB', tab: 'takeaway' })}
                        className="mt-4 text-xs text-text-muted hover:text-white hover:underline"
                    >
                        Saltar a Para Llevar
                    </button>
                </div>
            </div>
        );
    }

    // Main View
    return (
        <div className="p-6 h-full flex flex-col">
            <header className="mb-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Punto de Venta</h1>
                        <p className="text-text-muted text-sm">Gestión de Sala y Pedidos</p>
                    </div>

                    {activeTab === 'tables' && (
                        <div className="flex gap-2">
                            <button onClick={() => send({ type: 'FETCH' })} className="p-2 text-text-muted hover:text-white bg-card-dark rounded-lg border border-border-dark">
                                <span className="material-symbols-outlined">refresh</span>
                            </button>
                        </div>
                    )}
                </div>

                {/* Tabs */}
                <div className="flex gap-6 border-b border-border-dark">
                    <button
                        onClick={() => send({ type: 'SET_TAB', tab: 'tables' })}
                        className={`pb-3 px-2 text-sm font-bold transition-all border-b-2 ${activeTab === 'tables'
                            ? 'border-accent-primary text-white'
                            : 'border-transparent text-text-muted hover:text-white'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined icon-filled">table_restaurant</span>
                            MESAS
                        </div>
                    </button>
                    <button
                        onClick={() => send({ type: 'SET_TAB', tab: 'takeaway' })}
                        className={`pb-3 px-2 text-sm font-bold transition-all border-b-2 ${activeTab === 'takeaway'
                            ? 'border-accent-primary text-white'
                            : 'border-transparent text-text-muted hover:text-white'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined icon-filled">shopping_bag</span>
                            PARA LLEVAR
                        </div>
                    </button>
                    <button
                        onClick={() => send({ type: 'SET_TAB', tab: 'delivery' })}
                        className={`pb-3 px-2 text-sm font-bold transition-all border-b-2 ${activeTab === 'delivery'
                            ? 'border-accent-primary text-white'
                            : 'border-transparent text-text-muted hover:text-white'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined icon-filled">sports_motorsports</span>
                            DOMICILIOS
                        </div>
                    </button>
                </div>
            </header>

            {/* Content: Tables */}
            {activeTab === 'tables' && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 overflow-y-auto pb-20">
                    {tables.map(table => (
                        <TableCard
                            key={table.id}
                            table={table}
                            orderInfo={tableOrders[table.id]}
                            onClick={() => handleTableClick(table)}
                            onAcceptOrder={() => { }} // Machine handles selection now
                        />
                    ))}
                </div>
            )}

            {/* Content: Takeaway */}
            {activeTab === 'takeaway' && (
                <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-border-dark rounded-2xl bg-card-dark/30 m-4">
                    <span className="material-symbols-outlined text-6xl text-text-muted mb-4">shopping_bag</span>
                    <h3 className="text-xl font-bold text-white mb-2">Pedidos Para Llevar</h3>
                    <p className="text-text-muted mb-6">Crea pedidos rápidos sin asignar número de mesa.</p>
                    <button
                        onClick={() => handleNewOrder('takeaway')}
                        className="bg-accent-primary hover:bg-accent-primary/90 text-white font-bold py-3 px-8 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-accent-primary/20"
                    >
                        <span className="material-symbols-outlined">add</span>
                        Nuevo Pedido
                    </button>
                </div>
            )}

            {/* Content: Delivery */}
            {activeTab === 'delivery' && (
                <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-border-dark rounded-2xl bg-card-dark/30 m-4">
                    <span className="material-symbols-outlined text-6xl text-text-muted mb-4">sports_motorsports</span>
                    <h3 className="text-xl font-bold text-white mb-2">Pedidos a Domicilio</h3>
                    <p className="text-text-muted mb-6">Gestiona órdenes con dirección y datos de cliente.</p>
                    <button
                        onClick={() => handleNewOrder('delivery')}
                        className="bg-accent-primary hover:bg-accent-primary/90 text-white font-bold py-3 px-8 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-accent-primary/20"
                    >
                        <span className="material-symbols-outlined">add</span>
                        Nuevo Domicilio
                    </button>
                </div>
            )}
            {/* Modals */}
            <OrderDetailsModal
                isOpen={state.matches('viewingOrder')}
                onClose={() => send({ type: 'CLOSE_DETAILS' })}
                order={selectedOrder}
                onStatusChange={() => send({ type: 'FETCH' })}
                onOpenPayment={(order) => {
                    send({ type: 'CLOSE_DETAILS' });
                    setIsPaymentOpen(true);
                }}
                onAddItems={(order) => {
                    navigate('/admin/orders/new', {
                        state: {
                            orderId: order.id,
                            tableId: order.table_id,
                            branchId: order.branch_id,
                            deliveryType: order.delivery_type,
                            existingItems: order.items
                        }
                    });
                }}
            />

            <PaymentModal
                isOpen={isPaymentOpen}
                onClose={() => {
                    setIsPaymentOpen(false);
                    send({ type: 'FETCH' });
                }}
                order={selectedOrder}
            />

            {state.matches('fetchingOrder') && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center">
                    <div className="bg-bg-dark p-6 rounded-2xl border border-border-dark flex flex-col items-center gap-4">
                        <div className="w-10 h-10 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-white font-bold">Cargando pedido...</p>
                    </div>
                </div>
            )}
        </div>
    );
};
