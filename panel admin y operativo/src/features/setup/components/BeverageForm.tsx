import { ArrowLeft, Save, Camera, Beer, Trash2, X, ShoppingCart, LayoutGrid, Factory, History, Plus } from 'lucide-react';
import { MutableRefObject, useState, useEffect } from 'react';
import { BatchHistoryModal } from './BatchHistoryModal';
import { QuickPurchaseModal } from './QuickPurchaseModal';
import { setupService } from '../setup.service';
import { kitchenService, type Ingredient } from '@/features/kitchen/kitchen.service';

interface BeverageFormProps {
    productForm: any;
    setProductForm: (form: any) => void;
    fileInputRef: MutableRefObject<HTMLInputElement | null>;
    handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    handleSave: () => void;
    onCancel: () => void;
    isSaving: boolean;
    products?: any[];
    selectedProduct?: any;
    onSelectProduct?: (product: any) => void;
    onDelete?: () => void;
    onCancelEdit?: () => void;
    allIngredients?: Ingredient[]; // Passed from parent for WAC calculation
    initialView?: 'HOME' | 'INVENTORY' | 'CATALOG';
}

export const BeverageForm = ({
    productForm,
    setProductForm,
    fileInputRef,
    handleFileChange,
    handleSave,
    onCancel,
    isSaving,
    products = [], // Default to empty array
    selectedProduct,
    onSelectProduct,
    onDelete,
    onCancelEdit,
    allIngredients = [],
    initialView = 'HOME'
}: BeverageFormProps) => {

    const [showBatchModal, setShowBatchModal] = useState(false);
    const [showQuickPurchase, setShowQuickPurchase] = useState(false);
    const [view, setView] = useState<'HOME' | 'INVENTORY' | 'CATALOG'>(initialView);
    const [inventoryFilter, setInventoryFilter] = useState('');
    const [localSelectedProduct, setLocalSelectedProduct] = useState<Ingredient | null>(null);
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);

    // Helper: Format stock with thousands separators and cleaner decimals
    const formatStock = (val: number | string) => {
        const n = Number(val);
        if (isNaN(n)) return '0';

        return new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: Number.isInteger(n) ? 0 : 2
        }).format(n);
    };

    // Helper: Refresh inventory data
    const refreshInventory = () => {
        kitchenService.getIngredients(undefined, 'MERCHANDISE').then(setIngredients);
    };

    useEffect(() => {
        if (view === 'INVENTORY') {
            refreshInventory();
        }
    }, [view, products]);

    // Switch to Catalog if a product is selected externally (e.g. from parent)
    // But ONLY if we are in HOME or already in CATALOG. 
    // If we are in INVENTORY, we handle selection locally for the modal.
    useEffect(() => {
        if (selectedProduct && view === 'HOME') setView('CATALOG');
    }, [selectedProduct]);



    // --- VALIDATION AND SAVE ---
    const handleLocalSave = () => {
        const name = productForm.name?.trim();
        if (!name) return;

        // Check for duplicates in ALL ingredients (Raw Material + Merchandise)
        // This prevents 409 Conflict if trying to use a name that exists as an ingredient but not a product
        const nameLower = name.toLowerCase();
        const duplicate = allIngredients.find(i => i.name.trim().toLowerCase() === nameLower);

        if (duplicate) {
            // If editing, allow if it's the same item (name hasn't changed)
            if (selectedProduct) {
                if (selectedProduct.name.trim().toLowerCase() !== nameLower) {
                    alert(`El nombre "${duplicate.name}" ya está siendo usado por otro producto. Por favor elige uno diferente.`);
                    return;
                }
            } else {
                // If creating, reject immediate duplicates
                alert(`El nombre "${duplicate.name}" ya existe en el sistema. Usa un nombre único.`);
                return;
            }
        }

        handleSave();
    };


    // --- FINANCIAL CALCULATIONS (Weighted Average Cost) ---
    const calculateFinancials = () => {
        const price = Number(productForm.price) || 0;
        const stdCost = Number(productForm.cost) || 0;

        // Use the cost from form (which is initialized with Backend Effective Cost)
        const realCost = stdCost;
        let isWeighted = false;

        if (allIngredients.length > 0 && productForm.name) {
            const match = allIngredients.find(i =>
                i.name.trim().toLowerCase() === productForm.name?.trim().toLowerCase()
            );

            if (match) {
                const stock = Number(match.stock);
                const totalVal = Number(match.total_inventory_value);
                // Check if it's weighted just for the tooltip
                if (stock > 0 && totalVal > 0) {
                    isWeighted = true;
                }
            }
        }

        const margin = price > 0 ? ((price - stdCost) / price) * 100 : 0;
        const realProfit = price - realCost;
        const realMargin = price > 0 ? ((price - realCost) / price) * 100 : 0;

        console.log("[DEBUG-FRONTEND] Financials:", { price, stdCost, realCost, realProfit, isWeighted });

        return { stdCost, realCost, margin, realProfit, realMargin, isWeighted };
    };

    const handleDeleteInventoryItem = async (ingredient: Ingredient) => {
        if (!confirm(`¿Estás seguro de eliminar "${ingredient.name}"? Esto lo quitará del catálogo de ventas y del inventario.`)) return;

        try {
            // Find if there's a matching product in the catalog to perform a cascading delete
            const matchingProduct = products.find(p => p.name.toLowerCase() === ingredient.name.toLowerCase());

            if (matchingProduct) {
                // Use the cascading delete service
                await setupService.deleteBeverage(matchingProduct.id);
            } else {
                // Fallback for ingredients without a 1:1 product link
                await kitchenService.deleteIngredient(ingredient.id);
            }

            // Refresh local inventory state
            const updatedIngs = await kitchenService.getIngredients(undefined, 'MERCHANDISE');
            setIngredients(updatedIngs);

            // Notify parent to refresh the product list
            onCancel();

        } catch (error: any) {
            console.error('Delete error:', error);
            alert('Error al eliminar: ' + (error.response?.data?.detail || error.message));
        }
    };

    const { realProfit, realMargin, isWeighted } = calculateFinancials();

    // Auto-calculate unit cost from Total Cost / Quantity
    const handleTotalCostChange = (total: string, qty: string) => {
        const t = Number(total);
        const q = Number(qty);
        if (t > 0 && q > 0) {
            const unitCost = t / q;
            setProductForm({ ...productForm, totalCost: total, stock: qty, cost: unitCost.toFixed(2) });
        } else {
            setProductForm({ ...productForm, totalCost: total, stock: qty });
        }
    };

    return (
        <>
            {/* HOME VIEW (DASHBOARD) */}
            {view === 'HOME' && (
                <div className="animate-in fade-in zoom-in-95 duration-300 grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
                    <button
                        onClick={() => setView('INVENTORY')}
                        className="group relative h-64 bg-card-dark border border-border-dark rounded-2xl p-8 hover:border-emerald-500/50 transition-all hover:bg-emerald-500/5 text-left flex flex-col justify-between overflow-hidden"
                    >
                        <div className="absolute right-0 top-0 p-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-all" />

                        <div className="bg-emerald-500/10 w-14 h-14 rounded-xl flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform mb-4 z-10">
                            <ShoppingCart size={32} />
                        </div>

                        <div className="z-10">
                            <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-emerald-400 transition-colors">Gestión de Compras</h3>
                            <p className="text-gray-400 group-hover:text-gray-300">
                                Ver y gestionar historial de lotes, existencias y costos de todos los productos.
                            </p>
                        </div>
                    </button>

                    <button
                        onClick={() => setView('CATALOG')}
                        className="group relative h-64 bg-card-dark border border-border-dark rounded-2xl p-8 hover:border-accent-primary/50 transition-all hover:bg-accent-primary/5 text-left flex flex-col justify-between overflow-hidden"
                    >
                        <div className="absolute right-0 top-0 p-32 bg-accent-primary/10 rounded-full blur-3xl group-hover:bg-accent-primary/20 transition-all" />

                        <div className="bg-accent-primary/10 w-14 h-14 rounded-xl flex items-center justify-center text-accent-primary group-hover:scale-110 transition-transform mb-4 z-10">
                            <LayoutGrid size={32} />
                        </div>

                        <div className="z-10">
                            <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-accent-primary transition-colors">Catálogo de Productos</h3>
                            <p className="text-gray-400 group-hover:text-gray-300">
                                Gestionar carta, precios, subir fotos y lanzar nuevos productos.
                            </p>
                        </div>
                    </button>
                </div>
            )}

            {/* INVENTORY VIEW */}
            {view === 'INVENTORY' && (
                <div className="animate-in slide-in-from-right-4 duration-300 space-y-6">
                    <div className="flex items-center gap-4">
                        <button onClick={() => setView('HOME')} className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition-colors">
                            <ArrowLeft size={24} />
                        </button>
                        <div>
                            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                                <Factory className="text-emerald-400" /> Inventario de Venta Directa
                            </h2>
                            <p className="text-gray-500 text-sm">Gestión centralizada de existencias y lotes</p>
                        </div>
                    </div>

                    <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden shadow-lg">
                        <div className="p-4 border-b border-border-dark flex gap-4">
                            <div className="relative flex-1">
                                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">search</span>
                                <input
                                    placeholder="Buscar producto..."
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg pl-10 pr-3 py-2 text-white focus:border-emerald-500 outline-none"
                                    value={inventoryFilter}
                                    onChange={e => setInventoryFilter(e.target.value)}
                                />
                            </div>
                        </div>
                        <table className="w-full text-sm text-left">
                            <thead className="bg-white/5 text-gray-400 font-medium border-b border-border-dark">
                                <tr>
                                    <th className="px-4 py-3">Producto</th>
                                    <th className="px-4 py-3 text-center">Stock Total</th>
                                    <th className="px-4 py-3 text-right">Valor Inventario</th>
                                    <th className="px-4 py-3 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark">
                                {ingredients.filter(p => p.name.toLowerCase().includes(inventoryFilter.toLowerCase())).map(p => (
                                    <tr key={p.id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-4 py-3">
                                            <div className="font-bold text-white">{p.name}</div>
                                            <div className="text-xs text-gray-500">{p.sku || 'S/N'}</div>
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`font-mono font-bold ${Number(p.stock) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {formatStock(p.stock || 0)} {p.base_unit || 'und'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right text-gray-300 font-mono">
                                            {/* Valor real calculado desde lotes activos */}
                                            ${Number(p.total_inventory_value || 0).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => {
                                                        setLocalSelectedProduct(p);
                                                        setShowQuickPurchase(true);
                                                    }}
                                                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1 transition-colors"
                                                    title="Registrar Compra"
                                                >
                                                    <Plus size={14} /> Compra
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteInventoryItem(p)}
                                                    className="text-gray-500 hover:text-red-400 p-1 rounded hover:bg-white/10 transition-colors"
                                                    title="Eliminar Insumo"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        setLocalSelectedProduct(p);
                                                        setShowBatchModal(true);
                                                    }}
                                                    className="text-emerald-400 hover:text-emerald-300 hover:underline text-xs flex items-center gap-1"
                                                >
                                                    <History size={14} /> Gestión Lotes
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div >
            )}

            {/* CATALOG VIEW (Existing) */}
            {
                view === 'CATALOG' && (
                    <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
                        <button onClick={() => setView('HOME')} className="text-xs text-gray-500 hover:text-white flex items-center gap-1 mb-[-20px] relative z-10">
                            <ArrowLeft size={14} /> Menú Anterior
                        </button>

                        {/* 2-Column Creative Grid - Reduced Gap */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">

                            {/* LEFT COL: Visual Identity (3 cols - Reduced width) */}
                            <div className="md:col-span-3 space-y-3">
                                {/* Polaroid-style Image Uploader - Scaled Down */}
                                <div
                                    className="aspect-[4/5] bg-white p-2 shadow-lg transform rotate-[-1deg] hover:rotate-0 transition-all duration-300 cursor-pointer group relative max-w-[220px] mx-auto md:mx-0"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <div className="w-full h-[85%] bg-gray-100 overflow-hidden relative">
                                        {productForm.image_url ? (
                                            <img src={productForm.image_url} className="w-full h-full object-cover" alt="Product" />
                                        ) : (
                                            <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                                                <Camera size={32} className="mb-1 opacity-50" />
                                                <span className="text-[10px] uppercase font-bold tracking-widest text-center">Foto del<br />Producto</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="h-[15%] flex items-end justify-center pb-1">
                                        <span className="font-handwriting text-gray-800 font-bold opacity-80 decoration-slice text-sm leading-tight truncate px-1">
                                            {productForm.name || 'Nuevo'}
                                        </span>
                                    </div>
                                </div>
                                <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileChange} />
                                <p className="text-center md:text-left text-[10px] text-gray-500 italic pl-2">Clic para subir imagen</p>
                            </div>

                            {/* RIGHT COL: Data Details (9 cols - Expanded width) */}
                            <div className="md:col-span-9 space-y-4">

                                {/* Header Section - Compacted */}
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-3 w-full">
                                        <button
                                            onClick={onCancel}
                                            className="p-1.5 bg-white/5 hover:bg-white/10 rounded-full text-white transition-colors border border-white/10 group"
                                            title="Volver al menú"
                                        >
                                            <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                                        </button>
                                        <div className="space-y-0.5 flex-1">
                                            <h2 className="text-2xl font-bold text-white tracking-tight leading-tight">
                                                {productForm.name || <span className="text-gray-600">Nombre del Producto</span>}
                                            </h2>
                                            <div className="flex gap-2">
                                                <span className="bg-amber-500/10 text-amber-400 px-1.5 py-0.5 text-[10px] font-bold uppercase rounded border border-amber-500/20">Venta Directa</span>
                                                {selectedProduct && (
                                                    <span className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 text-[10px] font-bold uppercase rounded border border-blue-500/20">
                                                        Editando
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={handleLocalSave}
                                                disabled={!productForm.name || isSaving}
                                                className={`${selectedProduct ? 'bg-blue-600 hover:bg-blue-700' : 'bg-accent-primary hover:bg-orange-600'} text-white px-4 py-2 rounded-full font-bold shadow-lg shadow-orange-500/20 disabled:opacity-50 transition-all flex items-center gap-2 transform hover:scale-105 active:scale-95 whitespace-nowrap text-sm`}
                                            >
                                                <Save size={16} /> {isSaving ? 'Guardando...' : (selectedProduct ? 'ACTUALIZAR' : 'LANZAR')}
                                            </button>
                                            {selectedProduct && onCancelEdit && (
                                                <button
                                                    onClick={onCancelEdit}
                                                    className="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-full transition-all border border-gray-600"
                                                    title="Cancelar edición"
                                                >
                                                    <X size={16} />
                                                </button>
                                            )}
                                            {selectedProduct && onDelete && (
                                                <button
                                                    onClick={onDelete}
                                                    disabled={isSaving}
                                                    className="p-2 bg-red-500/10 hover:bg-red-500 hover:text-white text-red-500 rounded-full transition-all border border-red-500/20"
                                                    title="Eliminar producto"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Inputs Grid - Compacted Padding */}
                                <div className="bg-card-dark/50 p-4 rounded-xl border border-border-dark space-y-4">

                                    <div className="grid grid-cols-3 gap-3">
                                        <div className="col-span-2 space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Nombre del Producto</label>
                                            <input
                                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 font-bold text-white focus:border-accent-primary outline-none transition-colors text-sm"
                                                placeholder="Ej. Coca Cola Zero"
                                                value={productForm.name}
                                                onChange={e => setProductForm({ ...productForm, name: e.target.value })}
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">SKU / CÓDIGO <span className="text-[9px] text-gray-600 normal-case">(Opcional)</span></label>
                                            <input
                                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 font-bold text-gray-300 focus:border-accent-primary outline-none transition-colors text-sm"
                                                placeholder="BEV-001"
                                                value={productForm.sku || ''}
                                                onChange={e => setProductForm({ ...productForm, sku: e.target.value })}
                                            />
                                        </div>
                                    </div>

                                    {/* Calculator Row - Compacted */}
                                    <div className="grid grid-cols-2 gap-5 pt-2 border-t border-border-dark/50">

                                        {/* COST CALC - MODE SWITCH */}
                                        {selectedProduct ? (
                                            // VIEW MODE: EDIT (Restrictions applied)
                                            <div className="space-y-2">
                                                <div className="bg-blue-500/10 border border-blue-500/20 rounded p-2">
                                                    <div className="flex items-start gap-2">
                                                        <span className="material-symbols-outlined text-blue-400 text-sm mt-0.5">info</span>
                                                        <div>
                                                            <h4 className="text-xs font-bold text-blue-400 mb-0.5">Gestión de Costos y Stock</h4>
                                                            <p className="text-[10px] text-gray-400 leading-tight">
                                                                Costos y existencias se gestionan desde el Inventario.
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Read-Only Display of Current Values */}
                                                <div className="grid grid-cols-2 gap-2 opacity-50">
                                                    <div>
                                                        <label className="text-[9px] text-gray-500 block mb-0.5">Costo Unitario</label>
                                                        <div className="bg-bg-deep px-2 py-1.5 rounded border border-border-dark text-white text-xs">
                                                            ${Number(productForm.cost).toLocaleString()}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="text-[9px] text-gray-500 block mb-0.5">Stock Actual</label>
                                                        <div className="bg-bg-deep px-2 py-1.5 rounded border border-border-dark text-white text-xs">
                                                            {formatStock(productForm.stock)} u
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            // VIEW MODE: CREATE (Full Access)
                                            <div className="space-y-2">
                                                <h4 className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                                                    COSTO ADQUISICIÓN (TOTAL)
                                                </h4>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <div>
                                                        <label className="text-[9px] text-gray-500 block mb-0.5">Costo Total Lote</label>
                                                        <div className="relative">
                                                            <span className="absolute left-2 top-1.5 text-gray-500 text-xs">$</span>
                                                            <input
                                                                type="number"
                                                                className="w-full bg-bg-deep pl-5 pr-2 py-1.5 rounded border border-border-dark text-white text-xs focus:border-emerald-500 outline-none"
                                                                placeholder="0"
                                                                value={productForm.totalCost || ''}
                                                                onChange={e => handleTotalCostChange(e.target.value, productForm.stock)}
                                                            />
                                                        </div>
                                                        <p className="text-[9px] text-gray-500 mt-0.5 leading-tight">¿Total pagado?</p>
                                                    </div>
                                                    <div>
                                                        <label className="text-[9px] text-gray-500 block mb-0.5">Unidades</label>
                                                        <input
                                                            type="number"
                                                            className="w-full bg-bg-deep px-2 py-1.5 rounded border border-border-dark text-white text-xs focus:border-emerald-500 outline-none"
                                                            placeholder="1"
                                                            value={productForm.stock || ''}
                                                            onChange={e => handleTotalCostChange(productForm.totalCost, e.target.value)}
                                                        />
                                                        <p className="text-[9px] text-gray-500 mt-0.5 leading-tight">Unidades recibidas</p>
                                                    </div>
                                                </div>
                                                <div className="bg-emerald-500/10 p-2 rounded border border-emerald-500/20 flex justify-between items-center">
                                                    <span className="text-[10px] text-emerald-400 font-bold">COSTO UNITARIO</span>
                                                    <span className="text-sm font-bold text-emerald-400">
                                                        ${Number(productForm.cost).toLocaleString()}
                                                    </span>
                                                </div>
                                            </div>
                                        )}

                                        {/* PRICE CALC (Always Visible) */}
                                        <div className="space-y-2 border-l border-border-dark/50 pl-4">
                                            <h4 className="text-xs font-bold text-accent-primary flex items-center gap-1">
                                                PRECIO VENTA (UNITARIO)
                                            </h4>
                                            <div>
                                                <label className="text-[9px] text-gray-500 block mb-0.5">Precio Carta</label>
                                                <div className="relative">
                                                    <span className="absolute left-3 top-2 text-gray-500 text-sm">$</span>
                                                    <input
                                                        type="number"
                                                        className="w-full bg-bg-deep pl-6 pr-3 py-1.5 rounded border border-border-dark text-white text-lg font-bold focus:border-accent-primary outline-none"
                                                        placeholder="0"
                                                        value={productForm.price || ''}
                                                        onChange={e => setProductForm({ ...productForm, price: e.target.value })}
                                                    />
                                                </div>
                                            </div>
                                            <div className="bg-bg-deep p-2 rounded border border-border-dark flex justify-between items-center relative group/profit">
                                                {isWeighted && (
                                                    <div className="absolute -top-10 left-0 bg-gray-800 text-xs p-2 rounded shadow-xl border border-gray-700 opacity-0 group-hover/profit:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                                                        Calculado con Costo Promedio Ponderado.
                                                    </div>
                                                )}

                                                <div className="flex flex-col">
                                                    <span className="text-[9px] text-gray-400 flex items-center gap-1">
                                                        {isWeighted ? 'MARGEN REAL' : 'MARGEN REF.'}
                                                        {isWeighted && <span className="material-symbols-outlined text-[10px] text-emerald-400">verified</span>}
                                                    </span>
                                                    <span className={`text-base font-bold ${realMargin >= 30 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                        {realMargin.toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-[9px] text-gray-400 block">Ganancia Neta</span>
                                                    <span className="text-xs font-bold text-white">
                                                        ${realProfit.toLocaleString()}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div>
                                            {selectedProduct ? null : (
                                                <>
                                                    <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-0.5">Proveedor</label>
                                                    <input
                                                        className="w-full bg-bg-deep border border-border-dark rounded px-2 py-1.5 text-white text-xs focus:border-white/20 outline-none"
                                                        placeholder="Ej. Coca-Cola Company"
                                                        value={productForm.supplier || ''}
                                                        onChange={e => setProductForm({ ...productForm, supplier: e.target.value })}
                                                    />
                                                </>
                                            )}
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-0.5">
                                                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Stock Total</label>
                                            </div>
                                            <div className="flex gap-2">
                                                <input
                                                    className="w-full bg-bg-deep border border-border-dark rounded px-2 py-1.5 text-white text-xs focus:border-white/20 outline-none"
                                                    value={formatStock(productForm.stock)}
                                                    disabled
                                                    title="Calculado según lotes activos"
                                                />
                                                {/* Removed Button for now to avoid ID mismatch (Int vs UUID) */}
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>

                        {/* --- PRODUCT LIST SECTION --- */}
                        <div className="col-span-full pt-8 border-t border-border-dark animate-in slide-in-from-bottom-4 duration-700 delay-200">
                            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                <Beer size={20} className="text-accent-primary" />
                                Catálogo de Venta Directa
                            </h3>

                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                                {products.length === 0 ? (
                                    <div className="col-span-full p-6 text-center bg-gray-800/30 rounded-lg border border-dashed border-gray-700">
                                        <p className="text-gray-500 text-sm italic">No hay productos registrados aún.</p>
                                    </div>
                                ) : (
                                    products.map((p: any) => (
                                        <div
                                            key={p.id}
                                            onClick={() => onSelectProduct && onSelectProduct(p)}
                                            className={`group bg-card-dark hover:bg-white/5 border ${selectedProduct?.id === p.id ? 'border-accent-primary ring-1 ring-accent-primary' : 'border-border-dark'} hover:border-accent-primary/50 p-2 rounded-lg transition-all duration-300 cursor-pointer`}
                                        >
                                            <div className="aspect-square bg-black/20 rounded-md mb-2 overflow-hidden relative">
                                                {p.image_url ? (
                                                    <img src={p.image_url} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" alt={p.name} />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center text-gray-700">
                                                        <Beer size={24} />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="space-y-1">
                                                <h4 className="font-bold text-gray-200 text-sm truncate" title={p.name}>{p.name}</h4>
                                                <div className="flex justify-between items-center text-xs">
                                                    <span className="text-gray-500">Precio</span>
                                                    <span className="font-bold text-accent-primary">${Number(p.price).toLocaleString()}</span>
                                                </div>
                                                <div className="flex justify-between items-center text-[10px] text-gray-600">
                                                    <span>Stock</span>
                                                    <span className={p.stock > 10 ? 'text-emerald-500' : 'text-red-500'}>
                                                        {Number.isInteger(Number(p.stock)) ? Math.round(p.stock) : Number(p.stock).toFixed(2)} u
                                                    </span>
                                                </div>
                                                {p.sku && <div className="text-[9px] text-gray-500 uppercase tracking-wider">{p.sku}</div>}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                    </div>
                )
            }

            {/* BATCH HISTORY MODAL */}
            {
                showBatchModal && localSelectedProduct && (
                    <BatchHistoryModal
                        productId={localSelectedProduct.id}
                        productName={localSelectedProduct.name}
                        baseUnit={localSelectedProduct.base_unit || 'und'}
                        onClose={() => {
                            setShowBatchModal(false);
                            setLocalSelectedProduct(null);
                        }}
                    />
                )
            }

            {/* QUICK PURCHASE MODAL */}
            {
                showQuickPurchase && localSelectedProduct && (
                    <QuickPurchaseModal
                        product={{
                            id: localSelectedProduct.id,
                            name: localSelectedProduct.name,
                            stock: Number(localSelectedProduct.stock),
                            base_unit: localSelectedProduct.base_unit
                        }}
                        onClose={() => {
                            setShowQuickPurchase(false);
                            setLocalSelectedProduct(null);
                        }}
                        onSuccess={() => {
                            refreshInventory();
                        }}
                    />
                )
            }
        </>
    );
};
