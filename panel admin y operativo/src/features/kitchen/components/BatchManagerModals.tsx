import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
    kitchenService,
    Ingredient,
    IngredientBatch,
    ProductionDetail,
    ProductionInputDetail
} from '../kitchen.service';
import { formatCurrency, formatNumber } from '@/utils/formatters';

// --- SUB-COMPONENT: ProductionInputsView ---
const ProductionInputsView = ({ batchId }: { batchId: string }) => {
    const [details, setDetails] = useState<ProductionDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        kitchenService.getProductionByBatch(batchId)
            .then(data => {
                if (mounted) setDetails(data);
            })
            .catch((err: any) => {
                if (mounted) {
                    if (err.response && err.response.status === 404) {
                        setDetails(null);
                    } else {
                        console.error("Error loading production details:", err);
                    }
                }
            })
            .finally(() => {
                if (mounted) setLoading(false);
            });

        return () => { mounted = false; };
    }, [batchId]);

    if (loading) return <div className="mt-2 text-[10px] text-text-muted animate-pulse">Cargando insumos...</div>;
    if (!details || !details.inputs || details.inputs.length === 0) return <div className="mt-2 text-[10px] text-text-muted italic">No hay detalles de insumos registrados.</div>;

    return (
        <div className="mt-2 bg-black/20 rounded p-2 border border-white/5 animate-in fade-in slide-in-from-top-1 duration-200">
            <p className="text-[10px] text-text-muted mb-2 font-semibold uppercase flex items-center gap-1">
                <span className="material-symbols-outlined text-[10px]">dismount</span>
                Insumos Consumidos
            </p>
            <div className="space-y-1">
                {details.inputs.map((input: ProductionInputDetail, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs border-b border-white/5 last:border-0 pb-1 last:pb-0">
                        <span className="text-gray-300">{input.ingredient_name}</span>
                        <div className="text-right">
                            <div className="font-mono text-amber-400/80">
                                {formatNumber(input.quantity, 4)} {input.unit}
                            </div>
                            {(input.cost_allocated || 0) > 0 && (
                                <div className="text-[10px] text-gray-500 font-mono">
                                    {formatCurrency(input.cost_allocated, 2)}
                                    <span className="mx-1 text-gray-600">
                                        ({formatCurrency(input.cost_per_unit || 0, 6)}/{input.unit})
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
            {details.notes && (
                <div className="mt-2 text-[10px] text-gray-500 italic border-t border-white/5 pt-1">
                    "{details.notes}"
                </div>
            )}
        </div>
    );
};

// --- SUB-COMPONENT: BatchItem (Memoized) ---
interface BatchItemProps {
    batch: IngredientBatch;
    ingredientType: string;
    baseUnit: string;
    isExpanded: boolean;
    onToggleDetails: (id: string) => void;
    onEdit: (batch: IngredientBatch) => void;
    onDelete: (id: string) => void;
    isFirstActiveBatch: boolean; // Added for the FIFO indicator
}

const BatchItem = React.memo(({
    batch,
    ingredientType,
    baseUnit,
    isExpanded,
    onToggleDetails,
    onEdit,
    onDelete,
    isFirstActiveBatch
}: BatchItemProps) => {
    const usagePercent = Math.min(100, Math.round(((batch.quantity_initial - batch.quantity_remaining) / batch.quantity_initial) * 100));
    const daysOld = Math.floor((new Date().getTime() - new Date(batch.acquired_at).getTime()) / (1000 * 3600 * 24));
    const isOld = daysOld > 30;

    return (
        <div className={`bg-bg-deep border rounded-xl overflow-hidden transition-all hover:border-white/20 ${batch.is_active ? 'border-border-dark' : 'border-red-900/20 opacity-60'}`}>
            {/* Header & Status */}
            <div className="px-4 py-3 bg-white/5 border-b border-white/5 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter ${batch.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                        {batch.is_active ? 'Activo' : 'Agotado'}
                    </span>
                    <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[14px] text-text-muted">calendar_today</span>
                        <span className="text-[11px] text-white font-bold">
                            {new Date(batch.acquired_at).toLocaleDateString()}
                        </span>
                    </div>
                    <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded bg-black/30 border ${isOld ? 'border-amber-500/30 text-amber-500' : 'border-white/5 text-text-muted'}`}>
                        <span className="material-symbols-outlined text-[12px]">{isOld ? 'warning' : 'schedule'}</span>
                        <span className="text-[9px] font-black uppercase tracking-tighter">
                            Hace {daysOld} días
                        </span>
                    </div>
                </div>

                {isFirstActiveBatch && (
                    <div className="animate-pulse flex items-center gap-1 bg-amber-500 text-white px-2 py-0.5 rounded-full">
                        <span className="material-symbols-outlined text-[12px]">priority_high</span>
                        <span className="text-[8px] font-black uppercase tracking-tighter">Próximo a agotar (FIFO)</span>
                    </div>
                )}
            </div>

            <div className="p-4">
                <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                        {batch.supplier && (
                            <div className="mb-3">
                                <div className="text-[8px] text-text-muted font-bold uppercase tracking-widest mb-1">Proveedor / Origen</div>
                                <span className="text-sm text-gray-200 font-bold flex items-center gap-2">
                                    <span className="material-symbols-outlined text-amber-500 text-base">store</span>
                                    {batch.supplier}
                                </span>
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-4 mt-2">
                            <div>
                                <div className="text-[8px] text-text-muted font-bold uppercase tracking-widest mb-1 underline decoration-emerald-500/50">Costo Adquisición</div>
                                <div className="text-lg font-black text-white font-mono leading-none">
                                    {formatCurrency(batch.total_cost, 2)}
                                </div>
                            </div>
                            <div>
                                <div className="text-[8px] text-text-muted font-bold uppercase tracking-widest mb-1 underline decoration-amber-500/50">Costo Unitario</div>
                                <div className="text-sm font-black text-amber-400 font-mono leading-none">
                                    {formatCurrency(batch.cost_per_unit, 4)}
                                    <span className="text-[10px] text-text-muted font-normal ml-1">/{baseUnit}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                        <div className={`w-14 h-14 rounded-full border-4 flex flex-col items-center justify-center ${usagePercent > 80 ? 'border-rose-500/30' : 'border-emerald-500/30'} bg-black/20`}>
                            <span className={`text-[11px] font-black ${usagePercent > 80 ? 'text-rose-400' : 'text-emerald-400'}`}>{100 - usagePercent}%</span>
                            <span className="text-[7px] text-text-muted font-bold uppercase">Libre</span>
                        </div>
                    </div>
                </div>

                <div className="mt-4 mb-4">
                    <div className="flex justify-between text-[9px] font-black uppercase tracking-wider mb-1.5">
                        <span className="text-text-muted">Progreso de Consumo</span>
                        <span className={usagePercent > 80 ? 'text-rose-400' : 'text-emerald-400'}>{usagePercent}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden border border-white/5">
                        <div
                            className={`h-full rounded-full transition-all duration-1000 ${usagePercent > 80 ? 'bg-gradient-to-r from-rose-600 to-rose-400' : 'bg-gradient-to-r from-emerald-600 to-emerald-400'}`}
                            style={{ width: `${usagePercent}%` }}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                    <div className="bg-black/40 p-2 rounded-lg border border-white/5 flex flex-col items-center text-center">
                        <span className="text-[8px] text-text-muted font-bold uppercase mb-1">Inicial</span>
                        <span className="text-xs text-white font-mono font-bold">{formatNumber(batch.quantity_initial)}</span>
                    </div>
                    <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 flex flex-col items-center text-center shadow-inner">
                        <span className="text-[8px] text-emerald-400 font-bold uppercase mb-1">Disponible</span>
                        <span className="text-xs text-emerald-300 font-mono font-black">{formatNumber(batch.quantity_remaining)}</span>
                    </div>
                    <div className="bg-rose-500/10 p-2 rounded-lg border border-rose-500/20 flex flex-col items-center text-center shadow-inner">
                        <span className="text-[8px] text-rose-400 font-bold uppercase mb-1">Consumido</span>
                        <span className="text-sm text-rose-300 font-mono font-bold leading-none">{formatNumber(batch.quantity_initial - batch.quantity_remaining)}</span>
                    </div>
                </div>

                {ingredientType === 'PROCESSED' && (
                    <div className="mt-4 border-t border-white/5 pt-3">
                        <button
                            onClick={() => onToggleDetails(batch.id)}
                            className="flex items-center gap-2 text-[10px] text-text-muted hover:text-white transition-colors w-full justify-center py-1 bg-black/20 rounded hover:bg-black/40"
                        >
                            <span className="material-symbols-outlined text-sm">
                                {isExpanded ? 'expand_less' : 'expand_more'}
                            </span>
                            {isExpanded ? 'Ocultar Insumos' : 'Ver Insumos Consumidos'}
                        </button>

                        {isExpanded && (
                            <ProductionInputsView batchId={batch.id} />
                        )}
                    </div>
                )}

                {batch.is_active && (
                    <div className="mt-4 flex justify-end gap-2">
                        {ingredientType !== 'PROCESSED' && (
                            <button
                                onClick={() => onEdit(batch)}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-[9px] bg-white/5 text-text-muted rounded-lg hover:bg-white/10 hover:text-white transition-all uppercase font-black tracking-widest"
                            >
                                <span className="material-symbols-outlined text-sm">edit</span>
                                Corregir
                            </button>
                        )}
                        <button
                            onClick={() => onDelete(batch.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-[9px] bg-rose-950/30 text-rose-500 rounded-lg hover:bg-rose-500 hover:text-white transition-all border border-rose-500/20 uppercase font-black tracking-widest"
                        >
                            <span className="material-symbols-outlined text-sm">{ingredientType === 'PROCESSED' ? 'history' : 'delete'}</span>
                            {ingredientType === 'PROCESSED' ? 'Deshacer Prod.' : 'Eliminar Lote'}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}, (prev, next) => {
    return (
        prev.batch.id === next.batch.id &&
        prev.batch.updated_at === next.batch.updated_at && // Check if batch data itself changed
        prev.batch.quantity_remaining === next.batch.quantity_remaining && // Specific check for remaining quantity
        prev.isExpanded === next.isExpanded && // Check if expanded state changed
        prev.ingredientType === next.ingredientType && // Check if ingredient type changed (unlikely but good for completeness)
        prev.baseUnit === next.baseUnit && // Check if base unit changed (unlikely)
        prev.isFirstActiveBatch === next.isFirstActiveBatch // Check for FIFO indicator
        // Functions (onToggleDetails, onEdit, onDelete) are assumed stable due to useCallback in parent
    );
});


// --- MAIN COMPONENT: BatchViewerModal ---
interface BatchViewerModalProps {
    ingredient: Ingredient;
    onClose: () => void;
    onDeleteBatch: (batchId: string) => Promise<void>;
    onEditBatch: (batch: IngredientBatch) => void;
    onRegisterNewPurchase: () => void;
}

export const BatchViewerModal: React.FC<BatchViewerModalProps> = ({
    ingredient,
    onClose,
    onDeleteBatch,
    onEditBatch,
    onRegisterNewPurchase
}) => {
    const [batches, setBatches] = useState<IngredientBatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [showHistory, setShowHistory] = useState(false);

    // Track which batches have their details expanded
    const [expandedBatches, setExpandedBatches] = useState<Set<string>>(new Set());

    const loadBatches = async () => {
        setLoading(true);
        try {
            const data = await kitchenService.getIngredientBatches(ingredient.id, !showHistory);
            setBatches(data);
        } catch (error) {
            console.error("Error loading batches:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadBatches();
    }, [ingredient.id, showHistory]);

    // Optimize calculations with useMemo
    const { totalInvested, avgCostPerUnit } = useMemo(() => {
        const remaining = batches.reduce((sum, b) => sum + b.quantity_remaining, 0);
        const invested = batches.reduce((sum, b) => sum + (b.quantity_remaining * b.cost_per_unit), 0);
        const avg = remaining > 0 ? invested / remaining : 0;
        return { totalInvested: invested, avgCostPerUnit: avg };
    }, [batches]);

    // Use useCallback for stable function references passed to memoized items
    const toggleBatchDetails = useCallback((batchId: string) => {
        setExpandedBatches(prev => {
            const newExpanded = new Set(prev);
            if (newExpanded.has(batchId)) {
                newExpanded.delete(batchId);
            } else {
                newExpanded.add(batchId);
            }
            return newExpanded;
        });
    }, []);

    const handleDelete = useCallback(async (batchId: string) => {
        await onDeleteBatch(batchId);
        // We reload batches, which will naturally update the list
        // Note: we can't easily memoize loadBatches without wrapping it too, 
        // but for now this is triggered by user action, so it's fine.
        // The important part is that scrolling doesn't lag.
        loadBatches();
    }, [onDeleteBatch, loadBatches]); // Added loadBatches to dependency array for completeness, though it's stable

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-border-dark bg-white/5">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined">inventory_2</span>
                        Historial de Lotes - {ingredient.name}
                    </h3>
                    <p className="text-text-muted text-sm">Auditoría de compras y costos por lote</p>
                </div>

                <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full"></div>
                        </div>
                    ) : (
                        <>
                            {/* Summary Cards Grid */}
                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className={`${ingredient.ingredient_type === 'PROCESSED' ? 'bg-purple-500/10 border-purple-500/30' : 'bg-emerald-500/10 border-emerald-500/30'} border rounded-xl p-4 shadow-lg shadow-black/20 relative overflow-hidden`}>
                                    <div className="absolute top-0 right-0 p-2 opacity-10">
                                        <span className="material-symbols-outlined text-4xl">payments</span>
                                    </div>
                                    <span className={`${ingredient.ingredient_type === 'PROCESSED' ? 'text-purple-300' : 'text-emerald-300'} font-black text-[10px] uppercase tracking-widest block mb-1`}>
                                        {ingredient.ingredient_type === 'PROCESSED' ? 'Costo Producción Total' : 'Inversión Actual'}
                                    </span>
                                    <div className={`text-xl font-black ${ingredient.ingredient_type === 'PROCESSED' ? 'text-purple-400' : 'text-emerald-400'} font-mono`}>
                                        {formatCurrency(totalInvested, 2)}
                                    </div>
                                    <p className={`text-[8px] ${ingredient.ingredient_type === 'PROCESSED' ? 'text-purple-400/50' : 'text-emerald-400/50'} mt-1 font-bold uppercase`}>
                                        En {batches.length} lotes activos
                                    </p>
                                </div>

                                <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 shadow-lg shadow-black/20 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-2 opacity-10">
                                        <span className="material-symbols-outlined text-4xl">calculate</span>
                                    </div>
                                    <span className="text-amber-300 font-black text-[10px] uppercase tracking-widest block mb-1">
                                        Costo Promedio (WAC)
                                    </span>
                                    <div className="text-xl font-black text-amber-400 font-mono">
                                        {formatCurrency(avgCostPerUnit, 2)}
                                    </div>
                                    <p className="text-[8px] text-amber-400/50 mt-1 font-bold uppercase">
                                        Por {ingredient.base_unit}
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-between items-center mb-4">
                                <span className="text-xs text-text-muted uppercase tracking-widest font-bold">Detalle por lote</span>
                                <label className="flex items-center gap-2 text-xs text-text-muted cursor-pointer hover:text-white transition-colors bg-white/5 px-2 py-1 rounded">
                                    <input
                                        type="checkbox"
                                        checked={showHistory}
                                        onChange={(e) => setShowHistory(e.target.checked)}
                                        className="rounded border-border-dark bg-bg-dark text-emerald-500 focus:ring-emerald-500/20"
                                    />
                                    Ver historial agotado
                                </label>
                            </div>

                            <div className="space-y-3">
                                {batches.length === 0 ? (
                                    <div className="text-center py-12 text-text-muted bg-white/5 border border-dashed border-border-dark rounded-xl">
                                        <span className="material-symbols-outlined text-4xl mb-2 opacity-20">inbox</span>
                                        <p>No hay lotes que coincidan con el filtro</p>
                                    </div>
                                ) : (
                                    batches.map((batch, idx) => (
                                        <BatchItem
                                            key={batch.id}
                                            batch={batch}
                                            ingredientType={ingredient.ingredient_type}
                                            baseUnit={ingredient.base_unit}
                                            isExpanded={expandedBatches.has(batch.id)}
                                            onToggleDetails={toggleBatchDetails}
                                            onEdit={onEditBatch}
                                            onDelete={handleDelete}
                                            isFirstActiveBatch={idx === 0 && batch.is_active}
                                        />
                                    ))
                                )}
                            </div>
                        </>
                    )}
                </div>

                <div className="p-4 border-t border-border-dark bg-bg-deep/50 flex justify-between items-center">
                    {ingredient.is_active && ingredient.ingredient_type !== 'PROCESSED' && (
                        <button
                            onClick={onRegisterNewPurchase}
                            className="px-4 py-2 bg-emerald-600 text-white rounded-lg flex items-center gap-2 hover:bg-emerald-700 transition-all font-bold text-sm shadow-lg shadow-emerald-900/20"
                        >
                            <span className="material-symbols-outlined text-[18px]">add_shopping_cart</span>
                            Nueva Compra
                        </button>
                    )}
                    <button onClick={onClose} className="px-6 py-2 text-text-muted hover:text-white transition-colors ml-auto font-medium text-sm">
                        Cerrar Auditoría
                    </button>
                </div>
            </div>
        </div>
    );
};

// --- MAIN COMPONENT: BatchEditModal ---
interface BatchEditModalProps {
    batch: IngredientBatch;
    onClose: () => void;
    onSave: (updates: any) => Promise<void>;
}

export const BatchEditModal: React.FC<BatchEditModalProps> = ({
    batch,
    onClose,
    onSave
}) => {
    const [editData, setEditData] = useState({
        supplier: batch.supplier || '',
        quantity_initial: batch.quantity_initial,
        quantity_remaining: batch.quantity_remaining,
        total_cost: batch.total_cost,
        cost_per_unit: batch.cost_per_unit
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSave = async () => {
        setIsSubmitting(true);
        try {
            await onSave(editData);
            onClose();
        } catch (error) {
            console.error("Error saving batch edit:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[60] p-4 backdrop-blur-md">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="p-6 border-b border-border-dark bg-blue-500/5">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-blue-400">edit_note</span>
                        Corrección Manual de Lote
                    </h3>
                    <p className="text-text-muted text-xs mt-1">Modifica los valores registrados originalmente para este lote.</p>
                </div>

                <div className="p-6 space-y-5">
                    <div>
                        <label className="block text-[10px] text-text-muted uppercase tracking-widest mb-1.5 font-bold">Proveedor / Origen</label>
                        <input
                            type="text"
                            value={editData.supplier}
                            onChange={e => setEditData({ ...editData, supplier: e.target.value })}
                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:border-blue-500 transition-colors"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-[10px] text-text-muted uppercase tracking-widest mb-1.5 font-bold">Cant. Adquirida</label>
                            <input
                                type="number"
                                step="any"
                                value={editData.quantity_initial}
                                onChange={e => {
                                    const val = parseFloat(e.target.value) || 0;
                                    setEditData({
                                        ...editData,
                                        quantity_initial: val,
                                        cost_per_unit: val > 0 ? editData.total_cost / val : 0
                                    });
                                }}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white font-mono"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] text-text-muted uppercase tracking-widest mb-1.5 font-bold">Cant. Restante</label>
                            <input
                                type="number"
                                step="any"
                                value={editData.quantity_remaining}
                                onChange={e => setEditData({ ...editData, quantity_remaining: parseFloat(e.target.value) || 0 })}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white font-mono"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-[10px] text-text-muted uppercase tracking-widest mb-1.5 font-bold">Costo Total Factura</label>
                            <input
                                type="number"
                                step="any"
                                value={editData.total_cost}
                                onChange={e => {
                                    const val = parseFloat(e.target.value) || 0;
                                    setEditData({
                                        ...editData,
                                        total_cost: val,
                                        cost_per_unit: editData.quantity_initial > 0 ? val / editData.quantity_initial : 0
                                    });
                                }}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white font-mono"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] text-text-muted uppercase tracking-widest mb-1.5 font-bold">Costo Unit. (Auto)</label>
                            <div className="bg-white/5 border border-border-dark rounded-lg px-4 py-2.5 text-blue-400 font-mono text-sm h-[42px] flex items-center">
                                {formatCurrency(editData.cost_per_unit, 4)}
                            </div>
                        </div>
                    </div>

                    <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex gap-3">
                        <span className="material-symbols-outlined text-amber-500 text-sm">warning</span>
                        <p className="text-[10px] text-amber-200/80">
                            <strong>Atención:</strong> Estas modificaciones son directas a la base de datos y podrían causar discrepancias en reportes históricos. Úsalas solo para correcciones manuales.
                        </p>
                    </div>
                </div>

                <div className="p-4 border-t border-border-dark flex justify-end gap-3 bg-bg-deep/30">
                    <button onClick={onClose} disabled={isSubmitting} className="px-4 py-2 text-text-muted hover:text-white font-medium">Cancelar</button>
                    <button
                        onClick={handleSave}
                        disabled={isSubmitting}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all font-bold shadow-lg shadow-blue-900/20 flex items-center gap-2"
                    >
                        {isSubmitting ? <div className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> : <span className="material-symbols-outlined text-sm">save</span>}
                        Guardar Cambios
                    </button>
                </div>
            </div>
        </div>
    );
};
