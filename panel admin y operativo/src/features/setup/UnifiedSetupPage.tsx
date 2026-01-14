import { useState, useEffect, DragEvent, useRef } from 'react';
import { setupService, Product, Category, ProductModifier } from './setup.service';
import { useNavigate } from 'react-router-dom';
import {
    Search, Plus, Save, Info,
    ChefHat, UtensilsCrossed,
    GripVertical, Package, ArrowLeft, CheckCircle2,
    Beer, Cookie, Camera
} from 'lucide-react';

// --- Types & Constants ---

type MacroType = 'HOME' | 'INSUMOS' | 'CARTA' | 'BEBIDAS' | 'EXTRAS';

interface RecipeItemRow {
    ingredientId: number;
    name: string;
    cost: number;
    quantity: number;
    unit: string;
}

const CARDS = [
    {
        id: 'INSUMOS',
        label: 'Insumos / Inventario',
        icon: Package,
        color: 'bg-emerald-100 text-emerald-700',
        desc: 'Cosas que compras para cocinar (Tomate, Harina).',
        categoryName: 'Materia Prima'
    },
    {
        id: 'CARTA',
        label: 'Plato de Carta',
        icon: UtensilsCrossed,
        color: 'bg-amber-100 text-amber-700',
        desc: 'Lo que el cliente ve en el menú (Hamburguesas).',
        hasRecipe: true
    },
    {
        id: 'BEBIDAS',
        label: 'Bebidas',
        icon: Beer,
        color: 'bg-blue-100 text-blue-700',
        desc: 'Productos listos para vender (Gaseosas).',
        hasRecipe: false
    },
    {
        id: 'EXTRAS',
        label: 'Extras / Adiciones',
        icon: Cookie,
        color: 'bg-purple-100 text-purple-700',
        desc: 'Opciones adicionales (Queso extra).',
        hasRecipe: false
    }
];

