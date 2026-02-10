/**
 * IngredientManager - CRUD for Kitchen Ingredients (Insumos)
 * Uses the centralized kitchen.service
 */

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { kitchenService, Ingredient, IngredientCreate, IngredientUpdate, IngredientBatch } from '../kitchen.service';
import { FactoryModal } from './FactoryModal';
import { ActionConfirmationModal } from './ActionConfirmationModal';
import { StockUpdateModal } from './StockUpdateModal';
import { BatchViewerModal, BatchEditModal } from './BatchManagerModals';
import { IngredientFormModal, CostUpdateModal } from './IngredientFormModals';
import { GlobalAuditHistoryModal, InventoryHistoryModal } from './HistoryModals';
import {
    formatCurrency,
    formatInputValue
} from '@/utils/formatters';



export const IngredientManager = () => {
    const [searchParams] = useSearchParams();
    const forcedTab = searchParams.get('tab') as 'RAW' | 'PROCESSED' | null;

    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<'RAW' | 'PROCESSED'>(forcedTab || 'RAW');
    const [viewMode, setViewMode] = useState<'MENU' | 'LIST' | 'INGRESAR'>('MENU');

    // Reset view mode or force LIST for PROCESSED
    useEffect(() => {
        if (activeTab === 'PROCESSED') {
            setViewMode('LIST');
        } else {
            // Optional: Reset to MENU when switching back to RAW? 
            // The user might prefer to stay in LIST if they were there. 
            // For now, let's reset search but keep viewMode flexible or default to MENU for RAW if desired.
            // But per request, only PROCESSED needs to skip menu.
            setSearchQuery('');
            if (viewMode === 'INGRESAR') setViewMode('MENU'); // Reset INGRESAR but keep LIST/MENU context
        }
    }, [activeTab]);


    // Modal states
    const [showModal, setShowModal] = useState(false);
    const [showStockModal, setShowStockModal] = useState(false);
    const [showBatchModal, setShowBatchModal] = useState(false);
    const [showBatchEditModal, setShowBatchEditModal] = useState(false);

    const [selectedForHistory, setSelectedForHistory] = useState<Ingredient | null>(null);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [isGlobalHistoryOpen, setIsGlobalHistoryOpen] = useState(false);
    const [globalHistoryFilter, setGlobalHistoryFilter] = useState<'all' | 'audit'>('all');

    const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
    const [selectedForCost, setSelectedForCost] = useState<Ingredient | null>(null);
    const [selectedForStock, setSelectedForStock] = useState<Ingredient | null>(null);
    const [selectedForBatches, setSelectedForBatches] = useState<Ingredient | null>(null);
    const [editingBatch, setEditingBatch] = useState<IngredientBatch | null>(null);

    // Form states
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
    // Factory Modal State
    const [showFactoryModal, setShowFactoryModal] = useState(false);

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
            if (editingIngredient) {
                // Update existing
                await kitchenService.updateIngredient(editingIngredient.id, formData as IngredientUpdate);
            } else {
                // Create new + handle initial stock
                const { initial_quantity, total_cost_paid, ...coreData } = formData;
                await kitchenService.createIngredientWithStock(
                    { ...coreData, ingredient_type: activeTab } as IngredientCreate,
                    initial_quantity,
                    total_cost_paid
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




    const closeCostModal = () => {
        setSelectedForCost(null);
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
        setShowStockModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingIngredient(null);
    };

    // Abrir modal de lotes
    const openBatchModal = (ingredient: Ingredient) => {
        setSelectedForBatches(ingredient);
        setShowBatchModal(true);
    };

    // Abrir modal de historial (Kardex)
    const openHistoryModal = (ingredient: Ingredient) => {
        setSelectedForHistory(ingredient);
        setShowHistoryModal(true);
    };


    // Execute batch deletion after confirmation
    const executeBatchDeletion = async (batchId: string) => {
        try {
            await kitchenService.deleteBatch(batchId);

            // 2. Recargar lista principal de ingredientes (actualizar stock y costos globales)
            await loadIngredients();

            // Note: BatchViewerModal will handle its own refresh if needed, 
            // but since we are calling this FROM the modal, we might want to tell it.
            // However, the modal should probably refresh when the promise resolves.

        } catch (err) {
            console.error('Error deleting batch', err);
            alert('Error al eliminar el lote. Verifica que el backend esté corriendo.');
        }
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
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary"></div>
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
                        <span className="material-symbols-outlined text-accent-primary">
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
                                    ? 'bg-accent-primary hover:bg-orange-600 shadow-orange-500/20 text-white'
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
                            ? 'border-accent-primary text-accent-primary'
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

                {/* MENU VIEW - Only show when NOT viewing deactivated items AND NOT in PROCESSED tab */}
                {viewMode === 'MENU' && !showDeleted && activeTab !== 'PROCESSED' && (
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

                        {/* Card 3: Kardex General */}
                        <button
                            onClick={() => {
                                setGlobalHistoryFilter('all');
                                setIsGlobalHistoryOpen(true);
                            }}
                            className="bg-card-dark border border-border-dark p-8 rounded-2xl hover:bg-white/5 transition-all group text-left relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <span className="material-symbols-outlined text-[120px] text-amber-500">list_alt</span>
                            </div>
                            <div className="relative z-10">
                                <span className="w-16 h-16 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center mb-4 text-3xl group-hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined">list_alt</span>
                                </span>
                                <h3 className="text-xl font-bold text-white mb-2">Kardex General</h3>
                                <p className="text-text-muted">
                                    Historial completo de todos los movimientos de inventario del sistema.
                                </p>
                            </div>
                        </button>

                        {/* Card 4: Auditorías */}
                        <button
                            onClick={() => {
                                setGlobalHistoryFilter('audit');
                                setIsGlobalHistoryOpen(true);
                            }}
                            className="bg-card-dark border border-border-dark p-8 rounded-2xl hover:bg-white/5 transition-all group text-left relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <span className="material-symbols-outlined text-[120px] text-rose-500">gavel</span>
                            </div>
                            <div className="relative z-10">
                                <span className="w-16 h-16 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mb-4 text-3xl group-hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined">gavel</span>
                                </span>
                                <h3 className="text-xl font-bold text-white mb-2">Auditorías</h3>
                                <p className="text-text-muted">
                                    Ver solo los ajustes manuales y correcciones de preventa.
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
                            {/* Hide Back button in PROCESSED mode as there is no Menu */}
                            {activeTab !== 'PROCESSED' && (
                                <button
                                    onClick={() => setViewMode('MENU')}
                                    className="text-xs flex items-center gap-1 text-text-muted hover:text-white"
                                >
                                    <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                                    Volver al menú
                                </button>
                            )}
                        </div>

                        {/* Search */}
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">search</span>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder={`Buscar ${activeTab === 'RAW' ? 'materia prima' : 'producción'} por nombre o SKU...`}
                                className="w-full bg-card-dark border border-border-dark rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-text-muted focus:outline-none focus:border-accent-primary"
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
                                                            {/* Trust backend's calculated total value */}
                                                            <span className="font-mono text-emerald-400 font-semibold">
                                                                {formatCurrency((ingredient as any).total_inventory_value || 0, 2)}
                                                            </span>
                                                            <span className="text-[10px] text-text-muted">
                                                                {formatCurrency((ingredient as any).calculated_cost || ingredient.current_cost, 2)}/{ingredient.base_unit}
                                                            </span>
                                                        </div>
                                                    </td>

                                                    <td className="px-4 py-3 text-right">
                                                        <div className="flex items-center justify-end gap-1">
                                                            <button
                                                                onClick={() => openBatchModal(ingredient)}
                                                                className="p-1.5 text-purple-400 hover:bg-purple-500/10 rounded"
                                                                title="Auditoría de Lotes"
                                                            >
                                                                <span className="material-symbols-outlined text-[18px]">inventory_2</span>
                                                            </button>

                                                            <button
                                                                onClick={() => openHistoryModal(ingredient)}
                                                                className="p-1.5 text-amber-400 hover:bg-amber-500/10 rounded"
                                                                title="Kardex (Historial)"
                                                            >
                                                                <span className="material-symbols-outlined text-[18px]">history</span>
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


            {/* MODALS SECTION */}

            {showStockModal && selectedForStock && (
                <StockUpdateModal
                    ingredient={selectedForStock}
                    onClose={() => setShowStockModal(false)}
                    onUpdate={async (quantity, totalCost, supplier) => {
                        if (!selectedForStock) return;
                        await kitchenService.addStockPurchase(
                            selectedForStock.id,
                            quantity,
                            totalCost,
                            supplier
                        );
                        await loadIngredients();
                    }}
                />
            )}

            <IngredientFormModal
                isOpen={showModal}
                activeTab={activeTab}
                editingIngredient={editingIngredient}
                formData={formData}
                setFormData={setFormData}
                onClose={closeModal}
                onSubmit={handleSubmit}
                handleFormattedInput={(e, setter) => {
                    const rawValue = e.target.value.replace(/[^0-9]/g, '');
                    const numericValue = parseInt(rawValue, 10) || 0;
                    setter(numericValue);
                }}
            />

            {selectedForCost && (
                <CostUpdateModal
                    isOpen={!!selectedForCost}
                    ingredient={selectedForCost}
                    onClose={closeCostModal}
                    onUpdate={async (newCostValue) => {
                        if (!selectedForCost) return;
                        await kitchenService.updateIngredientCost(selectedForCost.id, newCostValue, 'Manual update');
                        await loadIngredients();
                        closeCostModal();
                    }}
                />
            )}

            {showBatchModal && selectedForBatches && (
                <BatchViewerModal
                    ingredient={selectedForBatches}
                    onClose={() => setShowBatchModal(false)}
                    onDeleteBatch={executeBatchDeletion}
                    onEditBatch={(batch) => {
                        setEditingBatch(batch);
                        setShowBatchEditModal(true);
                    }}
                    onRegisterNewPurchase={() => {
                        setShowBatchModal(false);
                        openStockUpdate(selectedForBatches);
                    }}
                />
            )}

            {showBatchEditModal && editingBatch && (
                <BatchEditModal
                    batch={editingBatch}
                    onClose={() => setShowBatchEditModal(false)}
                    onSave={async (updates) => {
                        await kitchenService.updateBatch(editingBatch.id, updates);
                        await loadIngredients();
                        if (selectedForBatches) {
                            // Refresh viewer data implicitly (re-render will fetch new data if needed or we could add a trigger)
                        }
                    }}
                />
            )}

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

            {/* NEW: History Modals */}
            {showHistoryModal && selectedForHistory && (
                <InventoryHistoryModal
                    item={selectedForHistory}
                    isOpen={showHistoryModal}
                    onClose={() => setShowHistoryModal(false)}
                />
            )}

            {isGlobalHistoryOpen && (
                <GlobalAuditHistoryModal
                    isOpen={isGlobalHistoryOpen}
                    onClose={() => setIsGlobalHistoryOpen(false)}
                    onRevertSuccess={loadIngredients}
                    initialFilter={globalHistoryFilter === 'audit' ? 'audit' : 'all'}
                />
            )}
        </div>
    );
};

export default IngredientManager;
