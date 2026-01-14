import { useState } from 'react';

// Mock Data
const INVENTORY_DATA = [
    { id: 1, name: 'Burger Bun Artisan', sku: 'BUN-001', category: 'Panadería', stock: 120, minStock: 50, price: 800, status: 'in_stock' },
    { id: 2, name: 'Carne Res Premium', sku: 'PAT-002', category: 'Cárnicos', stock: 15, minStock: 20, price: 4500, status: 'low_stock' },
    { id: 3, name: 'Queso Cheddar', sku: 'DAI-003', category: 'Lácteos', stock: 8, minStock: 10, price: 1200, status: 'critical' },
    { id: 4, name: 'Salsa Especial', sku: 'SAU-004', category: 'Salsas', stock: 50, minStock: 15, price: 500, status: 'in_stock' },
    { id: 5, name: 'Lechuga Fresca', sku: 'VEG-005', category: 'Vegetales', stock: 0, minStock: 10, price: 1000, status: 'out_of_stock' },
    { id: 6, name: 'Tomate', sku: 'VEG-006', category: 'Vegetales', stock: 25, minStock: 15, price: 800, status: 'in_stock' },
    { id: 7, name: 'Coca Cola 1.5L', sku: 'BEV-007', category: 'Bebidas', stock: 45, minStock: 12, price: 5000, status: 'in_stock' },
];

export const InventoryPage = () => {
    const [searchTerm, setSearchTerm] = useState('');

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'in_stock': return 'text-status-success bg-status-success/10 border-status-success/20';
            case 'low_stock': return 'text-status-warning bg-status-warning/10 border-status-warning/20';
            case 'critical': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'out_of_stock': return 'text-status-alert bg-status-alert/10 border-status-alert/20';
            default: return 'text-text-muted bg-white/5 border-white/10';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'in_stock': return 'En Stock';
            case 'low_stock': return 'Bajo Stock';
            case 'critical': return 'Crítico';
            case 'out_of_stock': return 'Agotado';
            default: return status;
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Inventario</h1>
                    <p className="text-text-muted text-sm">Gestión de insumos y productos en tiempo real</p>
                </div>
                <button className="flex items-center gap-2 bg-accent-orange hover:bg-orange-600 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-accent-orange/20">
                    <span className="material-symbols-outlined">add</span>
                    Nuevo Producto
                </button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                        <span className="material-symbols-outlined text-2xl">inventory_2</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Total Productos</p>
                        <h3 className="text-2xl font-bold text-white">1,248</h3>
                    </div>
                </div>
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-status-alert/10 flex items-center justify-center text-status-alert">
                        <span className="material-symbols-outlined text-2xl">warning</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Stock Crítico</p>
                        <h3 className="text-2xl font-bold text-white">12</h3>
                    </div>
                </div>
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-status-success/10 flex items-center justify-center text-status-success">
                        <span className="material-symbols-outlined text-2xl">attach_money</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Valor Inventario</p>
                        <h3 className="text-2xl font-bold text-white">$45.2M</h3>
                    </div>
                </div>
            </div>

            {/* Controls Bar */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <span className="material-symbols-outlined absolute left-3 top-2.5 text-text-muted">search</span>
                    <input
                        type="text"
                        placeholder="Buscar por nombre, SKU o categoría..."
                        className="w-full bg-card-dark border border-border-dark rounded-lg py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-accent-orange focus:ring-1 focus:ring-accent-orange transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex gap-2">
                    <button className="flex items-center gap-2 px-4 py-2 bg-card-dark border border-border-dark rounded-lg text-text-muted hover:text-white hover:border-white/20 transition-colors text-sm">
                        <span className="material-symbols-outlined text-[18px]">filter_list</span>
                        Filtros
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 bg-card-dark border border-border-dark rounded-lg text-text-muted hover:text-white hover:border-white/20 transition-colors text-sm">
                        <span className="material-symbols-outlined text-[18px]">download</span>
                        Exportar
                    </button>
                </div>
            </div>

            {/* Inventory Table */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Producto / SKU</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Categoría</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Stock</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Precio Unit.</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Estado</th>
                                <th className="px-6 py-4 text-right font-semibold text-text-muted uppercase tracking-wider text-xs">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {INVENTORY_DATA.map((item) => (
                                <tr key={item.id} className="group hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-white">{item.name}</span>
                                            <span className="text-xs text-text-muted font-mono">{item.sku}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-300">
                                        {item.category}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="w-full max-w-[120px]">
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="font-medium text-white">{item.stock}</span>
                                                <span className="text-text-muted">min: {item.minStock}</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-bg-deep rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${item.stock === 0 ? 'bg-status-alert' :
                                                            item.stock < item.minStock ? 'bg-status-warning' :
                                                                'bg-status-success'
                                                        }`}
                                                    style={{ width: `${Math.min(100, (item.stock / (item.minStock * 2)) * 100)}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-gray-300">
                                        ${item.price.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(item.status)}`}>
                                            {getStatusLabel(item.status)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="text-text-muted hover:text-white transition-colors p-1 rounded hover:bg-white/10">
                                            <span className="material-symbols-outlined text-[20px]">more_vert</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {/* Pagination Placeholder */}
                <div className="px-6 py-4 border-t border-border-dark flex items-center justify-between text-xs text-text-muted">
                    <span>Mostrando 7 de 1,248 resultados</span>
                    <div className="flex gap-2">
                        <button className="px-3 py-1 bg-bg-deep border border-border-dark rounded hover:border-white/20 transition-colors">Anterior</button>
                        <button className="px-3 py-1 bg-bg-deep border border-border-dark rounded hover:border-white/20 transition-colors">Siguiente</button>
                    </div>
                </div>
            </div>
        </div>
    );
};
