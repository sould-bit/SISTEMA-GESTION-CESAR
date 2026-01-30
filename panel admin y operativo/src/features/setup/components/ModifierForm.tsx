import { Cookie, Save, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { RecipeBuilder } from './RecipeBuilder';

interface ModifierFormProps {
    modifiers: any[];
    handleSaveModifier: (data: any) => Promise<void>;
    isSaving: boolean;
    recipeItems: any[];
    setRecipeItems: (items: any[]) => void;
    ingredients: any[];
}

export const ModifierForm = ({
    modifiers,
    handleSaveModifier,
    isSaving,
    recipeItems,
    setRecipeItems,
    ingredients
}: ModifierFormProps) => {

    const [form, setForm] = useState({
        name: '',
        description: '',
        extra_price: '0'
    });

    // Minimal local state for selection usage
    const [selectedModifier, setSelectedModifier] = useState<any>(null);

    const onSelect = (mod: any) => {
        setSelectedModifier(mod);
        setForm({
            name: mod.name,
            description: mod.description || '',
            extra_price: mod.extra_price?.toString() || '0'
        });
        // We would need to load recipe items here if we want to edit them
        // For now, assuming new creation flow simplicity
    };

    const handleSave = async () => {
        await handleSaveModifier({
            ...form,
            id: selectedModifier?.id,
            recipe_items: recipeItems
        });
        // Reset
        setForm({ name: '', description: '', extra_price: '0' });
        setSelectedModifier(null);
        setRecipeItems([]);
    };

    return (
        <div className="space-y-6 animate-in slide-in-from-right-4">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Cookie className="text-purple-400" /> Modificadores & Extras
                </h2>
                <button
                    onClick={handleSave}
                    disabled={!form.name || isSaving}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center gap-2"
                >
                    <Save size={18} /> {isSaving ? 'Guardando...' : 'Guardar Extra'}
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Form */}
                <div className="bg-card-dark p-6 rounded-xl border border-border-dark space-y-4">
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Nombre</label>
                        <input
                            className="w-full bg-bg-deep border border-border-dark rounded px-3 py-2 text-white focus:border-purple-500 outline-none"
                            value={form.name}
                            onChange={e => setForm({ ...form, name: e.target.value })}
                            placeholder="Ej. Extra Queso"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Precio Extra</label>
                        <div className="relative">
                            <span className="absolute left-3 top-2 text-gray-500">$</span>
                            <input
                                type="number"
                                className="w-full bg-bg-deep pl-7 px-3 py-2 border border-border-dark rounded text-white focus:border-purple-500 outline-none"
                                value={form.extra_price}
                                onChange={e => setForm({ ...form, extra_price: e.target.value })}
                                placeholder="0"
                            />
                        </div>
                    </div>
                </div>

                {/* List of Existing Modifiers */}
                <div className="bg-card-dark p-4 rounded-xl border border-border-dark h-64 overflow-y-auto">
                    <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">Existentes</h3>
                    <div className="space-y-2">
                        {modifiers.map(mod => (
                            <div
                                key={mod.id}
                                onClick={() => onSelect(mod)}
                                className={`p-2 rounded border cursor-pointer hover:bg-white/5 transition-colors flex justify-between ${selectedModifier?.id === mod.id ? 'border-purple-500 bg-purple-500/10' : 'border-border-dark'}`}
                            >
                                <span className="text-sm text-gray-200">{mod.name}</span>
                                <span className="text-xs text-purple-400 font-bold">+${mod.extra_price}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Recipe Builder for the Extra (Cost Calculation) */}
            <div className="pt-4 border-t border-border-dark">
                <h3 className="text-sm font-bold text-gray-400 mb-2">Receta del Extra (Costo)</h3>
                <RecipeBuilder
                    recipeItems={recipeItems}
                    setRecipeItems={setRecipeItems}
                    ingredients={ingredients}
                />
            </div>
        </div>
    );
};
