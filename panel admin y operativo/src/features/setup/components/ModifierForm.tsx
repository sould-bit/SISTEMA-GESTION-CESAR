import { Cookie, Save, Plus, Trash2, ArrowLeft, Info, Pizza } from 'lucide-react';
import { useModifierForm } from '../hooks/useModifierForm';
import { RecipeBuilder } from './RecipeBuilder';
import { ProductModifier } from '../setup.service';

interface ModifierFormProps {
    modifiers: ProductModifier[];
    ingredients: any[];
    onRefresh: () => Promise<void>;
    onBack: () => void;
}

export const ModifierForm = ({
    modifiers,
    ingredients,
    onRefresh,
    onBack
}: ModifierFormProps) => {

    const {
        form,
        setForm,
        isSaving,
        selectedModifier,
        recipeItems,
        setRecipeItems,
        handleSelectModifier,
        handleSave,
        handleDelete,
        resetForm
    } = useModifierForm(onRefresh);

    const totalCost = recipeItems.reduce((acc, item) => acc + (item.cost * item.quantity), 0);
    const profit = (Number(form.extra_price) || 0) - totalCost;
    const margin = Number(form.extra_price) > 0 ? (profit / Number(form.extra_price)) * 100 : 0;

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header / Navigation */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card-dark/40 p-6 rounded-2xl border border-border-dark backdrop-blur-md">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition-all transform active:scale-95"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div>
                        <h2 className="text-2xl font-black text-white flex items-center gap-2 tracking-tight">
                            <Cookie className="text-purple-400 animate-pulse" />
                            {selectedModifier ? 'Editando Complemento' : 'Nuevo Complemento'}
                        </h2>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-[0.2em]">
                            Modificadores & Extras Personalizados
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {selectedModifier && (
                        <button
                            onClick={resetForm}
                            className="px-4 py-2 text-gray-400 hover:text-white text-sm font-bold transition-colors"
                        >
                            CANCELAR
                        </button>
                    )}
                    <button
                        onClick={handleSave}
                        disabled={!form.name || isSaving}
                        className={`relative group overflow-hidden px-8 py-3 rounded-full font-black text-sm transition-all flex items-center gap-2 transform active:scale-95 shadow-xl ${selectedModifier
                            ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/20'
                            : 'bg-purple-600 hover:bg-purple-500 shadow-purple-500/20'
                            } disabled:opacity-50 disabled:grayscale`}
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                        <Save size={18} className="group-hover:rotate-12 transition-transform" />
                        {isSaving ? 'GUARDANDO...' : (selectedModifier ? 'ACTUALIZAR' : 'CREAR EXTRA')}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Side: Form & Financials */}
                <div className="lg:col-span-4 space-y-6">
                    {/* Basic Info */}
                    <div className="bg-card-dark rounded-2xl border border-border-dark overflow-hidden shadow-2xl">
                        <div className="p-1 bg-gradient-to-r from-purple-500/20 to-blue-500/20" />
                        <div className="p-6 space-y-5">
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] font-black text-purple-400 uppercase tracking-widest block mb-2">
                                        Nombre del Extra
                                    </label>
                                    <input
                                        className="w-full bg-bg-deep border border-border-dark rounded-xl px-4 py-3 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all placeholder:text-gray-700"
                                        value={form.name}
                                        onChange={e => setForm({ ...form, name: e.target.value })}
                                        placeholder="Ej. Doble Queso, Salsa especial..."
                                    />
                                </div>

                                <div>
                                    <label className="text-[10px] font-black text-purple-400 uppercase tracking-widest block mb-2">
                                        Precio de Venta
                                    </label>
                                    <div className="relative group">
                                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-purple-400 transition-colors font-bold">$</span>
                                        <input
                                            type="number"
                                            className="w-full bg-bg-deep pl-8 pr-4 py-3 border border-border-dark rounded-xl text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all font-bold text-lg"
                                            value={form.extra_price}
                                            onChange={e => setForm({ ...form, extra_price: e.target.value })}
                                            placeholder="0"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="text-[10px] font-black text-purple-400 uppercase tracking-widest block mb-2">
                                        Descripción (Opcional)
                                    </label>
                                    <textarea
                                        rows={2}
                                        className="w-full bg-bg-deep border border-border-dark rounded-xl px-4 py-3 text-white focus:border-purple-500 outline-none resize-none transition-all placeholder:text-gray-700 text-sm"
                                        value={form.description}
                                        onChange={e => setForm({ ...form, description: e.target.value })}
                                        placeholder="Breve nota sobre este extra..."
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Financial Summary Card */}
                    <div className="bg-gradient-to-br from-indigo-950/40 to-black rounded-2xl border border-white/5 p-6 space-y-4 shadow-xl">
                        <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-2">
                            <Info size={14} /> Análisis de Rentabilidad
                        </h4>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                                <span className="text-[9px] text-gray-500 uppercase block mb-1">Costo Total</span>
                                <span className="text-xl font-bold text-gray-200">${totalCost.toFixed(2)}</span>
                            </div>
                            <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                                <span className="text-[9px] text-gray-500 uppercase block mb-1">Ganancia</span>
                                <span className={`text-xl font-bold ${profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    ${profit.toFixed(2)}
                                </span>
                            </div>
                            <div className="col-span-2 bg-emerald-500/10 p-4 rounded-xl border border-emerald-500/20 flex justify-between items-center">
                                <div>
                                    <span className="text-[9px] text-emerald-500/60 uppercase block font-black">Margen Prod.</span>
                                    <span className="text-2xl font-black text-emerald-400">{margin.toFixed(1)}%</span>
                                </div>
                                <div className="h-10 w-10 rounded-full border-2 border-emerald-500/20 flex items-center justify-center">
                                    <div className="h-6 w-6 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin" style={{ animationDuration: '3s' }} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main: Recipe Component */}
                <div className="lg:col-span-8 flex flex-col gap-6">
                    <div className="bg-card-dark rounded-2xl border border-border-dark overflow-hidden flex flex-col flex-1 shadow-2xl min-h-[600px]">
                        <div className="p-6 border-b border-border-dark bg-white/5 flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-bold text-white tracking-tight">Arquitectura del Complemento</h3>
                                <p className="text-gray-500 text-xs">Añade los insumos que componen este extra para calcular su rentabilidad exacta.</p>
                            </div>
                            <div className="bg-purple-500/10 px-3 py-1 rounded-full border border-purple-500/20 text-purple-400 text-[10px] font-black uppercase tracking-tighter">
                                Receta Técnica
                            </div>
                        </div>
                        <div className="flex-1 overflow-hidden flex">
                            <RecipeBuilder
                                recipeItems={recipeItems}
                                setRecipeItems={setRecipeItems}
                                ingredients={ingredients}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* List of Existing Modifiers Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-3">
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-800 to-transparent" />
                    <h3 className="text-xs font-black text-gray-600 uppercase tracking-[0.3em] whitespace-nowrap">
                        Librería de Modificadores
                    </h3>
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-800 to-transparent" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {/* Add New Trigger Card */}
                    {!selectedModifier && (
                        <div className="bg-purple-500/5 border border-dashed border-purple-500/30 rounded-2xl p-6 flex flex-col items-center justify-center gap-3 opacity-60 hover:opacity-100 transition-all group cursor-default">
                            <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                                <Plus size={24} />
                            </div>
                            <span className="text-[10px] font-black text-purple-400/50 uppercase">Nuevo Registro</span>
                        </div>
                    )}

                    {modifiers.map(mod => (
                        <div
                            key={mod.id}
                            onClick={() => handleSelectModifier(mod)}
                            className={`group relative bg-card-dark hover:bg-white/5 border ${selectedModifier?.id === mod.id
                                ? 'border-purple-500 ring-2 ring-purple-500/20'
                                : 'border-border-dark'
                                } p-4 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden shadow-lg`}
                        >
                            <div className={`absolute top-0 right-0 p-12 blur-3xl rounded-full opacity-10 transition-colors ${selectedModifier?.id === mod.id ? 'bg-purple-500' : 'bg-gray-500'}`} />

                            <div className="relative z-10 flex flex-col gap-3">
                                <div className="flex justify-between items-start">
                                    <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-gray-500 group-hover:text-purple-400 transition-colors">
                                        <Pizza size={16} />
                                    </div>
                                    <span className="font-black text-purple-400 text-sm tracking-tight">${mod.extra_price}</span>
                                </div>

                                <div>
                                    <h4 className="font-bold text-gray-200 text-sm truncate" title={mod.name}>{mod.name}</h4>
                                    <p className="text-[10px] text-gray-500 line-clamp-1">{mod.description || 'Sin descripción'}</p>
                                </div>

                                <div className="pt-2 border-t border-white/5 flex justify-between items-center text-[9px] font-black text-gray-600 uppercase">
                                    <span>id: {mod.id}</span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDelete(mod.id);
                                        }}
                                        className="text-gray-700 hover:text-red-500 transition-colors"
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
