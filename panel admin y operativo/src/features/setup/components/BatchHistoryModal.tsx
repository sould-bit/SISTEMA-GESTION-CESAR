import { useState, useEffect } from 'react';
import { kitchenService, IngredientBatch } from '../../kitchen/kitchen.service';

// Helpers
const formatCurrency = (value: number, decimals: number = 0) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

const formatNumber = (value: number, decimals: number = 4) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

interface BatchHistoryModalProps {
    productId: string;
    productName: string;
    baseUnit: string;
    onClose: () => void;
}

export const BatchHistoryModal = ({ productId, productName, baseUnit, onClose }: BatchHistoryModalProps) => {
    const [batches, setBatches] = useState<IngredientBatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAll, setShowAll] = useState(false);

    // Edit State
    const [editingBatch, setEditingBatch] = useState<IngredientBatch | null>(null);
    const [batchEditData, setBatchEditData] = useState({
        supplier: '',
        quantity_initial: 0,
        quantity_remaining: 0,
        total_cost: 0,
        cost_per_unit: 0
    });

    // Stock Add State
    const [showAddStock, setShowAddStock] = useState(false);
    const [stockData, setStockData] = useState({
        quantity: 0,
        total_cost: 0,
        supplier: ''
    });

    useEffect(() => {
        loadBatches();
    }, [showAll]);

    const loadBatches = async () => {
        setLoading(true);
        try {
            // Using productId as ingredientId
            const data = await kitchenService.getIngredientBatches(productId, !showAll);

            // Normalize
            const safeNumber = (val: any) => isNaN(Number(val)) ? 0 : Number(val);
            const normalized = data.map(b => ({
                ...b,
                quantity_initial: safeNumber(b.quantity_initial),
                quantity_remaining: safeNumber(b.quantity_remaining),
                cost_per_unit: safeNumber(b.cost_per_unit),
                total_cost: safeNumber(b.total_cost) || (safeNumber(b.quantity_initial) * safeNumber(b.cost_per_unit))
            }));

            setBatches(normalized);
        } catch (error) {
            console.error("Error loading batches:", error);
            alert("Error cargando lotes. Asegúrate que este producto tenga seguimiento de inventario.");
        } finally {
            setLoading(false);
        }
    };

    const handleSaveBatchEdit = async () => {
        if (!editingBatch) return;
        try {
            await kitchenService.updateBatch(editingBatch.id, {
                supplier: batchEditData.supplier,
                quantity_initial: batchEditData.quantity_initial,
                quantity_remaining: batchEditData.quantity_remaining,
                total_cost: batchEditData.total_cost,
                cost_per_unit: batchEditData.cost_per_unit
            });
            setEditingBatch(null);
            await loadBatches();
        } catch (error) {
            console.error(error);
            alert("Error al actualizar lote");
        }
    };

    const handleDeleteBatch = async (batchId: string) => {
        if (!confirm("¿Eliminar este lote permanentemente? Se reducirá el stock.")) return;
        try {
            await kitchenService.deleteBatch(batchId);
            await loadBatches();
        } catch (error) {
            console.error(error);
            alert("Error eliminando lote");
        }
    };

    const handleAddStock = async () => {
        try {
            const unitCost = stockData.quantity > 0 ? stockData.total_cost / stockData.quantity : 0;

            await kitchenService.updateIngredientStock(
                productId,
                stockData.quantity,
                'IN',
                'Compra registrada desde Panel Bebidas',
                unitCost,
                stockData.supplier
            );

            setShowAddStock(false);
            setStockData({ quantity: 0, total_cost: 0, supplier: '' });
            await loadBatches();
            alert("Compra registrada correctamente");
        } catch (error) {
            console.error(error);
            alert("Error al registrar compra");
        }
    };

    const formatInputValue = (val: number) => val === 0 ? '' : val.toString();

    // Render Logic

    // Sub-render: Edit Modal
    if (editingBatch) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
                <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined">edit</span> Editar Lote
                    </h3>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Proveedor</label>
                        <input
                            value={batchEditData.supplier}
                            onChange={e => setBatchEditData({ ...batchEditData, supplier: e.target.value })}
                            className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Adquirido</label>
                            <input
                                type="number"
                                value={formatInputValue(batchEditData.quantity_initial)}
                                onChange={e => {
                                    const val = Number(e.target.value);
                                    setBatchEditData({
                                        ...batchEditData,
                                        quantity_initial: val,
                                        quantity_remaining: val, // Sync logic
                                        cost_per_unit: (val > 0 && batchEditData.total_cost > 0) ? batchEditData.total_cost / val : 0
                                    });
                                }}
                                className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Restante</label>
                            <input
                                type="number"
                                value={formatInputValue(batchEditData.quantity_remaining)}
                                onChange={e => setBatchEditData({ ...batchEditData, quantity_remaining: Number(e.target.value) })}
                                className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Costo Total</label>
                        <input
                            type="number"
                            value={formatInputValue(batchEditData.total_cost)}
                            onChange={e => {
                                const val = Number(e.target.value);
                                setBatchEditData({
                                    ...batchEditData,
                                    total_cost: val,
                                    cost_per_unit: batchEditData.quantity_initial > 0 ? val / batchEditData.quantity_initial : 0
                                });
                            }}
                            className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white"
                        />
                    </div>

                    <div className="flex justify-end gap-2 pt-4">
                        <button onClick={() => setEditingBatch(null)} className="px-4 py-2 text-gray-400">Cancelar</button>
                        <button onClick={handleSaveBatchEdit} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Guardar</button>
                    </div>
                </div>
            </div>
        );
    }

    // Sub-render: Add Stock Modal
    if (showAddStock) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
                <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined">add_shopping_cart</span> Nueva Compra
                    </h3>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Cantidad ({baseUnit})</label>
                        <input
                            type="number"
                            autoFocus
                            value={formatInputValue(stockData.quantity)}
                            onChange={e => setStockData({ ...stockData, quantity: Number(e.target.value) })}
                            className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white font-mono text-lg"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Costo Total ($)</label>
                        <input
                            type="number"
                            value={formatInputValue(stockData.total_cost)}
                            onChange={e => setStockData({ ...stockData, total_cost: Number(e.target.value) })}
                            className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white font-mono text-lg"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Proveedor (Opcional)</label>
                        <input
                            value={stockData.supplier}
                            onChange={e => setStockData({ ...stockData, supplier: e.target.value })}
                            className="w-full bg-bg-deep border border-border-dark rounded p-2 text-white"
                            placeholder="Ej. Makro"
                        />
                    </div>

                    <div className="flex justify-end gap-2 pt-4">
                        <button onClick={() => setShowAddStock(false)} className="px-4 py-2 text-gray-400">Cancelar</button>
                        <button onClick={handleAddStock} className="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700">Registrar</button>
                    </div>
                </div>
            </div>
        );
    }

    // Main Modal
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
                <div className="p-6 border-b border-border-dark bg-white/5 flex justify-between items-center">
                    <div>
                        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined">inventory_2</span>
                            Historial de Lotes: {productName}
                        </h3>
                        <p className="text-gray-500 text-xs">Gestiona las compras y existencias.</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="p-6 overflow-y-auto flex-1">
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">Cargando...</div>
                    ) : batches.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <span className="material-symbols-outlined text-4xl mb-2">inbox</span>
                            <p>No hay lotes registrados.</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {/* Summary Card */}
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 mb-4 flex justify-between items-center">
                                <div>
                                    <p className="text-emerald-300 font-medium text-xs uppercase">Total Invertido (Activo)</p>
                                    <p className="text-2xl font-bold text-emerald-400 font-mono">
                                        {formatCurrency(batches.reduce((sum, b) => sum + (b.quantity_remaining * b.cost_per_unit), 0))}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-gray-400 uppercase">Stock Total</p>
                                    <p className="text-xl font-bold text-white font-mono">
                                        {formatNumber(batches.reduce((sum, b) => sum + b.quantity_remaining, 0))} {baseUnit}
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end mb-2">
                                <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
                                    <input type="checkbox" checked={showAll} onChange={e => setShowAll(e.target.checked)} />
                                    Ver historial completo (Lotes en 0)
                                </label>
                            </div>

                            {batches.map((batch, idx) => (
                                <div key={batch.id} className="bg-bg-deep border border-border-dark rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                                                    Lote #{batches.length - idx}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {new Date(batch.acquired_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                            {batch.supplier && (
                                                <span className="text-xs bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded border border-amber-500/20">
                                                    🏢 {batch.supplier}
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-right">
                                            <div className="text-emerald-400 font-mono font-bold">{formatCurrency(batch.total_cost, 0)}</div>
                                            <div className="text-[10px] text-gray-500">{formatCurrency(batch.cost_per_unit, 0)} / {baseUnit}</div>
                                        </div>
                                    </div>

                                    <div className="mt-3 pt-2 border-t border-border-dark grid grid-cols-3 gap-2 text-xs">
                                        <div className="flex flex-col">
                                            <span className="text-gray-500">Comprado</span>
                                            <span className="font-mono text-white">{formatNumber(batch.quantity_initial)}</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-gray-500">Restante</span>
                                            <span className="font-mono text-amber-400">{formatNumber(batch.quantity_remaining)}</span>
                                        </div>
                                        <div className="flex flex-col text-right">
                                            <span className="text-gray-500">Acciones</span>
                                            <div className="flex justify-end gap-2 mt-1">
                                                <button onClick={() => {
                                                    setEditingBatch(batch);
                                                    setBatchEditData({
                                                        supplier: batch.supplier || '',
                                                        quantity_initial: batch.quantity_initial,
                                                        quantity_remaining: batch.quantity_remaining,
                                                        total_cost: batch.total_cost,
                                                        cost_per_unit: batch.cost_per_unit
                                                    });
                                                }} className="text-blue-400 hover:text-blue-300">
                                                    <span className="material-symbols-outlined text-[16px]">edit</span>
                                                </button>
                                                <button onClick={() => handleDeleteBatch(batch.id)} className="text-red-400 hover:text-red-300">
                                                    <span className="material-symbols-outlined text-[16px]">delete</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-border-dark flex justify-between">
                    <button
                        onClick={() => setShowAddStock(true)}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg flex items-center gap-2 hover:bg-emerald-700"
                    >
                        <span className="material-symbols-outlined">add_shopping_cart</span>
                        Registrar Compra
                    </button>
                    <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white">Cerrar</button>
                </div>
            </div>
        </div>
    );
};
