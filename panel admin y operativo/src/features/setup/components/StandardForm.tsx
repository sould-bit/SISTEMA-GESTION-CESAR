import { Package, UtensilsCrossed, Save, Info, CheckCircle2 } from 'lucide-react';
import { RecipeBuilder } from './RecipeBuilder';
import { MutableRefObject } from 'react';

interface StandardFormProps {
    viewMode: string;
    productForm: any;
    setProductForm: (form: any) => void;
    handleSave: () => void;
    isSaving: boolean;
    recipeItems: any[];
    setRecipeItems: (items: any[]) => void;
    ingredients: any[];
    selectedCategory?: any;
    fileInputRef?: MutableRefObject<HTMLInputElement | null>;
    handleFileChange?: (e: any) => void;
}

export const StandardForm = ({
    viewMode,
    productForm,
    setProductForm,
    handleSave,
    isSaving,
    recipeItems,
    setRecipeItems,
    ingredients,
    selectedCategory,
    fileInputRef,
}: StandardFormProps) => {

    const isIngredient = viewMode === 'INSUMOS';

    return (
        <div className="bg-card-dark border border-border-dark rounded-xl shadow-xl overflow-hidden animate-in slide-in-from-bottom-2">

            {/* Header / Toolbar */}
            <div className="p-4 border-b border-border-dark bg-black/20 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isIngredient ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                        {isIngredient ? <Package size={20} /> : <UtensilsCrossed size={20} />}
                    </div>
                    <div>
                        <h3 className="font-bold text-gray-200">
                            {isIngredient ? 'Definiendo Insumo' : 'Definiendo Producto'}
                        </h3>
                        {selectedCategory && (
                            <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="text-[10px] text-gray-500 uppercase font-bold">Categoría:</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded border ${isIngredient ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-300' : 'bg-amber-500/5 border-amber-500/10 text-amber-300'}`}>
                                    {selectedCategory.name}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={handleSave}
                    disabled={!productForm.name || isSaving}
                    className={`px-4 py-2 rounded-lg font-bold text-sm shadow-lg flex items-center gap-2 transition-all ${isIngredient ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-500/20' : 'bg-accent-primary hover:bg-orange-600 text-white shadow-accent-primary/20'} disabled:opacity-50 disabled:grayscale`}
                >
                    <Save size={16} />
                    {isSaving ? 'Guardando...' : 'Guardar'}
                </button>
            </div>

            <div className="p-6">
                <div className="grid grid-cols-12 gap-6">
                    {/* Basic Info */}
                    <div className="col-span-12 md:col-span-8 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1.5">Nombre</label>
                                <input
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-3 py-2 text-white focus:border-accent-primary outline-none transition-colors"
                                    placeholder={isIngredient ? "Ej. Harina de Trigo" : "Ej. Hamburguesa Clásica"}
                                    value={productForm.name}
                                    onChange={e => setProductForm({ ...productForm, name: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
                                    {isIngredient ? 'Costo Compra / Unidad' : 'Precio Venta'}
                                </label>
                                <div className="relative">
                                    <span className="absolute left-3 top-2 text-gray-500">$</span>
                                    <input
                                        type="number"
                                        className="w-full bg-bg-deep pl-7 pr-3 py-2 border border-border-dark rounded-lg text-white focus:border-accent-primary outline-none"
                                        placeholder="0.00"
                                        value={productForm.price}
                                        onChange={e => setProductForm({ ...productForm, price: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1.5">Stock Inicial</label>
                                <input
                                    type="number"
                                    className="w-full bg-bg-deep px-3 py-2 border border-border-dark rounded-lg text-white focus:border-accent-primary outline-none"
                                    placeholder="0"
                                    value={productForm.stock}
                                    onChange={e => setProductForm({ ...productForm, stock: e.target.value })}
                                />
                            </div>
                        </div>

                        {!isIngredient && (
                            <div className="mt-4">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${productForm.hasRecipe ? 'bg-accent-primary border-accent-primary' : 'bg-transparent border-border-dark group-hover:border-gray-500'}`}>
                                        {productForm.hasRecipe && <CheckCircle2 size={14} className="text-white" />}
                                    </div>
                                    <input
                                        type="checkbox"
                                        className="hidden"
                                        checked={productForm.hasRecipe}
                                        onChange={e => setProductForm({ ...productForm, hasRecipe: e.target.checked })}
                                    />
                                    <span className="text-sm text-gray-300 font-medium">Este producto tiene receta (escandallo)</span>
                                </label>
                                <p className="text-xs text-gray-500 mt-1 ml-7">
                                    Habilita esto si el producto se prepara combinando insumos (Ej. Hamburguesa con pan, carne, queso).
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Meta Info (Right) */}
                    <div className="col-span-12 md:col-span-4 space-y-4">
                        <div className="bg-black/20 p-4 rounded-lg border border-border-dark">
                            <h4 className="text-xs font-bold text-gray-400 uppercase mb-3 flex items-center gap-2">
                                <Info size={14} /> Detalles
                            </h4>
                            <div className="space-y-3">
                                <div>
                                    <label className="text-[10px] text-gray-500 uppercase block mb-1">SKU / Código</label>
                                    <input
                                        className="w-full bg-bg-deep border border-border-dark rounded px-2 py-1.5 text-xs text-white focus:border-white/20 outline-none"
                                        value={productForm.sku}
                                        onChange={e => setProductForm({ ...productForm, sku: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-gray-500 uppercase block mb-1">Stock Mínimo</label>
                                    <input
                                        className="w-full bg-bg-deep border border-border-dark rounded px-2 py-1.5 text-xs text-white focus:border-white/20 outline-none"
                                        value={productForm.minStock}
                                        onChange={e => setProductForm({ ...productForm, minStock: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] text-gray-500 uppercase block mb-1">Unidad Medida</label>
                                    <select
                                        className="w-full bg-bg-deep border border-border-dark rounded px-2 py-1.5 text-xs text-white focus:border-white/20 outline-none"
                                        value={productForm.unit}
                                        onChange={e => setProductForm({ ...productForm, unit: e.target.value })}
                                    >
                                        <option value="UNIDAD">Unidad (u)</option>
                                        <option value="KG">Kilogramos (kg)</option>
                                        <option value="L">Litros (L)</option>
                                        <option value="PORCION">Porción</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RECIPE BUILDER */}
                {productForm.hasRecipe && !isIngredient && (
                    <RecipeBuilder
                        recipeItems={recipeItems}
                        setRecipeItems={setRecipeItems}
                        ingredients={ingredients}
                    />
                )}
            </div>
        </div>
    );
};
