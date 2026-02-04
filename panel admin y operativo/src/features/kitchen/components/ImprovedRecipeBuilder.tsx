import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { useState, useEffect, useMemo } from 'react';
import { kitchenService, Ingredient, RecipePayload, ProductSummary, Category } from '../kitchen.service';
import { HelpIcon } from '@/components/ui/Tooltip';
import { ImageUploader } from './ImageUploader';

interface RecipeFormData {
    name: string;
    product_id: string;
    category_id?: string; // New field for product creation
    preparation_time: number;
    selling_price: number;
    image_url?: string; // Product image URL
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
    const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    // Fix: check both locations for image URL (recipe top-level or nested product)
    const [imageUrl, setImageUrl] = useState<string>(existingRecipe?.product_image_url || existingRecipe?.product?.image_url || '');

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
    const watchedCategoryId = useWatch({ control, name: 'category_id' });

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
    // Create or Update category
    const handleSaveCategory = async () => {
        if (!newCategoryName.trim()) return;

        setCreatingCategory(true);
        try {
            if (editingCategoryId) {
                // Update existing
                const currentCat = categories.find(c => c.id.toString() === editingCategoryId);
                const isActive = currentCat ? currentCat.is_active : true;
                await kitchenService.updateCategory(Number(editingCategoryId), newCategoryName.trim(), newCategoryDesc.trim(), isActive);
            } else {
                // Create new
                const newCat = await kitchenService.createCategory(newCategoryName.trim(), newCategoryDesc.trim());
                if (!editingCategoryId) {
                    setValue('category_id', newCat.id.toString());
                }
            }

            await loadCategoriesList();
            setShowCategoryModal(false);
            setNewCategoryName('');
            setNewCategoryDesc('');
            setEditingCategoryId(null);
        } catch (error: any) {
            console.error('Error saving category:', error);
            const errorData = error.response?.data;
            let errorMessage = 'Error al guardar la categoría';

            if (errorData?.detail) {
                if (Array.isArray(errorData.detail)) {
                    // Pydantic validation errors
                    errorMessage = `Error de validación:\n` + errorData.detail.map((def: any) =>
                        `- ${def.loc.join('.')}: ${def.msg}`
                    ).join('\n');
                } else {
                    errorMessage = errorData.detail;
                }
            }

            alert(errorMessage);
            console.log('FULL ERROR RESPONSE:', errorData);
        } finally {
            setCreatingCategory(false);
        }
    };

    const handleEditCategory = () => {
        if (!watchedCategoryId) return;
        const cat = categories.find(c => c.id.toString() === watchedCategoryId);
        if (cat) {
            setNewCategoryName(cat.name);
            setNewCategoryDesc(cat.description || '');
            setEditingCategoryId(cat.id.toString());
            setShowCategoryModal(true);
        }
    };

