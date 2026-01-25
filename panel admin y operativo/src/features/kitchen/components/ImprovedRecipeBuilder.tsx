/**
 * ImprovedRecipeBuilder - Constructor de Recetas Vivas con react-hook-form
 * 
 * Features:
 * - Dynamic ingredient list with useFieldArray
 * - Real-time cost calculation
 * - Merma (yield) visualization
 * - Ingredient spotlight search
 * - Profitability indicators
 */

import { useForm, useFieldArray } from 'react-hook-form';
import { useState, useEffect, useMemo } from 'react';
import { kitchenService, Ingredient, RecipePayload } from '../kitchen.service';
import { HelpIcon } from '@/components/ui/Tooltip';

interface RecipeFormData {
    name: string;
    product_id: string;
    preparation_time: number;
    selling_price: number;
    items: {
        ingredient_id: string;
        ingredient_name: string;
        gross_quantity: number;
        measure_unit: string;
        unit_cost: number;
        yield_factor: number;
    }[];
}

interface Props {
    productId?: number;
    onSave?: (recipe: any) => void;
    onCancel?: () => void;
}

export const ImprovedRecipeBuilder = ({ productId, onSave, onCancel }: Props) => {
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearch, setShowSearch] = useState(false);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    const { register, control, handleSubmit, watch, formState: { errors } } = useForm<RecipeFormData>({
        defaultValues: {
            name: '',
            product_id: productId?.toString() || '',
            preparation_time: 0,
            selling_price: 0,
            items: []
        }
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: 'items'
    });

    const watchedItems = watch('items');
    const watchedSellingPrice = watch('selling_price');

    // Fetch ingredients
    useEffect(() => {
        const fetchIngredients = async () => {
            setLoading(true);
            try {
                const data = await kitchenService.getIngredients();
                setIngredients(data);
            } catch (error) {
                console.error('Error loading ingredients:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchIngredients();
    }, []);

    // Filtered ingredients for search
    const filteredIngredients = useMemo(() => {
        if (!searchQuery.trim()) return ingredients.slice(0, 8);
        return ingredients.filter(i =>
            i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            i.sku.toLowerCase().includes(searchQuery.toLowerCase())
        ).slice(0, 8);
    }, [ingredients, searchQuery]);

    // Calculate totals
    const calculations = useMemo(() => {
        const totalCost = watchedItems.reduce((sum, item) => {
            const grossQty = Number(item.gross_quantity) || 0;
            const unitCost = Number(item.unit_cost) || 0;
            return sum + (grossQty * unitCost);
        }, 0);

        const sellingPrice = Number(watchedSellingPrice) || 0;
        const margin = sellingPrice > 0 ? ((sellingPrice - totalCost) / sellingPrice) * 100 : 0;
        const foodCostPct = sellingPrice > 0 ? (totalCost / sellingPrice) * 100 : 0;

        return { totalCost, margin, foodCostPct };
    }, [watchedItems, watchedSellingPrice]);

    const addIngredient = (ingredient: Ingredient) => {
        // Check if already added
        if (watchedItems.some(i => i.ingredient_id === ingredient.id)) {
            setShowSearch(false);
            setSearchQuery('');
            return;
        }

        append({
            ingredient_id: ingredient.id,
            ingredient_name: ingredient.name,
            gross_quantity: 0,
            measure_unit: ingredient.base_unit,
            unit_cost: ingredient.current_cost,
            yield_factor: ingredient.yield_factor
        });
        setShowSearch(false);
        setSearchQuery('');
    };

    const onSubmit = async (data: RecipeFormData) => {
        setSaving(true);
        try {
            const payload: RecipePayload = {
                product_id: Number(data.product_id),
                name: data.name,
                preparation_time: data.preparation_time,
                items: data.items.map(item => ({
                    ingredient_id: item.ingredient_id,
                    gross_quantity: item.gross_quantity,
                    measure_unit: item.measure_unit
                }))
            };

            const result = await kitchenService.createRecipe(payload);
            onSave?.(result);
        } catch (error) {
            console.error('Error saving recipe:', error);
            alert('Error al guardar la receta');
        } finally {
            setSaving(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(value);
    };

    const getProfitabilityColor = () => {
        if (calculations.foodCostPct === 0) return 'text-gray-400';
        if (calculations.foodCostPct <= 28) return 'text-emerald-400';
        if (calculations.foodCostPct <= 35) return 'text-amber-400';
        return 'text-red-400';
    };

    return (
        <div className="bg-card-dark border border-border-dark rounded-2xl p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-accent-orange">menu_book</span>
                            Constructor de Recetas Vivas
                        </h2>
                        <p className="text-text-muted text-sm">Vincula ingredientes con cálculo de costos en tiempo real</p>
                    </div>
                </div>

                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center">
                            Nombre de la Receta
                            <HelpIcon text="Nombre descriptivo para identificar esta receta. Ej: 'Hamburguesa Clásica 200g'" />
                        </label>
                        <input
                            {...register('name', { required: 'Nombre requerido' })}
                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white placeholder-text-muted focus:outline-none focus:border-accent-orange"
                            placeholder="Ej: Hamburguesa Clásica"
                        />
                        {errors.name && <span className="text-red-400 text-xs">{errors.name.message}</span>}
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                            Tiempo Preparación (min)
                        </label>
                        <input
                            type="number"
                            {...register('preparation_time', { valueAsNumber: true })}
                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="15"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center">
                            Precio de Venta
                            <HelpIcon text="Precio al que vendes este platillo. Sirve para calcular automáticamente tu margen de ganancia y food cost %." />
                        </label>
                        <input
                            type="number"
                            {...register('selling_price', { valueAsNumber: true })}
                            className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="25000"
                        />
                    </div>
                </div>

                {/* Ingredients Section */}
                <div className="border border-border-dark rounded-xl p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-[20px]">nutrition</span>
                            Ingredientes
                        </h3>
                        <div className="relative">
                            <button
                                type="button"
                                onClick={() => setShowSearch(!showSearch)}
                                className="flex items-center gap-2 px-4 py-2 bg-accent-orange/10 text-accent-orange rounded-lg hover:bg-accent-orange/20 transition-colors text-sm font-medium"
                            >
                                <span className="material-symbols-outlined text-[18px]">add</span>
                                Agregar Insumo
                            </button>

                            {/* Search Dropdown */}
                            {showSearch && (
                                <div className="absolute right-0 top-full mt-2 w-80 bg-bg-deep border border-border-dark rounded-xl shadow-xl z-50">
                                    <div className="p-3 border-b border-border-dark">
                                        <input
                                            type="text"
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            placeholder="Buscar insumo..."
                                            className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-orange"
                                            autoFocus
                                        />
                                    </div>
                                    <div className="max-h-64 overflow-y-auto">
                                        {loading ? (
                                            <div className="p-4 text-center text-text-muted">Cargando...</div>
                                        ) : filteredIngredients.length === 0 ? (
                                            <div className="p-4 text-center text-text-muted">No encontrado</div>
                                        ) : (
                                            filteredIngredients.map((ing) => (
                                                <button
                                                    key={ing.id}
                                                    type="button"
                                                    onClick={() => addIngredient(ing)}
                                                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors text-left"
                                                >
                                                    <div>
                                                        <div className="text-white font-medium text-sm">{ing.name}</div>
                                                        <div className="text-text-muted text-xs">{ing.sku} • {ing.base_unit}</div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-emerald-400 font-mono text-sm">
                                                            {formatCurrency(ing.current_cost)}/{ing.base_unit}
                                                        </div>
                                                        <div className="text-text-muted text-xs">
                                                            Rend: {(ing.yield_factor * 100).toFixed(0)}%
                                                        </div>
                                                    </div>
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Ingredients Table */}
                    {fields.length === 0 ? (
                        <div className="text-center py-8 text-text-muted">
                            <span className="material-symbols-outlined text-4xl mb-2">restaurant</span>
                            <p>Agrega ingredientes para construir tu receta</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {/* Header */}
                            <div className="grid grid-cols-12 gap-2 px-3 py-2 text-xs text-text-muted font-medium uppercase">
                                <div className="col-span-3">Insumo</div>
                                <div className="col-span-2 text-center flex items-center justify-center gap-1">
                                    Cantidad Bruta
                                    <HelpIcon text="La cantidad que SACAS del almacén para hacer este platillo. Ej: 0.140 kg (140 gramos de carne)" position="bottom" />
                                </div>
                                <div className="col-span-1 text-center">Unidad</div>
                                <div className="col-span-2 text-center flex items-center justify-center gap-1">
                                    Merma
                                    <HelpIcon text="Porcentaje que pierdes al procesar (grasa, cáscaras, etc). Se calcula automáticamente del rendimiento del insumo." position="bottom" />
                                </div>
                                <div className="col-span-2 text-center flex items-center justify-center gap-1">
                                    Neto
                                    <HelpIcon text="Cantidad REAL que usas después de aplicar la merma. El sistema la calcula automáticamente." position="bottom" />
                                </div>
                                <div className="col-span-1 text-right">Costo</div>
                                <div className="col-span-1"></div>
                            </div>

                            {/* Items */}
                            {fields.map((field, index) => {
                                const item = watchedItems[index];
                                const netQty = (item?.gross_quantity || 0) * (item?.yield_factor || 1);
                                const itemCost = (item?.gross_quantity || 0) * (item?.unit_cost || 0);
                                const mermaPercent = ((1 - (item?.yield_factor || 1)) * 100).toFixed(0);

                                return (
                                    <div key={field.id} className="grid grid-cols-12 gap-2 items-center bg-bg-deep rounded-lg px-3 py-2">
                                        <div className="col-span-3">
                                            <span className="text-white text-sm font-medium">{item?.ingredient_name}</span>
                                        </div>
                                        <div className="col-span-2">
                                            <input
                                                type="number"
                                                step="0.001"
                                                {...register(`items.${index}.gross_quantity`, { valueAsNumber: true })}
                                                className="w-full bg-card-dark border border-border-dark rounded px-2 py-1.5 text-white text-sm text-center focus:outline-none focus:border-accent-orange"
                                            />
                                        </div>
                                        <div className="col-span-1 text-center text-text-muted text-sm">
                                            {item?.measure_unit}
                                        </div>
                                        <div className="col-span-2 text-center">
                                            <span className={`text-sm ${Number(mermaPercent) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                                                {mermaPercent}%
                                            </span>
                                        </div>
                                        <div className="col-span-2 text-center text-white font-mono text-sm">
                                            {netQty.toFixed(3)}
                                        </div>
                                        <div className="col-span-1 text-right text-emerald-400 font-mono text-sm">
                                            {formatCurrency(itemCost)}
                                        </div>
                                        <div className="col-span-1 text-right">
                                            <button
                                                type="button"
                                                onClick={() => remove(index)}
                                                className="p-1.5 text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">delete</span>
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Cost Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-bg-deep rounded-xl p-4 border border-border-dark">
                        <div className="text-text-muted text-xs uppercase mb-1">Costo Total</div>
                        <div className="text-2xl font-bold text-white font-mono">
                            {formatCurrency(calculations.totalCost)}
                        </div>
                    </div>
                    <div className="bg-bg-deep rounded-xl p-4 border border-border-dark">
                        <div className="text-text-muted text-xs uppercase mb-1">Food Cost %</div>
                        <div className={`text-2xl font-bold font-mono ${getProfitabilityColor()}`}>
                            {calculations.foodCostPct.toFixed(1)}%
                        </div>
                    </div>
                    <div className="bg-bg-deep rounded-xl p-4 border border-border-dark">
                        <div className="text-text-muted text-xs uppercase mb-1">Margen Bruto</div>
                        <div className={`text-2xl font-bold font-mono ${calculations.margin >= 65 ? 'text-emerald-400' : calculations.margin >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                            {calculations.margin.toFixed(1)}%
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-border-dark">
                    {onCancel && (
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-6 py-2.5 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                        >
                            Cancelar
                        </button>
                    )}
                    <button
                        type="submit"
                        disabled={saving || fields.length === 0}
                        className="px-6 py-2.5 bg-accent-orange text-white rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {saving ? (
                            <>
                                <span className="animate-spin material-symbols-outlined text-[18px]">progress_activity</span>
                                Guardando...
                            </>
                        ) : (
                            <>
                                <span className="material-symbols-outlined text-[18px]">save</span>
                                Guardar Receta
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ImprovedRecipeBuilder;
