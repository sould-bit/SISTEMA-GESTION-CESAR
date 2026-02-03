import { Package, Save, Trash2, ArrowLeft, Search, FlaskConical, Scale, History } from 'lucide-react';
import { useIngredientForm } from '../hooks/useIngredientForm';
import { Product } from '../setup.service';
import { StockAudit } from './StockAudit';

interface IngredientFormProps {
    ingredients: Product[];
    onRefresh: () => Promise<void>;
    onBack: () => void;
}

export const IngredientForm = ({
    ingredients,
    onRefresh,
    onBack
}: IngredientFormProps) => {

    const {
        form,
        setForm,
        isSaving,
        selectedIngredient,
        handleSelectIngredient,
        handleSave,
        handleDelete,
        resetForm
    } = useIngredientForm(onRefresh);

    const [viewMode, setViewMode] = useState<'LIST' | 'AUDIT'>('LIST');

    const activeIngredients = ingredients.filter(i => i.is_active !== false);

    if (viewMode === 'AUDIT') {
        return <StockAudit onBack={() => setViewMode('LIST')} />;
    }

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
                            <Package className="text-emerald-400 animate-pulse" />
                            {selectedIngredient ? 'Actualizar Insumo' : 'Registro de Materia Prima'}
                        </h2>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-[0.2em]">
                            Control de Stock e Insumos Básicos
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setViewMode('AUDIT')}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 hover:text-purple-300 rounded-full font-bold text-xs uppercase tracking-wider border border-purple-500/20 transition-all"
                    >
                        <History size={16} /> Auditoría
                    </button>
                    {selectedIngredient && (
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
                        className={`relative group overflow-hidden px-8 py-3 rounded-full font-black text-sm transition-all flex items-center gap-2 transform active:scale-95 shadow-xl ${selectedIngredient
                            ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/20'
                            : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20'
                            } disabled:opacity-50 disabled:grayscale`}
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                        <Save size={18} className="group-hover:translate-y-[-2px] transition-transform" />
                        {isSaving ? 'GUARDANDO...' : (selectedIngredient ? 'MODIFICAR INSUMO' : 'REGISTRAR INSUMO')}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Side: Basic Config */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-card-dark rounded-2xl border border-border-dark overflow-hidden shadow-2xl">
                        <div className="p-1 bg-gradient-to-r from-emerald-500/20 to-teal-500/20" />
                        <div className="p-6 space-y-5">
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-2">
                                        Nombre del Insumo
                                    </label>
                                    <div className="relative">
                                        <FlaskConical className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-600" size={18} />
                                        <input
                                            className="w-full bg-bg-deep border border-border-dark rounded-xl pl-12 pr-4 py-3 text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all placeholder:text-gray-700 font-medium"
                                            value={form.name}
                                            onChange={e => setForm({ ...form, name: e.target.value })}
                                            placeholder="Ej. Harina de Trigo, Sal, Tomate..."
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-2">
                                            Stock Inicial
                                        </label>
                                        <input
                                            type="number"
                                            className="w-full bg-bg-deep px-4 py-3 border border-border-dark rounded-xl text-white focus:border-emerald-500 outline-none transition-all font-bold"
                                            value={form.stock}
                                            onChange={e => setForm({ ...form, stock: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-2">
                                            Unidad
                                        </label>
                                        <select
                                            className="w-full bg-bg-deep px-4 py-3 border border-border-dark rounded-xl text-white focus:border-emerald-500 outline-none transition-all text-sm font-bold appearance-none cursor-pointer"
                                            value={form.unit}
                                            onChange={e => setForm({ ...form, unit: e.target.value })}
                                        >
                                            <option value="UNIDAD">Unidad (u)</option>
                                            <option value="KG">Kilos (kg)</option>
                                            <option value="GR">Gramos (g)</option>
                                            <option value="L">Litros (L)</option>
                                            <option value="ML">Mililitros (ml)</option>
                                        </select>
                                    </div>
                                </div>

                                <div>
                                    <label className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-2">
                                        Costo por {form.unit}
                                    </label>
                                    <div className="relative group">
                                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-emerald-400 transition-colors font-bold">$</span>
                                        <input
                                            type="number"
                                            className="w-full bg-bg-deep pl-8 pr-4 py-3 border border-border-dark rounded-xl text-white focus:border-emerald-500 outline-none transition-all font-bold text-lg"
                                            value={form.cost}
                                            onChange={e => setForm({ ...form, cost: e.target.value })}
                                            placeholder="0"
                                        />
                                    </div>
                                    <p className="text-[9px] text-gray-500 mt-2 px-2 italic">Este es el costo base que se usará para calcular el costo de tus platos y bebidas.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Inventory Stats Card */}
                    <div className="bg-gradient-to-br from-emerald-950/40 to-black rounded-2xl border border-white/5 p-6 space-y-4 shadow-xl">
                        <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-2">
                            <Scale size={14} /> Control de Inventario
                        </h4>

                        <div className="space-y-4">
                            <div>
                                <label className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-2">
                                    Stock Mínimo (Alerta)
                                </label>
                                <input
                                    type="number"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white focus:border-emerald-500 outline-none transition-all text-sm"
                                    value={form.minStock}
                                    onChange={e => setForm({ ...form, minStock: e.target.value })}
                                />
                            </div>

                            <div className="p-4 bg-black/40 rounded-xl border border-white/5 space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] text-gray-500 uppercase font-black tracking-tight">Valoración Inv.</span>
                                    <span className="text-sm font-bold text-emerald-400">
                                        ${(Number(form.cost) * Number(form.stock)).toLocaleString()}
                                    </span>
                                </div>
                                <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500 rounded-full w-2/3 opacity-50 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main: Catalog / List */}
                <div className="lg:col-span-8 space-y-6">
                    <div className="bg-card-dark rounded-2xl border border-border-dark overflow-hidden flex flex-col h-full shadow-2xl min-h-[500px]">
                        <div className="p-6 border-b border-border-dark bg-white/5 flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-bold text-white tracking-tight">Catálogo de Insumos</h3>
                                <p className="text-gray-500 text-xs">Visualiza y gestiona todos tus insumos registrados ({activeIngredients.length}).</p>
                            </div>
                            <div className="relative group">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-emerald-400 transition-colors" size={14} />
                                <input
                                    className="bg-bg-deep border border-border-dark rounded-full pl-9 pr-4 py-1.5 text-xs text-white focus:border-emerald-500 outline-none w-48 transition-all"
                                    placeholder="Consultar insumo..."
                                />
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {activeIngredients.map(ing => {
                                    // Alert Logic
                                    const minStock = ing.min_stock || 5;
                                    const isLowStock = ing.stock <= minStock;

                                    return (
                                        <div
                                            key={ing.id}
                                            onClick={() => handleSelectIngredient(ing)}
                                            className={`group relative p-4 rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden ${selectedIngredient?.id === ing.id
                                                ? 'bg-emerald-500/10 border-emerald-500 ring-1 ring-emerald-500/20'
                                                : `bg-bg-deep border-border-dark hover:border-emerald-500/30 hover:bg-white/5 shadow-lg ${isLowStock ? 'border-orange-500/50 hover:border-orange-500' : ''}`
                                                }`}
                                        >
                                            <div className="relative z-10 flex flex-col h-full">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isLowStock ? 'bg-orange-500/10 text-orange-500 animate-pulse' : 'bg-emerald-500/10 text-emerald-400'}`}>
                                                        <FlaskConical size={16} />
                                                    </div>
                                                    <span className="text-xs font-black text-gray-400 group-hover:text-emerald-400 transition-colors tracking-tighter">
                                                        ID: {ing.id}
                                                    </span>
                                                </div>

                                                <h4 className="font-bold text-gray-200 text-sm mb-1 truncate" title={ing.name}>
                                                    {ing.name}
                                                </h4>

                                                <div className="mt-auto pt-3 flex items-center justify-between border-t border-white/5">
                                                    <div>
                                                        <span className="text-[9px] text-gray-500 uppercase block leading-none mb-1">Stock Actual</span>
                                                        <span className={`text-xs font-black ${isLowStock ? 'text-orange-400' : 'text-emerald-400'}`}>
                                                            {ing.stock} {(ing as any).unit || 'un'}
                                                        </span>
                                                    </div>
                                                    {isLowStock && (
                                                        <div className="text-[9px] bg-orange-500/10 text-orange-400 px-1.5 py-0.5 rounded border border-orange-500/20 font-bold uppercase tracking-wider">
                                                            Bajo Stock (Min: {minStock})
                                                        </div>
                                                    )}
                                                    {!isLowStock && (
                                                        <div className="text-right">
                                                            <span className="text-[9px] text-gray-500 uppercase block leading-none mb-1">Costo Unit.</span>
                                                            <span className="text-xs font-black text-gray-200">
                                                                ${Number(ing.price).toLocaleString()}
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Quick Actions Hover Overlay */}
                                                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-300">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDelete(ing.id);
                                                        }}
                                                        className="p-1.5 bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white rounded-lg transition-all"
                                                    >
                                                        <Trash2 size={12} />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}

                                {/* Add New Placeholder Card */}
                                {!selectedIngredient && (
                                    <div className="border-2 border-dashed border-gray-800 rounded-xl p-4 flex flex-col items-center justify-center gap-2 opacity-50 hover:opacity-100 hover:border-emerald-500/50 transition-all group cursor-default">
                                        <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-gray-500 group-hover:scale-110 group-hover:text-emerald-400 transition-all">
                                            <History size={18} />
                                        </div>
                                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">En espera...</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
