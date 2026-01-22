import { ArrowLeft, Save, Camera, Beer, Trash2, X } from 'lucide-react';
import { MutableRefObject, useState } from 'react';
import { BatchHistoryModal } from './BatchHistoryModal';

interface BeverageFormProps {
    productForm: any;
    setProductForm: (form: any) => void;
    fileInputRef: MutableRefObject<HTMLInputElement | null>;
    handleFileChange: (e: any) => void;
    handleSave: () => void;
    onCancel: () => void;
    isSaving: boolean;
    selectedProduct?: any;
    onSelectProduct?: (product: any) => void;
    onDelete?: () => void;
    onCancelEdit?: () => void;
    products?: any[];
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
    onCancelEdit
}: BeverageFormProps) => {

    const [showBatchModal, setShowBatchModal] = useState(false);


    const calculateMargin = () => {
        const cost = Number(productForm.cost) || 0;
        const price = Number(productForm.price) || 0;
        if (price === 0) return 0;
        return ((price - cost) / price) * 100;
    };

    const margin = calculateMargin();

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
        <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
            {/* 2-Column Creative Grid */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

                {/* LEFT COL: Visual Identity (4 cols) */}
                <div className="md:col-span-4 space-y-4">
                    {/* Polaroid-style Image Uploader */}
                    <div
                        className="aspect-[4/5] bg-white p-3 shadow-xl transform rotate-[-2deg] hover:rotate-0 transition-all duration-300 cursor-pointer group relative"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className="w-full h-[85%] bg-gray-100 overflow-hidden relative">
                            {productForm.image_url ? (
                                <img src={productForm.image_url} className="w-full h-full object-cover" alt="Product" />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                                    <Camera size={48} className="mb-2 opacity-50" />
                                    <span className="text-xs uppercase font-bold tracking-widest text-center">Foto del<br />Producto</span>
                                </div>
                            )}
                        </div>
                        <div className="h-[15%] flex items-end justify-center pb-2">
                            <span className="font-handwriting text-gray-800 font-bold opacity-80 decoration-slice text-xl">
                                {productForm.name || 'Nueva Bebida'}
                            </span>
                        </div>
                    </div>
                    <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileChange} />
                    <p className="text-center text-xs text-gray-500 italic">Clic en la foto para subir imagen</p>
                </div>

                {/* RIGHT COL: Data Details (8 cols) */}
                <div className="md:col-span-8 space-y-6">

                    {/* Header Section */}
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-4 w-full">
                            <button
                                onClick={onCancel}
                                className="p-2 bg-white/5 hover:bg-white/10 rounded-full text-white transition-colors border border-white/10 group"
                                title="Volver al menú"
                            >
                                <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                            </button>
                            <div className="space-y-1 flex-1">
                                <h2 className="text-3xl font-bold text-white tracking-tight">
                                    {productForm.name || <span className="text-gray-600">Nombre de la Bebida</span>}
                                </h2>
                                <div className="flex gap-2">
                                    <span className="bg-amber-500/10 text-amber-400 px-2 py-0.5 text-xs font-bold uppercase rounded border border-amber-500/20">Bebida / Cafetería</span>
                                    {selectedProduct && (
                                        <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 text-xs font-bold uppercase rounded border border-blue-500/20">
                                            Editando: {selectedProduct.name}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleSave}
                                    disabled={!productForm.name || isSaving}
                                    className={`${selectedProduct ? 'bg-blue-600 hover:bg-blue-700' : 'bg-accent-orange hover:bg-orange-600'} text-white px-6 py-3 rounded-full font-bold shadow-lg shadow-orange-500/20 disabled:opacity-50 transition-all flex items-center gap-2 transform hover:scale-105 active:scale-95 whitespace-nowrap`}
                                >
                                    <Save size={18} /> {isSaving ? 'Guardando...' : (selectedProduct ? 'ACTUALIZAR' : 'LANZAR PRODUCTO 🚀')}
                                </button>
                                {selectedProduct && onCancelEdit && (
                                    <button
                                        onClick={onCancelEdit}
                                        className="p-3 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-full transition-all border border-gray-600"
                                        title="Cancelar edición"
                                    >
                                        <X size={20} />
                                    </button>
                                )}
                                {selectedProduct && onDelete && (
                                    <button
                                        onClick={onDelete}
                                        disabled={isSaving}
                                        className="p-3 bg-red-500/10 hover:bg-red-500 hover:text-white text-red-500 rounded-full transition-all border border-red-500/20"
                                        title="Eliminar producto"
                                    >
                                        <Trash2 size={20} />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Inputs Grid */}
                    <div className="bg-card-dark/50 p-6 rounded-2xl border border-border-dark space-y-6">

                        <div className="grid grid-cols-3 gap-4">
                            <div className="col-span-2 space-y-1">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Nombre del Producto</label>
                                <input
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 font-bold text-white focus:border-accent-orange outline-none transition-colors"
                                    placeholder="Ej. Coca Cola Zero"
                                    value={productForm.name}
                                    onChange={e => setProductForm({ ...productForm, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">SKU / CÓDIGO <span className="text-[10px] text-gray-600 normal-case">(Opcional)</span></label>
                                <input
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 font-bold text-gray-300 focus:border-accent-orange outline-none transition-colors"
                                    placeholder="BEV-001"
                                    value={productForm.sku}
                                    onChange={e => setProductForm({ ...productForm, sku: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Calculator Row */}
                        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-border-dark/50">

                            {/* COST CALC */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                                    COSTO ADQUISICIÓN (TOTAL)
                                </h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] text-gray-500 block mb-1">Costo Total Lote</label>
                                        <div className="relative">
                                            <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                                            <input
                                                type="number"
                                                className="w-full bg-bg-deep pl-7 pr-3 py-2 rounded border border-border-dark text-white text-sm focus:border-emerald-500 outline-none"
                                                placeholder="0"
                                                value={productForm.totalCost}
                                                onChange={e => handleTotalCostChange(e.target.value, productForm.stock)}
                                            />
                                        </div>
                                        <p className="text-[10px] text-gray-500 mt-1">¿Cuánto pagaste por todo el lote?</p>
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-gray-500 block mb-1">Unidades</label>
                                        <input
                                            type="number"
                                            className="w-full bg-bg-deep px-3 py-2 rounded border border-border-dark text-white text-sm focus:border-emerald-500 outline-none"
                                            placeholder="1"
                                            value={productForm.stock}
                                            onChange={e => handleTotalCostChange(productForm.totalCost, e.target.value)}
                                        />
                                        <p className="text-[10px] text-gray-500 mt-1">Botellas/Unidades que vinieron.</p>
                                    </div>
                                </div>
                                <div className="bg-emerald-500/10 p-3 rounded border border-emerald-500/20 flex justify-between items-center">
                                    <span className="text-xs text-emerald-400 font-bold">COSTO UNITARIO</span>
                                    <span className="text-lg font-bold text-emerald-400">
                                        ${Number(productForm.cost).toLocaleString()}
                                    </span>
                                </div>
                            </div>

                            {/* PRICE CALC */}
                            <div className="space-y-4 border-l border-border-dark/50 pl-6">
                                <h4 className="text-sm font-bold text-accent-orange flex items-center gap-2">
                                    PRECIO VENTA (UNITARIO)
                                </h4>
                                <div>
                                    <label className="text-[10px] text-gray-500 block mb-1">Precio Carta</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                                        <input
                                            type="number"
                                            className="w-full bg-bg-deep pl-7 pr-3 py-2 rounded border border-border-dark text-white text-xl font-bold focus:border-accent-orange outline-none"
                                            placeholder="0"
                                            value={productForm.price}
                                            onChange={e => setProductForm({ ...productForm, price: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="bg-bg-deep p-3 rounded border border-border-dark flex justify-between items-center">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] text-gray-400">PROFIT MARGIN</span>
                                        <span className={`text-xl font-bold ${margin >= 30 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {margin.toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-[10px] text-gray-400 block">Net Profit</span>
                                        <span className="text-sm font-bold text-white">
                                            ${(Number(productForm.price) - Number(productForm.cost)).toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            </div>

                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Proveedor</label>
                                <input
                                    className="w-full bg-bg-deep border border-border-dark rounded px-3 py-2 text-white text-sm focus:border-white/20 outline-none"
                                    placeholder="Ej. Coca-Cola Company"
                                    value={productForm.supplier}
                                    onChange={e => setProductForm({ ...productForm, supplier: e.target.value })}
                                />
                            </div>
                            <div>
                                <div className="flex justify-between items-center mb-1">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Stock Total</label>
                                    {selectedProduct && (
                                        <button
                                            onClick={() => setShowBatchModal(true)}
                                            className="text-[10px] text-blue-400 hover:text-white underline"
                                        >
                                            Gestionar Lotes
                                        </button>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <input
                                        className="w-full bg-bg-deep border border-border-dark rounded px-3 py-2 text-white text-sm focus:border-white/20 outline-none"
                                        value={productForm.stock}
                                        disabled
                                        title="Calculado según lotes activos"
                                    />
                                    {selectedProduct && (
                                        <button
                                            onClick={() => setShowBatchModal(true)}
                                            className="bg-blue-600/20 text-blue-400 border border-blue-600/40 rounded px-3 hover:bg-blue-600 hover:text-white transition-colors"
                                            title="Ver historial de lotes"
                                        >
                                            <span className="material-symbols-outlined text-[18px]">inventory_2</span>
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>

            {/* --- BEVERAGE LIST SECTION --- */}
            <div className="col-span-full pt-8 border-t border-border-dark animate-in slide-in-from-bottom-4 duration-700 delay-200">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    <Beer size={20} className="text-accent-orange" />
                    Catálogo de Bebidas
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {products.length === 0 ? (
                        <div className="col-span-full p-8 text-center bg-gray-800/30 rounded-xl border border-dashed border-gray-700">
                            <p className="text-gray-500 italic">No hay bebidas registradas aún.</p>
                        </div>
                    ) : (
                        products.map((p: any) => (
                            <div
                                key={p.id}
                                onClick={() => onSelectProduct && onSelectProduct(p)}
                                className={`group bg-card-dark hover:bg-white/5 border ${selectedProduct?.id === p.id ? 'border-accent-orange ring-1 ring-accent-orange' : 'border-border-dark'} hover:border-accent-orange/50 p-3 rounded-xl transition-all duration-300 cursor-pointer`}
                            >
                                <div className="aspect-square bg-black/20 rounded-lg mb-3 overflow-hidden relative">
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
                                        <span className="font-bold text-accent-orange">${p.price?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-[10px] text-gray-600">
                                        <span>Stock</span>
                                        <span className={p.stock > 10 ? 'text-emerald-500' : 'text-red-500'}>{p.stock} u</span>
                                    </div>
                                    {p.sku && <div className="text-[9px] text-gray-500 uppercase tracking-wider">{p.sku}</div>}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {showBatchModal && selectedProduct && (
                <BatchHistoryModal
                    productId={selectedProduct.id}
                    productName={selectedProduct.name}
                    baseUnit={productForm.unit || 'und'}
                    onClose={() => setShowBatchModal(false)}
                />
            )}
        </div >
    );
};
