import React, { useState, useMemo } from 'react';
import { kitchenService, Recipe } from '../kitchen.service';
import { useQuery } from '@tanstack/react-query';

import { ImprovedRecipeBuilder } from './ImprovedRecipeBuilder';

// 🎨 Definición de colores y estilos inline
const THEME = {
    bg: "bg-[#0F172A]", // Slate 900
    surface: "bg-[#1E293B]", // Slate 800
    surfaceHighlight: "bg-[#334155]", // Slate 700
    border: "border-[#334155]", // Slate 700 border
    text: "text-slate-50",
    textMuted: "text-[#94A3B8]", // Slate 400
    primary: "bg-[#FF6B00]",
    primaryHover: "hover:bg-[#e56000]",
    primaryText: "text-[#FF6B00]",
    primaryBorder: "border-[#FF6B00]",
    inputBg: "bg-[#0F172A]",
};

// --- SUBSISTEMA DE ICONOS ---
const Icon = ({ name, className = "" }: { name: string; className?: string }) => (
    <span className={`material-symbols-outlined ${className}`}>{name}</span>
);

export default function RecipeManagerV2() {
    // --- ESTADOS ---
    const [selectedRecipeId, setSelectedRecipeId] = useState<number | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");


    // --- DATA FETCHING ---
    const { data: recipes = [], isLoading } = useQuery<Recipe[]>({
        queryKey: ['recipes'],
        queryFn: () => kitchenService.getRecipes()
    });

    // --- COMPUTED ---
    const filteredRecipes = useMemo(() => {
        return recipes.filter(r =>
            r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (r.product_name && r.product_name.toLowerCase().includes(searchQuery.toLowerCase()))
        );
    }, [recipes, searchQuery]);

    const activeRecipe = useMemo(() => {
        if (!selectedRecipeId) return null;
        return recipes.find(r => r.id === selectedRecipeId);
    }, [selectedRecipeId, recipes]);

    // --- HANDLERS ---
    const handleCreateNew = () => {
        setSelectedRecipeId(null);
        setIsEditing(true);
    };

    if (isLoading) {
        return (
            <div className={`flex h-[calc(100vh-4rem)] ${THEME.bg} items-center justify-center`}>
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#334155] border-t-[#FF6B00]"></div>
                    <span className="text-[#94A3B8] font-mono text-sm animate-pulse">Cargando Sistema...</span>
                </div>
            </div>
        );
    }

    // Determinar si el panel de edición debe mostrarse
    const showEditor = selectedRecipeId !== null || isEditing;

    return (
        <div className={`flex h-[calc(100vh-4rem)] ${THEME.bg} text-slate-50 font-sans overflow-hidden font-['Plus_Jakarta_Sans']`}>

            {/* 1️⃣ PANEL IZQUIERDO: CATÁLOGO */}
            <div className={`
                flex flex-col border-r border-[#334155] transition-all duration-500 ease-in-out
                ${showEditor ? 'w-[450px] min-w-[450px]' : 'w-full'}
            `}>

                {/* Header */}
                <div className="p-6 border-b border-[#334155] flex flex-col gap-4">
                    <div className="flex justify-between items-center">
                        <h2 className="text-2xl font-bold tracking-tight text-white flex gap-2 items-center">
                            <Icon name="restaurant_menu" className="text-[#FF6B00]" />
                            Catálogo de Productos
                        </h2>
                        <span className="text-xs font-mono text-[#94A3B8] bg-[#1E293B] px-2 py-1 rounded border border-[#334155]">
                            V2.0 EXPERIMENTAL
                        </span>
                    </div>

                    {/* Toolbar */}
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
                            <input
                                type="text"
                                placeholder="Buscar productos, código..."
                                className={`w-full ${THEME.inputBg} ${THEME.border} border rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[#FF6B00] focus:border-transparent placeholder-slate-500`}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <button className={`flex items-center justify-center w-10 h-10 rounded-lg border ${THEME.border} bg-[#0F172A] text-[#94A3B8] hover:border-[#FF6B00] hover:text-[#FF6B00] transition-colors`}>
                            <Icon name="filter_list" />
                        </button>
                        <button
                            onClick={handleCreateNew}
                            className={`flex items-center gap-2 px-4 rounded-lg ${THEME.primary} hover:bg-[#e56000] text-white font-bold text-sm transition-all shadow-lg shadow-orange-500/20`}
                        >
                            <Icon name="add" />
                            <span>Add Product</span>
                        </button>
                    </div>
                </div>

                {/* Lista */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    <table className="w-full text-left border-collapse">
                        <thead className={`bg-[#1E293B] sticky top-0 z-10 shadow-sm`}>
                            <tr>
                                <th className="px-5 py-3 text-[#94A3B8] text-xs font-bold uppercase tracking-wider w-16">Image</th>
                                <th className="px-5 py-3 text-[#94A3B8] text-xs font-bold uppercase tracking-wider">Product</th>
                                <th className={`px-5 py-3 text-[#94A3B8] text-xs font-bold uppercase tracking-wider ${showEditor ? 'hidden lg:table-cell' : ''}`}>Category</th>
                                <th className="px-5 py-3 text-[#94A3B8] text-xs font-bold uppercase tracking-wider">Cost</th>
                                <th className={`px-5 py-3 text-[#94A3B8] text-xs font-bold uppercase tracking-wider ${showEditor ? 'hidden' : ''}`}>Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#334155]/50">
                            {filteredRecipes.map((recipe: Recipe) => (
                                <tr
                                    key={recipe.id}
                                    onClick={() => { setSelectedRecipeId(recipe.id); setIsEditing(false); }}
                                    className={`
                                        cursor-pointer transition-all border-l-4 
                                        ${selectedRecipeId === recipe.id
                                            ? 'bg-[#FF6B00]/10 border-l-[#FF6B00]'
                                            : 'hover:bg-[#1E293B]/80 border-l-transparent'}
                                    `}
                                >
                                    <td className="px-5 py-4">
                                        <div
                                            className={`rounded-lg w-10 h-10 shadow-sm border border-[#334155] bg-cover bg-center bg-[#0F172A]`}
                                            style={{
                                                backgroundImage: recipe.product_image_url
                                                    ? `url(${recipe.product_image_url})`
                                                    : 'none'
                                            }}
                                        >
                                            {!recipe.product_image_url && (
                                                <div className="w-full h-full flex items-center justify-center text-[#94A3B8]">
                                                    <Icon name="lunch_dining" className="text-lg" />
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-5 py-4">
                                        <div className="font-semibold text-white truncate max-w-[200px]">{recipe.name}</div>
                                        <div className="text-xs text-[#94A3B8] font-mono mt-0.5 truncate max-w-[150px]">ID: {recipe.id}</div>
                                    </td>
                                    <td className={`px-5 py-4 ${showEditor ? 'hidden lg:table-cell' : ''}`}>
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-[#0F172A] text-slate-300 border border-[#334155] font-mono">
                                            {recipe.category_name || 'Uncategorized'}
                                        </span>
                                    </td>
                                    <td className="px-5 py-4 text-white font-mono font-bold">
                                        ${Number(recipe.total_cost || 0).toFixed(2)}
                                    </td>
                                    <td className={`px-5 py-4 ${showEditor ? 'hidden' : ''}`}>
                                        {recipe.is_active ? (
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wide">
                                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                                Active
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20 uppercase tracking-wide">
                                                Inactive
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="p-4 border-t border-[#334155] bg-[#1E293B] flex justify-between items-center text-xs text-[#94A3B8]">
                    <span className="font-mono">Showing <strong className="text-white">{filteredRecipes.length}</strong> items</span>
                </div>
            </div>

            {/* 2️⃣ PANEL DERECHO: EDITOR (SLIDE-IN) */}
            <div className={`
                flex flex-col ${THEME.surface} border-l border-[#334155] relative shadow-2xl transition-all duration-500 ease-in-out transform
                ${showEditor ? 'flex-1 translate-x-0 opacity-100' : 'w-0 opacity-0 translate-x-full overflow-hidden'}
            `}>

                {showEditor && (
                    <ImprovedRecipeBuilder
                        existingRecipe={activeRecipe}
                        onCancel={() => { setSelectedRecipeId(null); setIsEditing(false); }}
                        onSave={() => {
                            // TODO: Invalidar queries cuando se termine la mutación
                            setSelectedRecipeId(null);
                            setIsEditing(false);
                        }}
                    />
                )}
            </div>

        </div>
    );
}
