/**
 * IngredientManager - CRUD for Kitchen Ingredients (Insumos)
 * Uses the centralized kitchen.service
 */

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { kitchenService, Ingredient, IngredientCreate, IngredientBatch, ProductionDetail, ProductionInputDetail } from '../kitchen.service';
import { FactoryModal } from './FactoryModal';
import { ActionConfirmationModal } from './ActionConfirmationModal';


const HelpIcon = ({ text }: { text: string }) => (
    <span className="ml-1 text-gray-400 hover:text-white cursor-help" title={text}>
        <span className="material-symbols-outlined text-[14px] align-middle">help</span>
    </span>
);

const formatCurrency = (value: number, decimals: number = 0) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

// Formatear número con separadores de miles
// Default to 4 decimals for quantities as per FastOps standard
const formatNumber = (value: number, decimals: number = 4) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

const ProductionInputsView = ({ batchId }: { batchId: string }) => {
    const [details, setDetails] = useState<ProductionDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        kitchenService.getProductionByBatch(batchId)
            .then(setDetails)
            .catch((err: any) => {
                if (err.response && err.response.status === 404) {
                    // Legacy batch or missing production data - just show nothing
                    setDetails(null);
                } else {
                    console.error("Error loading production details:", err);
                }
            })
            .finally(() => setLoading(false));
    }, [batchId]);



    if (loading) return <div className="mt-2 text-[10px] text-text-muted animate-pulse">Cargando insumos...</div>;
    if (!details || !details.inputs || details.inputs.length === 0) return null;

    return (
        <div className="mt-2 bg-black/20 rounded p-2 border border-white/5">
            <p className="text-[10px] text-text-muted mb-2 font-semibold uppercase flex items-center gap-1">
                <span className="material-symbols-outlined text-[10px]">dismount</span>
                Insumos Consumidos
            </p>
            <div className="space-y-1">
                {details.inputs.map((input: ProductionInputDetail, idx: number) => {
                    const totalCost = input.cost_allocated || 0;
                    const unitCost = input.cost_per_unit || 0;

                    return (
                        <div key={idx} className="flex justify-between items-center text-xs border-b border-white/5 last:border-0 pb-1 last:pb-0">
                            <span className="text-gray-300">{input.ingredient_name}</span>
                            <div className="text-right">
                                <div className="font-mono text-amber-400/80">
                                    {formatNumber(input.quantity, 4)} {input.unit}
                                </div>
                                {(totalCost > 0) && (
                                    <div className="text-[10px] text-gray-500 font-mono">
                                        {formatCurrency(totalCost, 2)}
                                        <span className="mx-1 text-gray-600">
                                            ({formatCurrency(unitCost, 6)}/{input.unit})
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
            {details.notes && (
                <div className="mt-2 text-[10px] text-gray-500 italic border-t border-white/5 pt-1">
                    "{details.notes}"
                </div>
            )}
        </div>
    );
};

export const IngredientManager = () => {
    const [searchParams] = useSearchParams();
    const forcedTab = searchParams.get('tab') as 'RAW' | 'PROCESSED' | null;

    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<'RAW' | 'PROCESSED'>(forcedTab || 'RAW');
    const [viewMode, setViewMode] = useState<'MENU' | 'LIST' | 'INGRESAR'>('MENU');

    // Reset view mode when tab changes if in list? No, keep context.
    // Actually, if switching tabs in INGRESAR mode, might want to reset search.
    useEffect(() => {
        setSearchQuery('');
    }, [activeTab]);


    // Modal states
    const [showModal, setShowModal] = useState(false);
    const [showCostModal, setShowCostModal] = useState(false);
    const [showStockModal, setShowStockModal] = useState(false);
    const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
    const [selectedForCost, setSelectedForCost] = useState<Ingredient | null>(null);
    const [selectedForStock, setSelectedForStock] = useState<Ingredient | null>(null);

    // Form state
    const [formData, setFormData] = useState<Partial<IngredientCreate> & { initial_quantity?: number; total_cost_paid?: number }>({
        name: '',
        sku: '',
        base_unit: 'kg',
        current_cost: 0,
        yield_factor: 1.0,
        ingredient_type: 'RAW',
        initial_quantity: 0,
        total_cost_paid: 0
    });
    const [newCost, setNewCost] = useState(0);
    const [costReason] = useState('');

    // Stock Form state
    const [stockData, setStockData] = useState({
        quantity: 0,
        type: 'IN' as 'IN' | 'OUT' | 'ADJUST',
        reason: '',
        total_cost: 0,
        supplier: ''
    });

    // Batch viewer state
    const [showBatchModal, setShowBatchModal] = useState(false);
    const [selectedForBatches, setSelectedForBatches] = useState<Ingredient | null>(null);
    const [batchData, setBatchData] = useState<IngredientBatch[]>([]);
    const [loadingBatches, setLoadingBatches] = useState(false);

    // Cache de totales invertidos por ingrediente (suma de lotes)
    const [ingredientTotals, setIngredientTotals] = useState<Record<string, { totalInvested: number; batchCount: number }>>({});

    // Batch edit modal state  
    const [showBatchEditModal, setShowBatchEditModal] = useState(false);
    const [editingBatch, setEditingBatch] = useState<IngredientBatch | null>(null);
    const [batchEditData, setBatchEditData] = useState({
        supplier: '',
        quantity_initial: 0,
        quantity_remaining: 0,
        total_cost: 0,
        cost_per_unit: 0, // Read-only but kept in state
        is_active: true
    });

    // Factory Modal State
    const [showFactoryModal, setShowFactoryModal] = useState(false);
    const [showAllBatches, setShowAllBatches] = useState(false);

    // Deletion Modal State
    // Deletion Modal State
    // Action Confirmation Modal State
    // Action Confirmation Modal State
    const [actionModal, setActionModal] = useState({
        isOpen: false,
        title: '',
        variant: 'danger' as 'danger' | 'warning' | 'info' | 'success',
        confirmText: '',
        onConfirm: () => { },
        children: null as React.ReactNode
    });

    const closeActionModal = () => setActionModal(prev => ({ ...prev, isOpen: false }));

    const [showDeleted, setShowDeleted] = useState(false);

    useEffect(() => {
        loadIngredients();
    }, [showDeleted]);

    const loadIngredients = async () => {
        setLoading(true);
        try {
            // If showDeleted is true, we fetch ALL including inactive (activeOnly=false)
            // If showDeleted is false, we fetch ONLY active (activeOnly=true)
            const data = await kitchenService.getIngredients(undefined, undefined, !showDeleted);
            setIngredients(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error loading ingredients');
        } finally {
            setLoading(false);
        }
    };

    const filteredIngredients = useMemo(() => {
        let filtered = ingredients;

        if (showDeleted) {
            // Show ONLY inactive items when in "Recycle Bin" mode
            filtered = filtered.filter(i => !i.is_active);
        } else {
            // Show ONLY active items (though backend usually filters this, double check)
            // And filter by Tab Type
            filtered = filtered.filter(i => {
                const type = i.ingredient_type || 'RAW'; // Default to RAW if undefined
                return i.is_active && type === activeTab;
            });
        }

        // Filter by Search
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(i =>
                i.name.toLowerCase().includes(query) ||
                i.sku.toLowerCase().includes(query)
            );
        }
        return filtered;
    }, [ingredients, searchQuery, activeTab, showDeleted]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Calcular costo unitario si es creación y hay cantidad/total
            let calculatedCost = formData.current_cost || 0;
            if (!editingIngredient && formData.initial_quantity && formData.initial_quantity > 0 && formData.total_cost_paid && formData.total_cost_paid > 0) {
                calculatedCost = formData.total_cost_paid / formData.initial_quantity;
            }

            const payload = {
                ...formData,
                // Ensure empty SKU is sent as undefined so backend handles auto-generation
                sku: formData.sku?.trim() || undefined,
                current_cost: calculatedCost,
                ingredient_type: activeTab // Force type based on current tab
            };

            // Remover campos temporales antes de enviar
            delete (payload as any).initial_quantity;
            delete (payload as any).total_cost_paid;

            // Crear ingrediente
            const newIngredient = await kitchenService.createIngredient(payload as IngredientCreate);

            // Crear entrada de stock inicial si hay cantidad
            if (formData.initial_quantity && formData.initial_quantity > 0 && newIngredient?.id) {
                await kitchenService.updateIngredientStock(
                    newIngredient.id,
                    formData.initial_quantity,
                    'IN',
                    'Stock inicial al crear insumo',
                    calculatedCost,
                    undefined
                );
            }
            await loadIngredients();
            closeModal();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error saving ingredient');
        }
    };

    const confirmDelete = async (id: string) => {
        try {
            await kitchenService.deleteIngredient(id);
            await loadIngredients();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error deleting ingredient');
        }
    };

    const confirmRestore = async (id: string) => {
        try {
            await kitchenService.updateIngredient(id, { is_active: true });
            await loadIngredients();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error restoring ingredient');
        }
    };

    const handleDeleteClick = (ingredient: Ingredient) => {
        const isProcessed = ingredient.ingredient_type === 'PROCESSED';

        if (isProcessed) {
            setActionModal({
                isOpen: true,
                title: 'Advertencia de Eliminación',
                variant: 'warning',
                confirmText: 'Entiendo, Eliminar',
                onConfirm: () => confirmDelete(ingredient.id),
                children: (
                    <>
                        <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg p-4 text-sm text-gray-300 space-y-3 mb-4">
                            <p className="font-semibold text-amber-400 flex items-center gap-2">
                                <span className="material-symbols-outlined text-lg">info</span>
                                Estás a punto de eliminar un producto de Producción Interna.
                            </p>
                            <ul className="list-disc pl-5 space-y-1 text-gray-400">
                                <li>Esto <strong>SOLO ocultará</strong> el producto de la lista (Soft Delete).</li>
                                <li><strong>NO devolverá</strong> los insumos al inventario.</li>
                                <li><strong>NO revertirá</strong> los costos ni el historial de producción.</li>
                            </ul>
                        </div>
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 text-sm">
                            <p className="text-blue-300 font-medium mb-1">¿Buscas recuperar los insumos?</p>
                            <p className="text-gray-400">
                                Si esto fue un error de producción y quieres recuperar el stock de materia prima,
                                <strong> Cancelar</strong> y usa la opción de <strong>Ver Lotes (📦)</strong> para eliminar el lote específico.
                            </p>
                        </div>
                    </>
                )
            });
        } else {
            setActionModal({
                isOpen: true,
                title: '¿Eliminar Insumo?',
                variant: 'danger',
                confirmText: 'Eliminar Permanentemente',
                onConfirm: () => confirmDelete(ingredient.id),
                children: (
                    <div className="text-gray-300">
                        <p>Esta acción eliminará el insumo <strong>{ingredient.name}</strong> del sistema.</p>
                        <p className="mt-2 text-sm text-gray-500">
                            El historial se mantendrá, pero el insumo ya no aparecerá en los listados activos.
                        </p>
                    </div>
                )
            });
        }
    };

    const handleRestoreClick = (ingredient: Ingredient) => {
        setActionModal({
            isOpen: true,
            title: 'Restaurar Insumo',
            variant: 'info',
            confirmText: 'Restaurar',
            onConfirm: () => confirmRestore(ingredient.id),
            children: (
                <p>¿Estás seguro de que deseas restaurar el insumo <strong>{ingredient.name}</strong> a la lista activa?</p>
            )
        });
    };



    const handleUpdateStock = async () => {
        if (!selectedForStock) return;
        try {
            // Usar el costo unitario calculado (total / cantidad)
            const unitCost = stockData.quantity > 0 ? stockData.total_cost / stockData.quantity : 0;

            await kitchenService.updateIngredientStock(
                selectedForStock.id,
                stockData.quantity,
                stockData.type,
                stockData.reason,
                stockData.type === 'IN' && unitCost > 0 ? unitCost : undefined,
                stockData.type === 'IN' ? stockData.supplier : undefined
            );
            await loadIngredients();
            closeStockModal();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error updating stock');
        }
    };

    const handleUpdateCost = async () => {
        if (!selectedForCost) return;
        try {
            await kitchenService.updateIngredientCost(selectedForCost.id, newCost, costReason);
            await loadIngredients();
            closeCostModal();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error updating cost');
        }
    };

    const openCreate = () => {
        setEditingIngredient(null);
        setFormData({
            name: '',
            sku: '',
            base_unit: activeTab === 'RAW' ? 'kg' : 'und',
            current_cost: 0,
            yield_factor: 1.0,
            ingredient_type: activeTab,
            initial_quantity: 0,
            total_cost_paid: 0
        });
        setShowModal(true);
    };

    const openFactory = () => {
        setShowFactoryModal(true);
    };



    const openStockUpdate = (ingredient: Ingredient) => {
        setSelectedForStock(ingredient);
        setStockData({
            quantity: 0,
            type: 'IN',
            reason: '',
            total_cost: 0,
            supplier: ''
        });
        setShowStockModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingIngredient(null);
    };

    const closeCostModal = () => {
        setShowCostModal(false);
        setSelectedForCost(null);
    };

    const closeStockModal = () => {
        setShowStockModal(false);
        setSelectedForStock(null);
    };

    // Abrir modal de lotes
    const openBatchModal = async (ingredient: Ingredient) => {
        setSelectedForBatches(ingredient);
        setShowAllBatches(false); // Reset to active only by default
        await loadBatchesForIngredient(ingredient, false);
        setShowBatchModal(true);
    };

    const loadBatchesForIngredient = async (ingredient: Ingredient, showAll: boolean) => {
        setLoadingBatches(true);
        try {
            const batches = await kitchenService.getIngredientBatches(ingredient.id, !showAll); // backend expects 'active_only'
            console.log('Raw batches from API:', batches); // Debug

            // Función helper para asegurar número válido
            const safeNumber = (val: any): number => {
                if (val === null || val === undefined) return 0;
                const num = Number(val);
                return isNaN(num) ? 0 : num;
            };

            // Normalizar los datos de cada batch para asegurar valores numéricos
            const normalizedBatches = batches.map(b => {
                const qtyInitial = safeNumber(b.quantity_initial);
                const qtyRemaining = safeNumber(b.quantity_remaining);
                const costPerUnit = safeNumber(b.cost_per_unit);
                const totalCost = safeNumber(b.total_cost) || (qtyInitial * costPerUnit);

                return {
                    ...b,
                    quantity_initial: qtyInitial,
                    quantity_remaining: qtyRemaining,
                    cost_per_unit: costPerUnit,
                    total_cost: totalCost
                };
            });

            console.log('Normalized batches:', normalizedBatches); // Debug
            setBatchData(normalizedBatches);

            // Calcular total invertido con mayor precisión (Evitar error de redondeo de unit_cost)
            // Si hay total_cost y quantity_initial, usamos prorrateo: (remaining / initial) * total_cost
            const totalInvested = normalizedBatches.reduce((sum, b) => {
                if (b.quantity_initial > 0 && b.total_cost > 0) {
                    const proportion = b.quantity_remaining / b.quantity_initial;
                    return sum + (b.total_cost * proportion);
                }
                return sum + (b.quantity_remaining * b.cost_per_unit);
            }, 0);
            console.log('Total invested (Active Stock) [Precise]:', totalInvested); // Debug

            setIngredientTotals(prev => ({
                ...prev,
                [ingredient.id]: { totalInvested, batchCount: normalizedBatches.length }
            }));
        } catch (err) {
            console.error('Error loading batches', err);
            setBatchData([]);
        } finally {
            setLoadingBatches(false);
        }
    };

    const closeBatchModal = () => {
        setShowBatchModal(false);
        setSelectedForBatches(null);
        setBatchData([]);
    };

    // Abrir modal de edición de lote
    const openBatchEdit = (batch: IngredientBatch) => {
        setEditingBatch(batch);
        setBatchEditData({
            supplier: batch.supplier || '',
            quantity_initial: batch.quantity_initial,
            quantity_remaining: batch.quantity_remaining,
            total_cost: batch.total_cost,
            cost_per_unit: batch.cost_per_unit,
            is_active: true
        });
        setShowBatchEditModal(true);
    };

    // Cerrar modal de edición de lote
    const closeBatchEdit = () => {
        setShowBatchEditModal(false);
        setEditingBatch(null);
    };

    // Guardar cambios del lote
    const handleSaveBatchEdit = async () => {
        if (!editingBatch) return;

        try {
            await kitchenService.updateBatch(editingBatch.id, {
                supplier: batchEditData.supplier || undefined,
                quantity_initial: batchEditData.quantity_initial,
                quantity_remaining: batchEditData.quantity_remaining,
                total_cost: batchEditData.total_cost,
                cost_per_unit: batchEditData.cost_per_unit
            });
            closeBatchEdit();

            // Recargar lotes y lista principal
            if (selectedForBatches) {
                await openBatchModal(selectedForBatches);
            }
            await loadIngredients();
        } catch (err) {
            console.error('Error updating batch', err);
            alert('Error al actualizar el lote. Verifica que el backend esté corriendo.');
        }
    };

    // Execute batch deletion after confirmation
    const executeBatchDeletion = async (batchId: string) => {
        try {
            await kitchenService.deleteBatch(batchId);

            // 1. Recargar lotes del modal manteniendo el filtro actual
            if (selectedForBatches) {
                await loadBatchesForIngredient(selectedForBatches, showAllBatches);
            }

            // 2. Recargar lista principal de ingredientes (actualizar stock y costos globales)
            await loadIngredients();

        } catch (err) {
            console.error('Error deleting batch', err);
            alert('Error al eliminar el lote. Verifica que el backend esté corriendo.');
        }
    };

    // Eliminar lote (Trigger Modal)
    const handleDeleteBatch = async (batchId: string) => {
        const isProcessed = selectedForBatches?.ingredient_type === 'PROCESSED';

        if (isProcessed) {
            setActionModal({
                isOpen: true,
                title: '¿Deshacer Producción?',
                variant: 'warning',
                confirmText: 'Deshacer Producción',
                onConfirm: () => executeBatchDeletion(batchId),
                children: (
                    <div className="space-y-3">
                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-sm text-gray-300">
                            <p className="font-semibold text-amber-500 mb-1">Acción Reversible de Stock</p>
                            <p>Esto <strong>devolverá los insumos</strong> al inventario de Materia Prima y eliminará este registro de producto terminado.</p>
                        </div>
                        <p className="text-gray-400 text-sm">Esta acción es ideal si cometiste un error al registrar la producción.</p>
                    </div>
                )
            });
        } else {
            setActionModal({
                isOpen: true,
                title: '¿Eliminar Lote?',
                variant: 'danger',
                confirmText: 'Eliminar Lote',
                onConfirm: () => executeBatchDeletion(batchId),
                children: (
                    <div className="text-gray-300">
                        <p>Esta acción eliminará el registro de inventario <strong>permanentemente</strong>.</p>
                        <ul className="list-disc pl-5 mt-2 text-sm text-gray-400 space-y-1">
                            <li>El costo asociado a este lote desaparecerá.</li>
                            <li>El stock total se reducirá.</li>
                        </ul>
                    </div>
                )
            });
        }
    };



    // Convertir número a palabras en español
    const numberToWords = (num: number): string => {
        if (num === null || num === undefined || isNaN(num) || num === 0) return 'CERO PESOS';

        const units = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'];
        const teens = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'];
        const tens = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'];
        const hundreds = ['', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'];

        const roundedNum = Math.round(num);

        if (roundedNum < 0) return 'NÚMERO NEGATIVO';
        if (roundedNum < 10) return units[roundedNum] + ' PESO' + (roundedNum === 1 ? '' : 'S');
        if (roundedNum < 20) return teens[roundedNum - 10] + ' PESOS';
        if (roundedNum < 100) {
            const t = Math.floor(roundedNum / 10);
            const u = roundedNum % 10;
            if (u === 0) return tens[t] + ' PESOS';
            if (t === 2) return 'VEINTI' + units[u].toLowerCase() + ' PESOS';
            return tens[t] + ' Y ' + units[u] + ' PESOS';
        }
        if (roundedNum < 1000) {
            const h = Math.floor(roundedNum / 100);
            const rest = roundedNum % 100;
            if (rest === 0) return (h === 1 ? 'CIEN' : hundreds[h]) + ' PESOS';
            const prefix = h === 1 ? 'CIENTO' : hundreds[h];
            // Simplificado para resto
            if (rest < 10) return prefix + ' ' + units[rest] + ' PESOS';
            if (rest < 20) return prefix + ' ' + teens[rest - 10] + ' PESOS';
            const t = Math.floor(rest / 10);
            const u = rest % 10;
            if (u === 0) return prefix + ' ' + tens[t] + ' PESOS';
            return prefix + ' ' + tens[t] + ' Y ' + units[u] + ' PESOS';
        }
        if (roundedNum < 10000) {
            const k = Math.floor(roundedNum / 1000);
            const rest = roundedNum % 1000;
            const kWord = k === 1 ? 'MIL' : units[k] + ' MIL';
            if (rest === 0) return kWord + ' PESOS';
            if (rest < 100) return kWord + ' ' + rest + ' PESOS';
            return kWord + ' PESOS'; // Simplificado
        }
        if (roundedNum < 100000) {
            const k = Math.floor(roundedNum / 1000);
            return formatNumber(k) + ' MIL PESOS';
        }
        if (roundedNum < 1000000) {
            const k = Math.floor(roundedNum / 1000);
            return formatNumber(k) + ' MIL PESOS';
        }
        if (roundedNum < 1000000000) {
            const m = Math.floor(roundedNum / 1000000);
            const rest = roundedNum % 1000000;
            if (rest === 0) return (m === 1 ? 'UN MILLÓN' : formatNumber(m) + ' MILLONES') + ' DE PESOS';
            return (m === 1 ? 'UN MILLÓN' : formatNumber(m) + ' MILLONES') + ' ' + formatNumber(rest) + ' PESOS';
        }
        return formatNumber(roundedNum) + ' PESOS';
    };

    // Formatear input mientras el usuario escribe
    const formatInputValue = (value: number): string => {
        if (value === 0) return '';
        return formatNumber(value);
    };

    // Manejar cambio en input formateado
    const handleFormattedInput = (
        e: React.ChangeEvent<HTMLInputElement>,
        setter: (value: number) => void
    ) => {
        const rawValue = e.target.value;
        // Permitir solo números y puntos
        const cleaned = rawValue.replace(/[^\d]/g, '');
        const numValue = parseInt(cleaned, 10) || 0;
        setter(numValue);
    };
    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-orange"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-lg flex items-center gap-2">
                    <span className="material-symbols-outlined">error</span>
                    {error}
                </div>
            )}
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-accent-orange">
                            {activeTab === 'PROCESSED' ? 'factory' : 'nutrition'}
                        </span>
                        {activeTab === 'PROCESSED' ? 'Producción Interna' : 'Gestión de Insumos'}
                    </h1>
                    <p className="text-text-muted text-sm">
                        {activeTab === 'PROCESSED'
                            ? 'Gestión de recetas internas y productos semielaborados'
                            : 'Inventario de materia prima y compras'}
                    </p>
                </div>
                {/* Header Actions - Hide in MENU mode */}
                {viewMode !== 'MENU' && (
                    <div className="flex gap-2">
                        {/* Toggle Show Deleted */}
                        <button
                            onClick={() => {
                                const newShowDeleted = !showDeleted;
                                setShowDeleted(newShowDeleted);
                                // Auto-switch to LIST view when viewing deactivated items
                                if (newShowDeleted) {
                                    setViewMode('LIST');
                                }
                            }}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors font-medium border ${showDeleted
                                ? 'bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20'
                                : 'bg-transparent border-border-dark text-text-muted hover:text-white hover:bg-white/5'
                                }`}
                            title={showDeleted ? "Salir de Papelera" : "Ver Eliminados"}
                        >
                            <span className="material-symbols-outlined text-[20px]">
                                {showDeleted ? 'keyboard_return' : 'delete_sweep'}
                            </span>
                            {showDeleted ? 'Volver' : ''}
                        </button>

                        {!showDeleted && (
                            <button
                                onClick={activeTab === 'RAW' ? openCreate : openFactory}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors font-medium shadow-lg ${activeTab === 'RAW'
                                    ? 'bg-accent-orange hover:bg-orange-600 shadow-orange-500/20 text-white'
                                    : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20 text-white'
                                    }`}
                            >
                                <span className="material-symbols-outlined text-[20px]">{activeTab === 'RAW' ? 'add' : 'factory'}</span>
                                {activeTab === 'RAW' ? 'Crear Insumo' : 'Fábrica'}
                            </button>
                        )}
                    </div>
                )}
            </div>


            {/* Tabs - Only show if NOT in forced navigation mode */}
            {!forcedTab && (
                <div className="flex border-b border-border-dark">
                    <button
                        onClick={() => setActiveTab('RAW')}
                        className={`px-6 py-3 text-sm font-medium flex items-center gap-2 transition-colors border-b-2 ${activeTab === 'RAW'
                            ? 'border-accent-orange text-accent-orange'
                            : 'border-transparent text-text-muted hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <span className="material-symbols-outlined text-[18px]">local_shipping</span>
                        Materia Prima (Compras)
                    </button>
                    <button
                        onClick={() => setActiveTab('PROCESSED')}
                        className={`px-6 py-3 text-sm font-medium flex items-center gap-2 transition-colors border-b-2 ${activeTab === 'PROCESSED'
                            ? 'border-accent-purple text-accent-purple'
                            : 'border-transparent text-text-muted hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <span className="material-symbols-outlined text-[18px]">soup_kitchen</span>
                        Producciones Internas
                    </button>
                </div>
            )}

            {/* Content Logic */}
            <div className="flex flex-col gap-4">

                {/* MENU VIEW - Only show when NOT viewing deactivated items */}
                {viewMode === 'MENU' && !showDeleted && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                        {/* Card 1: Ingresar / Registrar */}
                        <button
                            onClick={() => setViewMode('INGRESAR')}
                            className="bg-card-dark border border-border-dark p-8 rounded-2xl hover:bg-white/5 transition-all group text-left relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <span className="material-symbols-outlined text-[120px] text-emerald-500">add_shopping_cart</span>
                            </div>
                            <div className="relative z-10">
                                <span className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 text-3xl group-hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined">add_shopping_cart</span>
                                </span>
                                <h3 className="text-xl font-bold text-white mb-2">
                                    {activeTab === 'RAW' ? 'Ingresar Compra' : 'Registrar Producción'}
                                </h3>
                                <p className="text-text-muted">
                                    {activeTab === 'RAW'
                                        ? 'Agregar stock de insumos o registrar facturas de compra.'
                                        : 'Registrar una nueva preparación o lote de producción.'}
                                </p>
                            </div>
                        </button>

                        {/* Card 2: Gestionar / Inventario */}
                        <button
                            onClick={() => setViewMode('LIST')}
                            className="bg-card-dark border border-border-dark p-8 rounded-2xl hover:bg-white/5 transition-all group text-left relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <span className="material-symbols-outlined text-[120px] text-blue-500">inventory_2</span>
                            </div>
                            <div className="relative z-10">
                                <span className="w-16 h-16 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center mb-4 text-3xl group-hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined">inventory_2</span>
                                </span>
                                <h3 className="text-xl font-bold text-white mb-2">
                                    {activeTab === 'RAW' ? 'Gestionar Inventario' : 'Historial de Producciones'}
                                </h3>
                                <p className="text-text-muted">
                                    Ver existencias, auditoría de lotes, costos y gestión general.
                                </p>
                            </div>
                        </button>
                    </div>
                )}

                {/* INGRESAR VIEW - Only show when NOT viewing deactivated items */}
                {viewMode === 'INGRESAR' && !showDeleted && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                        <div className="flex items-center justify-between mb-4">
                            <button
                                onClick={() => setViewMode('MENU')}
                                className="flex items-center gap-2 text-text-muted hover:text-white transition-colors"
                            >
                                <span className="material-symbols-outlined">arrow_back</span>
                                Volver al menú
                            </button>
                            <h2 className="text-lg font-semibold text-white">
                                {activeTab === 'RAW' ? 'Selecciona Insumo a Ingresar' : 'Selecciona Producto a Producir'}
                            </h2>
                        </div>

                        {/* Search Bar for Ingresar */}
                        <div className="relative mb-6">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500">search</span>
                            <input
                                type="text"
                                autoFocus
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Escribe el nombre para registrar compra..."
                                className="w-full bg-card-dark border border-emerald-500/30 rounded-xl pl-10 pr-4 py-4 text-white text-lg placeholder-text-muted focus:outline-none focus:border-emerald-500 shadow-lg shadow-emerald-500/5"
                            />
                        </div>

                        {/* List Grid for Selection */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {filteredIngredients.map(ingredient => (
                                <button
                                    key={ingredient.id}
                                    onClick={() => {
                                        if (activeTab === 'RAW') {
                                            openStockUpdate(ingredient);
                                        } else {
                                            // For Processed, maybe open Create Batch? Or same stock update?
                                            // Processed usually implies Factory. 
                                            // If "Registrar Produccion", we might want Factory Modal but pre-selected?
                                            // Currently FactoryModal is a global "Fabrica".
                                            // Maybe just open Stock Update (manual adjustment) or Factory.
                                            // For now, let's open Stock Update for 'IN' type, effectively adding stock manually.
                                            openStockUpdate(ingredient);
                                        }
                                    }}
                                    className="bg-card-dark border border-border-dark p-4 rounded-xl text-left hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all flex justify-between items-center group"
                                >
                                    <div>
                                        <div className="font-semibold text-white group-hover:text-emerald-300 transition-colors">{ingredient.name}</div>
                                        <div className="text-xs text-text-muted">{ingredient.sku}</div>
                                    </div>
                                    <span className="material-symbols-outlined text-border-dark group-hover:text-emerald-500">add_circle</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}


                {/* LIST VIEW (Original Table) */}
                {viewMode === 'LIST' && (
                    <>
                        <div className="flex items-center gap-2 mb-2">
                            <button
                                onClick={() => setViewMode('MENU')}
                                className="text-xs flex items-center gap-1 text-text-muted hover:text-white"
                            >
                                <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                                Volver al menú
                            </button>
                        </div>

                        {/* Search */}
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">search</span>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder={`Buscar ${activeTab === 'RAW' ? 'materia prima' : 'producción'} por nombre o SKU...`}
                                className="w-full bg-card-dark border border-border-dark rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-text-muted focus:outline-none focus:border-accent-orange"
                            />
                        </div>

                        {/* Table */}
                        <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden shadow-lg">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-bg-deep border-b border-border-dark">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Nombre / SKU</th>
                                            <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">
                                                Stock
                                            </th>
                                            {activeTab === 'RAW' && (
                                                <>
                                                    <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">Unidad Compra</th>
                                                    <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">Rendimiento</th>
                                                </>
                                            )}
                                            {activeTab === 'PROCESSED' && (
                                                <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">Unidad Stock</th>
                                            )}
                                            <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo Total Inv.</th>
                                            <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border-dark">
                                        {filteredIngredients.length === 0 ? (
                                            <tr>
                                                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                                                    No hay items de tipo {activeTab} registrados.
                                                </td>
                                            </tr>
                                        ) : (
                                            filteredIngredients.map((ingredient) => (
                                                <tr key={ingredient.id} className="hover:bg-white/5 transition-colors">
                                                    <td className="px-4 py-3">
                                                        <div className="font-medium text-white">{ingredient.name}</div>
                                                        <div className="text-xs text-text-muted">{ingredient.sku}</div>
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <div className="flex flex-col items-center">
                                                            <span className="font-mono text-white text-base font-semibold">
                                                                {new Intl.NumberFormat('es-CO', { maximumFractionDigits: 4 }).format((ingredient as any).stock || 0)}
                                                                <span className="text-xs text-text-muted ml-1">{ingredient.base_unit}</span>
                                                            </span>
                                                            <span className="text-[10px] text-amber-400/80 uppercase tracking-wide">
                                                                Total en inventario
                                                            </span>
                                                        </div>
                                                    </td>

                                                    <td className="px-4 py-3 text-center">
                                                        <span className="px-2 py-1 bg-white/5 rounded text-gray-300 text-xs font-mono">
                                                            {ingredient.base_unit}
                                                        </span>
                                                    </td>

                                                    {activeTab === 'RAW' && (
                                                        <td className="px-4 py-3 text-center">
                                                            <div className="flex items-center justify-center gap-2">
                                                                <div className="w-12 h-1.5 bg-bg-deep rounded-full overflow-hidden">
                                                                    <div
                                                                        className={`h-full ${ingredient.yield_factor >= 0.90 ? 'bg-emerald-400' : ingredient.yield_factor >= 0.80 ? 'bg-amber-400' : 'bg-red-400'}`}
                                                                        style={{ width: `${ingredient.yield_factor * 100}%` }}
                                                                    />
                                                                </div>
                                                                <span className="text-xs text-gray-400">{(ingredient.yield_factor * 100).toFixed(0)}%</span>
                                                            </div>
                                                        </td>
                                                    )}

                                                    <td className="px-4 py-3 text-right">
                                                        <div className="flex flex-col items-end">
                                                            {/* Mostrar total desde backend (más preciso) o cache de lotes */}
                                                            <span className="font-mono text-emerald-400 font-semibold">
                                                                {(ingredient as any).total_inventory_value != null && (ingredient as any).total_inventory_value > 0
                                                                    ? formatCurrency((ingredient as any).total_inventory_value, 2)
                                                                    : ingredientTotals[ingredient.id]
                                                                        ? formatCurrency(ingredientTotals[ingredient.id].totalInvested, 2)
                                                                        : formatCurrency(((ingredient as any).stock || 0) * ingredient.current_cost, 2)
                                                                }
                                                            </span>
                                                            <span className="text-[10px] text-text-muted">
                                                                {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 6 }).format(ingredient.current_cost)}/{ingredient.base_unit}
                                                            </span>
                                                        </div>
                                                    </td>

                                                    <td className="px-4 py-3 text-right">
                                                        <div className="flex items-center justify-end gap-1">
                                                            <button onClick={() => openBatchModal(ingredient)} className="p-1.5 text-purple-400 hover:bg-purple-500/10 rounded" title="Ver Lotes / Historial Compras">
                                                                <span className="material-symbols-outlined text-[18px]">inventory_2</span>
                                                            </button>

                                                            {showDeleted ? (
                                                                <button onClick={() => handleRestoreClick(ingredient)} className="p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded" title="Restaurar">
                                                                    <span className="material-symbols-outlined text-[18px]">restore_from_trash</span>
                                                                </button>
                                                            ) : (
                                                                <>
                                                                    {activeTab === 'RAW' && (
                                                                        <button onClick={() => openStockUpdate(ingredient)} className="p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded" title="Registrar Nueva Compra">
                                                                            <span className="material-symbols-outlined text-[18px]">add_shopping_cart</span>
                                                                        </button>
                                                                    )}

                                                                    <button onClick={() => handleDeleteClick(ingredient)} className="p-1.5 text-red-400 hover:bg-red-500/10 rounded" title="Eliminar">
                                                                        <span className="material-symbols-outlined text-[18px]">delete</span>
                                                                    </button>
                                                                </>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* Deletion Confirmation Modal */}


            {/* Create/Edit Modal */}
            {
                showModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md shadow-2xl">
                            <div className="p-6 border-b border-border-dark bg-white/5">
                                <h3 className="text-lg font-semibold text-white">
                                    {activeTab === 'RAW' ? 'Nueva Materia Prima' : 'Nueva Producción Interna'}
                                </h3>
                            </div>
                            <form onSubmit={handleSubmit} className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Nombre</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">SKU / Código</label>
                                    <input
                                        type="text"
                                        value={formData.sku}
                                        onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white placeholder-gray-600"
                                        placeholder="Opcional - Se generará automáticamente"
                                    />
                                    <p className="text-[10px] text-gray-500 mt-1">
                                        Dejar vacío para generar uno automático. Si usas código de barras, escanéalo aquí.
                                    </p>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">
                                            {activeTab === 'RAW' ? 'Unidad de Compra' : 'Unidad de Stock'}
                                        </label>
                                        <select
                                            value={formData.base_unit}
                                            onChange={(e) => setFormData({ ...formData, base_unit: e.target.value as any })}
                                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                        >
                                            <option value="kg">Kilogramo (kg)</option>
                                            <option value="g">Gramo (g)</option>
                                            <option value="lt">Litro (lt)</option>
                                            <option value="ml">Mililitro (ml)</option>
                                            <option value="und">Unidad (und)</option>
                                        </select>
                                    </div>
                                    <div>
                                        {/* SOLO al CREAR y es RAW: pedir cantidad */}
                                        {!editingIngredient && activeTab === 'RAW' ? (
                                            <>
                                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                                    📦 Cantidad Adquirida
                                                </label>
                                                <input
                                                    type="text"
                                                    inputMode="numeric"
                                                    value={formatInputValue(formData.initial_quantity || 0)}
                                                    onChange={(e) => handleFormattedInput(e, (val) => setFormData({ ...formData, initial_quantity: val }))}
                                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white font-mono text-lg"
                                                    placeholder={`Ej: 10.000`}
                                                />
                                            </>
                                        ) : activeTab === 'PROCESSED' ? (
                                            <>
                                                <label className="block text-sm font-medium text-gray-500 mb-1">Costo (Calculado)</label>
                                                <input
                                                    type="text"
                                                    value="Automático"
                                                    disabled
                                                    className="w-full bg-bg-deep/50 border border-border-dark rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
                                                />
                                            </>
                                        ) : null}
                                    </div>
                                </div>

                                {/* SOLO al CREAR y es RAW: pedir precio total pagado */}
                                {!editingIngredient && activeTab === 'RAW' && (
                                    <div className="space-y-4 p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                                        <div>
                                            <label className="block text-sm font-medium text-amber-300 mb-1">
                                                💰 Precio TOTAL que pagaste
                                            </label>
                                            <input
                                                type="text"
                                                inputMode="numeric"
                                                value={formatInputValue(formData.total_cost_paid || 0)}
                                                onChange={(e) => handleFormattedInput(e, (val) => setFormData({ ...formData, total_cost_paid: val }))}
                                                className="w-full bg-bg-deep border border-amber-500/30 rounded-lg px-3 py-2 text-white text-xl font-mono"
                                                placeholder="Ej: 80.000"
                                            />
                                            <p className="text-xs text-text-muted mt-1">
                                                Ingresa el total que pagaste por {formData.initial_quantity || 0} {formData.base_unit}
                                            </p>
                                        </div>

                                        {/* Costo Unitario Calculado */}
                                        {(formData.initial_quantity || 0) > 0 && (formData.total_cost_paid || 0) > 0 && (() => {
                                            const unitCost = (formData.total_cost_paid || 0) / (formData.initial_quantity || 1);
                                            const unitLabel = formData.base_unit === 'kg' ? 'kilogramo'
                                                : formData.base_unit === 'g' ? 'gramo'
                                                    : formData.base_unit === 'lt' ? 'litro'
                                                        : formData.base_unit === 'ml' ? 'mililitro'
                                                            : formData.base_unit === 'und' ? 'unidad'
                                                                : formData.base_unit;

                                            return (
                                                <div className="bg-emerald-500/10 border-2 border-emerald-500/40 rounded-xl p-4">
                                                    <div className="text-center">
                                                        <p className="text-xs text-emerald-300 uppercase tracking-wider mb-1">
                                                            Costo por cada {unitLabel}
                                                        </p>
                                                        <p className="text-3xl font-bold text-emerald-400 font-mono">
                                                            {new Intl.NumberFormat('es-CO', {
                                                                style: 'currency',
                                                                currency: 'COP',
                                                                minimumFractionDigits: unitCost < 100 ? 2 : 0,
                                                                maximumFractionDigits: unitCost < 100 ? 2 : 0
                                                            }).format(unitCost)}
                                                        </p>
                                                        <p className="text-xs text-amber-300 font-semibold mt-1 bg-amber-500/10 px-2 py-1 rounded inline-block">
                                                            ✍️ {numberToWords(unitCost)}
                                                        </p>
                                                        <p className="text-sm text-emerald-300 mt-2">
                                                            por cada <span className="font-bold">1 {formData.base_unit}</span>
                                                        </p>
                                                    </div>
                                                    <div className="mt-3 pt-3 border-t border-emerald-500/20 text-center">
                                                        <p className="text-xs text-text-muted">
                                                            📊 {formatCurrency(formData.total_cost_paid || 0)} ÷ {formatNumber(formData.initial_quantity || 0)} {formData.base_unit} = <span className="text-emerald-400 font-semibold">{formatCurrency(unitCost)}/{formData.base_unit}</span>
                                                        </p>
                                                    </div>
                                                </div>
                                            );
                                        })()}
                                    </div>
                                )}

                                {/* AL EDITAR: mostrar costo actual */}
                                {editingIngredient && activeTab === 'RAW' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">
                                            Costo Unitario Actual
                                            <HelpIcon text="Precio de compra por unidad base" />
                                        </label>
                                        <input
                                            type="number"
                                            value={formData.current_cost}
                                            onChange={(e) => setFormData({ ...formData, current_cost: Number(e.target.value) })}
                                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                        />
                                    </div>
                                )}

                                {activeTab === 'RAW' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center">
                                            Rendimiento (Yield) - {((formData.yield_factor || 1) * 100).toFixed(0)}%
                                            <HelpIcon text="Porcentaje aprovechable del insumo después de limpieza/merma." />
                                        </label>
                                        <input
                                            type="range"
                                            min="0.5"
                                            max="1"
                                            step="0.01"
                                            value={formData.yield_factor}
                                            onChange={(e) => setFormData({ ...formData, yield_factor: Number(e.target.value) })}
                                            className="w-full"
                                        />
                                    </div>
                                )}

                                <div className="flex justify-end gap-3 pt-4 border-t border-border-dark mt-4">
                                    <button type="button" onClick={closeModal} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Cancelar</button>
                                    <button type="submit" className="px-6 py-2 bg-accent-orange text-white rounded-lg hover:bg-orange-600 shadow-lg shadow-orange-500/20">
                                        {editingIngredient ? 'Guardar Cambios' : 'Crear Item'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )
            }

            {/* Cost Update Modal (Only for RAWS) */}
            {
                showCostModal && selectedForCost && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md">
                            <div className="p-6 border-b border-border-dark">
                                <h3 className="text-lg font-semibold text-white">Actualizar Costo</h3>
                                <p className="text-text-muted text-sm">{selectedForCost.name}</p>
                            </div>
                            <div className="p-6 space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-text-muted">Costo Actual:</span>
                                    <span className="text-white font-mono">{formatCurrency(selectedForCost.current_cost)}</span>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Nuevo Costo</label>
                                    <input
                                        type="number"
                                        value={newCost}
                                        onChange={(e) => setNewCost(Number(e.target.value))}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                    />
                                </div>
                                <div className="flex justify-end gap-3 pt-4">
                                    <button onClick={closeCostModal} className="px-4 py-2 text-gray-400">Cancelar</button>
                                    <button onClick={handleUpdateCost} className="px-4 py-2 bg-emerald-600 text-white rounded-lg">Actualizar</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            }
            {/* Stock Update Modal (PURCHASE MODE) */}
            {
                showStockModal && selectedForStock && (() => {
                    const currentStock = Number((selectedForStock as any).stock) || 0;
                    const adjustmentQty = Number(stockData.quantity) || 0;
                    // Force projection as IN since this is now a Purchase Module
                    const projectedStock = currentStock + adjustmentQty;

                    return (
                        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm animate-in fade-in duration-200">
                            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-xl shadow-2xl flex flex-col max-h-[90vh]">

                                {/* Header */}
                                <div className="p-6 border-b border-border-dark bg-emerald-500/5 flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                                                <span className="material-symbols-outlined text-[24px]">shopping_cart</span>
                                            </span>
                                            <h3 className="text-xl font-bold text-white">
                                                Registrar Nueva Compra
                                            </h3>
                                        </div>
                                        <p className="text-text-muted text-sm ml-11">Ingresa los detalles de la compra de <strong>{selectedForStock.name}</strong></p>
                                    </div>
                                    <div className="text-right hidden sm:block">
                                        <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Stock Actual</p>
                                        <p className="text-white font-mono font-bold text-lg">
                                            {formatNumber(currentStock, 4)} <span className="text-sm font-normal text-gray-400">{selectedForStock.base_unit}</span>
                                        </p>
                                    </div>
                                </div>

                                <div className="p-6 space-y-6 overflow-y-auto custom-scrollbar">

                                    {/* Main Inputs Grid */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                                        {/* Column 1: Quantity */}
                                        <div className="space-y-4">
                                            <label className="block text-sm font-medium text-gray-300">
                                                📦 Cantidad Comprada
                                            </label>
                                            <div className="relative group">
                                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                    <span className="material-symbols-outlined text-emerald-500 group-focus-within:text-emerald-400 transition-colors">add_circle</span>
                                                </div>
                                                <input
                                                    type="number"
                                                    inputMode="decimal"
                                                    step="any"
                                                    value={stockData.quantity || ''}
                                                    onChange={e => setStockData({ ...stockData, quantity: parseFloat(e.target.value) || 0, type: 'IN' })}
                                                    className="w-full bg-bg-deep border border-emerald-500/30 rounded-xl pl-10 pr-12 py-4 text-white font-mono text-2xl focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                                                    placeholder="0"
                                                    autoFocus
                                                />
                                                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                                                    <span className="text-emerald-500/50 font-mono text-sm uppercase font-bold">{selectedForStock.base_unit}</span>
                                                </div>
                                            </div>

                                            {/* New Stock Preview */}
                                            <div className="flex flex-col gap-1 text-xs bg-white/5 p-3 rounded-xl border border-white/5">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-text-muted">Nuevo Balance:</span>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-mono text-gray-400">{formatNumber(currentStock)}</span>
                                                        <span className="material-symbols-outlined text-[12px] text-emerald-500">arrow_forward</span>
                                                        <span className="font-mono font-bold text-emerald-400 text-lg">
                                                            {formatNumber(projectedStock)}
                                                        </span>
                                                    </div>
                                                </div>
                                                {/* DEBUG INFO - REMOVE LATER */}
                                                <div className="text-[10px] text-gray-600 font-mono text-right">
                                                    Raw: {currentStock} + {adjustmentQty} = {projectedStock}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Column 2: Cost */}
                                        <div className="space-y-4">
                                            <label className="block text-sm font-medium text-amber-300 flex items-center gap-2">
                                                💰 Costo Total (Pagado)
                                                <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30 uppercase tracking-wide">Importante</span>
                                            </label>
                                            <div className="relative group">
                                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                    <span className="material-symbols-outlined text-amber-500 group-focus-within:text-amber-400 transition-colors">payments</span>
                                                </div>
                                                <input
                                                    type="text"
                                                    inputMode="numeric"
                                                    value={formatInputValue(stockData.total_cost)}
                                                    onChange={e => handleFormattedInput(e, (val) => setStockData({ ...stockData, total_cost: val, type: 'IN' }))}
                                                    className="w-full bg-bg-deep border border-amber-500/30 rounded-xl pl-10 pr-4 py-4 text-white text-2xl font-mono focus:ring-2 focus:ring-amber-500/50 transition-all shadow-inner"
                                                    placeholder="$ 0"
                                                />
                                            </div>
                                            <p className="text-[10px] text-text-muted text-right">
                                                Ingresa el valor total de la factura por estos items.
                                            </p>
                                        </div>
                                    </div>

                                    {/* Supplier Input - Full Width */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">📍 Proveedor / Origen</label>
                                        <div className="relative group">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                <span className="material-symbols-outlined text-gray-500 group-focus-within:text-emerald-500 transition-colors">store</span>
                                            </div>
                                            <input
                                                type="text"
                                                value={stockData.supplier}
                                                onChange={e => setStockData({ ...stockData, supplier: e.target.value, type: 'IN' })}
                                                className="w-full bg-bg-deep border border-border-dark rounded-xl pl-10 pr-4 py-3 text-white focus:ring-2 focus:ring-emerald-500/30 transition-all placeholder-gray-600"
                                                placeholder="Ej: La Plaza, Makro, Fruver..."
                                            />
                                        </div>
                                    </div>

                                    {/* Unit Cost Calculation Card */}
                                    {(stockData.quantity > 0 && stockData.total_cost > 0) && (() => {
                                        const unitCost = stockData.total_cost / stockData.quantity;
                                        return (
                                            <div className="bg-gradient-to-br from-emerald-500/10 to-transparent border border-emerald-500/20 rounded-xl p-4 animate-in slide-in-from-bottom-2">
                                                <div className="flex justify-between items-center mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <span className="p-1.5 bg-emerald-500/20 rounded-lg text-emerald-400">
                                                            <span className="material-symbols-outlined text-[18px]">calculate</span>
                                                        </span>
                                                        <span className="text-xs font-semibold text-emerald-300 uppercase tracking-widest">Costo Unitario Calculado</span>
                                                    </div>
                                                </div>

                                                <div className="flex items-baseline justify-between">
                                                    <div className="flex items-baseline gap-1">
                                                        <span className="text-3xl font-bold text-emerald-400 font-mono tracking-tight">
                                                            {formatCurrency(unitCost)}
                                                        </span>
                                                        <span className="text-sm text-emerald-600 font-medium">/ {selectedForStock.base_unit}</span>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-[10px] text-emerald-400/60 font-mono block">
                                                            {formatCurrency(stockData.total_cost)} ÷ {formatNumber(stockData.quantity)}
                                                        </span>
                                                    </div>
                                                </div>
                                                <p className="text-[10px] text-amber-500/80 mt-2 font-medium bg-amber-500/5 inline-block px-2 py-1 rounded">
                                                    Este costo se promediará con el inventario actual.
                                                </p>
                                            </div>
                                        );
                                    })()}

                                </div>

                                <div className="p-6 border-t border-border-dark bg-bg-deep/50 rounded-b-2xl flex justify-end gap-3">
                                    <button
                                        onClick={closeStockModal}
                                        className="px-5 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors font-medium text-sm"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        onClick={() => { setStockData({ ...stockData, type: 'IN' }); handleUpdateStock(); }}
                                        className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-400 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-all font-bold flex items-center gap-2 group transform active:scale-95"
                                    >
                                        <span className="material-symbols-outlined group-hover:animate-bounce">save</span>
                                        Registrar Compra
                                    </button>
                                </div>
                            </div>
                        </div>
                    );
                })()
            }

            {/* Batch Viewer Modal */}
            {showBatchModal && selectedForBatches && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-border-dark bg-white/5">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined">inventory_2</span>
                                Historial de Lotes - {selectedForBatches.name}
                            </h3>
                            <p className="text-text-muted text-sm">Desglose de compras y costos por lote</p>
                        </div>

                        <div className="p-6 overflow-y-auto flex-1">
                            {loadingBatches ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="animate-spin w-8 h-8 border-2 border-accent-orange border-t-transparent rounded-full"></div>
                                </div>
                            ) : batchData.length === 0 ? (
                                <div className="text-center py-8 text-text-muted">
                                    <span className="material-symbols-outlined text-4xl mb-2">inbox</span>
                                    <p>No hay lotes activos registrados</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {/* Resumen Total */}
                                    <div className={`${selectedForBatches.ingredient_type === 'PROCESSED' ? 'bg-purple-500/10 border-purple-500/30' : 'bg-emerald-500/10 border-emerald-500/30'} border rounded-xl p-4 mb-4`}>
                                        <div className="flex justify-between items-center">
                                            <span className={`${selectedForBatches.ingredient_type === 'PROCESSED' ? 'text-purple-300' : 'text-emerald-300'} font-medium`}>
                                                {selectedForBatches.ingredient_type === 'PROCESSED' ? 'COSTO PRODUCCIÓN TOTAL' : 'TOTAL INVERTIDO'}
                                            </span>
                                            <span className={`text-2xl font-bold ${selectedForBatches.ingredient_type === 'PROCESSED' ? 'text-purple-400' : 'text-emerald-400'} font-mono`}>
                                                {formatCurrency(batchData.reduce((sum, b) => sum + (b.quantity_remaining * b.cost_per_unit), 0), 2)}
                                            </span>
                                        </div>
                                        <p className={`text-xs ${selectedForBatches.ingredient_type === 'PROCESSED' ? 'text-purple-400/70' : 'text-emerald-400/70'} mt-1`}>
                                            ✍️ {numberToWords(batchData.reduce((sum, b) => sum + (b.quantity_remaining * b.cost_per_unit), 0))}
                                        </p>
                                        <div className={`mt-2 pt-2 border-t ${selectedForBatches.ingredient_type === 'PROCESSED' ? 'border-purple-500/20' : 'border-emerald-500/20'} grid grid-cols-2 gap-4 text-sm`}>
                                            <div>
                                                <span className="text-text-muted">Stock Total:</span>
                                                <span className="text-white ml-2 font-mono">{formatNumber(batchData.reduce((sum, b) => sum + (b.quantity_remaining || 0), 0), 4)} {selectedForBatches.base_unit}</span>
                                            </div>
                                            <div>
                                                <span className="text-text-muted">Lotes activos:</span>
                                                <span className="text-white ml-2">{batchData.length}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Lista de Lotes */}
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="text-xs text-text-muted uppercase tracking-wider">
                                            {selectedForBatches.ingredient_type === 'PROCESSED' ? 'Historial de producción' : 'Detalle por lote'}
                                        </div>
                                        <label className="flex items-center gap-2 text-xs text-text-muted cursor-pointer hover:text-white transition-colors">
                                            <input
                                                type="checkbox"
                                                checked={showAllBatches}
                                                onChange={(e) => {
                                                    setShowAllBatches(e.target.checked);
                                                    if (selectedForBatches) {
                                                        loadBatchesForIngredient(selectedForBatches, e.target.checked);
                                                    }
                                                }}
                                                className="rounded border-border-dark bg-bg-dark text-emerald-500 focus:ring-emerald-500/20"
                                            />
                                            Ver historial completo
                                        </label>
                                    </div>
                                    {batchData.map((batch, idx) => (
                                        <div key={batch.id} className="bg-bg-deep border border-border-dark rounded-lg p-4">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                                                            {selectedForBatches.ingredient_type === 'PROCESSED' ? '#' : 'Lote #'} {batchData.length - idx}
                                                        </span>
                                                        <span className="text-xs text-text-muted">
                                                            📅 {new Date(batch.acquired_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                                                        </span>
                                                    </div>
                                                    {batch.supplier && (
                                                        <div className="mt-1">
                                                            <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">
                                                                {selectedForBatches.ingredient_type === 'PROCESSED' ? '🏭 Producción' : `🏢 ${batch.supplier}`}
                                                            </span>
                                                        </div>
                                                    )}

                                                    {/* Mostrar Inputs si es PROCESSED */}
                                                    {selectedForBatches.ingredient_type === 'PROCESSED' && (
                                                        <ProductionInputsView batchId={batch.id} />
                                                    )}
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-emerald-400 font-mono font-semibold">
                                                        {formatCurrency(batch.total_cost, 2)}
                                                    </div>
                                                    <div className="text-[10px] text-text-muted">
                                                        {formatCurrency(batch.cost_per_unit, 6)}/{selectedForBatches.base_unit}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="mt-3 pt-2 border-t border-border-dark grid grid-cols-3 gap-2 text-xs">
                                                <div>
                                                    <span className="text-text-muted">{selectedForBatches.ingredient_type === 'PROCESSED' ? 'Producido:' : 'Comprado:'}</span>
                                                    <span className="text-white ml-1 font-mono">{formatNumber(batch.quantity_initial, 4)}</span>
                                                </div>
                                                <div>
                                                    <span className="text-text-muted">Restante:</span>
                                                    <span className="text-amber-400 ml-1 font-mono">{formatNumber(batch.quantity_remaining, 4)}</span>
                                                </div>
                                                <div>
                                                    <span className="text-text-muted">Usado:</span>
                                                    <span className="text-red-400 ml-1 font-mono">{formatNumber(batch.quantity_initial - batch.quantity_remaining, 4)}</span>
                                                </div>
                                            </div>
                                            {/* Acciones del lote */}
                                            <div className="mt-3 pt-2 border-t border-border-dark flex justify-end gap-2">
                                                {selectedForBatches.ingredient_type !== 'PROCESSED' && (
                                                    <button
                                                        onClick={() => openBatchEdit(batch)}
                                                        className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30 flex items-center gap-1"
                                                        title="Editar lote"
                                                    >
                                                        <span className="material-symbols-outlined text-[14px]">edit</span>
                                                        Editar
                                                    </button>
                                                )}

                                                <button
                                                    onClick={() => handleDeleteBatch(batch.id)}
                                                    className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 flex items-center gap-1"
                                                    title={selectedForBatches.ingredient_type === 'PROCESSED' ? "Deshacer producción y devolver insumos" : "Eliminar lote"}
                                                >
                                                    <span className="material-symbols-outlined text-[14px]">
                                                        {selectedForBatches.ingredient_type === 'PROCESSED' ? 'undo' : 'delete'}
                                                    </span>
                                                    {selectedForBatches.ingredient_type === 'PROCESSED' ? 'Deshacer' : 'Eliminar'}
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-border-dark flex justify-between">
                            {selectedForBatches.ingredient_type !== 'PROCESSED' && selectedForBatches.is_active && (
                                <button
                                    onClick={() => {
                                        closeBatchModal();
                                        openStockUpdate(selectedForBatches);
                                    }}
                                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg flex items-center gap-2 hover:bg-emerald-700 transition-colors"
                                >
                                    <span className="material-symbols-outlined text-[18px]">add_shopping_cart</span>
                                    Registrar Nueva Compra
                                </button>
                            )}
                            <button onClick={closeBatchModal} className="px-4 py-2 text-gray-400 hover:text-white transition-colors ml-auto">
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Batch Edit Modal */}
            {showBatchEditModal && editingBatch && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
                    <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md">
                        <div className="p-6 border-b border-border-dark bg-white/5">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined">edit</span>
                                Editar Lote
                            </h3>
                            <p className="text-text-muted text-sm">Modifica los datos de este lote</p>
                        </div>

                        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar">

                            {/* Proveedor */}
                            <div>
                                <label className="block text-sm text-gray-300 mb-1">
                                    📍 Proveedor
                                </label>
                                <input
                                    type="text"
                                    value={batchEditData.supplier}
                                    onChange={e => setBatchEditData({ ...batchEditData, supplier: e.target.value })}
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                    placeholder="Ej: La Plaza, Makro"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Cantidad Inicial (Adquirida) */}
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">
                                        📥 Adquirido
                                    </label>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        value={formatInputValue(batchEditData.quantity_initial)}
                                        onChange={e => handleFormattedInput(e, (val) => {
                                            const newInitial = val;
                                            const newUnitCost = (newInitial > 0 && batchEditData.total_cost > 0)
                                                ? batchEditData.total_cost / newInitial
                                                : 0;

                                            setBatchEditData({
                                                ...batchEditData,
                                                quantity_initial: newInitial,
                                                quantity_remaining: newInitial, // Auto-sync: Si cambias adquirido, restante se iguala
                                                cost_per_unit: newUnitCost
                                            });
                                        })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white font-mono"
                                        placeholder="Cantidad inicial"
                                    />
                                    <p className="text-[10px] text-blue-300 mt-1 flex items-center gap-1">
                                        <span className="material-symbols-outlined text-[10px]">info</span>
                                        Al editar esto, el restante se igualará automáticamente.
                                    </p>
                                </div>

                                {/* Cantidad Restante */}
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">
                                        📦 Restante
                                    </label>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        value={formatInputValue(batchEditData.quantity_remaining)}
                                        onChange={e => handleFormattedInput(e, (val) => setBatchEditData({ ...batchEditData, quantity_remaining: val }))}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white font-mono"
                                        placeholder="Cantidad actual"
                                    />
                                    <p className="text-[10px] text-text-muted mt-1">
                                        Usado: {formatNumber(batchEditData.quantity_initial - batchEditData.quantity_remaining)}
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Costo Total */}
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">
                                        💰 Costo Total
                                    </label>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        value={formatInputValue(batchEditData.total_cost)}
                                        onChange={e => handleFormattedInput(e, (val) => {
                                            // Al cambiar costo total, recalculamos costo unitario
                                            const newTotal = val;
                                            const newUnitCost = (batchEditData.quantity_initial > 0)
                                                ? newTotal / batchEditData.quantity_initial
                                                : 0;

                                            setBatchEditData({
                                                ...batchEditData,
                                                total_cost: newTotal,
                                                cost_per_unit: newUnitCost
                                            });
                                        })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white font-mono"
                                        placeholder="Valor total pagado"
                                    />
                                </div>

                                {/* Costo Unitario */}
                                <div>
                                    <label className="block text-sm text-text-muted mb-1">
                                        🏷️ Costo Unitario (Calc)
                                    </label>
                                    <input
                                        type="text"
                                        readOnly
                                        disabled
                                        value={formatCurrency(batchEditData.cost_per_unit)}
                                        className="w-full bg-white/5 border border-border-dark rounded-lg px-3 py-2 text-gray-400 font-mono cursor-not-allowed"
                                        placeholder="Calculado autom."
                                    />
                                </div>
                            </div>

                            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-200">
                                <p>⚠️ Modificar estos valores afectará los cálculos de inventario y costos históricos.</p>
                            </div>
                        </div>

                        <div className="p-4 border-t border-border-dark flex justify-end gap-3">
                            <button onClick={closeBatchEdit} className="px-4 py-2 text-gray-400 hover:text-white">
                                Cancelar
                            </button>
                            <button onClick={handleSaveBatchEdit} className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2">
                                <span className="material-symbols-outlined text-[18px]">save</span>
                                Guardar Cambios
                            </button>
                        </div>
                    </div>
                </div>


            )}

            {/* Generic Action Modal */}
            <ActionConfirmationModal
                isOpen={actionModal.isOpen}
                onClose={closeActionModal}
                onConfirm={actionModal.onConfirm}
                title={actionModal.title}
                variant={actionModal.variant}
                confirmText={actionModal.confirmText}
            >
                {actionModal.children}
            </ActionConfirmationModal>

            <FactoryModal
                isOpen={showFactoryModal}
                onClose={() => setShowFactoryModal(false)}
                ingredients={ingredients}
                onSuccess={loadIngredients}
            />
        </div>
    );
};

export default IngredientManager;