    const handleOpenCreateCategory = () => {
        setNewCategoryName('');
        setNewCategoryDesc('');
        setEditingCategoryId(null);
        setShowCategoryModal(true);
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

    // Load Product Data (Price, Category) on Init
    useEffect(() => {
        const loadProductData = async () => {
            const targetProductId = existingRecipe?.product_id || productId;

            if (targetProductId) {
                try {
                    const product = await kitchenService.getProduct(Number(targetProductId));
                    if (product) {
                        // Update Price (always, as it might be 0 in recipe)
                        setValue('selling_price', product.price);

                        // Update Category if missing
                        if (!watchedCategoryId && product.category_id) {
                            setValue('category_id', product.category_id.toString());
                        }

                        // If creating new recipe from product, set name
                        if (!isEditMode && productId) {
                            setValue('name', product.name);
                        }
                    }
                } catch (error) {
                    console.error('Error loading product details:', error);
                }
            }
        };

        loadProductData();
    }, [existingRecipe, productId, isEditMode]);

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
                if (data.name !== existingRecipe.name || data.preparation_time !== existingRecipe.preparation_time) {
                    await kitchenService.updateRecipe(String(existingRecipe.id), {
                        name: data.name,
                        preparation_time: data.preparation_time
                    } as any);
                }

                // 2. Update product image if changed (or if just present to be safe)
                const currentImg = existingRecipe.product_image_url || existingRecipe.product?.image_url;
                if (imageUrl && existingRecipe.product_id) {
                    // We update if it's different OR if we just want to ensure consistency
                    try {
                        console.log('🖼️ Attempting to update product image for ID:', existingRecipe.product_id);
                        await kitchenService.updateProductImage(existingRecipe.product_id, imageUrl);
                        console.log('✅ Updated product image');
                    } catch (e) {
                        console.warn('Could not update product image:', e);
                    }
                }

                // 3. Update items (replaces all items)
                const updatedRecipe = await kitchenService.updateRecipeItems(
                    String(existingRecipe.id),
                    itemsPayload
                );

                // FORCE UPDATE LOCAL OBJECT: Ensure the image we just uploaded is reflected in the UI object
                // The backend response might not include the fresh joined product image immediately depending on the endpoint
                if (imageUrl) {
                    updatedRecipe.product_image_url = imageUrl;
                    if (updatedRecipe.product) {
                        updatedRecipe.product.image_url = imageUrl;
                    } else {
                        // If product object is missing, try to patch it minimally if we know it exists
                        updatedRecipe.product = { image_url: imageUrl } as any;
                    }
                }

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
                    stock: 0,
                    image_url: imageUrl || undefined
                });
                finalProductId = newProduct.id;
                console.log('✅ Created New Product:', newProduct);
            } else if (imageUrl) {
                // Update image for existing product
                try {
                    await kitchenService.updateProductImage(finalProductId, imageUrl);
                    console.log('✅ Updated product image');
                } catch (e) {
                    console.warn('Could not update product image:', e);
                }
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
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 pb-10">

                {/* 1. ENCABEZADO PAGE */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                            <span className="p-2.5 bg-accent-primary/10 rounded-xl text-accent-primary material-symbols-outlined icon-md">menu_book</span>
                            Constructor de Recetas
                        </h2>
                        <p className="text-text-muted mt-1 ml-1 text-sm">Configura los detalles técnicos y comerciales de tu producto.</p>
                    </div>
                </div>

                {/* 2. LAYOUT GRID PRINCIPAL: IMAGEN + DATOS */}
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

                    {/* COLUMNA IZQUIERDA: IMAGEN (Span 4) */}
                    <div className="xl:col-span-4">
                        <div className="bg-card-dark border border-border-dark rounded-2xl p-6 h-full flex flex-col shadow-lg shadow-black/20">
                            <div className="mb-4 flex items-center justify-between">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Presentación</h3>
                                {imageUrl && <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Imagen Lista</span>}
                            </div>

                            <div className="flex-1 flex flex-col">
                                <ImageUploader
                                    currentImageUrl={imageUrl}
                                    onImageUploaded={(url) => setImageUrl(url)}
                                    onError={(error) => alert(error)}
                                    label="Foto del Platillo"
                                />
                                <div className="mt-4 p-4 bg-purple-500/5 border border-purple-500/10 rounded-xl">
                                    <p className="text-xs text-purple-300 flex items-start gap-2 leading-relaxed">
                                        <span className="material-symbols-outlined text-[16px] shrink-0 mt-0.5">tips_and_updates</span>
                                        <span>Una fotografía profesional aumenta la percepción de valor y la conversión de venta un <strong>30%</strong>.</span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* COLUMNA DERECHA: DATOS DEL PRODUCTO (Span 8) */}
                    <div className="xl:col-span-8">
                        <div className="bg-card-dark border border-border-dark rounded-2xl p-8 space-y-8 h-full shadow-lg shadow-black/20 relative overflow-hidden">
                            {/* Background decoration */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

                            {/* SECCIÓN A: IDENTIFICACIÓN */}
                            <div className="relative z-10">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6 pb-2 border-b border-white/5">Información General</h3>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* Nombre & Link Producto */}
                                    <div className="relative space-y-2">
                                        <label className="block text-sm font-medium text-gray-300 flex justify-between">
                                            Nombre del Producto
                                            {watchedProductId && (
                                                <button type="button" onClick={clearProductSelection} className="text-xs text-blue-400 hover:text-blue-300 underline font-normal transition-colors">
                                                    Desvincular
                                                </button>
                                            )}
                                        </label>
                                        <div className="relative group">
                                            <input
                                                {...register('name', { required: 'Nombre requerido' })}
                                                autoComplete="off"
                                                className={`w-full bg-bg-deep border ${watchedProductId ? 'border-emerald-500/50 pl-10' : 'border-border-dark'} rounded-xl px-4 py-3 text-white placeholder-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all`}
                                                placeholder="Ej: Hamburguesa Doble Queso"
                                            />
                                            {watchedProductId ? (
                                                <span className="absolute left-3 top-3.5 text-emerald-400 material-symbols-outlined text-[18px]" title="Vinculado">link</span>
                                            ) : (
                                                <span className="absolute right-3 top-3.5 text-text-muted material-symbols-outlined text-[18px] opacity-0 group-hover:opacity-50 transition-opacity">edit</span>
                                            )}
                                        </div>

                                        {/* Dropdown Buscador */}

                                        <input type="hidden" {...register('product_id')} />
                                    </div>

                                    {/* Categoría */}
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-gray-300 flex items-center gap-2">
                                            Categoría
                                            {!watchedProductId && <span className="text-accent-primary text-xs">(Requerido)</span>}
                                        </label>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <select
                                                    {...register('category_id')}
                                                    disabled={!!watchedProductId}
                                                    className="w-full appearance-none bg-bg-deep border border-border-dark rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                                >
                                                    <option value="">-- Seleccionar --</option>
                                                    {categories.map(cat => (
                                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                                    ))}
                                                </select>
                                                <span className="material-symbols-outlined absolute right-3 top-3.5 text-text-muted pointer-events-none text-[20px]">expand_more</span>
                                            </div>
                                            {!watchedProductId && (
                                                <div className="flex gap-1">
                                                    {watchedCategoryId && (
                                                        <button
                                                            type="button"
                                                            onClick={handleEditCategory}
                                                            className="px-3 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-xl transition-colors"
                                                            title="Editar Categoría"
                                                        >
                                                            <span className="material-symbols-outlined text-[18px]">edit</span>
                                                        </button>
                                                    )}
                                                    <button
                                                        type="button"
                                                        onClick={handleOpenCreateCategory}
                                                        className="px-3 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-xl transition-colors"
                                                        title="Nueva Categoría"
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">add</span>
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN B: OPERATIVO */}
                            <div className="relative z-10 pt-2">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6 pb-2 border-b border-white/5">Datos Comerciales</h3>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Precio de Venta</label>
                                        <div className="relative">
                                            <span className="absolute left-4 top-3 text-text-muted font-mono">$</span>
                                            <input
                                                type="number"
                                                {...register('selling_price', { required: true, min: 0 })}
                                                className="w-full bg-bg-deep border border-border-dark rounded-xl pl-8 pr-4 py-3 text-white font-mono text-lg focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all"
                                                placeholder="0"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300">Tiempo de Preparación</label>
                                        <div className="relative">
                                            <span className="material-symbols-outlined absolute left-4 top-3 text-text-muted text-[20px]">schedule</span>
                                            <input
                                                type="number"
                                                {...register('preparation_time')}
                                                className="w-full bg-bg-deep border border-border-dark rounded-xl pl-11 pr-4 py-3 text-white font-mono text-lg focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all"
                                                placeholder="0"
                                            />
                                            <span className="absolute right-4 top-3.5 text-xs text-text-muted font-medium uppercase">Min</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>

                {/* 3. INGREDIENTES */}
                <div className="bg-card-dark border border-border-dark rounded-2xl p-8 shadow-lg shadow-black/20">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                        <div>
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <span className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400 material-symbols-outlined icon-sm">nutrition</span>
                                Composición de la Receta
                            </h3>
                            <p className="text-text-muted text-sm mt-1">Agrega los insumos necesarios para preparar una unidad de este producto.</p>
                        </div>

                        {/* Selector/Buscador (Simplificado visualmente) */}
                        <div className="relative w-full md:w-auto">
                            <button
                                type="button"
                                onClick={() => setShowSearch(!showSearch)}
                                className={`w-full md:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl transition-all font-bold text-sm shadow-lg shadow-accent-primary/10 ${showSearch ? 'bg-accent-primary text-white ring-2 ring-accent-primary ring-offset-2 ring-offset-[#0f172a]' : 'bg-accent-primary/10 text-accent-primary hover:bg-accent-primary hover:text-white'}`}
                            >
                                <span className="material-symbols-outlined text-[20px]">{showSearch ? 'close' : 'add'}</span>
                                {showSearch ? 'Cerrar Buscador' : 'Agregar Insumo'}
                            </button>

                            {/* Dropdown Resultados */}
                            {showSearch && (
                                <div className="absolute right-0 top-full mt-3 w-full md:w-[450px] bg-[#1E293B] border border-gray-700/50 rounded-2xl shadow-2xl z-50 overflow-hidden flex flex-col max-h-[500px] animate-in slide-in-from-top-2 duration-200 ring-1 ring-black/5">
                                    <div className="p-4 border-b border-gray-700/50 bg-[#0F172A]">
                                        <div className="relative">
                                            <span className="material-symbols-outlined absolute left-3 top-2.5 text-text-muted">search</span>
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder="Nombre, SKU o tipo..."
                                                className="w-full bg-[#1E293B] border border-gray-700 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all placeholder:text-gray-500"
                                                autoFocus
                                            />
                                        </div>
                                    </div>

                                    <div className="overflow-y-auto flex-1 custom-scrollbar scroll-smooth bg-[#1E293B]">
                                        {loading ? (
                                            <div className="p-8 text-center text-text-muted flex flex-col items-center gap-2">
                                                <span className="material-symbols-outlined animate-spin text-2xl">progress_activity</span>
                                                Buscando insumos...
                                            </div>
                                        ) : searchResults.length === 0 ? (
                                            <div className="p-12 text-center text-text-muted flex flex-col items-center gap-2">
                                                <span className="material-symbols-outlined text-4xl opacity-20">search_off</span>
                                                <p>No se encontraron resultados para "{searchQuery}"</p>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col pb-2">
                                                {(['PROCESSED', 'RAW', 'MERCHANDISE'] as const).map(type => {
                                                    const groupItems = searchResults.filter(i => {
                                                        if (type === 'RAW') return i.ingredient_type === 'RAW' || i.ingredient_type === 'RAW_MATERIAL' as any;
                                                        return i.ingredient_type === type;
                                                    });

                                                    if (groupItems.length === 0) return null;

                                                    const title = type === 'PROCESSED' ? 'Producciones Internas' :
                                                        type === 'RAW' ? 'Insumos / Materia Prima' : 'Mercadería (Venta Directa)';

                                                    // Usar colores sólidos oscuros con borde de color para diferenciar, en lugar de bg traslúcido
                                                    const headerStyle = type === 'PROCESSED' ? 'text-purple-400 border-l-4 border-purple-500 bg-[#162032]' :
                                                        type === 'RAW' ? 'text-blue-400 border-l-4 border-blue-500 bg-[#162032]' : 'text-emerald-400 border-l-4 border-emerald-500 bg-[#162032]';

                                                    return (
                                                        <div key={type}>
                                                            <div className={`px-5 py-2.5 text-[10px] font-bold uppercase tracking-wider sticky top-0 shadow-sm border-b border-gray-700/50 ${headerStyle}`}>
                                                                {title}
                                                            </div>
                                                            {groupItems.map(ing => (
                                                                <button
                                                                    key={ing.id}
                                                                    type="button"
                                                                    onClick={() => addIngredient(ing)}
                                                                    className="w-full px-5 py-3 hover:bg-white/5 transition-colors text-left border-b border-gray-700/30 flex items-center justify-between group"
                                                                >
                                                                    <div>
                                                                        <div className="text-white font-bold text-sm group-hover:text-accent-primary transition-colors">{ing.name}</div>
                                                                        <div className="text-gray-500 text-xs font-mono mt-0.5 opacity-80 group-hover:opacity-100">{ing.sku} • Base: {ing.base_unit}</div>
                                                                    </div>
                                                                    <div className="text-right">
                                                                        <div className="text-emerald-400 font-mono text-sm font-bold">
                                                                            {formatCurrency(ing.current_cost)}
                                                                        </div>
                                                                        <div className="text-gray-500 text-[10px] uppercase font-bold mt-0.5">
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

                    {/* Table Fields */}
                    <div className="space-y-3 min-h-[150px]">
                        {fields.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-16 border-2 border-dashed border-border-dark rounded-2xl bg-bg-deep/50">
                                <span className="material-symbols-outlined text-4xl text-text-muted mb-2 opacity-50">shopping_basket</span>
                                <p className="text-text-muted font-medium">Tu cesta de ingredientes está vacía</p>
                                <p className="text-xs text-text-muted opacity-60 mt-1">Usa el botón "Agregar Insumo" para comenzar</p>
                            </div>
                        ) : (
                            // Header Tabla
                            <div className="hidden md:grid grid-cols-12 gap-4 px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-white/5 mb-3">
                                <div className="col-span-4">Insumo</div>
                                <div className="col-span-2 text-center">Cantidad</div>
                                <div className="col-span-1 text-center">Unidad</div>
                                <div className="col-span-1 text-center">Merma</div>
                                <div className="col-span-2 text-center">Neto</div>
                                <div className="col-span-1 text-right">Costo</div>
                                <div className="col-span-1"></div>
                            </div>
                        )}

                        {fields.map((field, index) => {
                            const item = watchedItems[index];
                            const netQty = (item?.gross_quantity || 0) * (item?.yield_factor || 1);
                            const itemCost = (item?.gross_quantity || 0) * (item?.unit_cost || 0);

                            return (
                                <div key={field.id} className="grid grid-cols-1 md:grid-cols-12 gap-x-4 gap-y-2 items-center bg-bg-deep rounded-xl px-4 py-3 text-sm border border-transparent hover:border-gray-700 transition-all group animate-in fade-in duration-300">
                                    <div className="col-span-1 md:col-span-4">
                                        <div className="font-bold text-white text-base md:text-sm">{item?.ingredient_name}</div>
                                        <div className="text-xs text-text-muted md:hidden">Costo unit: {formatCurrency(item?.unit_cost || 0)}</div>
                                    </div>
                                    <div className="col-span-1 md:col-span-2">
                                        <input
                                            type="number" step="0.001"
                                            {...register(`items.${index}.gross_quantity`, { valueAsNumber: true })}
                                            className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2 text-white text-center font-mono focus:border-accent-primary focus:ring-1 focus:ring-accent-primary outline-none"
                                            placeholder="0"
                                        />
                                    </div>
                                    <div className="col-span-1 md:col-span-1 text-center text-text-muted font-mono text-xs">{item?.measure_unit}</div>
                                    <div className="col-span-1 md:col-span-1 text-center text-red-300 bg-red-500/5 rounded py-1 px-1 text-xs font-bold">
                                        {((1 - (item?.yield_factor || 1)) * 100).toFixed(0)}%
                                    </div>
                                    <div className="col-span-1 md:col-span-2 text-center text-white font-mono bg-white/5 rounded py-1 px-2 border border-white/5">
                                        {formatQuantity(netQty)}
                                    </div>
                                    <div className="col-span-1 md:col-span-1 text-right text-emerald-400 font-bold font-mono">
                                        {formatCurrency(itemCost)}
                                    </div>
                                    <div className="col-span-1 md:col-span-1 text-right">
                                        <button onClick={() => remove(index)} type="button" className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                                            <span className="material-symbols-outlined text-[20px]">delete</span>
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* 4. MÉTRICAS FINANCIERAS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Costo Total */}
                    <div className="bg-bg-deep border border-border-dark rounded-2xl p-6 relative overflow-hidden group hover:border-gray-600 transition-colors">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <span className="material-symbols-outlined text-4xl">payments</span>
                        </div>
                        <div className="text-text-muted text-xs font-bold uppercase tracking-wider mb-2">Costo Total</div>
                        <div className="text-3xl font-bold text-white font-mono tracking-tight">{formatCurrency(calculations.totalCost)}</div>
                        <div className="text-xs text-text-muted mt-2"> Costo directo por unidad</div>
                    </div>

                    {/* Food Cost */}
                    <div className="bg-bg-deep border border-border-dark rounded-2xl p-6 relative overflow-hidden hover:border-gray-600 transition-colors">
                        <div className={`text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2 ${getProfitabilityColor()}`}>
                            Food Cost
                            <span className={`px-2 py-0.5 rounded text-[10px] border opacity-80 current-color`}>
                                {calculations.foodCostPct <= 30 ? 'OPTIMAL' : 'HIGH'}
                            </span>
                        </div>
                        <div className={`text-3xl font-bold font-mono tracking-tight ${getProfitabilityColor()}`}>
                            {calculations.foodCostPct.toFixed(1)}%
                        </div>
                        <div className="text-xs text-text-muted mt-2">Objetivo ideal: &lt; 30%</div>
                    </div>

                    {/* Margen */}
                    <div className="bg-bg-deep border border-border-dark rounded-2xl p-6 relative overflow-hidden hover:border-gray-600 transition-colors">
                        <div className="text-text-muted text-xs font-bold uppercase tracking-wider mb-2">Margen Bruto</div>
                        <div className={`text-3xl font-bold font-mono tracking-tight ${calculations.marginAmount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {formatCurrency(calculations.marginAmount)}
                        </div>
                        <div className="text-xs text-text-muted mt-2 font-mono">
                            <span className={calculations.margin >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                {calculations.margin.toFixed(1)}%
                            </span> de rentabilidad
                        </div>
                    </div>
                </div>

                {/* ACTIONS */}
                <div className="flex justify-end gap-4 pt-6 mt-8 border-t border-white/5">
                    {onCancel && (
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-8 py-3 bg-transparent border border-gray-600 text-gray-300 rounded-xl hover:bg-gray-800 hover:text-white font-medium transition-all"
                        >
                            Cancelar
                        </button>
                    )}
                    <button
                        type="submit"
                        disabled={saving || fields.length === 0}
                        className="px-10 py-3 bg-accent-primary text-white rounded-xl hover:bg-orange-600 disabled:opacity-50 disabled:grayscale font-bold shadow-lg shadow-orange-500/20 flex items-center gap-3 transition-all transform hover:scale-[1.02] active:scale-95"
                    >
                        {saving ? (
                            <>
                                <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
                                Guardando...
                            </>
                        ) : (
                            <>
                                <span className="material-symbols-outlined text-[20px]">save</span>
                                {isEditMode ? 'Guardar Cambios' : 'Guardar Receta'}
                            </>
                        )}
                    </button>
                </div>

            </form>

            {/* Modal: Create Category */}
            {showCategoryModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200">
                    <div className="bg-bg-card rounded-2xl border border-border-dark p-8 w-full max-w-md shadow-2xl relative overflow-hidden">
                        {/* Glow effect */}
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-blue-500"></div>

                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                <span className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 material-symbols-outlined text-[20px]">category</span>
                                {editingCategoryId ? 'Editar Categoría' : 'Nueva Categoría'}
                            </h3>
                            <button
                                onClick={() => {
                                    setShowCategoryModal(false);
                                    setNewCategoryName('');
                                    setNewCategoryDesc('');
                                    setEditingCategoryId(null);
                                }}
                                className="p-1 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <div className="space-y-5">
                            <div>
                                <label className="block text-sm font-bold text-gray-300 mb-1.5">
                                    Nombre de la Categoría <span className="text-accent-primary">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={newCategoryName}
                                    onChange={(e) => setNewCategoryName(e.target.value)}
                                    placeholder="Ej: Hamburguesas, Jugos..."
                                    className="w-full bg-bg-deep border border-border-dark rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all font-medium"
                                    autoFocus
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-gray-300 mb-1.5">
                                    Descripción <span className="text-gray-500 font-normal text-xs">(Opcional)</span>
                                </label>
                                <input
                                    type="text"
                                    value={newCategoryDesc}
                                    onChange={(e) => setNewCategoryDesc(e.target.value)}
                                    placeholder="Breve descripción..."
                                    className="w-full bg-bg-deep border border-border-dark rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-all"
                                />
                            </div>

                            <div className="bg-blue-500/5 border border-blue-500/10 rounded-xl p-4 text-xs text-blue-200 leading-relaxed flex gap-3">
                                <span className="material-symbols-outlined text-[18px] shrink-0 text-blue-400">info</span>
                                <div>
                                    Una buena categorización ayuda a tus meseros a encontrar los productos más rápido durante el servicio.
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowCategoryModal(false);
                                    setNewCategoryName('');
                                    setNewCategoryDesc('');
                                    setEditingCategoryId(null);
                                }}
                                className="px-5 py-2.5 text-gray-400 hover:text-white font-medium transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                onClick={handleSaveCategory}
                                disabled={!newCategoryName.trim() || creatingCategory}
                                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed font-bold shadow-lg shadow-emerald-500/20 transition-all"
                            >
                                {creatingCategory ? (
                                    <>
                                        <span className="animate-spin material-symbols-outlined text-[18px]">progress_activity</span>
                                        Guardando...
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined text-[18px]">{editingCategoryId ? 'save' : 'check'}</span>
                                        {editingCategoryId ? 'Guardar Cambios' : 'Crear Categoría'}
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
