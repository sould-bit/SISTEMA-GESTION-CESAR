/**
 * RecipesPage - Gestión de Recetas Vivas & Inteligencia
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ImprovedRecipeBuilder } from './ImprovedRecipeBuilder';
import { RecipeIntelligenceCard } from './RecipeIntelligenceCard';
import { kitchenService, Recipe } from '../kitchen.service';

export const RecipesPage = () => {
    const navigate = useNavigate();
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

    const formatQuantity = (value: number | string) => {
        return Number(value).toString();
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
                    {/* Edit Button - Premium Design (Zapote Theme) */}
                    <button
                        onClick={() => setView('edit')}
                        className="group relative flex items-center gap-2.5 px-5 py-2.5 bg-card-dark border border-orange-500/30 text-orange-400 rounded-xl hover:bg-orange-500/10 hover:border-orange-500/60 transition-all duration-300 shadow-lg shadow-orange-500/5 hover:shadow-orange-500/20"
                    >
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
                                        <td className="px-4 py-3 text-center font-mono text-gray-300">
                                            {formatQuantity(item.gross_quantity)} {item.measure_unit}
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
                <div className="flex gap-3">
                    <button
                        onClick={() => navigate('/kitchen/recipes-v2')}
                        className="flex items-center gap-2 px-4 py-2 border border-purple-500/50 text-purple-300 rounded-lg hover:bg-purple-500/10 transition-colors"
                    >
                        <span className="material-symbols-outlined text-sm">science</span>
                        Probar Version 2.0
                    </button>
                    <button
                        onClick={() => setView('create')}
                        className="flex items-center gap-2 px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20"
                    >
                        <span className="material-symbols-outlined">add</span>
                        Nueva Receta
                    </button>
                </div>
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
                                                    className="bg-bg-deep border border-border-dark rounded-xl overflow-hidden cursor-pointer hover:border-accent-purple/50 transition-all hover:shadow-lg hover:shadow-purple-500/10 group"
                                                >
                                                    {/* Image Section */}
                                                    <div className="relative h-32 overflow-hidden bg-gradient-to-br from-purple-900/30 to-pink-900/20">
                                                        {recipe.product_image_url ? (
                                                            <img
                                                                src={recipe.product_image_url.startsWith('http')
                                                                    ? recipe.product_image_url
                                                                    : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${recipe.product_image_url}`
                                                                }
                                                                alt={recipe.name}
                                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                                            />
                                                        ) : (
                                                            <div className="w-full h-full flex items-center justify-center">
                                                                <span className="material-symbols-outlined text-5xl text-purple-500/30">restaurant</span>
                                                            </div>
                                                        )}
                                                        {/* Active Badge */}
                                                        <div className="absolute top-2 right-2">
                                                            {recipe.is_active ? (
                                                                <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-lg shadow-emerald-500/50 block"></span>
                                                            ) : (
                                                                <span className="w-3 h-3 rounded-full bg-red-400 block"></span>
                                                            )}
                                                        </div>
                                                        {/* Cost Badge */}
                                                        <div className="absolute bottom-2 right-2">
                                                            <span className="px-2 py-1 bg-black/60 backdrop-blur-sm rounded-lg text-emerald-400 font-mono text-sm font-medium">
                                                                {formatCurrency(recipe.total_cost)}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    {/* Content Section */}
                                                    <div className="p-4">
                                                        <h3 className="font-bold text-white group-hover:text-accent-purple transition-colors mb-1 truncate">
                                                            {recipe.name}
                                                        </h3>
                                                        <p className="text-sm text-text-muted mb-2 line-clamp-1">
                                                            {recipe.product_name || 'Sin producto vinculado'}
                                                        </p>
                                                        <div className="flex items-center gap-2 text-xs text-gray-500">
                                                            <span className="flex items-center gap-1">
                                                                <span className="material-symbols-outlined text-[14px]">nutrition</span>
                                                                {recipe.items_count ?? recipe.items?.length ?? 0} ingredientes
                                                            </span>
                                                            {recipe.preparation_time > 0 && (
                                                                <span className="flex items-center gap-1">
                                                                    <span className="material-symbols-outlined text-[14px]">schedule</span>
                                                                    {recipe.preparation_time} min
                                                                </span>
                                                            )}
                                                        </div>
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

