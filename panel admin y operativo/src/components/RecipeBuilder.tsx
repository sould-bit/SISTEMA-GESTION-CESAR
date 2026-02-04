/**
 * RecipeBuilder - Constructor de Recetas con Cálculo en Tiempo Real
 * 
 * Features:
 * - Spotlight search para ingredientes
 * - Cálculo de costo en tiempo real
 * - Visualización de merma
 * - Semáforo de rentabilidad
 */

import { useState, useMemo, useEffect } from 'react';
import { api } from '../../lib/api';
import { Ingredient } from '../../types/ingredient';

interface RecipeItemForm {
    ingredient_id: string;
    ingredient_name: string;
    gross_quantity: number;
    net_quantity: number;
    measure_unit: string;
    unit_cost: number;
    yield_factor: number;
    calculated_cost: number;
}

interface RecipeBuilderProps {
    productId?: number;
    onSave?: (recipeData: any) => void;
    onCancel?: () => void;
}

export const RecipeBuilder = ({ productId, onSave, onCancel }: RecipeBuilderProps) => {
    const [recipeName, setRecipeName] = useState('');
    const [preparationTime, setPreparationTime] = useState(0);
    const [items, setItems] = useState<RecipeItemForm[]>([]);

    // Ingredient search
    const [searchTerm, setSearchTerm] = useState('');
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [loading, setLoading] = useState(false);

    // Fetch ingredients on mount
    useEffect(() => {
        const fetchIngredients = async () => {
            try {
                const response = await api.get<Ingredient[]>('/ingredients/');
                setIngredients(response.data);
            } catch (err) {
                console.error('Error loading ingredients', err);
            }
        };
        fetchIngredients();
    }, []);

    // Filter ingredients based on search
    const filteredIngredients = useMemo(() => {
        if (!searchTerm) return ingredients.slice(0, 10);
        const term = searchTerm.toLowerCase();
        return ingredients
            .filter((ing) => ing.name.toLowerCase().includes(term) || ing.sku.toLowerCase().includes(term))
            .slice(0, 10);
    }, [ingredients, searchTerm]);

    // Total cost calculation
    const totalCost = useMemo(() => {
        return items.reduce((sum, item) => sum + item.calculated_cost, 0);
    }, [items]);

    // Add ingredient to recipe
    const addIngredient = (ingredient: Ingredient) => {
        // Check if already added
        if (items.some((item) => item.ingredient_id === ingredient.id)) {
            setSearchTerm('');
            setShowDropdown(false);
            return;
        }

        const newItem: RecipeItemForm = {
            ingredient_id: ingredient.id,
            ingredient_name: ingredient.name,
            gross_quantity: 0,
            net_quantity: 0,
            measure_unit: ingredient.base_unit,
            unit_cost: ingredient.current_cost,
            yield_factor: ingredient.yield_factor,
            calculated_cost: 0,
        };

        setItems([...items, newItem]);
        setSearchTerm('');
        setShowDropdown(false);
    };

    // Update item quantity and recalculate
    const updateItemQuantity = (index: number, grossQty: number) => {
        const newItems = [...items];
        const item = newItems[index];

        item.gross_quantity = grossQty;
        item.net_quantity = grossQty * item.yield_factor;
        item.calculated_cost = grossQty * item.unit_cost;

        setItems(newItems);
    };

    // Remove item
    const removeItem = (index: number) => {
        setItems(items.filter((_, i) => i !== index));
    };

    // Handle save
    const handleSave = async () => {
        if (!recipeName || items.length === 0) return;

        setLoading(true);
        try {
            const recipeData = {
                name: recipeName,
                preparation_time: preparationTime,
                items: items.map((item) => ({
                    ingredient_id: item.ingredient_id,
                    gross_quantity: item.gross_quantity,
                    net_quantity: item.net_quantity,
                    measure_unit: item.measure_unit,
                })),
            };
            onSave?.(recipeData);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    // Get profitability color (food cost percentage thresholds)
    const getProfitabilityColor = (totalCost: number, sellingPrice: number = 0) => {
        if (sellingPrice === 0) return 'text-text-muted';
        const foodCostPercentage = (totalCost / sellingPrice) * 100;
        if (foodCostPercentage <= 28) return 'text-emerald-400'; // Excellent
        if (foodCostPercentage <= 35) return 'text-amber-400'; // Good
        return 'text-red-400'; // Needs attention
    };

    return (
        <div className="bg-card-dark border border-border-dark rounded-2xl overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-border-dark">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span className="material-symbols-outlined text-accent-primary">restaurant</span>
                    Constructor de Receta
                </h2>
                <p className="text-text-muted text-sm mt-1">
                    Añade ingredientes y calcula el costo automáticamente
                </p>
            </div>

            <div className="p-6 space-y-6">
                {/* Recipe Name & Time */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-text-muted mb-1">Nombre de la Receta *</label>
                        <input
                            type="text"
                            value={recipeName}
                            onChange={(e) => setRecipeName(e.target.value)}
                            placeholder="Ej: Hamburguesa Clásica"
                            className="w-full bg-bg-deep border border-border-dark rounded-lg py-2.5 px-4 text-white focus:outline-none focus:border-accent-primary transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-text-muted mb-1">Tiempo de Preparación (min)</label>
                        <input
                            type="number"
                            min="0"
                            value={preparationTime}
                            onChange={(e) => setPreparationTime(parseInt(e.target.value) || 0)}
                            className="w-full bg-bg-deep border border-border-dark rounded-lg py-2.5 px-4 text-white font-mono focus:outline-none focus:border-accent-primary transition-all"
                        />
                    </div>
                </div>

                {/* Ingredient Search (Spotlight) */}
                <div className="relative">
                    <label className="block text-sm font-medium text-text-muted mb-1">Buscar Ingrediente</label>
                    <div className="relative">
                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-text-muted">search</span>
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => {
                                setSearchTerm(e.target.value);
                                setShowDropdown(true);
                            }}
                            onFocus={() => setShowDropdown(true)}
                            placeholder="Buscar por nombre o SKU..."
                            className="w-full bg-bg-deep border border-border-dark rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-accent-primary transition-all"
                        />
                    </div>

                    {/* Dropdown */}
                    {showDropdown && filteredIngredients.length > 0 && (
                        <div className="absolute z-20 w-full mt-1 bg-card-dark border border-border-dark rounded-xl shadow-2xl max-h-64 overflow-y-auto">
                            {filteredIngredients.map((ingredient) => (
                                <button
                                    key={ingredient.id}
                                    onClick={() => addIngredient(ingredient)}
                                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors border-b border-border-dark last:border-b-0"
                                >
                                    <div className="flex flex-col items-start">
                                        <span className="font-medium text-white">{ingredient.name}</span>
                                        <span className="text-xs text-text-muted font-mono">{ingredient.sku} • {ingredient.base_unit}</span>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-emerald-400 font-mono text-sm">
                                            {formatCurrency(ingredient.current_cost)}/{ingredient.base_unit}
                                        </span>
                                        {ingredient.yield_factor < 1 && (
                                            <span className="text-xs text-amber-400 block">
                                                {((1 - ingredient.yield_factor) * 100).toFixed(0)}% merma
                                            </span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Items Table */}
                {items.length > 0 && (
                    <div className="border border-border-dark rounded-xl overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-bg-deep">
                                <tr>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Ingrediente</th>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Cantidad Bruta</th>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Cantidad Neta</th>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Merma</th>
                                    <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo</th>
                                    <th className="px-4 py-3"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark">
                                {items.map((item, index) => (
                                    <tr key={item.ingredient_id} className="hover:bg-white/5">
                                        <td className="px-4 py-3">
                                            <span className="font-medium text-white">{item.ingredient_name}</span>
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <input
                                                    type="number"
                                                    min="0"
                                                    step="0.01"
                                                    value={item.gross_quantity || ''}
                                                    onChange={(e) => updateItemQuantity(index, parseFloat(e.target.value) || 0)}
                                                    className="w-20 bg-bg-deep border border-border-dark rounded px-2 py-1 text-white font-mono text-center focus:outline-none focus:border-accent-primary"
                                                />
                                                <span className="text-text-muted">{item.measure_unit}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 font-mono text-gray-300">
                                            {item.net_quantity.toFixed(2)} {item.measure_unit}
                                        </td>
                                        <td className="px-4 py-3">
                                            {item.yield_factor < 1 ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-16 h-2 bg-bg-deep rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-amber-500"
                                                            style={{ width: `${(1 - item.yield_factor) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs text-amber-400">
                                                        {((1 - item.yield_factor) * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                            ) : (
                                                <span className="text-text-muted">-</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right font-mono text-emerald-400">
                                            {formatCurrency(item.calculated_cost)}
                                        </td>
                                        <td className="px-4 py-3">
                                            <button
                                                onClick={() => removeItem(index)}
                                                className="text-text-muted hover:text-red-400 transition-colors p-1 rounded hover:bg-red-500/10"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">close</span>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {items.length === 0 && (
                    <div className="text-center py-12 text-text-muted">
                        <span className="material-symbols-outlined text-4xl mb-2 block">receipt_long</span>
                        Busca y añade ingredientes para construir la receta
                    </div>
                )}

                {/* Total Cost */}
                {items.length > 0 && (
                    <div className="flex items-center justify-between p-4 bg-bg-deep rounded-xl border border-border-dark">
                        <div>
                            <span className="text-text-muted text-sm">Costo Total de la Receta</span>
                            <div className="text-2xl font-bold text-white font-mono">
                                {formatCurrency(totalCost)}
                            </div>
                        </div>
                        <div className="text-right">
                            <span className="text-text-muted text-sm">{items.length} ingredientes</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="p-6 border-t border-border-dark flex justify-end gap-3">
                <button
                    onClick={onCancel}
                    className="px-4 py-2 text-text-muted hover:text-white transition-colors"
                >
                    Cancelar
                </button>
                <button
                    onClick={handleSave}
                    disabled={!recipeName || items.length === 0 || loading}
                    className="px-6 py-2 bg-accent-primary hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                >
                    {loading ? 'Guardando...' : 'Guardar Receta'}
                </button>
            </div>
        </div>
    );
};
