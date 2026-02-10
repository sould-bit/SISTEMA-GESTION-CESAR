
import { Order, OrderStatus } from '../types';
import { differenceInMinutes } from 'date-fns';

interface OrderListItemProps {
    order: Order;
    onViewDetail: (order: Order) => void;
    onStatusChange: (orderId: number, newStatus: OrderStatus) => void;
    onOpenPayment: (order: Order) => void;
}

const getElapsedTime = (dateString: string) => {
    const start = new Date(dateString);
    const now = new Date();
    const diffMs = Math.max(0, now.getTime() - start.getTime());
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const STEPS: { status: OrderStatus; label: string }[] = [
    { status: 'pending', label: 'Pendiente' },
    { status: 'preparing', label: 'En Cocina' },
    { status: 'ready', label: 'Listo' },
    { status: 'delivered', label: 'Entregado' },
];

import { useOrderPermissions } from '../../../hooks/useOrderPermissions';

export const OrderListItem = ({ order, onViewDetail, onStatusChange, onOpenPayment }: OrderListItemProps) => {
    const { canAcceptOrder, canMarkReady, canDeliver } = useOrderPermissions();

    const minutesWaiting = differenceInMinutes(new Date(), new Date(order.created_at));
    const isHighPriority = minutesWaiting > 15 && order.status !== 'delivered' && order.status !== 'cancelled';

    const currentStepIndex = STEPS.findIndex(s => s.status === order.status);

    // Consideramos entregado como el último paso si no está en la lista de STEPS
    const displayStepIndex = currentStepIndex !== -1 ? currentStepIndex : (order.status === 'delivered' ? 3 : -1);

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
        <div
            onClick={() => onViewDetail(order)}
            className={`
                relative bg-gradient-to-br from-card-dark to-bg-deep p-6 rounded-[2rem] border border-white/5 hover:border-accent-primary/40 transition-all cursor-pointer group shadow-2xl flex flex-col gap-6 overflow-hidden backdrop-blur-xl
                ${isHighPriority ? 'animate-attention' : ''}
                ${(order.status === 'delivered' && !isPaid) ? 'border-accent-primary/30 shadow-accent-primary/5' : ''}
            `}
        >
            {/* Glossy overlay effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-accent-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

            {/* Status vertical indicator */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${order.status === 'delivered' ? 'bg-accent-primary' : (isHighPriority ? 'bg-status-alert' : 'bg-white/10 group-hover:bg-accent-primary')} transition-colors`} />

            {/* TOP ROW: Info + Items + Actions */}
            <div className="flex flex-col lg:flex-row items-center justify-between gap-6 w-full z-10">

                {/* Info Section */}
                <div className="flex items-center gap-4 min-w-[200px] w-full lg:w-auto">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-transform group-hover:scale-105 ${order.status === 'delivered' ? 'bg-accent-primary text-bg-deep border-accent-primary/20' : 'bg-accent-primary/10 text-accent-primary border-accent-primary/20'}`}>
                        <span className="material-symbols-outlined text-2xl">
                            {order.table_id ? 'restaurant' : (order.delivery_type === 'takeaway' ? 'takeout_dining' : 'local_shipping')}
                        </span>
                    </div>
                    <div>
                        <h4 className="font-black text-white text-xl tracking-tight leading-none">
                            {order.table_id ? `Mesa ${order.table_id}` : (order.delivery_type === 'takeaway' ? 'Para Llevar' : 'Domicilio')}
                        </h4>
                        <div className="flex items-center gap-3 mt-1">
                            <p className="text-accent-primary/80 font-black text-[10px] uppercase tracking-[0.15em]">{order.order_number}</p>
                            <div className={`flex items-center gap-1.5 text-[10px] font-black py-0.5 px-2 rounded-lg bg-black/40 border border-white/5 ${isHighPriority ? 'text-status-alert animate-pulse' : 'text-accent-secondary'}`}>
                                <span className="material-symbols-outlined text-[14px]">timer</span>
                                {getElapsedTime(order.created_at)}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Items Summary (Middle) */}
                <div className="flex-1 flex flex-wrap gap-2 px-4 justify-start lg:justify-center">
                    {order.items.slice(0, 5).map((item, idx) => (
                        <div key={idx} className="bg-white/5 px-2.5 py-1.5 rounded-xl text-[10px] text-white/90 font-bold flex items-center gap-2 border border-white/5 hover:bg-white/10 transition-colors">
                            <span className="text-accent-primary">{item.quantity}x</span>
                            <span className="truncate max-w-[100px]">{item.product_name}</span>
                        </div>
                    ))}
                </div>

                {/* Actions Section (Right) */}
                <div className="flex items-center gap-6 min-w-[240px] justify-end w-full lg:w-auto">
                    <div className="text-right">
                        <p className="text-white font-black text-2xl tracking-tighter leading-none">${Number(order.total).toLocaleString()}</p>
                        {order.status === 'delivered' && (
                            <div className={`text-[9px] font-black uppercase mt-1 ${isPaid ? 'text-status-success' : 'text-accent-primary animate-pulse'}`}>
                                {isPaid ? 'PAGADO' : 'PENDIENTE DE PAGO'}
                            </div>
                        )}
                    </div>

                    <div className="flex gap-2">
                        {order.status === 'delivered' && !isPaid && (isAdmin || isCashier) ? (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onOpenPayment(order);
                                }}
                                className="bg-accent-primary hover:bg-orange-500 text-bg-deep font-black px-8 py-3.5 rounded-2xl transition-all flex items-center gap-2 hover:scale-105 active:scale-95 shadow-lg shadow-accent-primary/20 group/btn whitespace-nowrap"
                            >
                                <span className="material-symbols-outlined text-[20px]">payments</span>
                                <span className="text-xs uppercase tracking-tighter">COBRAR</span>
                            </button>
                        ) : (canChangeStatus() && nextStatus) && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onStatusChange(order.id, nextStatus);
                                }}
                                className="bg-accent-primary hover:bg-orange-500 text-white font-black px-6 py-3.5 rounded-2xl transition-all flex items-center gap-2 hover:scale-105 active:scale-95 shadow-lg shadow-accent-primary/20 hover:shadow-accent-primary/40 group/btn whitespace-nowrap"
                            >
                                <span className="material-symbols-outlined text-[18px] group-hover/btn:translate-x-1 transition-transform">
                                    {nextStatus === 'delivered' ? 'check_circle' : 'bolt'}
                                </span>
                                <span className="text-xs uppercase tracking-tighter">{getStatusActionLabel(nextStatus)}</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* BOTTOM ROW: Full Width Progress Bar (Compact) */}
            <div className="w-full z-10 bg-black/15 p-3.5 rounded-2xl border border-white/5">
                <div className="flex items-center justify-between px-10 relative">
                    {/* Progress Line */}
                    <div className="absolute left-14 right-14 top-[12px] -translate-y-1/2 h-0.5 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-1000 ease-out rounded-full shadow-[0_0_10px_rgba(234,88,12,0.3)]"
                            style={{ width: `${(Math.max(0, displayStepIndex) / (STEPS.length - 1)) * 100}%` }}
                        />
                    </div>

                    {STEPS.map((step, idx) => {
                        const isActive = idx <= displayStepIndex;
                        const isCurrent = idx === displayStepIndex;

                        return (
                            <div key={idx} className="flex flex-col items-center gap-1.5 relative z-10">
                                <div
                                    className={`
                                        w-6 h-6 rounded-full flex items-center justify-center border transition-all duration-700
                                        ${isActive ? 'bg-accent-primary border-accent-primary text-bg-deep' : 'bg-bg-deep border-white/10 text-text-muted'}
                                        ${isCurrent && order.status !== 'delivered' ? 'scale-110 ring-4 ring-accent-primary/10 shadow-[0_0_15px_rgba(234,88,12,0.4)]' : ''}
                                        ${isActive && (idx < displayStepIndex || order.status === 'delivered') ? 'bg-status-success border-status-success text-white' : ''}
                                    `}
                                >
                                    {(isActive && idx < displayStepIndex) || (order.status === 'delivered') ? (
                                        <span className="material-symbols-outlined text-[14px] font-black">check</span>
                                    ) : (
                                        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-bg-deep' : 'bg-white/10'}`} />
                                    )}
                                </div>
                                <span className={`text-[8px] font-black uppercase tracking-[0.1em] transition-colors duration-500 ${isActive ? 'text-white' : 'text-text-muted/40'}`}>
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};
