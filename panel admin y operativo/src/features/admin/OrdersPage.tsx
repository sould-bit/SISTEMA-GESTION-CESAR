import { useState } from 'react';

// Mock Data
const ORDERS_DATA = {
    pending: [
        { id: 'ORD-001', table: 'Mesa 4', items: ['2x Burger Classic', '1x Papas Fritas', '2x Coke'], time: '2:30', total: 45000, priority: 'normal' },
        { id: 'ORD-004', table: 'Mesa 1', items: ['1x Ensalada César', '1x Agua'], time: '0:45', total: 22000, priority: 'high' },
    ],
    preparing: [
        { id: 'ORD-002', table: 'Mesa 8', items: ['1x Pizza Pepperoni', '2x Cerveza'], time: '12:15', total: 68000, priority: 'normal' },
        { id: 'ORD-005', table: 'Barra 2', items: ['3x Tacos Pastor', '1x Margarita'], time: '5:00', total: 35000, priority: 'normal' },
    ],
    ready: [
        { id: 'ORD-003', table: 'Mesa 2', items: ['1x Café Americano', '1x Cheesecake'], time: '15:20', total: 18000, priority: 'normal' },
    ]
};

const OrderCard = ({ order }: { order: any }) => (
    <div className={`
        bg-card-dark p-4 rounded-xl border border-border-dark hover:border-accent-orange/50 transition-colors cursor-pointer group shadow-lg
        ${order.priority === 'high' ? 'border-l-4 border-l-status-alert' : ''}
    `}>
        <div className="flex justify-between items-start mb-3">
            <div>
                <h4 className="font-bold text-white text-sm">{order.table}</h4>
                <p className="text-text-muted text-xs font-mono">{order.id}</p>
            </div>
            <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded bg-bg-deep font-mono ${parseInt(order.time) > 10 ? 'text-status-alert' : 'text-status-success'}`}>
                <span className="material-symbols-outlined text-[14px]">timer</span>
                {order.time}
            </div>
        </div>

        <div className="space-y-1 mb-4">
            {order.items.map((item: string, idx: number) => (
                <p key={idx} className="text-xs text-gray-300 flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-accent-orange"></span>
                    {item}
                </p>
            ))}
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-border-dark/50">
            <span className="font-bold text-white text-sm">${order.total.toLocaleString()}</span>
            <button className="text-xs font-medium text-accent-orange opacity-0 group-hover:opacity-100 transition-opacity hover:underline">
                Ver Detalles
            </button>
        </div>
    </div>
);

export const OrdersPage = () => {
    const [viewMode, setViewMode] = useState<'board' | 'list'>('board');

    return (
        <div className="space-y-6 h-[calc(100vh-140px)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Comandas Activas</h1>
                    <p className="text-text-muted text-sm">Monitoreo de cocina y despachos</p>
                </div>

                <div className="flex bg-card-dark rounded-lg p-1 border border-border-dark">
                    <button
                        onClick={() => setViewMode('board')}
                        className={`p-2 rounded flex items-center ${viewMode === 'board' ? 'bg-bg-deep text-white shadow-sm' : 'text-text-muted hover:text-white'}`}
                    >
                        <span className="material-symbols-outlined">view_kanban</span>
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded flex items-center ${viewMode === 'list' ? 'bg-bg-deep text-white shadow-sm' : 'text-text-muted hover:text-white'}`}
                    >
                        <span className="material-symbols-outlined">view_list</span>
                    </button>
                </div>
            </div>

            {/* Kanban Board */}
            <div className="flex-1 overflow-x-auto">
                <div className="flex gap-6 min-w-[900px] h-full">
                    {/* Pending Column */}
                    <div className="flex-1 flex flex-col gap-4">
                        <div className="flex items-center justify-between p-3 bg-card-dark/50 rounded-lg border border-border-dark/50">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-status-alert"></div>
                                <span className="font-bold text-sm text-white uppercase tracking-wider">Pendientes</span>
                            </div>
                            <span className="bg-bg-deep text-white text-xs font-bold px-2 py-0.5 rounded-full">{ORDERS_DATA.pending.length}</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-2">
                            {ORDERS_DATA.pending.map(order => <OrderCard key={order.id} order={order} />)}
                        </div>
                    </div>

                    {/* Preparing Column */}
                    <div className="flex-1 flex flex-col gap-4">
                        <div className="flex items-center justify-between p-3 bg-card-dark/50 rounded-lg border border-border-dark/50">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-status-warning"></div>
                                <span className="font-bold text-sm text-white uppercase tracking-wider">En Preparación</span>
                            </div>
                            <span className="bg-bg-deep text-white text-xs font-bold px-2 py-0.5 rounded-full">{ORDERS_DATA.preparing.length}</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-2">
                            {ORDERS_DATA.preparing.map(order => <OrderCard key={order.id} order={order} />)}
                        </div>
                    </div>

                    {/* Ready Column */}
                    <div className="flex-1 flex flex-col gap-4">
                        <div className="flex items-center justify-between p-3 bg-card-dark/50 rounded-lg border border-border-dark/50">
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-status-success"></div>
                                <span className="font-bold text-sm text-white uppercase tracking-wider">Despacho</span>
                            </div>
                            <span className="bg-bg-deep text-white text-xs font-bold px-2 py-0.5 rounded-full">{ORDERS_DATA.ready.length}</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-2">
                            {ORDERS_DATA.ready.map(order => <OrderCard key={order.id} order={order} />)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
