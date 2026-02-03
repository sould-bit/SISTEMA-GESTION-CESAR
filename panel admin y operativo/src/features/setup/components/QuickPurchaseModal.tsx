import { useState, useRef, useEffect } from 'react';
import { kitchenService } from '@/features/kitchen/kitchen.service';
import { ShoppingCart, Package, DollarSign, Truck } from 'lucide-react';

interface QuickPurchaseModalProps {
    product: {
        id: string;
        name: string;
        stock: number;
        base_unit?: string;
    };
    onClose: () => void;
    onSuccess: () => void;
}

export const QuickPurchaseModal = ({ product, onClose, onSuccess }: QuickPurchaseModalProps) => {
    const [quantity, setQuantity] = useState<string>('');
    const [totalCost, setTotalCost] = useState<string>('');
    const [supplier, setSupplier] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const qtyInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        // Focus quantity on mount
        setTimeout(() => qtyInputRef.current?.focus(), 100);
    }, []);

    // Calculate derived values
    const numQty = parseFloat(quantity) || 0;
    const numTotal = parseFloat(totalCost) || 0;
    const unitCost = numQty > 0 ? numTotal / numQty : 0;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!numQty || numQty <= 0) return alert('La cantidad debe ser mayor a 0');
        if (!numTotal || numTotal < 0) return alert('El costo total es requerido');

        setIsSubmitting(true);
        try {
            await kitchenService.updateIngredientStock(
                product.id,
                numQty,
                'IN',
                'Compra Rápida - Panel',
                unitCost,
                supplier || 'Proveedor General'
            );

            // Play a subtle success sound or interaction? (Optional)
            onSuccess();
            onClose();
        } catch (error: any) {
            console.error(error);
            alert('Error al registrar compra: ' + (error.response?.data?.detail || error.message));
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[70] p-4 animate-in fade-in duration-200">
            <div className="bg-[#1a1c23] border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl transform transition-all animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="p-6 border-b border-gray-700/50 flex justify-between items-start bg-gradient-to-r from-emerald-900/10 to-transparent rounded-t-2xl">
                    <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <ShoppingCart className="text-emerald-400" size={24} />
                            Registrar Compra
                        </h2>
                        <p className="text-gray-400 text-sm mt-1">Ingreso de mercancía para: <span className="text-emerald-300 font-medium">{product.name}</span></p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-white transition-colors p-2 rounded-full hover:bg-white/5"
                    >
                        <span className="material-symbols-outlined text-xl">close</span>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">

                    {/* Main Inputs */}
                    <div className="grid grid-cols-2 gap-6">

                        {/* Quantity */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                                <Package size={16} /> Cantidad
                            </label>
                            <div className="relative group">
                                <input
                                    ref={qtyInputRef}
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={quantity}
                                    onChange={e => setQuantity(e.target.value)}
                                    className="w-full bg-[#0f1115] border border-gray-700 rounded-xl px-4 py-3 text-white text-lg font-mono focus:border-emerald-500 hover:border-gray-600 outline-none transition-all placeholder:text-gray-700"
                                    placeholder="0"
                                    required
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-xs font-bold uppercase pointer-events-none">
                                    {product.base_unit || 'UND'}
                                </span>
                            </div>
                        </div>

                        {/* Total Cost */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                                <DollarSign size={16} /> Costo Total
                            </label>
                            <div className="relative group">
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-emerald-500 font-bold pointer-events-none">$</span>
                                <input
                                    type="number"
                                    step="100"
                                    min="0"
                                    value={totalCost}
                                    onChange={e => setTotalCost(e.target.value)}
                                    className="w-full bg-[#0f1115] border border-gray-700 rounded-xl pl-10 pr-4 py-3 text-white text-lg font-mono focus:border-emerald-500 hover:border-gray-600 outline-none transition-all placeholder:text-gray-700"
                                    placeholder="0"
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    {/* Auto-Calc Info */}
                    <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3 flex justify-between items-center text-sm">
                        <span className="text-gray-400">Costo Unitario Calculado:</span>
                        <span className="font-mono font-bold text-emerald-400">
                            ${unitCost > 0 ? unitCost.toLocaleString('es-CO', { maximumFractionDigits: 2 }) : '0'} / {product.base_unit?.toLowerCase()}
                        </span>
                    </div>

                    {/* Supplier */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                            <Truck size={16} /> Proveedor <span className="text-gray-600 text-xs font-normal">(Opcional)</span>
                        </label>
                        <input
                            type="text"
                            value={supplier}
                            onChange={e => setSupplier(e.target.value)}
                            className="w-full bg-[#0f1115] border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-emerald-500 outline-none transition-all placeholder:text-gray-700"
                            placeholder="Ej. Makro, Tienda Local..."
                        />
                    </div>

                    {/* Buttons */}
                    <div className="pt-2 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-3 rounded-xl border border-gray-700 text-gray-300 hover:bg-white/5 transition-colors font-medium"
                            disabled={isSubmitting}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl px-4 py-3 font-bold shadow-lg shadow-emerald-900/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? (
                                <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                            ) : (
                                <>
                                    <span className="material-symbols-outlined">add_shopping_cart</span>
                                    Registrar Ingreso
                                </>
                            )}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};
