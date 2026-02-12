import { useMemo, useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { Clock, CheckCircle, AlertTriangle, XCircle, Play, Info, Loader2 } from 'lucide-react';
import { Order } from '../../admin/types';
import { useSocket } from '../../../components/SocketProvider';
import { api } from '../../../lib/api';
import { useOrderPermissions } from '../../../hooks/useOrderPermissions';
import { ConfirmModal } from '../../../components/ConfirmModal';
import { useMachine } from '@xstate/react';
import { orderMachine } from '../order.machine';
import { inspector } from '../../../lib/inspector';

interface KitchenOrderCardProps {
    order: Order;
}

export const KitchenOrderCard = ({ order }: KitchenOrderCardProps) => {
    const [confirmModal, setConfirmModal] = useState<{ type: 'approve' | 'deny'; onConfirm: (value?: string) => Promise<void> } | null>(null);
    const { isConnected: _ } = useSocket();
    const { canAcceptOrder, canMarkReady } = useOrderPermissions();

    const [state, send] = useMachine(orderMachine, {
        input: { order },
        inspect: inspector?.inspect
    });

    // Keep machine in sync with prop updates (from sockets)
    useEffect(() => {
        send({ type: 'UPDATE_ORDER', order });
    }, [order, send]);

    const currentOrder = state.context.order;
    const isUpdating = state.matches('updating');

    const timeElapsed = useMemo(() => {
        try {
            return formatDistanceToNow(new Date(currentOrder.created_at), { addSuffix: true, locale: es });
        } catch (e) {
            return 'Hace un momento';
        }
    }, [currentOrder.created_at]);

    const isCancellationPending = currentOrder.cancellation_status === 'pending';

    // Status Colors
    const statusColor = {
        pending: 'border-yellow-500/50 bg-yellow-500/5 hover:border-yellow-400',
        confirmed: 'border-blue-500/50 bg-blue-500/5 hover:border-blue-400',
        preparing: 'border-purple-500/50 bg-purple-500/5 hover:border-purple-400',
        ready: 'border-green-500/50 bg-green-500/5 hover:border-green-400',
        delivered: 'border-gray-500/50 bg-gray-500/5 opacity-50',
        cancelled: 'border-red-500/50 bg-red-500/5 opacity-50'
    }[currentOrder.status] || 'border-gray-500/50';

    const handleCancellationProcess = (approved: boolean) => {
        if (approved) {
            setConfirmModal({
                type: 'approve',
                onConfirm: async () => {
                    try {
                        await api.post(`/orders/${currentOrder.id}/cancel-process`, { approved: true, notes: 'Aprobado desde KDS' });
                    } catch (error) {
                        console.error('Failed to process cancellation:', error);
                    }
                },
            });
        } else {
            setConfirmModal({
                type: 'deny',
                onConfirm: async (value) => {
                    const notes = value?.trim() || 'Sin motivo especificado';
                    try {
                        await api.post(`/orders/${currentOrder.id}/cancel-process`, { approved: false, notes });
                    } catch (error) {
                        console.error('Failed to process cancellation:', error);
                    }
                },
            });
        }
    };

    return (
        <>
            <div className={`relative flex flex-col justify-between rounded-xl border-l-4 bg-bg-card p-4 shadow-lg transition-all hover:translate-y-[-2px] hover:shadow-xl ${statusColor}`}>

                {/* Header */}
                <div>
                    <div className="mb-3 flex items-start justify-between">
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold text-white">#{currentOrder.order_number.slice(-4)}</span>
                                {currentOrder.table_id && (
                                    <span className="rounded bg-accent-primary/20 px-2 py-0.5 text-xs font-bold text-accent-primary">
                                        Mesa {currentOrder.table_id}
                                    </span>
                                )}
                                {currentOrder.delivery_type !== 'dine_in' && (
                                    <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs font-bold text-blue-400 capitalize">
                                        {currentOrder.delivery_type.replace('_', ' ')}
                                    </span>
                                )}
                            </div>
                            <div className="mt-1 flex items-center gap-1 text-xs text-text-secondary">
                                <Clock size={12} />
                                <span>{timeElapsed}</span>
                            </div>
                        </div>

                        {/* Status Badge */}
                        <div className="text-right">
                            <span className={`text-xs font-bold uppercase tracking-wider ${currentOrder.status === 'ready' ? 'text-green-400' :
                                currentOrder.status === 'preparing' ? 'text-purple-400' :
                                    'text-yellow-400'
                                }`}>
                                {isUpdating ? 'Actualizando...' : currentOrder.status}
                            </span>
                            <div className="text-[10px] text-text-muted mt-0.5">{currentOrder.created_by_name || 'Staff'}</div>
                        </div>
                    </div>

                    {/* Cancellation Alert Overlay */}
                    {isCancellationPending && currentOrder.status !== 'cancelled' && (
                        <div className="mb-4 animate-pulse rounded-lg border border-red-500/30 bg-red-500/10 p-3">
                            <div className="flex items-center gap-2 text-red-400 mb-2">
                                <AlertTriangle size={16} />
                                <span className="font-bold">Solicitud de Cancelación</span>
                            </div>
                            <p className="text-sm text-text-secondary mb-3 italic">
                                "{currentOrder.cancellation_reason || 'Sin motivo'}"
                            </p>
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => handleCancellationProcess(false)}
                                    className="flex items-center justify-center gap-2 rounded-lg bg-gray-700/50 px-3 py-2 text-xs font-bold text-white hover:bg-gray-700 transition-colors"
                                >
                                    <XCircle size={14} /> RECHAZAR
                                </button>
                                <button
                                    onClick={() => handleCancellationProcess(true)}
                                    className="flex items-center justify-center gap-2 rounded-lg bg-red-500/20 px-3 py-2 text-xs font-bold text-red-400 hover:bg-red-500/30 transition-colors"
                                >
                                    <CheckCircle size={14} /> APROBAR
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Items List */}
                    <div className="space-y-3 overflow-y-auto pr-1 custom-scrollbar max-h-[300px]">
                        {currentOrder.items.map((item) => (
                            <div key={item.id} className="border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                <div className="flex items-start justify-between">
                                    <span className="font-medium text-text-primary text-sm">
                                        <span className="text-accent-primary mr-1 font-bold">{item.quantity}x</span>
                                        {item.product_name}
                                    </span>
                                </div>

                                {/* Modifiers & Notes */}
                                <div className="ml-5 mt-1 space-y-0.5 text-xs">
                                    {item.modifiers?.map((mod, idx) => (
                                        <div key={idx} className="flex items-center gap-1 text-green-400/90">
                                            <span className="size-1 rounded-full bg-green-500"></span>
                                            <span>{mod.modifier?.name || 'Modificador'}</span>
                                            {mod.quantity > 1 && <span className="text-[10px] opacity-75">({mod.quantity}x)</span>}
                                        </div>
                                    ))}

                                    {item.removed_ingredients?.map((removed, idx) => (
                                        <div key={idx} className="flex items-center gap-1 text-red-400/90">
                                            <span className="size-1 rounded-full bg-red-500"></span>
                                            <span className="line-through decoration-red-500/50">Sin {removed}</span>
                                        </div>
                                    ))}

                                    {item.notes && (
                                        <div className="mt-1 flex gap-1 text-yellow-400/90 italic bg-yellow-400/5 p-1 rounded">
                                            <Info size={12} className="shrink-0 mt-[1px]" />
                                            <span>{item.notes}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer Actions */}
                {!isCancellationPending && currentOrder.status !== 'cancelled' && currentOrder.status !== 'delivered' && (
                    <div className="mt-4 pt-3 border-t border-white/5">
                        {currentOrder.status === 'pending' && canAcceptOrder && (
                            <button
                                onClick={() => send({ type: 'CONFIRM' })}
                                disabled={isUpdating}
                                className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-sm font-bold text-white hover:bg-blue-500 disabled:opacity-50 transition-all active:scale-[0.98] shadow-lg shadow-blue-600/20"
                            >
                                {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                                Confirmar Pedido
                            </button>
                        )}

                        {currentOrder.status === 'confirmed' && canAcceptOrder && (
                            <button
                                onClick={() => send({ type: 'PREPARE' })}
                                disabled={isUpdating}
                                className="w-full flex items-center justify-center gap-2 rounded-lg bg-accent-primary px-4 py-3 text-sm font-bold text-white hover:bg-accent-active disabled:opacity-50 transition-all active:scale-[0.98] shadow-lg shadow-accent-primary/20"
                            >
                                {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
                                Empezar Preparación
                            </button>
                        )}

                        {currentOrder.status === 'preparing' && canMarkReady && (
                            <button
                                onClick={() => send({ type: 'READY' })}
                                disabled={isUpdating}
                                className="w-full flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-sm font-bold text-white hover:bg-green-500 disabled:opacity-50 transition-all active:scale-[0.98] shadow-lg shadow-green-600/20"
                            >
                                {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                                Pedido Listo
                            </button>
                        )}

                        {currentOrder.status === 'ready' && (
                            <div className="text-center p-2 text-sm font-medium text-green-400 animate-pulse bg-green-400/5 rounded-lg border border-green-400/20">
                                Esperando entrega...
                            </div>
                        )}
                    </div>
                )}
            </div>

            {confirmModal && (
                <ConfirmModal
                    isOpen={!!confirmModal}
                    onClose={() => setConfirmModal(null)}
                    title="Confirmar acción"
                    message={confirmModal.type === 'approve'
                        ? '¿Está seguro de aprobar la cancelación?'
                        : 'Ingrese el motivo del rechazo:'}
                    confirmText="Aceptar"
                    cancelText="Cancelar"
                    onConfirm={confirmModal.onConfirm}
                    promptPlaceholder={confirmModal.type === 'deny' ? 'Motivo del rechazo...' : undefined}
                />
            )}
        </>
    );
};