export const UnifiedSetupPage = () => {
    const navigate = useNavigate();

    // --- Global State ---
    const [viewMode, setViewMode] = useState<MacroType>('HOME');

    // --- Data State ---
    const [categories, setCategories] = useState<Category[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [ingredients, setIngredients] = useState<Product[]>([]);
    const [modifiers, setModifiers] = useState<ProductModifier[]>([]);

    // --- Selection State ---
    const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [selectedModifier, setSelectedModifier] = useState<ProductModifier | null>(null);

    // --- Form State ---
    const [isCreatingCategory, setIsCreatingCategory] = useState(false);
    const [newCategoryName, setNewCategoryName] = useState('');

    const [productForm, setProductForm] = useState({
        name: '',
        price: '', // Venta para Carta, Costo para Insumo
        stock: '0',
        unit: 'unidad', // Solo insumo
        description: '',
        hasRecipe: false,
        image_url: ''
    });

    const [modifierForm, setModifierForm] = useState({
        name: '',
        description: '',
        extra_price: '0'
    });

    const [recipeItems, setRecipeItems] = useState<RecipeItemRow[]>([]);
    const [pantrySearch, setPantrySearch] = useState('');
    const [margin, setMargin] = useState(30);

    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // --- Image Upload ---
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const url = await setupService.uploadImage(file);
            setProductForm(prev => ({ ...prev, image_url: url }));
        } catch (error) {
            console.error(error);
            alert("Error al subir imagen");
        }
    };

    // --- Init ---
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setIsLoading(true);
        try {
            await setupService.ensureIngredientCategory(); // Guarantee consistency
            const [cats, prods, mods] = await Promise.all([
                setupService.getCategories(),
                setupService.getProducts(),
                setupService.getModifiers()
            ]);
            setCategories(cats);
            setProducts(prods);
            setModifiers(mods);

            // Extract ingredients for Pantry
            const ingCat = cats.find(c => c.name === 'Materia Prima');
            if (ingCat) {
                setIngredients(prods.filter(p => p.category_id === ingCat.id));
            }
        } catch (e) {
            console.error(e);
            alert("Error conectando con el servidor");
        } finally {
            setIsLoading(false);
        }
    };

    // --- Logic ---

    const handleSelectMacro = (type: string) => {
        setViewMode(type as MacroType);
        setSelectedCategory(null);
        setSelectedProduct(null);
        setSelectedModifier(null); // Reset modifier

        // Auto-config based on type
        if (type === 'INSUMOS') {
            const matPrima = categories.find(c => c.name === 'Materia Prima');
            if (matPrima) handleSelectCategory(matPrima);
        } else if (type === 'EXTRAS') {
            // Extras doesn't need category selection, goes straight to list
            handleNewModifier();
        } else {
            // For others, we wait for user to select a category
            // Maybe filter categories visually? 
            setProductForm(prev => ({ ...prev, hasRecipe: type === 'CARTA' }));
        }
    };



    const handleSelectCategory = (cat: Category) => {
        setSelectedCategory(cat);
        setSelectedProduct(null);
        handleNewProduct(); // Reset form
    };

    const handleSelectProduct = (prod: Product) => {
        setSelectedProduct(prod);
        setProductForm({
            name: prod.name,
            price: prod.price.toString(),
            stock: prod.stock?.toString() || '0',
            unit: 'unidad', // TODO: Load from backend if supported
            description: prod.description || '',
            hasRecipe: viewMode === 'CARTA', // Default assumption
            image_url: prod.image_url || ''
        });

        // TODO: Load recipe items if exists
        setRecipeItems([]);
    };

    const handleNewProduct = () => {
        setSelectedProduct(null);
        setProductForm({
            name: '',
            price: '',
            stock: '0',
            unit: 'unidad',
            description: '',
            hasRecipe: viewMode === 'CARTA',
            image_url: ''
        });
        setRecipeItems([]);
    };

    // --- Modifier Logic ---
    const handleSelectModifier = (mod: ProductModifier) => {
        setSelectedModifier(mod);
        setModifierForm({
            name: mod.name,
            description: mod.description || '',
            extra_price: mod.extra_price.toString()
        });
        // Load recipe items
        if (mod.recipe_items) {
            setRecipeItems(mod.recipe_items.map(item => ({
                ingredientId: item.ingredient_product_id,
                name: item.ingredient?.name || `Ingrediente ${item.ingredient_product_id}`, // Backend should expand this or we look it up
                cost: 0, // We need to look up cost from ingredients list
                quantity: item.quantity,
                unit: item.unit
            })));
        } else {
            setRecipeItems([]);
        }
    };

    const handleNewModifier = () => {
        setSelectedModifier(null);
        setModifierForm({
            name: '',
            description: '',
            extra_price: '0'
        });
        setRecipeItems([]);
    };



    // We need to patch recipeItems loading to include correct name/cost
    useEffect(() => {
        if (selectedModifier && selectedModifier.recipe_items) {
            const items = selectedModifier.recipe_items.map(item => {
                const ing = ingredients.find(i => i.id === item.ingredient_product_id);
                return {
                    ingredientId: item.ingredient_product_id,
                    name: ing ? ing.name : 'Desconocido',
                    cost: ing ? ing.price : 0,
                    quantity: item.quantity,
                    unit: item.unit
                };
            });
            setRecipeItems(items);
        }
    }, [selectedModifier, ingredients]); // Re-run when modifiers selected or ingredients loaded


    const handleCreateCategory = async () => {
        if (!newCategoryName) return;
        setIsLoading(true);
        try {
            // Determine Tag
            let tag = '';
            if (viewMode === 'INSUMOS') tag = '#INSUMO';
            if (viewMode === 'CARTA') tag = '#CARTA';
            if (viewMode === 'BEBIDAS') tag = '#BEBIDAS';
            if (viewMode === 'EXTRAS') tag = '#EXTRAS';

            // Check for existing category (Case Insensitive)
            const existingCat = categories.find(c => c.name.toLowerCase() === newCategoryName.toLowerCase());

            if (existingCat) {
                // If exists, checks if it already has the tag
                const currentDesc = existingCat.description || '';
                if (!currentDesc.includes(tag)) {
                    // Update with new tag appended
                    const updatedDesc = currentDesc ? `${currentDesc} ${tag}` : tag;
                    const updatedCat = await setupService.updateCategory(existingCat.id, { description: updatedDesc });

                    setCategories(categories.map(c => c.id === updatedCat.id ? updatedCat : c));
                    handleSelectCategory(updatedCat);
                    alert(`⚠️ Categoría existente detectada. Se ha vinculado a ${viewMode}.`);
                } else {
                    handleSelectCategory(existingCat);
                    alert(`ℹ️ Esta categoría ya existe en ${viewMode}.`);
                }
            } else {
                // Create New if not exists
                const newCat = await setupService.createCategory(newCategoryName, tag);
                setCategories([...categories, newCat]);
                handleSelectCategory(newCat);
            }

            setNewCategoryName('');
            setIsCreatingCategory(false);
        } catch (e) {
            console.error(e);
            alert("Error procesando categoría.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveModifier = async () => {
        if (!modifierForm.name) return;
        setIsSaving(true);
        try {
            let modifier: ProductModifier;
            const payload = {
                name: modifierForm.name,
                description: modifierForm.description,
                extra_price: parseFloat(modifierForm.extra_price) || 0,
                company_id: 1 // TODO
            };

            if (selectedModifier) {
                // Update
                modifier = await setupService.updateModifier(selectedModifier.id, payload);
                // Update Recipe
                if (recipeItems.length > 0 || selectedModifier.recipe_items?.length) {
                    await setupService.updateModifierRecipe(modifier.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
                }
                alert("Modificador actualizado");
            } else {
                // Create
                modifier = await setupService.createModifier(payload);
                // Create Recipe
                if (recipeItems.length > 0) {
                    await setupService.updateModifierRecipe(modifier.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
                }
                alert("Modificador creado");
            }

            // Reload modifiers
            const mods = await setupService.getModifiers();
            setModifiers(mods);
            handleNewModifier();

        } catch (e) {
            console.error(e);
            alert("Error guardando modificador");
        } finally {
            setIsSaving(false);
        }
    };

    const handleSave = async () => {
        if (!selectedCategory || !productForm.name) return;
        setIsSaving(true);
        try {
            const priceVal = parseFloat(productForm.price) || 0;
            const isIngredient = viewMode === 'INSUMOS';

            // 1. Create/Update Product
            let product: Product;
            const payload = {
                name: productForm.name,
                price: priceVal,
                stock: parseFloat(productForm.stock) || 0,
                category_id: selectedCategory.id,
                description: isIngredient ? 'Ingrediente' : productForm.description,
                ...(isIngredient && { unit: productForm.unit }), // Add unit if ingredient
                image_url: productForm.image_url
            };

            if (selectedProduct) {
                // UPDATE
                product = await setupService.updateProduct(selectedProduct.id, payload);

                // Update local state
                setProducts(products.map(p => p.id === product.id ? product : p));
                if (isIngredient) {
                    setIngredients(ingredients.map(i => i.id === product.id ? product : i));
                }

                alert(`✅ Producto actualizado: ${product.name}`);
            } else {
                // CREATE
                if (isIngredient) {
                    product = await setupService.createIngredient(payload);
                    setIngredients([...ingredients, product]);
                } else {
                    product = await setupService.createProduct(payload);
                }
                setProducts([...products, product]);
                alert(`✅ Producto creado: ${product.name}`);
            }

            // 2. Create/Update Recipe if needed (Only on Create for now or Rewrite?)
            // TODO: Implement Recipe Update logic. For now, we only create recipes for new items or append?
            // Current limitation: We rewrite recipe if it exists? Backend handles it?
            // Let's assume for now we only handle product fields update.
            if (!isIngredient && productForm.hasRecipe && recipeItems.length > 0) {
                // Check if recipe exists
                const existingRecipe = await setupService.getRecipeByProduct(product.id);

                if (existingRecipe) {
                    await setupService.updateRecipeItems(existingRecipe.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
                    // console.log("Receta actualizada");
                } else {
                    await setupService.createRecipe({
                        product_id: product.id,
                        name: `Receta de ${product.name}`,
                        description: 'Receta creada desde el panel de Ingeniería de Menú',
                        items: recipeItems.map(i => ({
                            ingredient_product_id: i.ingredientId,
                            quantity: i.quantity,
                            unit: i.unit
                        }))
                    });
                    // console.log("Receta creada");
                }
            }

            // await loadData(); // No need to reload everything if we update local state
            // But for safety initially let's keep it or optimize?
            // Optimized above.

            // Reset form
            handleNewProduct();

        } catch (e: any) {
            console.error(e);
            const msg = e.response?.data?.detail || "Error al guardar. Verifique los datos.";
            alert(`❌ Error: ${msg}`);
        } finally {
            setIsSaving(false);
        }
    };

    // --- Drag & Drop Recipe ---
    const handleDragStart = (e: DragEvent<HTMLDivElement>, ingredient: Product) => {
        e.dataTransfer.setData('json', JSON.stringify(ingredient));
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const data = e.dataTransfer.getData('json');
        if (data) addRecipeItem(JSON.parse(data));
    };

    const addRecipeItem = (ing: Product) => {
        if (recipeItems.find(i => i.ingredientId === ing.id)) return;
        setRecipeItems([...recipeItems, {
            ingredientId: ing.id,
            name: ing.name,
            cost: ing.price || 0,
            quantity: 1,
            unit: 'unidad'
        }]);
    };

    // --- Render Helpers ---
    const filteredProducts = products.filter(p => selectedCategory && p.category_id === selectedCategory.id);

    const recipeCost = recipeItems.reduce((sum, item) => sum + (item.cost * item.quantity), 0);
    const visualMargin = productForm.price ? ((parseFloat(productForm.price) - recipeCost) / parseFloat(productForm.price)) * 100 : 0;

    // --- HOME VIEW ---
    if (viewMode === 'HOME') {
        return (
            <div className="min-h-screen bg-gray-50 p-8 flex flex-col items-center justify-center font-sans">
                <div className="max-w-4xl w-full text-center">
                    <div className="w-16 h-16 bg-amber-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-amber-500/20">
                        <ChefHat size={32} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">Ingeniería de Menú</h1>
                    <p className="text-gray-500 mb-12">¿Qué deseas ingresar al sistema hoy?</p>

                    <div className="grid grid-cols-2 gap-6">
                        {CARDS.map(card => {
                            const Icon = card.icon;
                            return (
                                <button
                                    key={card.id}
                                    onClick={() => handleSelectMacro(card.id)}
                                    className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:scale-[1.02] transition-all text-left group"
                                >
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${card.color}`}>
                                        <Icon size={24} />
                                    </div>
                                    <h3 className="text-xl font-bold text-gray-800 mb-1 group-hover:text-amber-600 transition-colors">
                                        {card.label}
                                    </h3>
                                    <p className="text-sm text-gray-400">
                                        {card.desc}
                                    </p>
                                </button>
                            )
                        })}
                    </div>
                    <button onClick={() => navigate('/admin/dashboard')} className="mt-12 text-sm text-gray-400 hover:text-gray-600">
                        Volver al Dashboard
                    </button>
                </div>
            </div>
        );
    }

    // --- WORKSTATION VIEW (The 3-Pane Layout) ---
    return (
        <div className="h-screen flex text-gray-800 bg-gray-50 overflow-hidden font-sans">

            {/* PANE 1: NAVIGATION & CATEGORIES */}
            <aside className="w-64 bg-white border-r border-gray-200 flex flex-col z-20 shadow-md">
                <div className="p-4 border-b border-gray-100 flex items-center gap-3">
                    <button onClick={() => setViewMode('HOME')} className="p-2 hover:bg-gray-100 rounded-lg">
                        <ArrowLeft size={20} className="text-gray-500" />
                    </button>
                    <div>
                        <h2 className="font-bold text-gray-800 text-sm leading-tight">
                            {CARDS.find(c => c.id === viewMode)?.label}
                        </h2>
                        <p className="text-xs text-gray-400">Selector de Categoría</p>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3">
                    {/* Category List */}
                    {viewMode === 'INSUMOS' ? (
                        <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100 text-emerald-800 text-sm font-bold flex items-center gap-2">
                            <CheckCircle2 size={16} /> Materia Prima
                        </div>
                    ) : (
                        <>
                            <div className="space-y-1">
                                {categories
                                    .filter(c => {
                                        // LOGIC: Filter by ViewMode Tag
                                        if (viewMode === 'CARTA') return c.description?.includes('#CARTA');
                                        if (viewMode === 'BEBIDAS') return c.description?.includes('#BEBIDAS');
                                        if (viewMode === 'EXTRAS') return c.description?.includes('#EXTRAS');
                                        return false;
                                    })
                                    .map(cat => (
                                        <button
                                            key={cat.id}
                                            onClick={() => handleSelectCategory(cat)}
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors
                                            ${selectedCategory?.id === cat.id
                                                    ? 'bg-gray-800 text-white shadow-lg shadow-gray-800/20'
                                                    : 'text-gray-500 hover:bg-gray-100'}
                                        `}
                                        >
                                            {cat.name}
                                        </button>
                                    ))}
                            </div>

                            {/* Create Category */}
                            {isCreatingCategory ? (
                                <div className="mt-4 p-2 bg-gray-50 rounded-lg border border-gray-200">
                                    <input
                                        autoFocus
                                        className="w-full text-sm bg-white border border-gray-300 rounded p-1.5 mb-2 outline-none"
                                        placeholder="Nombre..."
                                        value={newCategoryName}
                                        onChange={e => setNewCategoryName(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleCreateCategory()}
                                    />
                                    <button onClick={handleCreateCategory} className="w-full bg-gray-800 text-white text-xs py-1.5 rounded">
                                        Crear
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setIsCreatingCategory(true)}
                                    className="w-full mt-4 py-2 border border-dashed border-gray-300 rounded-lg text-xs text-gray-400 hover:border-amber-400 hover:text-amber-500 transition-colors flex items-center justify-center gap-1"
                                >
                                    <Plus size={14} /> Nueva Categoría
                                </button>
                            )}
                        </>
                    )}
                </div>
            </aside>

            {/* PANE 2: LISTER */}
            <section className="w-72 bg-gray-50/50 border-r border-gray-200 flex flex-col">
                <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                    <h3 className="font-bold text-gray-700 text-sm">
                        {viewMode === 'EXTRAS' ? 'Mis Extras' : (selectedCategory ? selectedCategory.name : 'Seleccione Categoría')}
                    </h3>
                    <button onClick={viewMode === 'EXTRAS' ? handleNewModifier : handleNewProduct} className="text-amber-600 hover:bg-amber-100 p-1.5 rounded-lg transition-colors">
                        <Plus size={18} />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2">
                    {viewMode === 'EXTRAS' ? (
                        modifiers.map(m => (
                            <div
                                key={m.id}
                                onClick={() => handleSelectModifier(m)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md
                                    ${selectedModifier?.id === m.id
                                        ? 'bg-white border-purple-400 shadow-md ring-1 ring-purple-100'
                                        : 'bg-white border-gray-100 hover:border-purple-200'}
                                `}
                            >
                                <div className="flex justify-between">
                                    <span className="font-bold text-sm text-gray-700">{m.name}</span>
                                    <span className="text-xs bg-purple-50 px-1.5 py-0.5 rounded text-purple-700">+${m.extra_price}</span>
                                </div>
                            </div>
                        ))
                    ) : (
                        filteredProducts.map(p => (
                            <div
                                key={p.id}
                                onClick={() => handleSelectProduct(p)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md
                                ${selectedProduct?.id === p.id
                                        ? 'bg-white border-amber-400 shadow-md ring-1 ring-amber-100'
                                        : 'bg-white border-gray-100 hover:border-amber-200'}
                            `}
                            >
                                <div className="flex justify-between">
                                    <span className="font-bold text-sm text-gray-700">{p.name}</span>
                                    <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">${p.price}</span>
                                </div>
                            </div>
                        )))}
                </div>
            </section>

            {/* PANE 3: EDITOR (The Core) */}
            <main className="flex-1 bg-white relative flex flex-col">
                {!selectedCategory && viewMode !== 'EXTRAS' ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-300">
                        <Info size={48} className="mb-2 opacity-50" />
                        <p>Seleccione una categoría para comenzar</p>
                    </div>
                ) : (
                    <>
                        {/* Header/Form */}
                        <div className="p-6 border-b border-gray-100 bg-white z-10">
                            {viewMode === 'EXTRAS' ? (
                                // --- MODIFIER FORM HEADER ---
                                <>
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <span className="text-xs font-bold text-purple-600 uppercase tracking-wider">
                                                Definiendo Modificador
                                            </span>
                                            <div className="flex gap-4 items-center mt-2">
                                                <div className="flex gap-2 flex-1">
                                                    <input
                                                        className="block text-2xl font-bold text-gray-900 border-none p-0 focus:ring-0 placeholder-gray-300 w-full"
                                                        placeholder="Ej. Queso Extra"
                                                        value={modifierForm.name}
                                                        onChange={e => setModifierForm({ ...modifierForm, name: e.target.value })}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleSaveModifier}
                                            disabled={!modifierForm.name || isSaving}
                                            className="bg-purple-600 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-purple-500/20 hover:bg-purple-700 transition-all flex items-center gap-2 disabled:opacity-50 disabled:grayscale"
                                        >
                                            <Save size={18} /> {isSaving ? 'Guardando...' : 'Guardar Extra'}
                                        </button>
                                    </div>
                                    <div className="flex gap-6">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-gray-400">Precio Extra ($)</label>
                                            <input
                                                type="number"
                                                className="block w-32 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 font-bold text-gray-700 outline-none focus:border-purple-400"
                                                value={modifierForm.extra_price}
                                                onChange={e => setModifierForm({ ...modifierForm, extra_price: e.target.value })}
                                            />
                                        </div>
                                        <div className="flex items-center pt-5 pl-4 border-l border-gray-100 text-xs text-gray-400">
                                            Describe la "Mini Receta" de este extra abajo.
                                        </div>
                                    </div>
                                </>
                            ) : (
                                // --- PRODUCT FORM HEADER ---
                                <>
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">
                                                {viewMode === 'INSUMOS' ? 'Definiendo Insumo' : 'Definiendo Producto'}
                                            </span>
                                            <div className="flex gap-4 items-center">
                                                {/* Image Uploader */}
                                                <div
                                                    className="w-16 h-16 rounded-xl border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:border-amber-400 hover:bg-amber-50 relative overflow-hidden group transition-all"
                                                    onClick={() => fileInputRef.current?.click()}
                                                >
                                                    {productForm.image_url ? (
                                                        <img
                                                            src={productForm.image_url}
                                                            alt="Preview"
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <Camera size={24} className="text-gray-300 group-hover:text-amber-500" />
                                                    )}
                                                    <input
                                                        type="file"
                                                        ref={fileInputRef}
                                                        className="hidden"
                                                        accept="image/*"
                                                        onChange={handleFileChange}
                                                    />
                                                    {productForm.image_url && (
                                                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <Camera size={16} className="text-white" />
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Inputs */}
                                                <div className="flex gap-2 flex-1">
                                                    <input
                                                        className="block text-2xl font-bold text-gray-900 border-none p-0 focus:ring-0 placeholder-gray-300 w-full"
                                                        placeholder={viewMode === 'INSUMOS' ? "Ej. Carne Molida" : "Ej. Hamburguesa Royal"}
                                                        value={productForm.name}
                                                        onChange={e => setProductForm({ ...productForm, name: e.target.value })}
                                                    />
                                                    {viewMode === 'INSUMOS' && (
                                                        <select
                                                            className="bg-gray-100 border-none rounded-lg text-sm font-bold text-gray-600 px-3 outline-none focus:ring-2 focus:ring-amber-400"
                                                            value={productForm.unit}
                                                            onChange={e => setProductForm({ ...productForm, unit: e.target.value })}
                                                        >
                                                            <option value="unidad">Unidad</option>
                                                            <option value="kg">Kilo (Kg)</option>
                                                            <option value="gr">Gramo (Gr)</option>
                                                            <option value="lt">Litro (Lt)</option>
                                                            <option value="ml">Mililitro (Ml)</option>
                                                        </select>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleSave}
                                            disabled={!productForm.name || isSaving}
                                            className="bg-amber-500 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-amber-500/20 hover:bg-amber-600 transition-all flex items-center gap-2 disabled:opacity-50 disabled:grayscale"
                                        >
                                            <Save size={18} /> {isSaving ? 'Guardando...' : 'Guardar'}
                                        </button>
                                    </div>

                                    <div className="flex gap-6">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-gray-400">
                                                {viewMode === 'INSUMOS' ? 'Costo Unitario ($)' : 'Precio Venta ($)'}
                                            </label>
                                            <div className="relative group">
                                                <input
                                                    type="number"
                                                    className="block w-32 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 font-bold text-gray-700 outline-none focus:border-amber-400"
                                                    value={productForm.price}
                                                    onChange={e => setProductForm({ ...productForm, price: e.target.value })}
                                                />
                                                {viewMode === 'INSUMOS' && (
                                                    <div className="absolute top-full left-0 mt-2 w-48 p-2 bg-gray-800 text-white text-[10px] rounded shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-20">
                                                        Ingresa el costo por la UNIDAD que usarás en las recetas (Ej: Costo de 1 Kg, 1 Lt, o 1 Unidad).
                                                    </div>
                                                )}
                                            </div>
                                            {viewMode === 'INSUMOS' && (
                                                <p className="text-[10px] text-amber-600 font-medium max-w-[150px] leading-tight pt-1">
                                                    *Costo por {productForm.unit || 'unidad'}
                                                </p>
                                            )}
                                        </div>

                                        {/* Stock Logic: Show for Insumos OR (Non-Carta Items without Recipe) */}
                                        {(viewMode === 'INSUMOS' || (viewMode !== 'CARTA' && !productForm.hasRecipe)) && (
                                            <div className="space-y-1 animate-in fade-in">
                                                <label className="text-xs font-bold text-gray-400">
                                                    Stock Inicial
                                                </label>
                                                <input
                                                    type="number"
                                                    className="block w-32 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 font-bold text-gray-700 outline-none focus:border-amber-400"
                                                    value={productForm.stock}
                                                    onChange={e => setProductForm({ ...productForm, stock: e.target.value })}
                                                />
                                            </div>
                                        )}

                                        {viewMode === 'CARTA' && (
                                            <div className="flex items-center pt-5 pl-4 border-l border-gray-100">
                                                <div className="text-xs text-gray-400 max-w-[150px]">
                                                    <strong className="block text-amber-600">Sin Stock Directo</strong>
                                                    La disponibilidad depende de los insumos.
                                                </div>
                                            </div>
                                        )}

                                        {viewMode !== 'INSUMOS' && (
                                            <div className="flex items-center pt-5 ml-auto">
                                                <label className="flex items-center gap-2 cursor-pointer select-none">
                                                    <div className={`w-10 h-6 rounded-full p-1 transition-colors ${productForm.hasRecipe ? 'bg-amber-500' : 'bg-gray-200'}`}
                                                        onClick={() => setProductForm({ ...productForm, hasRecipe: !productForm.hasRecipe })}
                                                    >
                                                        <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${productForm.hasRecipe ? 'translate-x-4' : 'translate-x-0'}`} />
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-600">Tiene Receta</span>
                                                </label>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>

                        {/* RECIPE BUILDER BODY */}
                        {/* Show if it has Recipe (Products) OR is Extra (Modifiers always have recipe ability) */}
                        {((productForm.hasRecipe && viewMode !== 'INSUMOS' && viewMode !== 'EXTRAS') || (viewMode === 'EXTRAS')) && (
                            <div className="flex-1 flex overflow-hidden">
                                {/* Pantry (Left) */}
                                <div className="w-72 bg-gray-50 border-r border-gray-200 flex flex-col">
                                    <div className="p-3 border-b border-gray-200 bg-gray-100/50">
                                        <h4 className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2">
                                            <Search size={14} /> La Despensa
                                        </h4>
                                        <input
                                            className="w-full mt-2 text-sm bg-white border border-gray-200 rounded px-2 py-1.5 focus:border-amber-400 outline-none"
                                            placeholder="Buscar insumo..."
                                            value={pantrySearch}
                                            onChange={e => setPantrySearch(e.target.value)}
                                        />
                                    </div>
                                    <div className="flex-1 overflow-y-auto p-2 space-y-2">
                                        {ingredients.filter(i => i.name.toLowerCase().includes(pantrySearch.toLowerCase())).map(ing => (
                                            <div
                                                key={ing.id}
                                                draggable
                                                onDragStart={e => handleDragStart(e, ing)}
                                                onClick={() => addRecipeItem(ing)}
                                                className="bg-white border border-gray-200 p-2.5 rounded-lg shadow-sm hover:border-amber-400 cursor-grab active:cursor-grabbing flex justify-between items-center group select-none"
                                            >
                                                <div>
                                                    <p className="font-bold text-sm text-gray-700">{ing.name}</p>
                                                    <p className="text-xs text-green-600 font-mono">${ing.price}</p>
                                                </div>
                                                <GripVertical size={16} className="text-gray-300 group-hover:text-amber-500" />
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Builder (Right) */}
                                <div
                                    className="flex-1 flex flex-col bg-amber-50/20"
                                    onDragOver={e => e.preventDefault()}
                                    onDrop={handleDrop}
                                >
                                    <div className="flex-1 overflow-y-auto p-6">
                                        {recipeItems.length === 0 ? (
                                            <div className="h-full border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center text-gray-400">
                                                <UtensilsCrossed size={48} className="mb-4 opacity-20" />
                                                <p className="font-medium">Arrastra ingredientes aquí para armar el plato</p>
                                            </div>
                                        ) : (
                                            <div className="space-y-3">
                                                {recipeItems.map((item, idx) => (
                                                    <div key={idx} className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex items-center gap-4 animate-in slide-in-from-bottom-2">
                                                        <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold">
                                                            {idx + 1}
                                                        </span>
                                                        <div className="flex-1">
                                                            <p className="font-bold text-gray-800">{item.name}</p>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <input
                                                                type="number" className="w-20 bg-gray-50 border border-gray-200 rounded px-2 py-1 text-sm font-bold text-center"
                                                                value={item.quantity}
                                                                onChange={e => {
                                                                    const copy = [...recipeItems];
                                                                    copy[idx].quantity = parseFloat(e.target.value) || 0;
                                                                    setRecipeItems(copy);
                                                                }}
                                                            />
                                                            <select
                                                                className="text-xs bg-transparent text-gray-500 outline-none"
                                                                value={item.unit}
                                                                onChange={e => {
                                                                    const copy = [...recipeItems];
                                                                    copy[idx].unit = e.target.value;
                                                                    setRecipeItems(copy);
                                                                }}
                                                            >
                                                                <option value="unidad">un</option>
                                                                <option value="kg">kg</option>
                                                                <option value="gr">gr</option>
                                                                <option value="lt">lt</option>
                                                            </select>
                                                        </div>
                                                        <div className="text-right min-w-[80px]">
                                                            <p className="font-bold text-gray-700">${(item.cost * item.quantity).toFixed(2)}</p>
                                                            <button onClick={() => setRecipeItems(recipeItems.filter((_, i) => i !== idx))} className="text-xs text-red-400 hover:text-red-600">Quitar</button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Footer Analysis */}
                                    <div className="bg-white border-t border-gray-200 p-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex gap-8">
                                                <div>
                                                    <p className="text-xs text-gray-400 uppercase font-bold">Costo Ingredientes</p>
                                                    <p className="text-xl font-bold text-gray-800">${recipeCost.toFixed(2)}</p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-400 uppercase font-bold">Margen Real</p>
                                                    <p className={`text-xl font-bold ${visualMargin < 30 ? 'text-red-500' : 'text-green-600'}`}>
                                                        {visualMargin.toFixed(1)}%
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs text-green-600 font-medium">
                                                    {visualMargin > 50 ? '¡Excelente Margen!' : visualMargin < 20 ? 'Margen Crítico' : 'Buen Margen'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* INSUMO EXPLANATION */}
                        {viewMode === 'INSUMOS' && (
                            <div className="flex-1 flex flex-col items-center justify-center bg-emerald-50/30 p-8 text-center">
                                <Package size={64} className="text-emerald-200 mb-4" />
                                <h3 className="text-xl font-bold text-emerald-900">Gestión de Insumos</h3>
                                <p className="text-emerald-700/60 max-w-md">
                                    Aquí defines los costos de tus materias primas. Estos valores se usarán automáticamente para calcular la rentabilidad de tus platos.
                                </p>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
};
