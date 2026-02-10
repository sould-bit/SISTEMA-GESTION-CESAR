import React, { useState } from 'react';
import { Ingredient, IngredientCreate } from '../kitchen.service';
import { formatCurrency, formatNumber, numberToWords, formatInputValue } from '@/utils/formatters';

const HelpIcon = ({ text, color = 'text-gray-400' }: { text: string, color?: string }) => (
    <span className={`ml-1 ${color} hover:text-white cursor-help`} title={text}>
        <span className="material-symbols-outlined text-[14px] align-middle">help</span>
    </span>
);

interface IngredientFormModalProps {
    isOpen: boolean;
    activeTab: 'RAW' | 'PROCESSED';
    editingIngredient: Ingredient | null;
    formData: Partial<IngredientCreate> & { initial_quantity?: number; total_cost_paid?: number };
    setFormData: (data: any) => void;
    onClose: () => void;
    onSubmit: (e: React.FormEvent) => void;
    handleFormattedInput: (e: React.ChangeEvent<HTMLInputElement>, setter: (val: number) => void) => void;
}

export const IngredientFormModal: React.FC<IngredientFormModalProps> = ({
    isOpen,
    activeTab,
    editingIngredient,
    formData,
    setFormData,
    onClose,
    onSubmit,
    handleFormattedInput
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md shadow-2xl">
                <div className="p-6 border-b border-border-dark bg-white/5">
                    <h3 className="text-lg font-semibold text-white">
                        {editingIngredient ? 'Editar' : (activeTab === 'RAW' ? 'Nueva Materia Prima' : 'Nueva Producción Interna')}
                    </h3>
                </div>
                <form onSubmit={onSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Nombre</label>
                        <input
                            type="text"
                            value={formData?.name || ''}
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
                                                {formatCurrency(unitCost, unitCost < 100 ? 2 : 0)}
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

                    {editingIngredient && activeTab === 'RAW' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                                Costo Unitario Actual
                                <HelpIcon text="Precio de compra por unidad base" color="text-blue-400/80" />
                            </label>
                            <input
                                type="number"
                                value={formData?.current_cost || 0}
                                onChange={(e) => setFormData({ ...formData, current_cost: Number(e.target.value) })}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                            />
                        </div>
                    )}

                    {activeTab === 'RAW' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center">
                                Rendimiento (Yield) - {((formData?.yield_factor || 1) * 100).toFixed(0)}%
                                <HelpIcon text="Porcentaje aprovechable del insumo después de limpieza/merma." color="text-amber-400/80" />
                            </label>
                            <input
                                type="range"
                                min="0.5"
                                max="1"
                                step="0.01"
                                value={formData?.yield_factor || 1}
                                onChange={(e) => setFormData({ ...formData, yield_factor: Number(e.target.value) })}
                                className="w-full"
                            />
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4 border-t border-border-dark mt-4">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Cancelar</button>
                        <button type="submit" className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-orange-600 shadow-lg shadow-orange-500/20">
                            {editingIngredient ? 'Guardar Cambios' : 'Crear Item'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

interface CostUpdateModalProps {
    isOpen: boolean;
    ingredient: Ingredient | null;
    onClose: () => void;
    onUpdate: (newCost: number) => Promise<void>;
}

export const CostUpdateModal: React.FC<CostUpdateModalProps> = ({
    isOpen,
    ingredient,
    onClose,
    onUpdate
}) => {
    const [newCost, setNewCost] = useState(ingredient?.current_cost || 0);

    if (!isOpen || !ingredient) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md">
                <div className="p-6 border-b border-border-dark">
                    <h3 className="text-lg font-semibold text-white">Actualizar Costo</h3>
                    <p className="text-text-muted text-sm">{ingredient.name}</p>
                </div>
                <div className="p-6 space-y-4">
                    <div className="flex justify-between text-sm">
                        <span className="text-text-muted">Costo Actual:</span>
                        <span className="text-white font-mono">{formatCurrency(ingredient.current_cost)}</span>
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
                        <button onClick={onClose} className="px-4 py-2 text-gray-400">Cancelar</button>
                        <button onClick={() => onUpdate(newCost)} className="px-4 py-2 bg-emerald-600 text-white rounded-lg">Actualizar</button>
                    </div>
                </div>
            </div>
        </div>
    );
};
