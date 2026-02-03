
import { useState, useMemo, useEffect } from 'react';
import { StockAudit } from '../setup/components/StockAudit';
import { useSetupData } from '../setup/hooks/useSetupData'; // Importing the hook
import { setupService } from '../setup/setup.service';
import { InventoryHistoryModal } from './InventoryHistoryModal';
import { GlobalAuditHistoryModal } from './GlobalAuditHistoryModal';

export const InventoryPage = () => {
    const [searchTerm, setSearchTerm] = useState('');

    // Connect to the source of truth
    const { ingredients, categories, isLoading, isRefreshing, refreshData } = useSetupData();

    const [filterStatus, setFilterStatus] = useState<'all' | 'critical' | 'low_stock' | 'in_stock'>('all');

    // Derived State: Filtered & Processed Inventory
    const inventoryItems = useMemo(() => {
        return ingredients
            .filter(item => item.is_active) // Only active items
            .map(item => {
                const minStock = item.min_stock !== undefined && item.min_stock !== null ? Number(item.min_stock) : 10;
                const stock = item.stock || 0;

                let status = 'in_stock';
                if (stock === 0) status = 'out_of_stock';
                else if (stock <= minStock) status = 'critical';
                else if (stock <= minStock * 1.5) status = 'low_stock';

                // Resolve category name if missing, using the ID link
                let categoryName = item.category_name || (item as any).category?.name;

                // Fallback: Try to find by ID (handling string/number mismatch)
                if (!categoryName) {
                    const catId = item.category_id || (item as any).categoryId;
                    if (catId) {
                        const foundCat = categories.find(c => String(c.id) === String(catId));
                        if (foundCat) categoryName = foundCat.name;
                    }
                }

                // Final Fallback: Smart assignment based on ingredient_type
                if (!categoryName) {
                    const type = (item as any).ingredient_type;
                    if (type === 'RAW') categoryName = 'Materia Prima';
                    else if (type === 'PROCESSED') categoryName = 'Procesado';
                    else if (type === 'MERCHANDISE') categoryName = 'Mercancía';
                }

                return {
                    ...item,
                    category_name: categoryName,
                    minStock,
                    stock,
                    price: item.price || 0,
                    status
                };
            })
            .filter(item => {
                // 1. Search Filter
                const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (item.sku && item.sku.toLowerCase().includes(searchTerm.toLowerCase()));

                // 2. Status Filter
                let matchesStatus = true;
                if (filterStatus === 'critical') {
                    // Critical includes both red alerts
                    matchesStatus = item.status === 'critical' || item.status === 'out_of_stock';
                } else if (filterStatus === 'low_stock') {
                    matchesStatus = item.status === 'low_stock';
                } else if (filterStatus === 'in_stock') {
                    matchesStatus = item.status === 'in_stock';
                }

                return matchesSearch && matchesStatus;
            });
    }, [ingredients, categories, searchTerm, filterStatus]);

    // Derived State: Stats (Calculated on the UNFILTERED list to show overview)
    const stats = useMemo(() => {
        // We use ingredients source to behave like a dashboard, 
        // but we need the Processed versions (map result) efficiently.
        // For performance, let's reuse the logic but applied to all.
        // Or simpler: Just calculate on the fly for stats (since we don't have the processed list accessible outside inventoryItems if we filter it).
        // WARNING: inventoryItems IS filtered now. We want global stats.
        // Let's recalculate basic stats from raw 'ingredients' + our status logic strictly for counters.

        let totalItems = 0;
        let criticalItems = 0;
        let lowStockItems = 0;
        let totalValue = 0;

        ingredients.forEach(item => {
            if (!item.is_active) return;
            totalItems++;

            const stock = item.stock || 0;
            const minStock = item.min_stock !== undefined && item.min_stock !== null ? Number(item.min_stock) : 10;

            if (stock <= minStock) criticalItems++;
            else if (stock <= minStock * 1.5) lowStockItems++;

            totalValue += (stock * (Number(item.price) || 0));
        });

        return { totalItems, criticalItems, lowStockItems, totalValue };
    }, [ingredients]);

    // State for Editing
    const [editingItem, setEditingItem] = useState<any>(null);
    const [historyItem, setHistoryItem] = useState<any>(null);

    const handleSaveEdit = async (newMinStock: number) => {
        if (!editingItem) return;

        try {
            // 2. Update Settings if changed
            if (newMinStock !== editingItem.minStock) {
                await setupService.updateIngredientSettings(
                    editingItem.id,
                    newMinStock
                );
            }

            // 3. Refresh
            await refreshData();
        } catch (error) {
            console.error("Failed to update inventory", error);
            alert("Error al actualizar inventario");
        }
    };

    const [auditConfig, setAuditConfig] = useState<{ type: 'FLASH' | 'FULL', initialSelection?: string[] } | null>(null);
    const [isGlobalHistoryOpen, setIsGlobalHistoryOpen] = useState(false);

    if (auditConfig) {
        return (
            <StockAudit
                onBack={() => setAuditConfig(null)}
                initialType={auditConfig.type}
                initialSelection={auditConfig.initialSelection}
            />
        );
    }

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

    if (isLoading && !isRefreshing && ingredients.length === 0) {
        return <div className="p-10 text-center text-gray-500 animate-pulse">Cargando inventario...</div>;
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        Inventario
                        {isRefreshing && <span className="text-xs font-normal text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full border border-emerald-400/20 animate-pulse">Sincronizando...</span>}
                    </h1>
                    <p className="text-text-muted text-sm">Gestión de insumos y productos en tiempo real</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setAuditConfig({ type: 'FLASH' })}
                        className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold text-sm tracking-wide shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
                    >
                        <span className="material-symbols-outlined">rule</span>
                        AUDITORÍA
                    </button>
                    <button
                        onClick={() => setIsGlobalHistoryOpen(true)}
                        className="flex items-center gap-2 bg-card-dark hover:bg-white/5 text-text-muted hover:text-white border border-border-dark px-4 py-2 rounded-lg font-bold text-sm tracking-wide transition-all"
                        title="Historial General de Auditorías"
                    >
                        <span className="material-symbols-outlined">history</span>
                        HISTORIAL
                    </button>
                    {/* Botón de Nuevo Producto removido por solicitud, gestión centralizada en Insumos */}
                </div>
            </div>

            {/* Quick Stats - Clickable Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div
                    onClick={() => setFilterStatus('all')}
                    className={`bg - card - dark p - 4 rounded - xl border ${filterStatus === 'all' ? 'border-indigo-500 bg-indigo-500/5' : 'border-border-dark'} flex items - center gap - 4 cursor - pointer hover: border - indigo - 500 / 50 transition - all`}
                >
                    <div className="h-12 w-12 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                        <span className="material-symbols-outlined text-2xl">inventory_2</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Total Items</p>
                        <h3 className="text-2xl font-bold text-white">{stats.totalItems}</h3>
                    </div>
                </div>
                <div
                    onClick={() => setFilterStatus('critical')}
                    className={`bg - card - dark p - 4 rounded - xl border ${filterStatus === 'critical' ? 'border-status-alert bg-status-alert/5' : 'border-border-dark'} flex items - center gap - 4 cursor - pointer hover: border - status - alert / 50 transition - all`}
                >
                    <div className="h-12 w-12 rounded-lg bg-status-alert/10 flex items-center justify-center text-status-alert">
                        <span className="material-symbols-outlined text-2xl">warning</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Stock Crítico</p>
                        <h3 className="text-2xl font-bold text-white">{stats.criticalItems}</h3>
                    </div>
                </div>
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-status-success/10 flex items-center justify-center text-status-success">
                        <span className="material-symbols-outlined text-2xl">attach_money</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Valor Inventario</p>
                        <h3 className="text-2xl font-bold text-white">${stats.totalValue.toLocaleString()}</h3>
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
                {/* Filter Group */}
                <div className="flex bg-card-dark rounded-lg p-1 border border-border-dark shadow-sm h-11 self-start md:self-auto">
                    <button
                        onClick={() => setFilterStatus('all')}
                        className={`px - 4 rounded - md text - xs font - bold transition - all ${filterStatus === 'all'
                            ? 'bg-white/10 text-white shadow-sm'
                            : 'text-text-muted hover:text-white hover:bg-white/5'
                            } `}
                    >
                        Todos
                    </button>
                    <button
                        onClick={() => setFilterStatus('critical')}
                        className={`px - 4 rounded - md text - xs font - bold transition - all flex items - center gap - 2 ${filterStatus === 'critical'
                            ? 'bg-status-alert text-white shadow-sm'
                            : 'text-text-muted hover:text-white hover:bg-white/5'
                            } `}
                    >
                        Críticos
                        {stats.criticalItems > 0 && (
                            <span className="bg-black/20 px-1.5 py-0.5 rounded text-[10px]">{stats.criticalItems}</span>
                        )}
                    </button>
                    <button
                        onClick={() => setFilterStatus('low_stock')}
                        className={`px - 4 rounded - md text - xs font - bold transition - all flex items - center gap - 2 ${filterStatus === 'low_stock'
                            ? 'bg-status-warning text-white shadow-sm'
                            : 'text-text-muted hover:text-white hover:bg-white/5'
                            } `}
                    >
                        Bajo Stock
                        {stats.lowStockItems > 0 && (
                            <span className="bg-black/20 px-1.5 py-0.5 rounded text-[10px]">{stats.lowStockItems}</span>
                        )}
                    </button>
                </div>
            </div>

            {/* Inventory Table */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden shadow-xl">
                {/* Desktop Table View */}
                <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Producto / SKU</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Categoría</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Stock</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Stock Mínimo</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Estado</th>
                                <th className="px-6 py-4 text-right font-semibold text-text-muted uppercase tracking-wider text-xs">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {inventoryItems.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-10 text-center text-text-muted">
                                        No se encontraron productos en el inventario.
                                    </td>
                                </tr>
                            ) : (
                                inventoryItems.map((item) => (
                                    <tr key={item.id} className="group hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-medium text-white">{item.name}</span>
                                                <span className="text-xs text-text-muted font-mono">{item.sku || 'N/A'}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300">
                                            {item.category_name || 'Sin Categoría'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="w-full max-w-[120px] cursor-pointer" onClick={() => setAuditConfig({ type: 'FLASH', initialSelection: [item.id!] })} title="Clic para auditar">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className="font-medium text-white">{Number(item.stock).toLocaleString('es-MX', { maximumFractionDigits: 2 })} {item.unit}</span>
                                                    <span className="text-text-muted underline decoration-dotted">min: {Number(item.minStock).toLocaleString('es-MX', { maximumFractionDigits: 2 })}</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-bg-deep rounded-full overflow-hidden">
                                                    <div
                                                        className={`h - full rounded - full ${item.status === 'out_of_stock' ? 'bg-status-alert' :
                                                            item.status === 'critical' ? 'bg-status-alert' :
                                                                item.status === 'low_stock' ? 'bg-status-warning' :
                                                                    'bg-status-success'
                                                            } `}
                                                        style={{ width: `${Math.min(100, (item.stock / (item.minStock * 2)) * 100)}% ` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-gray-300">
                                            {Number(item.minStock).toLocaleString('es-MX', { maximumFractionDigits: 2 })} {item.unit}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline - flex items - center px - 2.5 py - 0.5 rounded - full text - xs font - medium border ${getStatusColor(item.status)} `}>
                                                {getStatusLabel(item.status)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                {/* Edit Settings Button */}
                                                <button
                                                    onClick={() => setEditingItem(item)}
                                                    className="inline-flex items-center justify-center p-1.5 rounded-lg text-text-muted hover:bg-white/10 transition-all hover:text-white"
                                                    title="Configurar Alerta"
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">settings</span>
                                                </button>

                                                {/* History Button */}
                                                <button
                                                    onClick={() => setHistoryItem(item)}
                                                    className="inline-flex items-center justify-center p-1.5 rounded-lg text-text-muted hover:bg-white/10 transition-all hover:text-white mr-1"
                                                    title="Ver Historial"
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">history</span>
                                                </button>

                                                {/* Action Button: Audit vs Define Alert */}
                                                {(item.status === 'critical' || item.status === 'out_of_stock' || item.status === 'low_stock') ? (
                                                    <button
                                                        onClick={() => setAuditConfig({ type: 'FLASH', initialSelection: [item.id!] })}
                                                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-status-alert/10 border border-status-alert/20 text-status-alert hover:bg-status-alert hover:text-white transition-all text-xs font-bold shadow-sm shadow-status-alert/10 active:scale-95 animate-pulse"
                                                        title="Auditoría Requerida debido a bajo stock"
                                                    >
                                                        <span className="material-symbols-outlined text-[16px]">gavel</span>
                                                        Aud. Requerida
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => setAuditConfig({ type: 'FLASH', initialSelection: [item.id!] })}
                                                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20 hover:text-indigo-300 transition-all text-xs font-semibold shadow-sm hover:shadow-indigo-500/10 active:scale-95"
                                                        title="Realizar Auditoría Regular"
                                                    >
                                                        <span className="material-symbols-outlined text-[16px]">check_circle</span>
                                                        Aud. Regular
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Mobile Card View */}
                <div className="md:hidden divide-y divide-border-dark">
                    {inventoryItems.length === 0 ? (
                        <div className="p-8 text-center text-text-muted">
                            No se encontraron productos en el inventario.
                        </div>
                    ) : (
                        inventoryItems.map((item) => (
                            <div key={item.id} className="p-4 space-y-3 bg-card-dark active:bg-white/5 transition-colors">
                                {/* Top Row: Name and Status */}
                                <div className="flex justify-between items-start gap-3">
                                    <div>
                                        <h3 className="font-bold text-white text-sm">{item.name}</h3>
                                        <p className="text-xs text-text-muted font-mono">{item.sku || 'N/A'} • {item.category_name}</p>
                                    </div>
                                    <span className={`shrink - 0 inline - flex items - center px - 2 py - 0.5 rounded - full text - [10px] uppercase font - bold border ${getStatusColor(item.status)} `}>
                                        {getStatusLabel(item.status)}
                                    </span>
                                </div>

                                {/* Middle Row: Stock Bar */}
                                <div className="space-y-1">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-white font-medium">{Number(item.stock).toLocaleString('es-MX', { maximumFractionDigits: 2 })} {item.unit}</span>
                                        <span className="text-text-muted text-[10px]">Min: {Number(item.minStock).toLocaleString('es-MX', { maximumFractionDigits: 2 })}</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-bg-deep rounded-full overflow-hidden">
                                        <div
                                            className={`h - full rounded - full ${item.status === 'out_of_stock' ? 'bg-status-alert' :
                                                item.status === 'critical' ? 'bg-status-alert' :
                                                    item.status === 'low_stock' ? 'bg-status-warning' :
                                                        'bg-status-success'
                                                } `}
                                            style={{ width: `${Math.min(100, (item.stock / (item.minStock * 2)) * 100)}% ` }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Bottom Row: Actions */}
                                <div className="flex items-center justify-between pt-2">
                                    <button
                                        onClick={() => setEditingItem(item)}
                                        className="text-text-muted hover:text-white p-2"
                                    >
                                        <span className="material-symbols-outlined text-[20px]">settings</span>
                                    </button>

                                    {(item.status === 'critical' || item.status === 'out_of_stock' || item.status === 'low_stock') ? (
                                        <button
                                            onClick={() => setAuditConfig({ type: 'FLASH', initialSelection: [item.id!] })}
                                            className="flex-1 ml-4 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-status-alert text-white font-bold text-sm shadow-lg shadow-status-alert/20 animate-pulse active:scale-95"
                                        >
                                            <span className="material-symbols-outlined text-[18px]">gavel</span>
                                            Auditoría Requerida
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => setAuditConfig({ type: 'FLASH', initialSelection: [item.id!] })}
                                            className="flex-1 ml-4 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-sm hover:bg-indigo-500/20 active:scale-95"
                                        >
                                            <span className="material-symbols-outlined text-[18px]">check_circle</span>
                                            Auditoría Regular
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
                {/* Pagination Placeholder */}
                <div className="px-6 py-4 border-t border-border-dark flex items-center justify-between text-xs text-text-muted">
                    <span>Mostrando {inventoryItems.length} resultados</span>
                    <div className="flex gap-2">
                        <button className="px-3 py-1 bg-bg-deep border border-border-dark rounded hover:border-white/20 transition-colors cursor-not-allowed opacity-50">Anterior</button>
                        <button className="px-3 py-1 bg-bg-deep border border-border-dark rounded hover:border-white/20 transition-colors cursor-not-allowed opacity-50">Siguiente</button>
                    </div>
                </div>
            </div>

            {/* Inventory Edit Modal (Settings) */}
            <InventoryEditModal
                item={editingItem}
                isOpen={!!editingItem}
                onClose={() => setEditingItem(null)}
                onSave={handleSaveEdit}
            />

            {/* Inventory History Modal */}
            {/* Modal de Historial Individual */}
            <InventoryHistoryModal
                item={historyItem}
                isOpen={!!historyItem}
                onClose={() => setHistoryItem(null)}
            />

            {/* Modal de Historial Global / Revertir */}
            <GlobalAuditHistoryModal
                isOpen={isGlobalHistoryOpen}
                onClose={() => setIsGlobalHistoryOpen(false)}
                onRevertSuccess={refreshData}
            />
        </div>
    );
};

// Subcomponent for Modal
interface InventoryEditModalProps {
    item: any;
    isOpen: boolean;
    onClose: () => void;
    onSave: (minStock: number) => Promise<void>;
}

const InventoryEditModal = ({ item, isOpen, onClose, onSave }: InventoryEditModalProps) => {
    // const [stock, setStock] = useState(0); // Removed physical stock editing
    const [minStock, setMinStock] = useState(0);
    const [isSaving, setIsSaving] = useState(false);

    // Sync state when item changes
    useEffect(() => {
        if (item) {
            // setStock(Number(item.stock) || 0);
            setMinStock(Number(item.minStock) || 0);
        }
    }, [item]);

    if (!isOpen || !item) return null;

    const handleSave = async () => {
        setIsSaving(true);
        // Pass only minStock
        await onSave(minStock);
        setIsSaving(false);
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[60] p-4 animate-in fade-in duration-200">
            <div className="bg-card-dark border border-border-dark rounded-xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-border-dark bg-white/5 flex justify-between items-center">
                    <div>
                        <h3 className="text-xl font-bold text-white">Editar Configuración</h3>
                        <p className="text-sm text-text-muted mt-1">{item.name}</p>
                    </div>
                    <button onClick={onClose} className="text-text-muted hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div className="p-6 space-y-5">
                    {/* Removed Stock Input */}

                    <div>
                        <label className="block text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">Stock Mínimo (Alerta Crítica)</label>
                        <div className="relative">
                            <span className="absolute left-3 top-3.5 text-text-muted material-symbols-outlined text-[18px]">notification_important</span>
                            <input
                                type="number"
                                step="0.01"
                                className="w-full bg-bg-deep border border-border-dark rounded-lg py-3 pl-10 pr-4 text-white focus:ring-1 focus:ring-accent-orange focus:border-accent-orange outline-none transition-all"
                                value={minStock}
                                onChange={(e) => setMinStock(e.target.value === '' ? '' as any : parseFloat(e.target.value))}
                            />
                        </div>
                        <p className="text-[11px] text-gray-500 mt-2 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">info</span>
                            Si el stock baja de este nivel, se marcará como CRÍTICO.
                        </p>
                    </div>
                </div>
                <div className="p-6 pt-0 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-5 py-2.5 rounded-lg border border-border-dark text-text-muted hover:bg-white/5 transition-colors font-medium"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                    >
                        {isSaving ? <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span> : <span className="material-symbols-outlined text-sm">save</span>}
                        Guardar Cambios
                    </button>
                </div>
            </div>
        </div>
    );
};



