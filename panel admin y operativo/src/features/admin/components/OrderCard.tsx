import { useState } from 'react';
import { Order, OrderStatus } from '../types';
import { differenceInMinutes } from 'date-fns';
import { api } from '../../../lib/api';
import { ConfirmModal } from '../../../components/ConfirmModal';

interface OrderCardProps {
    order: Order;
    onViewDetail: (order: Order) => void;
    onStatusChange: (orderId: number, newStatus: OrderStatus) => void;
    onOpenPayment: (order: Order) => void;
}

const getStatusBadgeStyles = (status: string) => {
    switch (status) {
        case 'pending': return 'bg-status-alert/10 text-status-alert border-status-alert/20';
        case 'confirmed': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        case 'preparing': return 'bg-accent-secondary/10 text-accent-secondary border-accent-secondary/20';
        case 'ready': return 'bg-status-success/10 text-status-success border-status-success/20';
        case 'delivered': return 'bg-accent-primary/10 text-accent-primary border-accent-primary/20';
        default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
};

const getDeliveryBadgeStyles = (type: string) => {
    switch (type) {
        case 'dine_in': return 'bg-accent-primary/10 text-accent-primary border-accent-primary/20';
        case 'takeaway': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
        case 'delivery': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
};

const getElapsedTime = (dateString: string) => {
    const start = new Date(dateString);
    const now = new Date();
    const diffMs = Math.max(0, now.getTime() - start.getTime());
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

import { useOrderPermissions } from '../../../hooks/useOrderPermissions';

export const OrderCard = ({ order, onViewDetail, onStatusChange, onOpenPayment }: OrderCardProps) => {
    const [confirmModal, setConfirmModal] = useState<{ type: 'approve' | 'deny'; onConfirm: (value?: string) => Promise<void> } | null>(null);
    const { canAcceptOrder, canMarkReady, canDeliver, canProcessCancellation: canProcess, canOpenPayment } = useOrderPermissions();

    const isCancellationPending = order.cancellation_status === 'pending';
    const canProcessCancellation = isCancellationPending && canProcess;

    const handleCancellationProcess = (approved: boolean, e: React.MouseEvent) => {
        e.stopPropagation();
        if (approved) {
            setConfirmModal({
                type: 'approve',
                onConfirm: async () => {
                    try {
                        await api.post(`/orders/${order.id}/cancel-process`, { approved: true, notes: 'Aprobado desde Panel' });
                        onStatusChange(order.id, order.status);
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
                        await api.post(`/orders/${order.id}/cancel-process`, { approved: false, notes });
                        onStatusChange(order.id, order.status);
                    } catch (error) {
                        console.error('Failed to process cancellation:', error);
                    }
                },
            });
        }
    };

    const minutesWaiting = differenceInMinutes(new Date(), new Date(order.created_at));
    const isHighPriority = minutesWaiting > 15 && order.status !== 'delivered' && order.status !== 'cancelled';

    const totalPaid = order.payments?.reduce((acc, p) => acc + (p.status === 'completed' ? Number(p.amount) : 0), 0) || 0;
    const isPaid = totalPaid >= order.total;

    const getNextStatus = (current: OrderStatus): OrderStatus | null => {
        switch (current) {
            case 'pending': return 'preparing';
            case 'confirmed': return 'preparing';
            case 'preparing': return 'ready';
            case 'ready': return 'delivered';
            default: return null;
        }
    };

    const nextStatus = getNextStatus(order.status);

    const getStatusActionLabel = (status: OrderStatus) => {
        switch (status) {
            case 'preparing': return 'Preparar';
            case 'ready': return '¡Listo!';
            case 'delivered': return 'Entregar';
            default: return '';
        }
    };

    // Permission logic for the next status button (based on orders.update)
    const canChangeStatus = () => {
        if (!nextStatus) return false;
        if (nextStatus === 'preparing') return canAcceptOrder || canMarkReady;
        if (nextStatus === 'ready') return canMarkReady;
        if (nextStatus === 'delivered') return canDeliver;
        return false;
    };

    return (
        <>
            <div
                onClick={() => onViewDetail(order)}
                className={`
                bg-card-dark p-4 rounded-xl border border-border-dark hover:border-accent-primary/50 transition-all cursor-pointer group shadow-lg flex flex-col h-full
                ${isHighPriority ? 'border-l-4 border-l-status-alert ring-1 ring-status-alert/10' : ''}
                ${(order.status === 'delivered' && !isPaid) ? 'border-accent-primary/40 shadow-xl shadow-accent-primary/5' : ''}
            `}
            >
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <h4 className="font-bold text-white text-sm">
                            {order.table_id ? `Mesa ${order.table_id}` : (order.delivery_type === 'takeaway' ? 'Para Llevar' : 'Domicilio')}
                        </h4>
                        <div className="flex gap-2 mt-1">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${getDeliveryBadgeStyles(order.delivery_type)}`}>
                                {order.delivery_type.toUpperCase()}
                            </span>
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${getStatusBadgeStyles(order.status)}`}>
                                {order.status.toUpperCase()}
                            </span>
                        </div>
                        <p className="text-text-muted text-[10px] font-mono mt-1 uppercase">{order.order_number}</p>
                    </div>
                    <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded bg-bg-deep font-mono ${isHighPriority ? 'text-status-alert animate-pulse' : 'text-status-success'}`}>
                        <span className="material-symbols-outlined text-[14px]">timer</span>
                        {getElapsedTime(order.created_at)}
                    </div>
                </div>

                {/* Cancellation Alert Banner */}
                {canProcessCancellation && (
                    <div className="mb-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 animate-pulse">
                        <div className="flex items-center gap-2 text-red-400 mb-2">
                            <span className="material-symbols-outlined text-[16px]">warning</span>
                            <span className="text-xs font-bold uppercase">Solicitud de Cancelación</span>
                        </div>
                        <p className="text-xs text-gray-300 italic mb-2">
                            "{order.cancellation_reason || 'Sin motivo especificado'}"
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={(e) => handleCancellationProcess(false, e)}
                                className="bg-gray-700/50 hover:bg-gray-700 text-white text-[10px] font-bold py-1.5 rounded transition-colors flex items-center justify-center gap-1"
                            >
                                <span className="material-symbols-outlined text-[14px]">close</span>
                                RECHAZAR
                            </button>
                            <button
                                onClick={(e) => handleCancellationProcess(true, e)}
                                className="bg-red-500/20 hover:bg-red-500/40 text-red-400 text-[10px] font-bold py-1.5 rounded transition-colors flex items-center justify-center gap-1"
                            >
                                <span className="material-symbols-outlined text-[14px]">check</span>
                                APROBAR
                            </button>
                        </div>
                    </div>
                )}

                <div className="space-y-1 mb-4 flex-grow">
                    {order.items.slice(0, 4).map((item, idx) => (
                        <p key={idx} className="text-xs text-gray-300 flex items-center gap-2 truncate">
                            <span className="w-1 h-1 rounded-full bg-accent-primary shrink-0"></span>
                            <span className="font-medium text-accent-primary/80">{item.quantity}x</span>
                            <span className="truncate">{item.product_name}</span>
                        </p>
                    ))}
                    {order.items.length > 4 && (
                        <p className="text-xs text-text-muted pl-3">... +{order.items.length - 4} más</p>
                    )}
                </div>

                <div className="border-t border-border-dark/50 pt-3 mt-auto">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex flex-col">
                            <span className="font-bold text-white text-base">${Number(order.total).toLocaleString()}</span>
                            {order.status === 'delivered' && (
                                <span className={`text-[9px] font-black uppercase ${isPaid ? 'text-status-success' : 'text-accent-primary animate-pulse'}`}>
                                    {isPaid ? 'Pagado' : 'Por Cobrar'}
                                </span>
                            )}
                        </div>
                        {order.created_by_name && (
                            <span className="text-[10px] text-text-muted italic flex items-center gap-1">
                                <span className="material-symbols-outlined text-[12px]">person</span>
                                {order.created_by_name}
                            </span>
                        )}
                    </div>

                    <div className="flex gap-2">
                        {order.status === 'delivered' && !isPaid && canOpenPayment ? (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onOpenPayment(order);
                                }}
                                className="flex-1 bg-accent-primary hover:bg-orange-500 text-bg-deep text-xs font-black py-2.5 rounded-lg transition-all flex items-center justify-center gap-1 group/btn shadow-lg shadow-accent-primary/20"
                            >
                                <span className="material-symbols-outlined text-[18px]">payments</span>
                                COBRAR
                            </button>
                        ) : (canChangeStatus() && nextStatus) && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onStatusChange(order.id, nextStatus);
                                }}
                                className="flex-1 bg-accent-primary hover:bg-accent-primary/90 text-bg-deep text-xs font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-1 group/btn"
                            >
                                <span className="material-symbols-outlined text-[16px] group-hover/btn:scale-110 transition-transform">
                                    {nextStatus === 'delivered' ? 'check_circle' : 'arrow_forward'}
                                </span>
                                {getStatusActionLabel(nextStatus)}
                            </button>
                        )}
                        <button
                            className="bg-bg-deep hover:bg-border-dark text-text-muted hover:text-white p-2 rounded-lg transition-colors border border-border-dark"
                            onClick={(e) => {
                                e.stopPropagation();
                                onViewDetail(order);
                            }}
                        >
                            <span className="material-symbols-outlined text-[18px]">visibility</span>
                        </button>
                    </div>
                </div>
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
