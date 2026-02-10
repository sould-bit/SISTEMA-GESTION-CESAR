import { Table } from './tables.service';
import { TableOrderInfo } from './useTableOrders';

interface TableCardProps {
    table: Table;
    orderInfo?: TableOrderInfo;
    onClick: () => void;
    onAcceptOrder?: (orderId: number) => void;
}

/**
 * Reusable table card component with visual states for different order statuses.
 * 
 * Visual States:
 * - Available: Gray, subtle hover effect
 * - Pending: Yellow pulse animation, "Nuevo Pedido" badge
 * - Preparing: Red solid, waiter name displayed
 */
import { useOrderPermissions } from '../../hooks/useOrderPermissions';

export const TableCard = ({ table, orderInfo, onClick, onAcceptOrder }: TableCardProps) => {
    const { canAcceptOrder } = useOrderPermissions();

    const isPending = orderInfo?.status === 'pending';
    const isOccupied = table.status === 'occupied' || !!orderInfo;
    const isPreparingOrConfirmed = orderInfo?.status === 'preparing' || orderInfo?.status === 'confirmed';
    const isReady = orderInfo?.status === 'ready';
    const isDeliveredUnpaid = orderInfo?.status === 'delivered';

    const getCardStyles = () => {
        if (isPending) {
            return 'bg-status-warning/10 border-status-warning text-status-warning animate-attention';
        }
        if (isReady) {
            return 'bg-status-success/10 border-status-success text-status-success';
        }
        if (isDeliveredUnpaid) {
            return 'bg-accent-primary/10 border-accent-primary text-accent-primary';
        }
        if (isPreparingOrConfirmed || isOccupied) {
            return 'bg-status-alert/10 border-status-alert text-status-alert';
        }
        return 'bg-card-dark border-border-dark text-text-muted hover:border-accent-primary hover:text-accent-primary';
    };

    const getStatusLabel = () => {
        if (isPending) return 'Pendiente';
        if (isPreparingOrConfirmed) return 'Preparando';
        if (isReady) return 'Por Entregar';
        if (isDeliveredUnpaid) return 'Por Cobrar';
        if (isOccupied) return 'Ocupada';
        return 'Libre';
    };

    const getIndicatorStyles = () => {
        if (isPending) {
            return 'bg-status-warning shadow-[0_0_10px_rgba(245,158,11,0.5)]';
        }
        if (isReady) {
            return 'bg-status-success shadow-[0_0_10px_rgba(34,197,94,0.5)]';
        }
        if (isDeliveredUnpaid) {
            return 'bg-accent-primary shadow-[0_0_10px_rgba(234,88,12,0.5)]';
        }
        if (isPreparingOrConfirmed || isOccupied) {
            return 'bg-status-alert shadow-[0_0_10px_rgba(239,68,68,0.5)]';
        }
        return '';
    };

    const handleAcceptClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (orderInfo && onAcceptOrder) {
            onAcceptOrder(orderInfo.orderId);
        }
    };

    return (
        <div
            onClick={onClick}
            className={`
                relative aspect-square rounded-2xl border-2 flex flex-col items-center justify-center cursor-pointer transition-all hover:scale-105 active:scale-95 p-3
                ${getCardStyles()}
                ${isPending && onAcceptOrder && (isAdmin || isCashier) ? 'mb-4' : ''}
            `}
        >
            {/* Header row: Price + Indicator */}
            <div className="absolute top-2 left-2 right-2 flex justify-between items-center">
                {/* Order total (for pending orders) */}
                {isPending && orderInfo ? (
                    <span className="text-[10px] font-bold bg-black/30 px-2 py-0.5 rounded-full">
                        ${orderInfo.total.toLocaleString()}
                    </span>
                ) : <span />}

                {/* Status indicator dot */}
                {(isOccupied || orderInfo) && (
                    <div className={`size-3 rounded-full animate-pulse ${getIndicatorStyles()}`}></div>
                )}
            </div>

            {/* Main content - centered */}
            <div className="flex flex-col items-center justify-center">
                {/* Table icon */}
                <span className="material-symbols-outlined text-3xl mb-1">table_restaurant</span>

                {/* Table number */}
                <span className="text-base sm:text-lg font-bold leading-tight">Mesa {table.table_number}</span>

                {/* Status label */}
                <span className="text-[9px] sm:text-[10px] uppercase tracking-wide font-semibold mt-0.5 whitespace-nowrap">
                    {getStatusLabel()}
                </span>

                {/* Waiter name - inline below status */}
                {orderInfo?.waiterName && (
                    <span className="text-[9px] text-current/70 mt-1 truncate max-w-full">
                        👤 {orderInfo.waiterName}
                    </span>
                )}
            </div>

            {/* Accept order quick action (for pending orders) */}
            {isPending && onAcceptOrder && canAcceptOrder && (
                <button
                    onClick={handleAcceptClick}
                    className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-accent-primary hover:bg-accent-primary/90 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg transition-all hover:scale-110 flex items-center gap-1 z-10"
                >
                    <span className="material-symbols-outlined text-sm">check</span>
                    Aceptar
                </button>
            )}
        </div>
    );
};
