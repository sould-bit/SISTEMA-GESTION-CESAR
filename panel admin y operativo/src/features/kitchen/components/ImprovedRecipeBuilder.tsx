import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { useState, useEffect, useMemo } from 'react';
import { kitchenService, Ingredient, RecipePayload, ProductSummary, Category } from '../kitchen.service';
import { HelpIcon } from '@/components/ui/Tooltip';

interface RecipeFormData {
    name: string;
    product_id: string;
    category_id?: string; // New field for product creation
    preparation_time: number;
    selling_price: number;
    items: {
        ingredient_id: string;
        ingredient_name: string;
        gross_quantity: number;
        measure_unit: string;
        unit_cost: number;
        yield_factor: number;
    }[];
}

interface Props {
    productId?: number;
    existingRecipe?: any;  // Recipe to edit (if in edit mode)
    onSave?: (recipe: any) => void;
    onCancel?: () => void;
}

export const ImprovedRecipeBuilder = ({ productId, existingRecipe, onSave, onCancel }: Props) => {
    const isEditMode = !!existingRecipe;
    // State
    const [categories, setCategories] = useState<Category[]>([]);
    const [productSearchResults, setProductSearchResults] = useState<ProductSummary[]>([]);
    const [showProductSearch, setShowProductSearch] = useState(false);

    const [searchResults, setSearchResults] = useState<Ingredient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearch, setShowSearch] = useState(false);

    // Category creation modal state
    const [showCategoryModal, setShowCategoryModal] = useState(false);
    const [newCategoryName, setNewCategoryName] = useState('');
    const [newCategoryDesc, setNewCategoryDesc] = useState('');
    const [creatingCategory, setCreatingCategory] = useState(false);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<RecipeFormData>({
        defaultValues: {
            name: existingRecipe?.name || '',
            product_id: existingRecipe?.product_id?.toString() || productId?.toString() || '',
            category_id: existingRecipe?.category_id?.toString() || '',
            preparation_time: existingRecipe?.preparation_time || 0,
            selling_price: existingRecipe?.selling_price || 0,
            items: existingRecipe?.items?.map((item: any) => ({
                ingredient_id: item.ingredient_id,
                ingredient_name: item.ingredient_name || `Ingrediente ${item.ingredient_id}`,
                gross_quantity: Number(item.gross_quantity) || 0,
                measure_unit: item.measure_unit || 'g',
                unit_cost: Number(item.unit_cost || item.calculated_cost / item.gross_quantity) || 0,
                yield_factor: item.yield_factor || 1
            })) || []
        }
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: 'items'
    });

    const watchedItems = useWatch({ control, name: 'items', defaultValue: [] });
    const watchedSellingPrice = useWatch({ control, name: 'selling_price', defaultValue: 0 });
    const watchedName = useWatch({ control, name: 'name' });
    const watchedProductId = useWatch({ control, name: 'product_id' });

    // Load Categories on mount
    useEffect(() => {
        loadCategoriesList();
    }, []);

    const loadCategoriesList = async () => {
        try {
            const data = await kitchenService.getCategories();
            setCategories(data.filter(c => c.is_active));
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    };

    // Create new category
    const handleCreateCategory = async () => {
        if (!newCategoryName.trim()) return;

        setCreatingCategory(true);
        try {
            const newCat = await kitchenService.createCategory(newCategoryName.trim(), newCategoryDesc.trim());
            await loadCategoriesList();
            setValue('category_id', newCat.id.toString());
            setShowCategoryModal(false);
            setNewCategoryName('');
            setNewCategoryDesc('');
        } catch (error: any) {
            console.error('Error creating category:', error);
            alert(error.response?.data?.detail || 'Error al crear la categoría');
        } finally {
            setCreatingCategory(false);
        }
    };

    // Search Products when Name changes (and no Product ID is set)
    useEffect(() => {
        if (productId) return; // Don't search if editing specific product
        if (watchedProductId) return; // Don't search if already selected
        if (!watchedName || watchedName.length < 2) {
            setShowProductSearch(false);
            return;
        }

        const timer = setTimeout(() => {
            fetchProducts(watchedName);
        }, 300);
        return () => clearTimeout(timer);
    }, [watchedName, watchedProductId, productId]);

    const fetchProducts = async (query: string) => {
        try {
            const data = await kitchenService.getProducts(query);
            setProductSearchResults(data);
            setShowProductSearch(true);
        } catch (error) {
            console.error('Error searching products:', error);
        }
    };

    const handleSelectProduct = (product: ProductSummary) => {
        setValue('product_id', product.id.toString());
        setValue('name', product.name);
        setValue('selling_price', product.price);
        if (product.category_id) {
            setValue('category_id', product.category_id.toString());
        }
        setShowProductSearch(false);
    };

    const clearProductSelection = () => {
        setValue('product_id', '');
        // Keep name and price, just unlink ID to allow creation
    };

    // Search Ingredients Logic
    useEffect(() => {
        if (showSearch) {
            fetchIngredients(searchQuery);
        }
    }, [showSearch]);

    useEffect(() => {
        const timer = setTimeout(() => {
            if (showSearch) fetchIngredients(searchQuery);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const fetchIngredients = async (query: string) => {
        setLoading(true);
        try {
            const data = await kitchenService.getIngredients(query);
            setSearchResults(data);
        } catch (error) {
            console.error('Error loading ingredients:', error);
        } finally {
            setLoading(false);
        }
    };

    // Calculate totals
    const calculations = useMemo(() => {
        const totalCost = watchedItems.reduce((sum, item) => {
            const grossQty = Number(item.gross_quantity) || 0;
            const unitCost = Number(item.unit_cost) || 0;
            return sum + (grossQty * unitCost);
        }, 0);

        const sellingPrice = Number(watchedSellingPrice) || 0;
        const marginAmount = sellingPrice - totalCost; // Margen en dinero
        const margin = sellingPrice > 0 ? ((sellingPrice - totalCost) / sellingPrice) * 100 : 0;
        const foodCostPct = sellingPrice > 0 ? (totalCost / sellingPrice) * 100 : 0;

        return { totalCost, marginAmount, margin, foodCostPct, sellingPrice };
    }, [watchedItems, watchedSellingPrice]);

    const addIngredient = (ingredient: Ingredient) => {
        if (watchedItems.some(i => i.ingredient_id === ingredient.id)) {
            setShowSearch(false);
            setSearchQuery('');
            return;
        }
        append({
            ingredient_id: ingredient.id,
            ingredient_name: ingredient.name,
            gross_quantity: 0,
            measure_unit: ingredient.base_unit,
            unit_cost: ingredient.current_cost,
            yield_factor: ingredient.yield_factor
        });
        setShowSearch(false);
        setSearchQuery('');
    };

    const onSubmit = async (data: RecipeFormData) => {
        setSaving(true);
        try {
            // Prepare items payload with proper type conversion and validation
            const itemsPayload = data.items
                .filter(item => item.ingredient_id && Number(item.gross_quantity) > 0)
                .map(item => ({
                    ingredient_id: item.ingredient_id,
                    gross_quantity: Number(item.gross_quantity),
                    measure_unit: item.measure_unit || 'g'
                }));

            if (itemsPayload.length === 0) {
                alert('Debes agregar al menos un ingrediente con cantidad mayor a 0');
                setSaving(false);
                return;
            }

            // EDIT MODE
            if (isEditMode && existingRecipe) {
                // 1. Update recipe basic info if name changed
                if (data.name !== existingRecipe.name) {
                    await kitchenService.updateRecipe(String(existingRecipe.id), {
                        name: data.name,
                        preparation_time: data.preparation_time
                    } as any);
                }

                // 2. Update items (replaces all items)
                const updatedRecipe = await kitchenService.updateRecipeItems(
                    String(existingRecipe.id),
                    itemsPayload
                );

                onSave?.(updatedRecipe);
                alert(`✅ Receta "${data.name}" actualizada correctamente`);
                return;
            }

            // CREATE MODE
            let finalProductId = data.product_id ? Number(data.product_id) : 0;

            // 1. Create Product if it doesn't exist
            if (!finalProductId) {
                if (!data.category_id) {
                    alert('Para crear un nuevo producto, debes seleccionar una Categoría.');
                    setSaving(false);
                    return;
                }
                const newProduct = await kitchenService.createProduct({
                    name: data.name,
                    price: data.selling_price,
                    category_id: Number(data.category_id),
                    stock: 0
                });
                finalProductId = newProduct.id;
                console.log('✅ Created New Product:', newProduct);
            }

            // 2. Create Recipe
            const payload: RecipePayload = {
                product_id: finalProductId,
                name: data.name,
                preparation_time: data.preparation_time,
                items: itemsPayload
            };

            const result = await kitchenService.createRecipe(payload);
            onSave?.(result);
            alert(`✅ Receta guardada para "${data.name}"`);

        } catch (error: any) {
            console.error('Error saving recipe:', error);
            const msg = error.response?.data?.detail || error.message || 'Error al guardar';
            alert(`Error: ${msg}`);
        } finally {
            setSaving(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    const getProfitabilityColor = () => {
        if (calculations.foodCostPct === 0) return 'text-gray-400';
        if (calculations.foodCostPct <= 28) return 'text-emerald-400';
        if (calculations.foodCostPct <= 35) return 'text-amber-400';
        return 'text-red-400';
    };

    const formatQuantity = (val: number) => new Intl.NumberFormat('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 3 }).format(val);

    return (
        <>
            <div className="bg-card-dark border border-border-dark rounded-2xl p-6">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-accent-orange">menu_book</span>
                                Constructor de Recetas Vivas
                            </h2>
                            <p className="text-text-muted text-sm">Define ingredientes y crea el producto automáticamente si no existe.</p>
                        </div>
                    </div>

                    {/* Main Product/Recipe Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Name & Product Link */}
                        <div className="relative z-20">
                            <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center justify-between">
                                Nombre del Platillo / Producto
                                {watchedProductId && (
                                    <button type="button" onClick={clearProductSelection} className="text-[10px] text-blue-400 hover:text-blue-300 underline">
                                        Desvincular (Crear Nuevo)
                                    </button>
                                )}
                            </label>
                            <div className="relative">
                                <input
                                    {...register('name', { required: 'Nombre requerido' })}
                                    autoComplete="off"
                                    className={`w-full bg-bg-deep border ${watchedProductId ? 'border-emerald-500/50' : 'border-border-dark'} rounded-lg px-4 py-2.5 text-white placeholder-text-muted focus:outline-none focus:border-accent-orange`}
                                    placeholder="Ej: Hamburguesa Clásica"
                                />
                                {watchedProductId && (
                                    <span className="absolute right-3 top-2.5 text-emerald-400 material-symbols-outlined text-sm" title="Vinculado a producto existente">link</span>
                                )}
                            </div>

                            {/* Autocomplete Dropdown */}
                            {showProductSearch && productSearchResults.length > 0 && !watchedProductId && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto z-50">
                                    <div className="px-3 py-2 text-[10px] text-gray-500 uppercase font-bold tracking-wider">
                                        Productos Existentes (Click para usar)
                                    </div>
                                    {productSearchResults.map(p => (
                                        <button
                                            key={p.id}
                                            type="button"
                                            onClick={() => handleSelectProduct(p)}
                                            className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm border-b border-gray-700/50 flex justify-between"
                                        >
                                            <span className="text-white font-medium">{p.name}</span>
                                            <span className="text-emerald-400 ml-2">{formatCurrency(p.price)}</span>
                                        </button>
                                    ))}
                                    <div className="px-3 py-2 text-[10px] text-accent-orange italic text-center">
                                        O sigue escribiendo para crear uno nuevo...
                                    </div>
                                </div>
                            )}
                            <input type="hidden" {...register('product_id')} />
                        </div>

                        {/* Category (Req for New) */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1 flex items-center gap-2">
                                Categoría {watchedProductId ? '(Existente)' : '(Requerido para Nuevo)'}
                                <HelpIcon content="La categoría organiza cómo se mostrarán tus platillos en el menú. Ejemplos: Hamburguesas, Jugos, Sándwiches, Platos Fuertes, Postres, Promociones." />
                            </label>
                            <div className="flex gap-2">
                                <select
                                    {...register('category_id')}
                                    disabled={!!watchedProductId}
                                    className={`flex-1 bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange disabled:opacity-50`}
                                >
                                    <option value="">-- Seleccionar Categoría --</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                                {!watchedProductId && (
                                    <button
                                        type="button"
                                        onClick={() => setShowCategoryModal(true)}
                                        className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-1 text-sm transition-colors"
                                        title="Crear nueva categoría"
                                    >
                                        <span className="material-symbols-outlined text-[18px]">add</span>
                                        Nueva
                                    </button>
                                )}
                            </div>
                            {!watchedProductId && (
                                <p className="text-xs text-text-muted mt-1.5 flex items-start gap-1.5">
                                    <span className="material-symbols-outlined text-[14px] text-blue-400 shrink-0 mt-0.5">lightbulb</span>
                                    <span>
                                        Agrupa los productos en tu menú. Crea categorías como: <span className="text-blue-400">Hamburguesas</span>, <span className="text-emerald-400">Bebidas</span>, <span className="text-purple-400">Platos Especiales</span>, <span className="text-amber-400">Promociones</span>.
                                    </span>
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Price & Time */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Precio de Venta</label>
                            <input
                                type="number"
                                {...register('selling_price', { required: true, min: 0 })}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Tiempo prep. (min)</label>
                            <input
                                type="number"
                                {...register('preparation_time')}
                                className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange"
                            />
                        </div>
                    </div>

                    {/* Ingredients Section */}
                    <div className="border border-border-dark rounded-xl p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-[20px]">nutrition</span>
                                Ingredientes
                            </h3>
                            {/* Add Ingredient Button & Search Logic (Unchanged but simplified) */}
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => setShowSearch(!showSearch)}
                                    className="flex items-center gap-2 px-4 py-2 bg-accent-orange/10 text-accent-orange rounded-lg hover:bg-accent-orange/20 transition-colors text-sm font-medium"
                                >
                                    <span className="material-symbols-outlined text-[18px]">add</span>
                                    Agregar Insumo
                                </button>
                                {/* Ingredient Search Dropdown */}
                                {showSearch && (
                                    <div className="absolute right-0 top-full mt-2 w-96 bg-bg-deep border border-border-dark rounded-xl shadow-xl z-50 overflow-hidden flex flex-col max-h-[500px]">
                                        <div className="p-3 border-b border-border-dark shrink-0">
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="Buscar insumo, producción o mercadería..."
                                                className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-orange"
                                                autoFocus
                                            />
                                        </div>

                                        <div className="overflow-y-auto flex-1">
                                            {loading ? (
                                                <div className="p-4 text-center text-text-muted">Cargando...</div>
                                            ) : searchResults.length === 0 ? (
                                                <div className="p-4 text-center text-text-muted">No encontrado</div>
                                            ) : (
                                                <div className="flex flex-col">
                                                    {/* Helper to render groups */}
                                                    {(['PROCESSED', 'RAW', 'MERCHANDISE'] as const).map(type => {
                                                        const groupItems = searchResults.filter(i => {
                                                            if (type === 'RAW') return i.ingredient_type === 'RAW' || i.ingredient_type === 'RAW_MATERIAL' as any;
                                                            return i.ingredient_type === type;
                                                        });

                                                        if (groupItems.length === 0) return null;

                                                        const title = type === 'PROCESSED' ? 'Producciones Internas' :
                                                            type === 'RAW' ? 'Insumos / Materia Prima' : 'Mercadería (Venta Directa)';

                                                        const headerColor = type === 'PROCESSED' ? 'text-purple-400 bg-purple-500/10 border-purple-500/20' :
                                                            type === 'RAW' ? 'text-blue-400 bg-blue-500/10 border-blue-500/20' :
                                                                'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';

                                                        return (
                                                            <div key={type}>
                                                                <div className={`px-4 py-1.5 text-xs font-bold uppercase tracking-wider border-y border-white/5 ${headerColor}`}>
                                                                    {title}
                                                                </div>
                                                                {groupItems.map(ing => (
                                                                    <button
                                                                        key={ing.id}
                                                                        type="button"
                                                                        onClick={() => addIngredient(ing)}
                                                                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors text-left border-b border-white/5 last:border-0"
                                                                    >
                                                                        <div>
                                                                            <div className="text-white font-medium text-sm">{ing.name}</div>
                                                                            <div className="text-text-muted text-xs">{ing.sku} • {ing.base_unit}</div>
                                                                        </div>
                                                                        <div className="text-right">
                                                                            <div className="text-emerald-400 font-mono text-sm">
                                                                                {formatCurrency(ing.current_cost)}
                                                                            </div>
                                                                            <div className="text-text-muted text-xs">
                                                                                Rend: {(ing.yield_factor * 100).toFixed(0)}%
                                                                            </div>
                                                                        </div>
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Ingredients Table (Fields map) */}
                        <div className="space-y-2">
                            {fields.length === 0 ? (
                                <div className="text-center py-8 text-text-muted">No hay ingredientes aún.</div>
                            ) : fields.map((field, index) => {
                                const item = watchedItems[index];
                                const netQty = (item?.gross_quantity || 0) * (item?.yield_factor || 1);
                                const itemCost = (item?.gross_quantity || 0) * (item?.unit_cost || 0);

                                return (
                                    <div key={field.id} className="grid grid-cols-12 gap-2 items-center bg-bg-deep rounded-lg px-3 py-2 text-sm">
                                        <div className="col-span-3 text-white truncate">{item?.ingredient_name}</div>
                                        <div className="col-span-2">
                                            <input
                                                type="number" step="0.001"
                                                {...register(`items.${index}.gross_quantity`, { valueAsNumber: true })}
                                                className="w-full bg-card-dark border border-border-dark rounded px-2 py-1 text-white text-center"
                                                placeholder="Cant"
                                            />
                                        </div>
                                        <div className="col-span-1 text-center text-text-muted">{item?.measure_unit}</div>
                                        <div className="col-span-2 text-center text-text-muted">{((1 - (item?.yield_factor || 1)) * 100).toFixed(0)}% Merma</div>
                                        <div className="col-span-2 text-center text-white">{formatQuantity(netQty)} Neto</div>
                                        <div className="col-span-1 text-right text-emerald-400">{formatCurrency(itemCost)}</div>
                                        <div className="col-span-1 text-right">
                                            <button onClick={() => remove(index)} type="button" className="text-red-400 hover:text-red-300">
                                                <span className="material-symbols-outlined text-[18px]">delete</span>
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Stats Footer */}
                    <div className="grid grid-cols-3 gap-4">
                        {/* Costo Total */}
                        <div className="bg-bg-deep rounded-lg p-4 border border-border-dark">
                            <div className="text-text-muted text-xs uppercase mb-1">Costo Total</div>
                            <div className="text-xl font-bold text-white font-mono">{formatCurrency(calculations.totalCost)}</div>
                            <div className="text-xs text-text-muted mt-1">de {formatCurrency(calculations.sellingPrice)} venta</div>
                        </div>

                        {/* Food Cost */}
                        <div className="bg-bg-deep rounded-lg p-4 border border-border-dark">
                            <div className="text-text-muted text-xs uppercase mb-1 flex items-center gap-1">
                                Food Cost
                                <HelpIcon content="Porcentaje del precio de venta que se gasta en ingredientes. Ideal: menor a 30%" />
                            </div>
                            <div className={`text-xl font-bold font-mono ${getProfitabilityColor()}`}>
                                {calculations.foodCostPct.toFixed(1)}%
                            </div>
                            <div className="text-xs text-text-muted mt-1 font-mono">
                                {formatCurrency(calculations.totalCost)} en insumos
                            </div>
                        </div>

                        {/* Margen */}
                        <div className="bg-bg-deep rounded-lg p-4 border border-border-dark">
                            <div className="text-text-muted text-xs uppercase mb-1 flex items-center gap-1">
                                Margen de Ganancia
                                <HelpIcon content="Ganancia neta por cada venta después de restar el costo de ingredientes" />
                            </div>
                            <div className={`text-xl font-bold font-mono ${calculations.marginAmount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {formatCurrency(calculations.marginAmount)}
                            </div>
                            <div className="text-xs text-text-muted mt-1 font-mono">
                                {calculations.margin.toFixed(1)}% del precio
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-border-dark">
                        {onCancel && <button type="button" onClick={onCancel} className="px-6 py-2 bg-gray-700 text-white rounded-lg">Cancelar</button>}
                        <button
                            type="submit"
                            disabled={saving || fields.length === 0}
                            className="px-6 py-2 bg-accent-orange text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 flex items-center gap-2"
                        >
                            {saving ? 'Guardando...' : isEditMode ? 'Actualizar Receta' : 'Guardar Receta'}
                        </button>
                    </div>
                </form>
            </div>

            {/* Modal: Create Category */}
            {showCategoryModal && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-bg-card rounded-xl border border-border-dark p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-emerald-400">add_circle</span>
                                Nueva Categoría
                            </h3>
                            <button
                                onClick={() => setShowCategoryModal(false)}
                                className="text-gray-400 hover:text-white"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Nombre de la Categoría *
                                </label>
                                <input
                                    type="text"
                                    value={newCategoryName}
                                    onChange={(e) => setNewCategoryName(e.target.value)}
                                    placeholder="Ej: Hamburguesas, Jugos, Platos Fuertes..."
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange placeholder:text-gray-500"
                                    autoFocus
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Descripción (opcional)
                                </label>
                                <input
                                    type="text"
                                    value={newCategoryDesc}
                                    onChange={(e) => setNewCategoryDesc(e.target.value)}
                                    placeholder="Ej: Todas las hamburguesas del menú"
                                    className="w-full bg-bg-deep border border-border-dark rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-accent-orange placeholder:text-gray-500"
                                />
                            </div>

                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-300">
                                <div className="flex items-start gap-2">
                                    <span className="material-symbols-outlined text-[16px] mt-0.5">info</span>
                                    <span>
                                        Las categorías agrupan tus productos en el menú.
                                        Crea categorías descriptivas para que tus clientes encuentren fácilmente lo que buscan.
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border-dark">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowCategoryModal(false);
                                    setNewCategoryName('');
                                    setNewCategoryDesc('');
                                }}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                onClick={handleCreateCategory}
                                disabled={!newCategoryName.trim() || creatingCategory}
                                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {creatingCategory ? (
                                    <>
                                        <span className="animate-spin material-symbols-outlined text-[18px]">progress_activity</span>
                                        Creando...
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined text-[18px]">check</span>
                                        Crear Categoría
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
export default ImprovedRecipeBuilder;
