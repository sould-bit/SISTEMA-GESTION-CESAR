import { Search, Plus, Trash2, GripVertical } from 'lucide-react';
import { DragEvent, useState } from 'react';
import { Product, RecipeItemRow } from '../setup.service';

interface RecipeBuilderProps {
    recipeItems: RecipeItemRow[];
    setRecipeItems: (items: RecipeItemRow[]) => void;
    ingredients: Product[];
}

export const RecipeBuilder = ({ recipeItems, setRecipeItems, ingredients }: RecipeBuilderProps) => {
    const [pantrySearch, setPantrySearch] = useState('');

    const handleDragStart = (e: DragEvent<HTMLDivElement>, ingredient: Product) => {
        e.dataTransfer.setData('ingredient', JSON.stringify(ingredient));
        e.dataTransfer.effectAllowed = 'copy';
    };

    const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const data = e.dataTransfer.getData('ingredient');
        if (data) {
            const ing = JSON.parse(data) as Product;
            addRecipeItem(ing);
        }
    };

    const addRecipeItem = (ing: Product) => {
        if (recipeItems.some(i => i.ingredientId === ing.id)) return;
        setRecipeItems([...recipeItems, {
            ingredientId: ing.id,
            name: ing.name,
            cost: ing.price,
            quantity: 1,
            unit: 'UNIDAD' // Default, should improve
        }]);
    };

    const removeRecipeItem = (id: number) => {
        setRecipeItems(recipeItems.filter(i => i.ingredientId !== id));
    };

    const updateItemQuantity = (id: number, qty: number) => {
        setRecipeItems(recipeItems.map(i => i.ingredientId === id ? { ...i, quantity: qty } : i));
    };

    const filteredIngredients = ingredients.filter(i =>
        i.name.toLowerCase().includes(pantrySearch.toLowerCase())
    );

    return (
        <div className="flex-1 flex overflow-hidden border-t border-border-dark mt-6 bg-bg-deep rounded-xl">
            {/* PANTRY (Left) */}
            <div className="w-72 bg-bg-deep border-r border-border-dark flex flex-col">
                <div className="p-3 border-b border-border-dark bg-card-dark/50">
                    <label className="text-xs font-bold text-gray-400 uppercase flex items-center gap-2">
                        <Search size={14} /> La Despensa
                    </label>
                    <input
                        className="w-full mt-2 text-sm bg-bg-deep border border-border-dark rounded-lg px-3 py-2 focus:border-accent-orange text-white outline-none transition-all shadow-sm placeholder-gray-600"
                        placeholder="Buscar insumo..."
                        value={pantrySearch}
                        onChange={e => setPantrySearch(e.target.value)}
                    />
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2">
                    {filteredIngredients.map(ing => (
                        <div
                            key={ing.id}
                            draggable
                            onDragStart={(e) => handleDragStart(e, ing)}
                            className="p-3 bg-card-dark border border-border-dark rounded-lg flex justify-between items-center cursor-move hover:border-accent-orange/50 hover:bg-accent-orange/5 transition-all group active:scale-95"
                        >
                            <span className="text-sm font-medium text-gray-200">{ing.name}</span>
                            <span className="text-xs text-emerald-400 font-mono bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                                ${ing.price}
                            </span>
                        </div>
                    ))}
                    {ingredients.length === 0 && (
                        <div className="p-4 text-center text-xs text-gray-500 italic">
                            No hay insumos registrados.
                        </div>
                    )}
                </div>
            </div>

            {/* RECIPE CANVAS (Right) */}
            <div
                className="flex-1 bg-black/20 p-4 overflow-y-auto relative"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
            >
                {recipeItems.length === 0 ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-gray-700/50 m-4 rounded-xl pointer-events-none">
                        <Plus size={32} className="mb-2 opacity-50" />
                        <p className="text-sm font-medium">Arrastra insumos aquí para crear la receta</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {recipeItems.map((item, idx) => (
                            <div key={item.ingredientId} className="flex items-center gap-3 bg-card-dark p-3 rounded-lg border border-border-dark animate-in slide-in-from-left-2 shadow-sm group hover:border-accent-orange/30">
                                <GripVertical size={16} className="text-gray-600 cursor-grab" />
                                <div className="flex-1">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-gray-200 text-sm">{item.name}</span>
                                        <span className="text-xs text-gray-500">Costo: ${(item.cost * item.quantity).toFixed(2)}</span>
                                    </div>
                                    <div className="flex gap-4 mt-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] text-gray-400 uppercase">Cant.</span>
                                            <input
                                                type="number"
                                                className="w-20 bg-bg-deep border border-border-dark rounded px-2 py-1 text-xs text-white focus:border-accent-orange outline-none"
                                                value={item.quantity}
                                                onChange={e => updateItemQuantity(item.ingredientId, Number(e.target.value))}
                                            />
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] text-gray-400 uppercase">Unidad</span>
                                            <span className="text-xs text-gray-300 font-mono bg-gray-800 px-2 py-1 rounded">{item.unit}</span>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeRecipeItem(item.ingredientId)}
                                    className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}

                        <div className="mt-4 pt-4 border-t border-border-dark flex justify-end">
                            <div className="text-right">
                                <span className="text-xs text-gray-400 uppercase block mb-1">Costo Total Receta</span>
                                <span className="text-xl font-bold text-emerald-400">
                                    ${recipeItems.reduce((acc, item) => acc + (item.cost * item.quantity), 0).toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
