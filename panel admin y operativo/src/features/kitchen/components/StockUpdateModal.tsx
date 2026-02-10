import React from 'react';
import { Ingredient, IngredientUpdate } from '../kitchen.service';
import { formatCurrency, formatNumber, formatInputValue } from '@/utils/formatters';

interface StockUpdateModalProps {
    ingredient: Ingredient;
    onClose: () => void;
    onUpdate: (quantity: number, totalCost: number, supplier: string) => Promise<void>;
}

export const StockUpdateModal: React.FC<StockUpdateModalProps> = ({
    ingredient,
    onClose,
    onUpdate
}) => {
    const [stockData, setStockData] = React.useState({
        quantity: 0,
        total_cost: 0,
        supplier: '',
        type: 'IN' as const
    });
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const currentStock = Number((ingredient as any).stock) || 0;
    const adjustmentQty = Number(stockData.quantity) || 0;
    const projectedStock = currentStock + adjustmentQty;

    const handleFormattedInput = (
        e: React.ChangeEvent<HTMLInputElement>,
        setter: (val: number) => void
    ) => {
        const rawValue = e.target.value.replace(/[^0-9]/g, '');
        const numericValue = parseInt(rawValue, 10) || 0;
        setter(numericValue);
    };

    const handleSubmit = async () => {
        if (stockData.quantity <= 0) return;
        setIsSubmitting(true);
        try {
            await onUpdate(stockData.quantity, stockData.total_cost, stockData.supplier);
            onClose();
        } catch (error) {
            console.error('Error updating stock:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

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
                        <p className="text-text-muted text-sm ml-11">Ingresa los detalles de la compra de <strong>{ingredient.name}</strong></p>
                    </div>
                    <div className="text-right hidden sm:block">
                        <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Stock Actual</p>
                        <p className="text-white font-mono font-bold text-lg">
                            {formatNumber(currentStock, 4)} <span className="text-sm font-normal text-gray-400">{ingredient.base_unit}</span>
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
                                    onChange={e => setStockData({ ...stockData, quantity: parseFloat(e.target.value) || 0 })}
                                    className="w-full bg-bg-deep border border-emerald-500/30 rounded-xl pl-10 pr-12 py-4 text-white font-mono text-2xl focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all shadow-inner"
                                    placeholder="0"
                                    autoFocus
                                />
                                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                                    <span className="text-emerald-500/50 font-mono text-sm uppercase font-bold">{ingredient.base_unit}</span>
                                </div>
                            </div>

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
                                    onChange={e => handleFormattedInput(e, (val) => setStockData({ ...stockData, total_cost: val }))}
                                    className="w-full bg-bg-deep border border-amber-500/30 rounded-xl pl-10 pr-4 py-4 text-white text-2xl font-mono focus:ring-2 focus:ring-amber-500/50 transition-all shadow-inner"
                                    placeholder="$ 0"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Supplier Input */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">📍 Proveedor / Origen</label>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-gray-500 group-focus-within:text-emerald-500 transition-colors">store</span>
                            </div>
                            <input
                                type="text"
                                value={stockData.supplier}
                                onChange={e => setStockData({ ...stockData, supplier: e.target.value })}
                                className="w-full bg-bg-deep border border-border-dark rounded-xl pl-10 pr-4 py-3 text-white focus:ring-2 focus:ring-emerald-500/30 transition-all placeholder-gray-600"
                                placeholder="Ej: La Plaza, Makro, Fruver..."
                            />
                        </div>
                    </div>

                    {/* Cost Calculation View handled by backend, but we show a preview */}
                    {(stockData.quantity > 0 && stockData.total_cost > 0) && (() => {
                        const unitCost = stockData.total_cost / stockData.quantity;
                        return (
                            <div className="bg-gradient-to-br from-emerald-500/10 to-transparent border border-emerald-500/20 rounded-xl p-4 animate-in slide-in-from-bottom-2">
                                <div className="flex justify-between items-center mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="p-1.5 bg-emerald-500/20 rounded-lg text-emerald-400">
                                            <span className="material-symbols-outlined text-[18px]">calculate</span>
                                        </span>
                                        <span className="text-xs font-semibold text-emerald-300 uppercase tracking-widest">Previsualización de Costo</span>
                                    </div>
                                </div>
                                <div className="flex items-baseline justify-between">
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-3xl font-bold text-emerald-400 font-mono tracking-tight">
                                            {formatCurrency(unitCost)}
                                        </span>
                                        <span className="text-sm text-emerald-600 font-medium">/ {ingredient.base_unit}</span>
                                    </div>
                                </div>
                                <p className="text-[10px] text-amber-500/80 mt-2 font-medium bg-amber-500/5 inline-block px-2 py-1 rounded">
                                    EL COSTO REAL SERÁ CALCULADO POR EL SERVIDOR (WAC).
                                </p>
                            </div>
                        );
                    })()}
                </div>

                <div className="p-6 border-t border-border-dark bg-bg-deep/50 rounded-b-2xl flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        disabled={isSubmitting}
                        className="px-5 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors font-medium text-sm"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || stockData.quantity <= 0}
                        className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-400 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-all font-bold flex items-center gap-2 group transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? (
                            <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                        ) : (
                            <>
                                <span className="material-symbols-outlined group-hover:animate-bounce">save</span>
                                Registrar Compra
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
