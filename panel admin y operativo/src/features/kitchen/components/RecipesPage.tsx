/**
 * RecipesPage - Gestión de Recetas Vivas & Inteligencia
 */

import { useState, useEffect } from 'react';
import { ImprovedRecipeBuilder } from './ImprovedRecipeBuilder';
import { RecipeIntelligenceCard } from './RecipeIntelligenceCard';
import { kitchenService, Recipe } from '../kitchen.service';

export const RecipesPage = () => {
    const [view, setView] = useState<'list' | 'create' | 'detail' | 'edit'>('list');
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
    const [loading, setLoading] = useState(false);
    const [recipeTypeFilter, setRecipeTypeFilter] = useState<'REAL' | 'AUTO' | 'ALL'>('REAL');

    useEffect(() => {
        loadRecipes();
    }, []);

    const loadRecipes = async () => {
        setLoading(true);
        try {
            const data = await kitchenService.getRecipes();
            setRecipes(data);
        } catch (error) {
            console.error('Error loading recipes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = (recipe: any) => {
        console.log('Recipe saved:', recipe);
        setView('list');
        loadRecipes();
    };

    const handleCancel = () => {
        if (view === 'create') setView('list');
        if (view === 'detail') setView('list');
        if (view === 'edit') setView('detail');
    };

    const selectRecipe = async (recipe: Recipe) => {
        // Fetch full detail with items from backend
        setLoading(true);
        try {
            const fullRecipe = await kitchenService.getRecipe(String(recipe.id));
            setSelectedRecipe(fullRecipe);
            setView('detail');
        } catch (error) {
            console.error('Error loading recipe details:', error);
            // Fallback to list recipe if detail fails
            setSelectedRecipe(recipe);
            setView('detail');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(value);
    };

    if (view === 'create') {
        return (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="flex items-center gap-4 mb-4">
                    <button onClick={handleCancel} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <span className="material-symbols-outlined text-white">arrow_back</span>
                    </button>
                    <h2 className="text-xl font-bold text-white">Nueva Receta</h2>
                </div>
                <ImprovedRecipeBuilder onSave={handleSave} onCancel={handleCancel} />
            </div>
        );
    }

    // Edit View - Reuse ImprovedRecipeBuilder with existing recipe
    if (view === 'edit' && selectedRecipe) {
        return (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="flex items-center gap-4 mb-4">
                    <button onClick={handleCancel} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <span className="material-symbols-outlined text-white">arrow_back</span>
                    </button>
                    <h2 className="text-xl font-bold text-white">Editar Receta: {selectedRecipe.name}</h2>
                </div>
                <ImprovedRecipeBuilder
                    existingRecipe={selectedRecipe}
                    onSave={(recipe) => {
                        handleSave(recipe);
                        setSelectedRecipe(recipe);
                    }}
                    onCancel={handleCancel}
                />
            </div>
        );
    }

    if (view === 'detail' && selectedRecipe) {
        return (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                        <button onClick={handleCancel} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                            <span className="material-symbols-outlined text-white">arrow_back</span>
                        </button>
                        <div>
                            <h2 className="text-xl font-bold text-white">{selectedRecipe.name}</h2>
                            <div className="flex gap-2 text-sm text-text-muted">
                                <span>{selectedRecipe.product_name || `Producto #${selectedRecipe.product_id}`}</span>
                                <span>•</span>
                                <span className="font-mono">{formatCurrency(Number(selectedRecipe.total_cost))}</span>
                            </div>
                        </div>
                    </div>
                    {/* Edit Button - Premium Design */}
                    <button
                        onClick={() => setView('edit')}
                        className="group relative flex items-center gap-2.5 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:from-violet-500 hover:to-purple-500 transition-all duration-300 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-[1.02] active:scale-[0.98]"
                    >
                        {/* Glow effect */}
                        <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-violet-400 to-purple-400 opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300"></span>

                        <span className="relative material-symbols-outlined text-[20px] group-hover:rotate-12 transition-transform duration-300">edit</span>
                        <span className="relative font-medium">Editar Receta</span>

                        {/* Arrow indicator on hover */}
                        <span className="relative material-symbols-outlined text-[16px] opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">arrow_forward</span>
                    </button>
                </div>

                {/* Intelligence Section */}
                <RecipeIntelligenceCard recipe={selectedRecipe} />

                {/* Ingredients List (Read Only) */}
                <div className="bg-card-dark border border-border-dark rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <span className="material-symbols-outlined">format_list_bulleted</span>
                        Ingredientes Actuales
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-gray-300">
                            <thead className="text-xs uppercase bg-white/5 text-gray-400">
                                <tr>
                                    <th className="px-4 py-3 rounded-l-lg">Ingrediente</th>
                                    <th className="px-4 py-3 text-center">Cant. Bruta</th>
                                    <th className="px-4 py-3 text-center">Costo Calc.</th>
                                    <th className="px-4 py-3 rounded-r-lg"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark">
                                {(selectedRecipe.items || []).map((item, idx) => (
                                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                                        <td className="px-4 py-3 font-medium text-white">
                                            {item.ingredient_name || `Ingrediente ${item.ingredient_id.substring(0, 8)}...`}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            {item.gross_quantity} {item.measure_unit}
                                        </td>
                                        <td className="px-4 py-3 text-center font-mono text-emerald-400">
                                            {formatCurrency(item.calculated_cost || 0)}
                                        </td>
                                        <td className="px-4 py-3"></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        );
    }

    // List View
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Recetas Vivas</h2>
                    <p className="text-text-muted">Gestiona tus recetas y supervísalas en tiempo real</p>
                </div>
                <button
                    onClick={() => setView('create')}
                    className="flex items-center gap-2 px-4 py-2 bg-accent-orange text-white rounded-lg hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20"
                >
                    <span className="material-symbols-outlined">add</span>
                    Nueva Receta
                </button>
            </div>

            {loading ? (
                <div className="text-center py-12 text-gray-500">Cargando recetas...</div>
            ) : (
                <>
                    {/* Filter Tabs */}
                    <div className="flex gap-2 border-b border-border-dark pb-4">
                        <button
                            onClick={() => setRecipeTypeFilter('REAL')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${recipeTypeFilter === 'REAL'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                                : 'text-gray-400 hover:bg-white/5'
                                }`}
                        >
                            🍳 Recetas Reales
                            <span className="ml-2 text-xs opacity-70">
                                ({recipes.filter(r => r.recipe_type === 'REAL').length})
                            </span>
                        </button>
                        <button
                            onClick={() => setRecipeTypeFilter('AUTO')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${recipeTypeFilter === 'AUTO'
                                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                                : 'text-gray-400 hover:bg-white/5'
                                }`}
                        >
                            🤖 Recetas Auto
                            <span className="ml-2 text-xs opacity-70">
                                ({recipes.filter(r => r.recipe_type === 'AUTO').length})
                            </span>
                        </button>
                        <button
                            onClick={() => setRecipeTypeFilter('ALL')}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${recipeTypeFilter === 'ALL'
                                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                                : 'text-gray-400 hover:bg-white/5'
                                }`}
                        >
                            📋 Todas
                            <span className="ml-2 text-xs opacity-70">
                                ({recipes.length})
                            </span>
                        </button>
                    </div>

                    {/* Grouped by Category */}
                    {(() => {
                        const filteredRecipes = recipes.filter(r => recipeTypeFilter === 'ALL' || r.recipe_type === recipeTypeFilter);

                        if (filteredRecipes.length === 0) {
                            return (
                                <div className="text-center py-12 bg-card-dark border border-border-dark rounded-2xl">
                                    <span className="material-symbols-outlined text-4xl text-gray-600 mb-2">menu_book</span>
                                    <p className="text-gray-400">No hay recetas en esta categoría</p>
                                </div>
                            );
                        }

                        // Group recipes by category
                        const grouped = filteredRecipes.reduce((acc, recipe) => {
                            const categoryName = recipe.category_name || 'Sin Categoría';
                            if (!acc[categoryName]) {
                                acc[categoryName] = [];
                            }
                            acc[categoryName].push(recipe);
                            return acc;
                        }, {} as Record<string, Recipe[]>);

                        // Sort categories alphabetically, but "Sin Categoría" goes last
                        const sortedCategories = Object.keys(grouped).sort((a, b) => {
                            if (a === 'Sin Categoría') return 1;
                            if (b === 'Sin Categoría') return -1;
                            return a.localeCompare(b);
                        });

                        return (
                            <div className="space-y-6">
                                {sortedCategories.map(categoryName => (
                                    <div key={categoryName} className="bg-card-dark border border-border-dark rounded-2xl overflow-hidden">
                                        {/* Category Header */}
                                        <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-purple-500/10 to-transparent border-b border-border-dark">
                                            <div className="flex items-center gap-3">
                                                <span className="material-symbols-outlined text-purple-400">category</span>
                                                <h3 className="text-lg font-semibold text-white">{categoryName}</h3>
                                                <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full">
                                                    {grouped[categoryName].length} recetas
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-400">
                                                Costo promedio: {formatCurrency(
                                                    grouped[categoryName].reduce((sum, r) => sum + Number(r.total_cost || 0), 0) / grouped[categoryName].length
                                                )}
                                            </div>
                                        </div>

                                        {/* Recipes Grid */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                                            {grouped[categoryName].map((recipe) => (
                                                <div
                                                    key={recipe.id}
                                                    onClick={() => selectRecipe(recipe)}
                                                    className="bg-bg-deep border border-border-dark rounded-xl p-4 cursor-pointer hover:border-accent-purple/50 transition-all hover:shadow-lg hover:shadow-purple-500/10 group"
                                                >
                                                    <div className="flex justify-between items-start mb-2">
                                                        <h3 className="font-bold text-white group-hover:text-accent-purple transition-colors">{recipe.name}</h3>
                                                        {recipe.is_active ?
                                                            <span className="w-2 h-2 rounded-full bg-emerald-400"></span> :
                                                            <span className="w-2 h-2 rounded-full bg-red-400"></span>
                                                        }
                                                    </div>
                                                    <p className="text-sm text-text-muted mb-3 line-clamp-1">
                                                        {recipe.product_name || 'Sin producto vinculado'}
                                                    </p>
                                                    <div className="flex items-center justify-between text-sm">
                                                        <span className="text-gray-500">{recipe.items_count ?? recipe.items?.length ?? 0} ingredientes</span>
                                                        <span className="font-mono text-emerald-400 font-medium">
                                                            {formatCurrency(recipe.total_cost)}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        );
                    })()}
                </>
            )}
        </div>
    );
};

export default RecipesPage;

