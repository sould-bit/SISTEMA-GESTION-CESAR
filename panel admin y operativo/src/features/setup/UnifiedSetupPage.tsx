import { useState, useEffect, DragEvent, useRef } from 'react';
import { setupService, Product, Category, ProductModifier } from './setup.service';
import { useNavigate } from 'react-router-dom';
import {
    Search, Plus, Save, Info,
    ChefHat, UtensilsCrossed,
    GripVertical, Package, ArrowLeft, CheckCircle2,
    Beer, Cookie, Camera, ArrowRight, LayoutGrid
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

// ✨ UX UPGRADE: Paletas de color semánticas ADAPTADAS A DARK THEME
const CARDS = [
    {
        id: 'INSUMOS',
        label: 'Despensa & Insumos',
        icon: Package,
        color: 'text-emerald-400',
        bgIcon: 'bg-emerald-500/10',
        border: 'hover:border-emerald-500/50',
        ring: 'group-hover:ring-emerald-500/20',
        gradient: 'from-emerald-500/5 to-transparent',
        desc: 'Gestiona la materia prima base. Costos, stock y unidades de medida.',
        categoryName: 'Materia Prima'
    },
    {
        id: 'CARTA',
        label: 'Platos de Carta',
        icon: UtensilsCrossed,
        color: 'text-amber-400',
        bgIcon: 'bg-amber-500/10',
        border: 'hover:border-amber-500/50',
        ring: 'group-hover:ring-amber-500/20',
        gradient: 'from-amber-500/5 to-transparent',
        desc: 'Diseña tus productos finales, asigna recetas y define precios de venta.',
        hasRecipe: true
    },
    {
        id: 'BEBIDAS',
        label: 'Bebidas & Cafetería',
        icon: Beer,
        color: 'text-blue-400',
        bgIcon: 'bg-blue-500/10',
        border: 'hover:border-blue-500/50',
        ring: 'group-hover:ring-blue-500/20',
        gradient: 'from-blue-500/5 to-transparent',
        desc: 'Productos directos listos para la venta sin receta compleja.',
        hasRecipe: false
    },
    {
        id: 'EXTRAS',
        label: 'Modificadores & Extras',
        icon: Cookie,
        color: 'text-purple-400',
        bgIcon: 'bg-purple-500/10',
        border: 'hover:border-purple-500/50',
        ring: 'group-hover:ring-purple-500/20',
        gradient: 'from-purple-500/5 to-transparent',
        desc: 'Adicionales, salsas y opciones personalizables para tus platos.',
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
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
            const ingCat = cats.find(c => c.name.toLowerCase() === 'materia prima');
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
            const matPrima = categories.find(c => c.name.toLowerCase() === 'materia prima');
            if (matPrima) {
                handleSelectCategory(matPrima);
            } else {
                // If not found in state yet, try reloading
                loadData().then(() => {
                    // We need to fetch from state REF or wait, but state won't update immediately.
                    // Ideally we just wait for user to click retry or rely on useEffect if we added one.
                });
            }
        } else if (type === 'EXTRAS') {
            // Extras doesn't need category selection, goes straight to list
            handleNewModifier();
        } else {
            // For others, we wait for user to select a category
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
                name: item.ingredient?.name || `Ingrediente ${item.ingredient_product_id}`,
                cost: 0,
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
    }, [selectedModifier, ingredients]);

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
                const currentDesc = existingCat.description || '';
                if (!currentDesc.includes(tag)) {
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
                modifier = await setupService.updateModifier(selectedModifier.id, payload);
                if (recipeItems.length > 0 || selectedModifier.recipe_items?.length) {
                    await setupService.updateModifierRecipe(modifier.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
                }
                alert("Modificador actualizado");
            } else {
                modifier = await setupService.createModifier(payload);
                if (recipeItems.length > 0) {
                    await setupService.updateModifierRecipe(modifier.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
                }
                alert("Modificador creado");
            }
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
        if (!productForm.name) {
            alert("El nombre es requerido");
            return;
        }

        // Fallback for INSUMOS if selectedCategory is missing (e.g. case sensitivity race)
        let targetCat = selectedCategory;
        if (viewMode === 'INSUMOS' && !targetCat) {
            targetCat = categories.find(c => c.name.toLowerCase() === 'materia prima') || null;
        }

        if (!targetCat) {
            alert("Error crítica: No hay categoría seleccionada. Para Insumos, debe existir 'Materia Prima'. Recargue la página.");
            return;
        }

        setIsSaving(true);
        try {
            const priceVal = parseFloat(productForm.price) || 0;
            const isIngredient = viewMode === 'INSUMOS';

            let product: Product;
            const payload = {
                name: productForm.name,
                price: priceVal,
                stock: parseFloat(productForm.stock) || 0,
                category_id: targetCat.id,
                description: isIngredient ? 'Ingrediente' : productForm.description,
                ...(isIngredient && { unit: productForm.unit }),
                image_url: productForm.image_url
            };

            if (selectedProduct) {
                product = await setupService.updateProduct(selectedProduct.id, payload);
                setProducts(products.map(p => p.id === product.id ? product : p));
                if (isIngredient) {
                    setIngredients(ingredients.map(i => i.id === product.id ? product : i));
                }
                alert(`✅ Producto actualizado: ${product.name}`);
            } else {
                if (isIngredient) {
                    product = await setupService.createIngredient(payload);
                    setIngredients([...ingredients, product]);
                } else {
                    product = await setupService.createProduct(payload);
                }
                setProducts([...products, product]);
                alert(`✅ Producto creado: ${product.name}`);
            }

            if (!isIngredient && productForm.hasRecipe && recipeItems.length > 0) {
                const existingRecipe = await setupService.getRecipeByProduct(product.id);
                if (existingRecipe) {
                    await setupService.updateRecipeItems(existingRecipe.id, recipeItems.map(i => ({
                        ingredient_product_id: i.ingredientId,
                        quantity: i.quantity,
                        unit: i.unit
                    })));
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
                }
            }
            handleNewProduct();
        } catch (e: any) {
            console.error(e);
            const msg = e.response?.data?.detail || "Error al guardar. Verifique los datos.";
            alert(`❌ Error: ${msg}`);
        } finally {
            setIsSaving(false);
        }
    };

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

    const filteredProducts = products.filter(p => selectedCategory && p.category_id === selectedCategory.id);
    const recipeCost = recipeItems.reduce((sum, item) => sum + (item.cost * item.quantity), 0);
    const visualMargin = productForm.price ? ((parseFloat(productForm.price) - recipeCost) / parseFloat(productForm.price)) * 100 : 0;

    // --- ✨ UX REFACTOR: HOME VIEW - "THE DARK ATELIER" ---
    if (viewMode === 'HOME') {
        return (
            <div className="min-h-screen bg-bg-deep flex flex-col font-sans text-white relative overflow-hidden animate-in fade-in duration-500">
                {/* Background Blobs */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                    <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-accent-orange/5 rounded-full blur-[120px]"></div>
                    <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] bg-status-info/5 rounded-full blur-[100px]"></div>
                </div>

                {/* Header Section */}
                <div className="bg-card-dark border-b border-border-dark px-8 py-8 shadow-sm relative z-10">
                    <div className="max-w-6xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-accent-orange/10 rounded-2xl text-accent-orange shadow-lg shadow-accent-orange/10 border border-accent-orange/20">
                                <ChefHat size={32} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white tracking-tight">Ingeniería de Menú</h1>
                                <p className="text-text-muted">Centro de control de costos y recetas</p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/admin/dashboard')}
                            className="px-4 py-2 bg-bg-deep border border-border-dark text-text-muted hover:text-white hover:border-accent-orange/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
                        >
                            <LayoutGrid size={16} /> Dashboard
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 max-w-6xl mx-auto w-full p-8 relative z-10">
                    <div className="mb-8">
                        <h2 className="text-xl font-semibold text-white mb-2">¿Qué deseas gestionar hoy?</h2>
                        <p className="text-text-muted max-w-2xl">
                            Selecciona un módulo para configurar tu restaurante. Recuerda que los <span className="font-medium text-emerald-400">Insumos</span> son la base para calcular la rentabilidad de tu <span className="font-medium text-amber-400">Carta</span>.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {CARDS.map(card => {
                            const Icon = card.icon;
                            return (
                                <button
                                    key={card.id}
                                    onClick={() => handleSelectMacro(card.id)}
                                    className={`
                                        group relative overflow-hidden bg-card-dark p-6 rounded-2xl border border-border-dark 
                                        shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 text-left
                                        flex flex-col h-full ${card.border} ${card.ring} ring-1 ring-transparent
                                    `}
                                >
                                    {/* Icon Background Blob */}
                                    <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl ${card.gradient} rounded-bl-full opacity-30 transition-transform group-hover:scale-125`} />

                                    <div className="relative z-10 flex-1">
                                        <div className={`w-14 h-14 ${card.bgIcon} ${card.color} rounded-xl flex items-center justify-center mb-4 shadow-sm group-hover:scale-110 transition-transform border border-white/5`}>
                                            <Icon size={28} strokeWidth={1.5} />
                                        </div>

                                        <h3 className="text-xl font-bold text-white mb-2">
                                            {card.label}
                                        </h3>

                                        <p className="text-sm text-text-muted leading-relaxed">
                                            {card.desc}
                                        </p>
                                    </div>

                                    <div className="relative z-10 mt-6 flex items-center gap-2 text-sm font-bold text-gray-500 group-hover:text-white transition-colors">
                                        <span>Ingresar</span>
                                        <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </button>
                            )
                        })}
                    </div>
                </div>
            </div>
        );
    }

    // --- WORKSTATION VIEW (The 3-Pane Layout) ---
    return (
        <div className="h-screen flex text-gray-200 bg-bg-deep overflow-hidden font-sans">
            {/* PANE 1: NAVIGATION & CATEGORIES */}
            <aside className="w-64 bg-card-dark border-r border-border-dark flex flex-col z-20 shadow-xl">
                <div className="p-4 border-b border-border-dark flex items-center gap-3">
                    <button onClick={() => setViewMode('HOME')} className="p-2 hover:bg-bg-deep rounded-lg group text-text-muted hover:text-white transition-colors" title="Volver al menú principal">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h2 className="font-bold text-white text-sm leading-tight">
                            {CARDS.find(c => c.id === viewMode)?.label}
                        </h2>
                        <p className="text-xs text-text-muted">Selector de Categoría</p>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3">
                    {/* Category List */}
                    {viewMode === 'INSUMOS' ? (
                        <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400 text-sm font-bold flex items-center gap-2">
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
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all
                                            ${selectedCategory?.id === cat.id
                                                    ? 'bg-accent-orange text-white shadow-lg shadow-accent-orange/20 border border-orange-500'
                                                    : 'text-text-muted hover:bg-bg-deep hover:text-white'}
                                        `}
                                        >
                                            {cat.name}
                                        </button>
                                    ))}
                            </div>

                            {/* Create Category */}
                            {isCreatingCategory ? (
                                <div className="mt-4 p-2 bg-bg-deep rounded-lg border border-border-dark animate-in fade-in zoom-in-95">
                                    <input
                                        autoFocus
                                        className="w-full text-sm bg-card-dark border border-border-dark rounded p-1.5 mb-2 outline-none focus:border-accent-orange text-white placeholder-text-muted"
                                        placeholder="Nombre..."
                                        value={newCategoryName}
                                        onChange={e => setNewCategoryName(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleCreateCategory()}
                                    />
                                    <button onClick={handleCreateCategory} className="w-full bg-accent-orange text-white text-xs py-1.5 rounded hover:bg-orange-600 transition-colors font-bold">
                                        Crear
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setIsCreatingCategory(true)}
                                    className="w-full mt-4 py-2 border border-dashed border-border-dark rounded-lg text-xs text-text-muted hover:border-accent-orange hover:text-accent-orange transition-colors flex items-center justify-center gap-1"
                                >
                                    <Plus size={14} /> Nueva Categoría
                                </button>
                            )}
                        </>
                    )}
                </div>
            </aside>

            {/* PANE 2: LISTER */}
            <section className="w-72 bg-bg-deep border-r border-border-dark flex flex-col relative">
                {/* Background ambient */}
                <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent to-bg-deep z-0" />

                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-card-dark/80 backdrop-blur-md sticky top-0 z-10">
                    <h3 className="font-bold text-white text-sm">
                        {viewMode === 'EXTRAS' ? 'Mis Extras' : (selectedCategory ? selectedCategory.name : 'Seleccione Categoría')}
                    </h3>
                    <button onClick={viewMode === 'EXTRAS' ? handleNewModifier : handleNewProduct} className="text-accent-orange hover:bg-accent-orange/10 p-1.5 rounded-lg transition-colors">
                        <Plus size={18} />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2 z-0">
                    {viewMode === 'EXTRAS' ? (
                        modifiers.map(m => (
                            <div
                                key={m.id}
                                onClick={() => handleSelectModifier(m)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md
                                    ${selectedModifier?.id === m.id
                                        ? 'bg-purple-500/10 border-purple-500/40 shadow-md ring-1 ring-purple-500/20'
                                        : 'bg-card-dark border-border-dark hover:border-purple-500/30'}
                                `}
                            >
                                <div className="flex justify-between">
                                    <span className="font-bold text-sm text-gray-200">{m.name}</span>
                                    <span className="text-xs bg-purple-500/20 px-1.5 py-0.5 rounded text-purple-300 font-mono">+${m.extra_price}</span>
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
                                        ? 'bg-accent-orange/10 border-accent-orange/40 shadow-md ring-1 ring-accent-orange/20'
                                        : 'bg-card-dark border-border-dark hover:border-accent-orange/30'}
                            `}
                            >
                                <div className="flex justify-between">
                                    <span className="font-bold text-sm text-gray-200">{p.name}</span>
                                    <span className="text-xs bg-bg-deep px-1.5 py-0.5 rounded text-text-muted font-mono border border-border-dark">${p.price}</span>
                                </div>
                            </div>
                        )))}
                </div>
            </section>

            {/* PANE 3: EDITOR (The Core) */}
            <main className="flex-1 bg-bg-deep relative flex flex-col">
                {/* Decoration */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-orange/5 rounded-full blur-[120px] pointer-events-none"></div>

                {!selectedCategory && viewMode !== 'EXTRAS' ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                        <div className="w-20 h-20 bg-card-dark border border-border-dark rounded-full flex items-center justify-center mb-4">
                            <Info size={32} className="opacity-50" />
                        </div>
                        <p className="font-medium">Seleccione una categoría para comenzar</p>
                    </div>
                ) : (
                    <>
                        {/* Header/Form */}
                        <div className="p-6 border-b border-border-dark bg-card-dark z-10 shadow-lg">
                            {viewMode === 'EXTRAS' ? (
                                // --- MODIFIER FORM HEADER ---
                                <>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex-1">
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-purple-500/10 text-xs font-bold text-purple-400 uppercase tracking-wider mb-2 border border-purple-500/20">
                                                <Cookie size={12} /> Definiendo Modificador
                                            </span>
                                            <div className="flex gap-4 items-center mt-2">
                                                <div className="flex gap-2 flex-1">
                                                    <input
                                                        className="block text-2xl font-bold text-white bg-transparent border-none p-0 focus:ring-0 placeholder-gray-600 w-full"
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
                                    <div className="flex gap-6 items-end">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-gray-400">Precio Extra ($)</label>
                                            <input
                                                type="number"
                                                className="block w-32 bg-bg-deep border border-border-dark rounded-lg px-3 py-2 font-bold text-white outline-none focus:border-purple-400 transition-all"
                                                value={modifierForm.extra_price}
                                                onChange={e => setModifierForm({ ...modifierForm, extra_price: e.target.value })}
                                            />
                                        </div>
                                        <div className="flex items-center pb-2 pl-4 border-l border-border-dark text-xs text-gray-500">
                                            Describe la "Mini Receta" de este extra abajo.
                                        </div>
                                    </div>
                                </>
                            ) : (
                                // --- PRODUCT FORM HEADER ---
                                <>
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex-1">
                                            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider mb-2 border ${viewMode === 'INSUMOS' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                                                {viewMode === 'INSUMOS' ? <Package size={12} /> : <UtensilsCrossed size={12} />}
                                                {viewMode === 'INSUMOS' ? 'Definiendo Insumo' : 'Definiendo Producto'}
                                            </span>
                                            <div className="flex gap-4 items-center mt-1">
                                                {/* Image Uploader */}
                                                <div
                                                    className={`w-16 h-16 rounded-xl border-2 border-dashed flex items-center justify-center cursor-pointer relative overflow-hidden group transition-all shrink-0 bg-bg-deep
                                                        ${viewMode === 'INSUMOS' ? 'border-emerald-500/30 hover:border-emerald-500 hover:bg-emerald-500/10' : 'border-amber-500/30 hover:border-amber-500 hover:bg-amber-500/10'}
                                                    `}
                                                    onClick={() => fileInputRef.current?.click()}
                                                >
                                                    {productForm.image_url ? (
                                                        <img
                                                            src={productForm.image_url}
                                                            alt="Preview"
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <Camera size={24} className="text-gray-500 group-hover:text-white" />
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
                                                <div className="flex gap-2 flex-1 items-center">
                                                    <input
                                                        className="block text-2xl font-bold text-white bg-transparent border-none p-0 focus:ring-0 placeholder-gray-600 w-full"
                                                        placeholder={viewMode === 'INSUMOS' ? "Ej. Carne Molida" : "Ej. Hamburguesa Royal"}
                                                        value={productForm.name}
                                                        onChange={e => setProductForm({ ...productForm, name: e.target.value })}
                                                    />
                                                    {viewMode === 'INSUMOS' && (
                                                        <select
                                                            className="bg-bg-deep border border-border-dark rounded-lg text-sm font-bold text-gray-300 px-3 py-1 outline-none focus:border-emerald-500"
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
                                            className={`text-white px-6 py-2.5 rounded-xl font-bold shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:grayscale
                                                ${viewMode === 'INSUMOS'
                                                    ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20'
                                                    : 'bg-accent-orange hover:bg-orange-600 shadow-accent-orange/20'}
                                            `}
                                        >
                                            <Save size={18} /> {isSaving ? 'Guardando...' : 'Guardar'}
                                        </button>
                                    </div>

                                    <div className="flex gap-6 mt-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-gray-400">
                                                {viewMode === 'INSUMOS' ? 'Costo Unitario ($)' : 'Precio Venta ($)'}
                                            </label>
                                            <div className="relative group">
                                                <input
                                                    type="number"
                                                    className={`block w-32 bg-bg-deep border border-border-dark rounded-lg px-3 py-2 font-bold text-white outline-none transition-all
                                                        ${viewMode === 'INSUMOS' ? 'focus:border-emerald-500' : 'focus:border-accent-orange'}
                                                    `}
                                                    value={productForm.price}
                                                    onChange={e => setProductForm({ ...productForm, price: e.target.value })}
                                                />
                                            </div>
                                            {viewMode === 'INSUMOS' && (
                                                <p className="text-[10px] text-emerald-400 font-medium max-w-[150px] leading-tight pt-1">
                                                    *Costo por {productForm.unit || 'unidad'}
                                                </p>
                                            )}
                                        </div>

                                        {/* Stock Logic */}
                                        {(viewMode === 'INSUMOS' || (viewMode !== 'CARTA' && !productForm.hasRecipe)) && (
                                            <div className="space-y-1 animate-in fade-in">
                                                <label className="text-xs font-bold text-gray-400">
                                                    Stock Inicial
                                                </label>
                                                <input
                                                    type="number"
                                                    className="block w-32 bg-bg-deep border border-border-dark rounded-lg px-3 py-2 font-bold text-white outline-none focus:border-accent-orange"
                                                    value={productForm.stock}
                                                    onChange={e => setProductForm({ ...productForm, stock: e.target.value })}
                                                />
                                            </div>
                                        )}

                                        {viewMode === 'CARTA' && (
                                            <div className="flex items-center pt-5 pl-4 border-l border-border-dark">
                                                <div className="text-xs text-text-muted max-w-[150px]">
                                                    <strong className="block text-accent-orange">Sin Stock Directo</strong>
                                                    La disponibilidad depende de los insumos.
                                                </div>
                                            </div>
                                        )}

                                        {viewMode !== 'INSUMOS' && (
                                            <div className="flex items-center pt-5 ml-auto">
                                                <label className="flex items-center gap-2 cursor-pointer select-none group">
                                                    <div className={`w-10 h-6 rounded-full p-1 transition-colors ${productForm.hasRecipe ? 'bg-accent-orange' : 'bg-gray-700 group-hover:bg-gray-600'}`}
                                                        onClick={() => setProductForm({ ...productForm, hasRecipe: !productForm.hasRecipe })}
                                                    >
                                                        <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${productForm.hasRecipe ? 'translate-x-4' : 'translate-x-0'}`} />
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-400 group-hover:text-white transition-colors">Configurar Receta</span>
                                                </label>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>

                        {/* RECIPE BUILDER BODY */}
                        {((productForm.hasRecipe && viewMode !== 'INSUMOS' && viewMode !== 'EXTRAS') || (viewMode === 'EXTRAS')) && (
                            <div className="flex-1 flex overflow-hidden">
                                {/* Pantry (Left) */}
                                <div className="w-72 bg-bg-deep border-r border-border-dark flex flex-col">
                                    <div className="p-3 border-b border-border-dark bg-card-dark/50">
                                        <h4 className="text-xs font-bold text-text-muted uppercase flex items-center gap-2">
                                            <Search size={14} /> La Despensa
                                        </h4>
                                        <input
                                            className="w-full mt-2 text-sm bg-bg-deep border border-border-dark rounded-lg px-3 py-2 focus:border-accent-orange text-white outline-none transition-all shadow-sm placeholder-text-muted"
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
                                                className="bg-card-dark border border-border-dark p-2.5 rounded-lg shadow-sm hover:border-accent-orange hover:shadow-md cursor-grab active:cursor-grabbing flex justify-between items-center group select-none transition-all"
                                            >
                                                <div>
                                                    <p className="font-bold text-sm text-gray-200">{ing.name}</p>
                                                    <p className="text-xs text-emerald-400 font-mono">${ing.price}</p>
                                                </div>
                                                <GripVertical size={16} className="text-gray-600 group-hover:text-accent-orange" />
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Builder (Right) */}
                                <div
                                    className="flex-1 flex flex-col bg-bg-deep/50 relative"
                                    onDragOver={e => e.preventDefault()}
                                    onDrop={handleDrop}
                                >
                                    <div className="flex-1 overflow-y-auto p-6 z-10">
                                        {recipeItems.length === 0 ? (
                                            <div className="h-full border-2 border-dashed border-border-dark rounded-2xl flex flex-col items-center justify-center text-gray-600 bg-card-dark/20">
                                                <UtensilsCrossed size={48} className="mb-4 opacity-50" />
                                                <p className="font-medium text-gray-400">Arrastra ingredientes de la despensa aquí</p>
                                                <p className="text-sm opacity-60">Para armar tu Escandallo / Receta</p>
                                            </div>
                                        ) : (
                                            <div className="space-y-3">
                                                {recipeItems.map((item, idx) => (
                                                    <div key={idx} className="bg-card-dark p-3 rounded-xl border border-border-dark shadow-sm flex items-center gap-4 animate-in slide-in-from-bottom-2 hover:shadow-md hover:border-border-dark/80 transition-all">
                                                        <span className="w-6 h-6 rounded-full bg-accent-orange/20 text-accent-orange flex items-center justify-center text-xs font-bold">
                                                            {idx + 1}
                                                        </span>
                                                        <div className="flex-1">
                                                            <p className="font-bold text-gray-200">{item.name}</p>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <input
                                                                type="number" className="w-20 bg-bg-deep border border-border-dark rounded px-2 py-1 text-sm font-bold text-center focus:border-accent-orange text-white outline-none"
                                                                value={item.quantity}
                                                                onChange={e => {
                                                                    const copy = [...recipeItems];
                                                                    copy[idx].quantity = parseFloat(e.target.value) || 0;
                                                                    setRecipeItems(copy);
                                                                }}
                                                            />
                                                            <select
                                                                className="text-xs bg-transparent text-gray-500 outline-none font-medium"
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
                                                            <p className="font-bold text-white">${(item.cost * item.quantity).toFixed(2)}</p>
                                                            <button onClick={() => setRecipeItems(recipeItems.filter((_, i) => i !== idx))} className="text-xs text-red-400 hover:text-red-300 font-medium">Quitar</button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Footer Analysis */}
                                    <div className="bg-card-dark border-t border-border-dark p-4 shadow-[0_-4px_20px_-1px_rgba(0,0,0,0.2)] z-20">
                                        <div className="flex items-center justify-between">
                                            <div className="flex gap-8">
                                                <div>
                                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Costo Ingredientes</p>
                                                    <p className="text-xl font-bold text-white">${recipeCost.toFixed(2)}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Margen Real</p>
                                                    <p className={`text-xl font-bold ${visualMargin < 30 ? 'text-red-500' : 'text-emerald-400'}`}>
                                                        {visualMargin.toFixed(1)}%
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className={`text-sm font-bold px-3 py-1 rounded-full border ${visualMargin > 50 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : visualMargin < 20 ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                                                    {visualMargin > 50 ? 'Excelente Margen' : visualMargin < 20 ? 'Margen Crítico' : 'Margen Aceptable'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* INSUMO EXPLANATION */}
                        {viewMode === 'INSUMOS' && (
                            <div className="flex-1 flex flex-col items-center justify-center bg-emerald-900/5 p-8 text-center animate-in fade-in">
                                <div className="bg-emerald-500/10 p-4 rounded-full mb-4 border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
                                    <Package size={48} className="text-emerald-500" />
                                </div>
                                <h3 className="text-xl font-bold text-white">Gestión de Insumos</h3>
                                <p className="text-gray-400 max-w-md mt-2">
                                    Aquí defines los costos base de tu negocio. Asegúrate de actualizar los precios regularmente para que tus cálculos de margen sean precisos.
                                </p>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
};
