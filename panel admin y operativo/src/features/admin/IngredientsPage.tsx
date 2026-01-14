/**
 * IngredientsPage - Gestión de Insumos/Materias Primas
 * 
 * Diferencia con Productos:
 * - Los insumos se compran y gastan, pero NO se venden directamente.
 * - Ejemplos: Aceite, Harina, Tomates, Carne.
 */

import { useState, useMemo } from 'react';
import { useIngredients } from '../../hooks/useIngredients';
import { Ingredient, IngredientCreate } from '../../types/ingredient';

// Base units for dropdown
const BASE_UNITS = [
    { value: 'kg', label: 'Kilogramo (kg)' },
    { value: 'g', label: 'Gramo (g)' },
    { value: 'lt', label: 'Litro (lt)' },
    { value: 'ml', label: 'Mililitro (ml)' },
    { value: 'und', label: 'Unidad (und)' },
    { value: 'lb', label: 'Libra (lb)' },
    { value: 'oz', label: 'Onza (oz)' },
];

export const IngredientsPage = () => {
    const { ingredients, loading, error, createIngredient, updateIngredient, deleteIngredient, updateCost } = useIngredients();
    const [searchTerm, setSearchTerm] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [showCostModal, setShowCostModal] = useState(false);
    const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
    const [formError, setFormError] = useState<string | null>(null);

    // Form state
    const [formData, setFormData] = useState<IngredientCreate>({
        name: '',
        sku: '',
        base_unit: 'kg',
        current_cost: 0,
        yield_factor: 1.0,
    });
    const [newCost, setNewCost] = useState<number>(0);

    const filteredIngredients = useMemo(() => {
        if (!searchTerm) return ingredients;
        const term = searchTerm.toLowerCase();
        return ingredients.filter(
            (ing) =>
                ing.name.toLowerCase().includes(term) ||
                ing.sku.toLowerCase().includes(term)
        );
    }, [ingredients, searchTerm]);

    const openCreateModal = () => {
        setEditingIngredient(null);
        setFormData({ name: '', sku: '', base_unit: 'kg', current_cost: 0, yield_factor: 1.0 });
        setFormError(null);
        setShowModal(true);
    };

    const openEditModal = (ingredient: Ingredient) => {
        setEditingIngredient(ingredient);
        setFormData({
            name: ingredient.name,
            sku: ingredient.sku,
            base_unit: ingredient.base_unit,
            current_cost: ingredient.current_cost,
            yield_factor: ingredient.yield_factor,
        });
        setFormError(null);
        setShowModal(true);
    };

    const openCostModal = (ingredient: Ingredient) => {
        setEditingIngredient(ingredient);
        setNewCost(ingredient.current_cost);
        setShowCostModal(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormError(null);
        try {
            if (editingIngredient) {
                await updateIngredient(editingIngredient.id, formData);
            } else {
                await createIngredient(formData);
            }
            setShowModal(false);
        } catch (err: any) {
            setFormError(err.response?.data?.detail || 'Error al guardar');
        }
    };

    const handleCostUpdate = async () => {
        if (!editingIngredient) return;
        try {
            await updateCost(editingIngredient.id, newCost);
            setShowCostModal(false);
        } catch (err: any) {
            setFormError(err.response?.data?.detail || 'Error al actualizar costo');
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm('¿Estás seguro de eliminar este insumo?')) {
            await deleteIngredient(id);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    if (loading && ingredients.length === 0) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-orange"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Insumos / Materias Primas</h1>
                    <p className="text-text-muted text-sm">Gestión de ingredientes para recetas</p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="flex items-center gap-2 bg-accent-orange hover:bg-orange-600 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-accent-orange/20"
                >
                    <span className="material-symbols-outlined">add</span>
                    Nuevo Insumo
                </button>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                        <span className="material-symbols-outlined text-2xl">nutrition</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Total Insumos</p>
                        <h3 className="text-2xl font-bold text-white">{ingredients.length}</h3>
                    </div>
                </div>
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
                        <span className="material-symbols-outlined text-2xl">scale</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Unidades en Uso</p>
                        <h3 className="text-2xl font-bold text-white">
                            {new Set(ingredients.map((i) => i.base_unit)).size}
                        </h3>
                    </div>
                </div>
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
                        <span className="material-symbols-outlined text-2xl">trending_up</span>
                    </div>
                    <div>
                        <p className="text-text-muted text-xs uppercase tracking-wider">Con Merma</p>
                        <h3 className="text-2xl font-bold text-white">
                            {ingredients.filter((i) => i.yield_factor < 1).length}
                        </h3>
                    </div>
                </div>
            </div>

            {/* Search */}
            <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-text-muted">search</span>
                <input
                    type="text"
                    placeholder="Buscar por nombre o SKU..."
                    className="w-full bg-card-dark border border-border-dark rounded-lg py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-accent-orange focus:ring-1 focus:ring-accent-orange transition-all"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Table */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Nombre / SKU</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Unidad</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Costo Actual</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Último Costo</th>
                                <th className="px-6 py-4 text-left font-semibold text-text-muted uppercase tracking-wider text-xs">Merma</th>
                                <th className="px-6 py-4 text-right font-semibold text-text-muted uppercase tracking-wider text-xs">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {filteredIngredients.map((ingredient) => (
                                <tr key={ingredient.id} className="group hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-white">{ingredient.name}</span>
                                            <span className="text-xs text-text-muted font-mono">{ingredient.sku}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-300 font-mono uppercase">
                                        {ingredient.base_unit}
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            onClick={() => openCostModal(ingredient)}
                                            className="font-mono text-emerald-400 hover:text-emerald-300 hover:underline transition-colors"
                                        >
                                            {formatCurrency(ingredient.current_cost)}
                                        </button>
                                    </td>
                                    <td className="px-6 py-4 font-mono text-text-muted">
                                        {formatCurrency(ingredient.last_cost)}
                                    </td>
                                    <td className="px-6 py-4">
                                        {ingredient.yield_factor < 1 ? (
                                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                                {((1 - ingredient.yield_factor) * 100).toFixed(0)}%
                                            </span>
                                        ) : (
                                            <span className="text-text-muted">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-1">
                                            <button
                                                onClick={() => openEditModal(ingredient)}
                                                className="text-text-muted hover:text-white transition-colors p-1.5 rounded hover:bg-white/10"
                                                title="Editar"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">edit</span>
                                            </button>
                                            <button
                                                onClick={() => handleDelete(ingredient.id)}
                                                className="text-text-muted hover:text-red-400 transition-colors p-1.5 rounded hover:bg-red-500/10"
                                                title="Eliminar"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">delete</span>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {filteredIngredients.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-text-muted">
                                        {searchTerm ? 'No se encontraron resultados' : 'No hay insumos registrados'}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between p-6 border-b border-border-dark">
                            <h2 className="text-lg font-semibold text-white">
                                {editingIngredient ? 'Editar Insumo' : 'Nuevo Insumo'}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="text-text-muted hover:text-white">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            {formError && (
                                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-3 py-2 rounded-lg text-sm">
                                    {formError}
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-text-muted mb-1">Nombre *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white focus:outline-none focus:border-accent-orange"
                                    placeholder="Ej: Carne de Res Premium"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-muted mb-1">SKU *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.sku}
                                        onChange={(e) => setFormData({ ...formData, sku: e.target.value.toUpperCase() })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white font-mono focus:outline-none focus:border-accent-orange"
                                        placeholder="MAT-001"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-muted mb-1">Unidad Base *</label>
                                    <select
                                        required
                                        value={formData.base_unit}
                                        onChange={(e) => setFormData({ ...formData, base_unit: e.target.value })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white focus:outline-none focus:border-accent-orange"
                                    >
                                        {BASE_UNITS.map((unit) => (
                                            <option key={unit.value} value={unit.value}>
                                                {unit.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-muted mb-1">Costo por Unidad</label>
                                    <input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={formData.current_cost}
                                        onChange={(e) => setFormData({ ...formData, current_cost: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white font-mono focus:outline-none focus:border-accent-orange"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-muted mb-1">
                                        Factor de Merma
                                        <span className="text-xs text-text-muted ml-1">(0.90 = 10% merma)</span>
                                    </label>
                                    <input
                                        type="number"
                                        min="0.01"
                                        max="1"
                                        step="0.01"
                                        value={formData.yield_factor}
                                        onChange={(e) => setFormData({ ...formData, yield_factor: parseFloat(e.target.value) || 1 })}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white font-mono focus:outline-none focus:border-accent-orange"
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-text-muted hover:text-white transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-accent-orange hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
                                >
                                    {editingIngredient ? 'Guardar Cambios' : 'Crear Insumo'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Cost Update Modal */}
            {showCostModal && editingIngredient && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-sm shadow-2xl">
                        <div className="flex items-center justify-between p-6 border-b border-border-dark">
                            <h2 className="text-lg font-semibold text-white">Actualizar Costo</h2>
                            <button onClick={() => setShowCostModal(false)} className="text-text-muted hover:text-white">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <p className="text-text-muted text-sm">
                                Actualizando costo de <span className="text-white font-medium">{editingIngredient.name}</span>
                            </p>
                            <div className="flex items-center gap-4">
                                <div className="flex-1">
                                    <label className="block text-xs text-text-muted mb-1">Costo Anterior</label>
                                    <div className="font-mono text-gray-400 line-through">
                                        {formatCurrency(editingIngredient.current_cost)}
                                    </div>
                                </div>
                                <span className="material-symbols-outlined text-text-muted">arrow_forward</span>
                                <div className="flex-1">
                                    <label className="block text-xs text-text-muted mb-1">Nuevo Costo</label>
                                    <input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={newCost}
                                        onChange={(e) => setNewCost(parseFloat(e.target.value) || 0)}
                                        className="w-full bg-bg-deep border border-border-dark rounded-lg py-2 px-3 text-white font-mono focus:outline-none focus:border-accent-orange"
                                    />
                                </div>
                            </div>
                            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm text-blue-400">
                                <span className="material-symbols-outlined text-base align-middle mr-1">info</span>
                                Las recetas que usan este insumo se recalcularán automáticamente.
                            </div>
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    onClick={() => setShowCostModal(false)}
                                    className="px-4 py-2 text-text-muted hover:text-white transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleCostUpdate}
                                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                                >
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
