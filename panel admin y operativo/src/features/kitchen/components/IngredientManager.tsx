/**
 * IngredientManager - CRUD for Kitchen Ingredients (Insumos)
 * Uses the centralized kitchen.service
 */

import { useState, useEffect, useMemo } from 'react';
import { kitchenService, Ingredient, IngredientCreate, IngredientUpdate } from '../kitchen.service';

export const IngredientManager = () => {
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    // Modal states
    const [showModal, setShowModal] = useState(false);
    const [showCostModal, setShowCostModal] = useState(false);
    const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
    const [selectedForCost, setSelectedForCost] = useState<Ingredient | null>(null);

    // Form state
    const [formData, setFormData] = useState<Partial<IngredientCreate>>({
        name: '',
        sku: '',
        base_unit: 'kg',
        current_cost: 0,
        yield_factor: 1.0,
    });
    const [newCost, setNewCost] = useState(0);
    const [costReason, setCostReason] = useState('');

    useEffect(() => {
        loadIngredients();
    }, []);

    const loadIngredients = async () => {
        setLoading(true);
        try {
            const data = await kitchenService.getIngredients();
            setIngredients(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error loading ingredients');
        } finally {
            setLoading(false);
        }
    };

    const filteredIngredients = useMemo(() => {
        if (!searchQuery.trim()) return ingredients;
        const query = searchQuery.toLowerCase();
        return ingredients.filter(i =>
            i.name.toLowerCase().includes(query) ||
            i.sku.toLowerCase().includes(query)
        );
    }, [ingredients, searchQuery]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingIngredient) {
                await kitchenService.updateIngredient(editingIngredient.id, formData as IngredientUpdate);
            } else {
                await kitchenService.createIngredient(formData as IngredientCreate);
            }
            await loadIngredients();
            closeModal();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error saving ingredient');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('¿Eliminar este insumo?')) return;
        try {
            await kitchenService.deleteIngredient(id);
            await loadIngredients();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error deleting ingredient');
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
        setFormData({ name: '', sku: '', base_unit: 'kg', current_cost: 0, yield_factor: 1.0 });
        setShowModal(true);
    };

    const openEdit = (ingredient: Ingredient) => {
        setEditingIngredient(ingredient);
        setFormData({
            name: ingredient.name,
            sku: ingredient.sku,
            base_unit: ingredient.base_unit,
            current_cost: ingredient.current_cost,
            yield_factor: ingredient.yield_factor,
        });
        setShowModal(true);
    };

    const openCostUpdate = (ingredient: Ingredient) => {
        setSelectedForCost(ingredient);
        setNewCost(ingredient.current_cost);
        setCostReason('');
        setShowCostModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingIngredient(null);
    };

    const closeCostModal = () => {
        setShowCostModal(false);
        setSelectedForCost(null);
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-orange"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-accent-orange">nutrition</span>
                        Gestión de Insumos
                    </h1>
                    <p className="text-text-muted text-sm">Materias primas para recetas vivas</p>
                </div>
                <button
                    onClick={openCreate}
                    className="flex items-center gap-2 px-4 py-2.5 bg-accent-orange text-white rounded-lg hover:bg-orange-600 transition-colors font-medium"
                >
                    <span className="material-symbols-outlined text-[20px]">add</span>
                    Nuevo Insumo
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">search</span>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar por nombre o SKU..."
                    className="w-full bg-card-dark border border-border-dark rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-text-muted focus:outline-none focus:border-accent-orange"
                />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-card-dark border border-border-dark rounded-xl p-4">
                    <div className="text-text-muted text-xs uppercase">Total Insumos</div>
                    <div className="text-2xl font-bold text-white">{ingredients.length}</div>
                </div>
                <div className="bg-card-dark border border-border-dark rounded-xl p-4">
                    <div className="text-text-muted text-xs uppercase">Activos</div>
                    <div className="text-2xl font-bold text-emerald-400">
                        {ingredients.filter(i => i.is_active).length}
                    </div>
                </div>
                <div className="bg-card-dark border border-border-dark rounded-xl p-4">
                    <div className="text-text-muted text-xs uppercase">Alta Merma (&gt;15%)</div>
                    <div className="text-2xl font-bold text-amber-400">
                        {ingredients.filter(i => i.yield_factor < 0.85).length}
                    </div>
                </div>
                <div className="bg-card-dark border border-border-dark rounded-xl p-4">
                    <div className="text-text-muted text-xs uppercase">Valor Inventario</div>
                    <div className="text-lg font-bold text-white font-mono">
                        {formatCurrency(ingredients.reduce((sum, i) => sum + i.current_cost, 0))}
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Nombre / SKU</th>
                                <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">Unidad</th>
                                <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo Actual</th>
                                <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo Anterior</th>
                                <th className="px-4 py-3 text-center text-text-muted font-medium text-xs uppercase">Rendimiento</th>
                                <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {filteredIngredients.map((ingredient) => {
                                const mermaPercent = ((1 - ingredient.yield_factor) * 100).toFixed(0);
                                const costChange = ingredient.current_cost - ingredient.last_cost;

                                return (
                                    <tr key={ingredient.id} className="hover:bg-white/5">
                                        <td className="px-4 py-3">
                                            <div className="font-medium text-white">{ingredient.name}</div>
                                            <div className="text-xs text-text-muted">{ingredient.sku}</div>
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className="px-2 py-1 bg-white/5 rounded text-gray-300 text-xs font-mono">
                                                {ingredient.base_unit}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <span className="text-white font-mono">{formatCurrency(ingredient.current_cost)}</span>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <span className="text-text-muted font-mono">{formatCurrency(ingredient.last_cost)}</span>
                                            {costChange !== 0 && (
                                                <span className={`ml-2 text-xs ${costChange > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                                    {costChange > 0 ? '+' : ''}{((costChange / ingredient.last_cost) * 100).toFixed(1)}%
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <div className="flex items-center justify-center gap-2">
                                                <div className="w-16 h-1.5 bg-bg-deep rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${ingredient.yield_factor >= 0.90 ? 'bg-emerald-400' : ingredient.yield_factor >= 0.80 ? 'bg-amber-400' : 'bg-red-400'}`}
                                                        style={{ width: `${ingredient.yield_factor * 100}%` }}
                                                    />
                                                </div>
                                                <span className={`text-xs font-mono ${ingredient.yield_factor >= 0.90 ? 'text-emerald-400' : ingredient.yield_factor >= 0.80 ? 'text-amber-400' : 'text-red-400'}`}>
                                                    {(ingredient.yield_factor * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <div className="flex items-center justify-end gap-1">
                                                <button
                                                    onClick={() => openCostUpdate(ingredient)}
                                                    className="p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors"
                                                    title="Actualizar Costo"
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">attach_money</span>
                                                </button>
                                                <button
                                                    onClick={() => openEdit(ingredient)}
                                                    className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                                                    title="Editar"
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">edit</span>
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(ingredient.id)}
                                                    className="p-1.5 text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                                    title="Eliminar"
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">delete</span>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md">
                        <div className="p-6 border-b border-border-dark">
                            <h3 className="text-lg font-semibold text-white">
                                {editingIngredient ? 'Editar Insumo' : 'Nuevo Insumo'}
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
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">SKU</label>
                                <input
                                    type="text"
                                    value={formData.sku}
                                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                    required
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Unidad Base</label>
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
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Costo</label>
                                    <input
                                        type="number"
                                        value={formData.current_cost}
                                        onChange={(e) => setFormData({ ...formData, current_cost: Number(e.target.value) })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                        required
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Rendimiento (Yield) - {((formData.yield_factor || 1) * 100).toFixed(0)}%
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
                                <div className="flex justify-between text-xs text-text-muted">
                                    <span>50% (Alta merma)</span>
                                    <span>100% (Sin merma)</span>
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-accent-orange text-white rounded-lg hover:bg-orange-600"
                                >
                                    {editingIngredient ? 'Guardar Cambios' : 'Crear Insumo'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Cost Update Modal */}
            {showCostModal && selectedForCost && (
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
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Razón (opcional)</label>
                                <input
                                    type="text"
                                    value={costReason}
                                    onChange={(e) => setCostReason(e.target.value)}
                                    placeholder="Ej: Ajuste de proveedor"
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white"
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button onClick={closeCostModal} className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600">
                                    Cancelar
                                </button>
                                <button onClick={handleUpdateCost} className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500">
                                    Actualizar Costo
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default IngredientManager;
