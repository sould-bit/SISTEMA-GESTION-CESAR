import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ModifierModal } from './ModifierModal';
import { DeliveryInfoForm } from './DeliveryInfoForm';
import { setupService, Product, Category, ProductModifier } from '../setup/setup.service';
import { api } from '../../lib/api';

interface OrderItem {
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    modifiers?: number[]; // IDs of extra modifiers
    removed_ingredients?: string[]; // IDs of removed ingredients
    comment?: string;
}

export const CreateOrderPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { tableId, tableNumber, branchId, deliveryType } = location.state || {};

    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [recipes, setRecipes] = useState<any[]>([]);
    const [globalModifiers, setGlobalModifiers] = useState<ProductModifier[]>([]); // All available modifiers
    const [isLoading, setIsLoading] = useState(true);
    const [orderItems, setOrderItems] = useState<OrderItem[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedProductForMod, setSelectedProductForMod] = useState<Product | null>(null);

    // UI State
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategoryId, setSelectedCategoryId] = useState<number | 'all'>('all');
    const [activeTab, setActiveTab] = useState<'menu' | 'cart'>('menu');
    const [expandedProductIds, setExpandedProductIds] = useState<Set<number>>(new Set());
    const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false);
    const [editingCartItemIndex, setEditingCartItemIndex] = useState<number | null>(null);
    const [generalComment, setGeneralComment] = useState('');

    // Delivery Info State
    const [deliveryDetails, setDeliveryDetails] = useState({
        customer_name: '',
        customer_phone: '',
        delivery_address: '',
        delivery_notes: ''
    });
    const [formErrors, setFormErrors] = useState<Partial<Record<string, string>>>({});
    const [cartStep, setCartStep] = useState<'items' | 'info'>('items');

    const toggleProduct = (productId: number) => {
        setExpandedProductIds(prev => {
            const newSet = new Set(prev);
            if (newSet.has(productId)) {
                newSet.delete(productId);
            } else {
                newSet.add(productId);
            }
            return newSet;
        });
    };

    // Long Press Logic (Shared for all items)
    const pressTimer = useRef<NodeJS.Timeout | null>(null);
    const isLongPress = useRef(false);

    const startPress = (product: Product) => {
        isLongPress.current = false;
        pressTimer.current = setTimeout(() => {
            isLongPress.current = true;
            handleProductClick(product); // Open Modal (Long Press)
            if (navigator.vibrate) navigator.vibrate(50);
        }, 500);
    };

    const cancelPress = () => {
        if (pressTimer.current) {
            clearTimeout(pressTimer.current);
            pressTimer.current = null;
        }
    };

    const endPress = (product: Product) => {
        if (pressTimer.current) {
            clearTimeout(pressTimer.current);
            pressTimer.current = null;
            if (!isLongPress.current) {
                // Short press: Add directly
                handleAddProduct(product);
            }
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [productsData, recipesData, categoriesData, modifiersData] = await Promise.all([
                setupService.getProducts(),
                setupService.getRecipes(),
                setupService.getCategories(),
                setupService.getModifiers()
            ]);

            // Filter: Hide ingredients (Materia Prima) and only active products
            const menuProducts = productsData.filter(p =>
                p.is_active &&
                p.category_name?.toLowerCase() !== 'materia prima'
            );

            setProducts(menuProducts);
            setRecipes(recipesData);
            setCategories(categoriesData.filter(c => c.name.toLowerCase() !== 'materia prima'));
            setGlobalModifiers(modifiersData.filter(m => m.is_active));
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const getRecipeForProduct = (productId: number) => {
        return recipes.find(r => r.product_id === productId);
    };

    // New Flow: Tap -> Open Modal
    const handleProductClick = (product: Product) => {
        setSelectedProductForMod(product);
        setIsModalOpen(true);
    };

    const handleConfirmModifiers = (removedIngredients: string[], selectedModIds: number[], comment?: string) => {
        if (!selectedProductForMod) return;

        if (editingCartItemIndex !== null) {
            // Update existing cart item
            setOrderItems(prev => {
                const newItems = [...prev];
                // Keep the quantity, just update config
                newItems[editingCartItemIndex] = {
                    ...newItems[editingCartItemIndex],
                    removed_ingredients: removedIngredients,
                    modifiers: selectedModIds,
                    comment: comment
                };
                return newItems;
            });
            setEditingCartItemIndex(null);
        } else {
            // Add new item
            handleAddProduct(selectedProductForMod, removedIngredients, selectedModIds, comment);
        }

        setIsModalOpen(false);
        setSelectedProductForMod(null);
    };

    const handleEditCartItem = (index: number) => {
        const item = orderItems[index];
        const product = products.find(p => p.id === item.product_id);
        if (product) {
            setSelectedProductForMod(product);
            setEditingCartItemIndex(index);
            setIsModalOpen(true);
        }
    };


    const handleAddProduct = (product: Product, removed: string[] = [], mods: number[] = [], comment?: string) => {
        setOrderItems(prev => {
            // Check for EXACT match (same product + same removed + same modifiers + same comment)
            // Use JSON stringify for simple array comparison (order might matter, assuming standardized sort if crucial)
            // For now, simple length check + every match
            const existingIndex = prev.findIndex(item =>
                item.product_id === product.id &&
                JSON.stringify(item.removed_ingredients?.sort()) === JSON.stringify(removed.sort()) &&
                JSON.stringify(item.modifiers?.sort()) === JSON.stringify(mods.sort()) &&
                (item.comment || '') === (comment || '')
            );

            if (existingIndex >= 0) {
                const newItems = [...prev];
                // Immutable update
                newItems[existingIndex] = {
                    ...newItems[existingIndex],
                    quantity: newItems[existingIndex].quantity + 1
                };
                return newItems;
            }

            return [...prev, {
                product_id: product.id,
                product_name: product.name,
                quantity: 1,
                unit_price: product.price,
                removed_ingredients: removed,
                modifiers: mods,
                comment: comment
            }];
        });

        // Auto switch back to items tab if adding from mobile search while in info step
        if (cartStep === 'info') setCartStep('items');
    };

    const handleUpdateQuantity = (index: number, delta: number) => {
        setOrderItems(prev => {
            return prev.map((item, idx) => {
                if (idx === index) {
                    const newQty = item.quantity + delta;
                    return { ...item, quantity: newQty };
                }
                return item;
            }).filter(item => item.quantity > 0);
        });
    };

    const handleRemoveItem = (index: number) => {
        setOrderItems(prev => prev.filter((_, idx) => idx !== index));
    };

    const handleRemoveOneProduct = (productId: number) => {
        setOrderItems(prev => {
            const arr = [...prev];
            // Find the last added item with this product ID (stack-like removal usually expected for 'quick remove', or just any)
            // Or better: Find any item with this product ID.
            // Since we have multiple variations (mods), this is ambiguous.
            // PROPOSAL: If we are on the card, we might not know which specific variation to remove if there are multiple.
            // Compatibility fix for findLastIndex
            let index = -1;
            for (let i = arr.length - 1; i >= 0; i--) {
                if (arr[i].product_id === productId) {
                    index = i;
                    break;
                }
            }

            if (index !== -1) {
                if (arr[index].quantity > 1) {
                    arr[index].quantity -= 1;
                } else {
                    arr.splice(index, 1);
                }
            }
            return arr;
        });
    };

    const calculateTotal = () => {
        return orderItems.reduce((sum, item) => {
            let itemTotal = Number(item.unit_price);

            // Add modifiers cost
            if (item.modifiers && item.modifiers.length > 0) {
                item.modifiers.forEach(modId => {
                    const mod = globalModifiers.find(m => Number(m.id) === Number(modId));
                    if (mod) itemTotal += Number(mod.extra_price);
                });
            }

            return sum + (item.quantity * itemTotal);
        }, 0);
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price);
    };

    const getModifierName = (modId: number) => {
        return globalModifiers.find(m => Number(m.id) === Number(modId))?.name || 'Extra Desconocido';
    };

    // Helper to get modifier total for display
    const getModifiersTotal = (modIds: number[]) => {
        return modIds.reduce((acc, modId) => {
            const mod = globalModifiers.find(m => Number(m.id) === Number(modId));
            return acc + (mod ? Number(mod.extra_price) : 0);
        }, 0);
    };

    // Helper to get removed names for display
    const getRemovedNames = (removedIds: string[], recipe: any) => {
        if (!recipe || !recipe.items) return [];
        return removedIds.map(id => {
            // Find in recipe items
            const item = recipe.items.find((i: any) =>
                String(i.ingredient_id) === String(id) ||
                String(i.ingredient_product_id) === String(id)
            );
            return item ? item.ingredient_name : 'Ingrediente';
        });
    };

    const filteredProducts = products.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = selectedCategoryId === 'all' || p.category_id === selectedCategoryId;
        return matchesSearch && matchesCategory;
    });

    const handleSubmit = async () => {
        if (orderItems.length === 0) return;

        // Validation for Info Step
        if (cartStep === 'items') {
            setCartStep('info');
            return;
        }

        // Validation for Delivery
        if (deliveryType === 'delivery') {
            const errors: any = {};
            if (!deliveryDetails.customer_name.trim()) errors.customer_name = 'El nombre es obligatorio';
            if (!deliveryDetails.customer_phone.trim()) errors.customer_phone = 'El teléfono es obligatorio';
            if (!deliveryDetails.delivery_address.trim()) errors.delivery_address = 'La dirección es obligatoria';

            if (Object.keys(errors).length > 0) {
                setFormErrors(errors);
                // Scroll to form or show toast
                alert('Por favor completa todos los datos de entrega');
                return;
            }
        }

        setIsSubmitting(true);
        setFormErrors({});

        try {
            const payload = {
                branch_id: branchId || 1,
                table_id: tableId,
                delivery_type: deliveryType || 'dine_in',
                items: orderItems.map(item => ({
                    product_id: item.product_id,
                    quantity: item.quantity,
                    modifiers: item.modifiers,
                    removed_ingredients: item.removed_ingredients,
                    notes: item.comment
                })),

                // Delivery Fields
                delivery_customer_name: deliveryDetails.customer_name,
                delivery_customer_phone: deliveryDetails.customer_phone,
                delivery_address: deliveryDetails.delivery_address,
                delivery_notes: deliveryDetails.delivery_notes,

                notes: generalComment
            };

            await api.post('/orders/', payload);
            navigate('/admin/orders');
        } catch (error) {
            console.error('Error creating order:', error);
            alert('Error al crear el pedido');
            setIsSubmitting(false);
        }
    };

    if (isLoading) return (
        <div className="h-full flex flex-col items-center justify-center gap-4">
            <div className="size-12 border-4 border-accent-primary/20 border-t-accent-primary rounded-full animate-spin"></div>
            <p className="text-text-muted font-medium">Cargando menú...</p>
        </div>
    );

    return (
        <div className="h-[calc(100vh-80px)] flex flex-col lg:flex-row gap-4 lg:gap-6 min-w-0 transition-all duration-300">
            {/* Left Panel: Header + Mobile Tabs + Product List */}
            <div className={`flex-1 flex flex-col min-w-0 h-full ${activeTab === 'cart' ? 'hidden lg:flex' : 'flex'} lg:pr-[440px] xl:pr-[480px] 2xl:pr-[520px]`}>
                {/* Header / Table Info */}
                <div className="flex justify-between items-center mb-4 shrink-0">
                    <div>
                        <h1 className="text-xl sm:text-2xl font-bold text-white leading-tight">Nueva Orden</h1>
                        <div className="flex items-center gap-2">
                            {deliveryType === 'takeaway' ? (
                                <span className="bg-accent-secondary/10 text-accent-secondary px-2 py-0.5 rounded text-sm font-bold border border-accent-secondary/20">
                                    Para Llevar
                                </span>
                            ) : deliveryType === 'delivery' ? (
                                <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-sm font-bold border border-blue-500/20">
                                    Domicilio
                                </span>
                            ) : tableNumber ? (
                                <span className="bg-accent-primary/10 text-accent-primary px-2 py-0.5 rounded text-sm font-bold border border-accent-primary/20">
                                    Mesa {tableNumber}
                                </span>
                            ) : null}
                            <span className="text-text-muted text-xs font-medium uppercase tracking-wider">
                                {deliveryType === 'takeaway' ? 'Pick-up' : deliveryType === 'delivery' ? 'Delivery' : 'Dine-in'}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={() => navigate('/admin/tables')}
                        className="p-2 text-text-muted hover:text-white transition-colors"
                    >
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* Mobile/Tablet Tab Switcher (Visible only on screens smaller than large tablets/desktop) */}
                <div className="flex lg:hidden bg-card-dark p-1 rounded-xl border border-border-dark mb-4 shrink-0">
                    <button
                        onClick={() => setActiveTab('menu')}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${activeTab === 'menu' ? 'bg-accent-primary text-bg-dark' : 'text-text-muted'}`}
                    >
                        <span className="material-symbols-outlined text-[20px]">restaurant_menu</span>
                        Menú
                    </button>
                    <button
                        onClick={() => setActiveTab('cart')}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 relative ${activeTab === 'cart' ? 'bg-accent-primary text-bg-dark' : 'text-text-muted'}`}
                    >
                        <span className="material-symbols-outlined text-[20px]">shopping_cart</span>
                        Pedido
                        {orderItems.length > 0 && (
                            <span className={`absolute -top-1 -right-1 size-5 rounded-full flex items-center justify-center text-[10px] font-bold border ${activeTab === 'cart' ? 'bg-bg-dark text-accent-primary border-bg-dark' : 'bg-accent-primary text-bg-dark border-bg-dark'}`}>
                                {orderItems.reduce((acc, curr) => acc + curr.quantity, 0)}
                            </span>
                        )}
                    </button>
                </div>

                {/* Product List Section */}
                <div className="flex-1 flex flex-col min-h-0">
                    {/* Filters (Search + Categories) */}
                    <div className="space-y-3 mb-4 shrink-0">
                        <div className="relative group">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-muted group-focus-within:text-accent-primary transition-colors text-[20px]">search</span>
                            <input
                                type="text"
                                placeholder="Buscar platillo..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-card-dark border border-border-dark rounded-xl pl-10 pr-4 py-2.5 text-white text-sm focus:outline-none focus:border-accent-primary/50 transition-all shadow-inner"
                            />
                        </div>

                        <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
                            <button
                                onClick={() => setSelectedCategoryId('all')}
                                className={`whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-bold border transition-all ${selectedCategoryId === 'all' ? 'bg-accent-primary/20 border-accent-primary text-accent-primary' : 'bg-card-dark border-border-dark text-text-muted'}`}
                            >
                                Todos
                            </button>
                            {categories.map(cat => (
                                <button
                                    key={cat.id}
                                    onClick={() => setSelectedCategoryId(cat.id)}
                                    className={`whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-bold border transition-all ${selectedCategoryId === cat.id ? 'bg-accent-primary/20 border-accent-primary text-accent-primary' : 'bg-card-dark border-border-dark text-text-muted'}`}
                                >
                                    {cat.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Menu Grid */}
                    <div className="flex-1 overflow-y-auto px-1 pb-6 min-h-0">
                        {filteredProducts.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-40 text-text-muted opacity-50">
                                <span className="material-symbols-outlined text-4xl mb-2">sentiment_dissatisfied</span>
                                <p className="text-sm">No se encontraron productos</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                                {filteredProducts.map(product => {
                                    const recipe = getRecipeForProduct(product.id);
                                    // Cart qty logic: Count total items with this product ID regardless of mods
                                    const cartQty = orderItems.filter(i => i.product_id === product.id).reduce((acc, i) => acc + i.quantity, 0);

                                    return (
                                        <div key={product.id} className={`group relative bg-card-dark p-4 rounded-2xl border-2 transition-all flex flex-col h-full shadow-lg cursor-pointer ${cartQty > 0 ? 'border-accent-primary bg-accent-primary/5' : 'border-border-dark hover:border-accent-primary/30'} select-none touch-manipulation`}
                                            onContextMenu={(e) => e.preventDefault()}
                                            onPointerDown={() => startPress(product)}
                                            onPointerUp={() => endPress(product)}
                                            onPointerLeave={cancelPress}
                                            onPointerCancel={cancelPress}
                                        >
                                            {cartQty > 0 && (
                                                <div className="absolute -top-2 -right-2 size-7 bg-accent-primary text-bg-dark rounded-full flex items-center justify-center font-bold text-sm ring-4 ring-bg-deep shadow-xl z-20 animate-in zoom-in">
                                                    {cartQty}
                                                </div>
                                            )}

                                            <div className="flex-1 mb-4 pointer-events-none">
                                                <div className="flex justify-between items-start mb-2 gap-2">
                                                    <h3 className="font-bold text-white text-base leading-tight group-hover:text-accent-primary transition-colors">{product.name}</h3>
                                                    <span className="text-status-success font-mono text-sm font-bold bg-status-success/10 px-2 py-0.5 rounded shrink-0">
                                                        {formatPrice(product.price)}
                                                    </span>
                                                </div>

                                                {recipe && recipe.items && recipe.items.length > 0 ? (
                                                    <div className="space-y-1.5 mt-3 pointer-events-auto">
                                                        <div
                                                            onClick={(e) => { e.stopPropagation(); toggleProduct(product.id); }}
                                                            onPointerDown={(e) => e.stopPropagation()}
                                                            className="flex items-center justify-between w-full text-[10px] uppercase tracking-widest font-black text-accent-secondary/60 hover:text-accent-secondary cursor-pointer transition-colors"
                                                        >
                                                            <span>Ingredientes</span>
                                                            <span className="material-symbols-outlined text-[14px]">
                                                                {expandedProductIds.has(product.id) ? 'expand_less' : 'expand_more'}
                                                            </span>
                                                        </div>
                                                        {expandedProductIds.has(product.id) && (
                                                            <div className="text-[11px] text-text-muted/80 leading-relaxed animate-in slide-in-from-top-1 fade-in duration-200">
                                                                {/* Dropdown / Expanded View */}
                                                                <ul className="list-disc list-inside">
                                                                    {recipe.items.map((i: any, idx: number) => (
                                                                        <li key={idx}>
                                                                            {i.ingredient_name}
                                                                            {i.quantity > 0 && <span className="text-[9px] opacity-50 ml-1">({i.quantity} {i.unit})</span>}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <p className="text-xs text-text-muted italic opacity-40 leading-relaxed mt-2">
                                                        {product.description || 'Sin ingredientes detallados'}
                                                    </p>
                                                )}
                                            </div>

                                            {/* Mobile Hint & Actions */}
                                            <div className="mt-auto pointer-events-none">
                                                <p className="flex items-center justify-center gap-1.5 text-[10px] text-accent-primary/50 font-medium mb-3 opacity-80">
                                                    <span className="material-symbols-outlined text-[14px]">touch_app</span>
                                                    Mantén presionado para personalizar
                                                </p>

                                                <div className="flex items-center gap-2 pointer-events-auto">
                                                    {cartQty > 0 ? (
                                                        <>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleRemoveOneProduct(product.id);
                                                                    if (navigator.vibrate) navigator.vibrate(50);
                                                                }}
                                                                onPointerDown={(e) => e.stopPropagation()}
                                                                onPointerUp={(e) => e.stopPropagation()}
                                                                className="size-10 rounded-xl bg-bg-deep border border-border-dark flex items-center justify-center text-status-alert hover:bg-status-alert/10 hover:border-status-alert/30 transition-all active:scale-95 z-30"
                                                            >
                                                                <span className="material-symbols-outlined">remove</span>
                                                            </button>

                                                            <div className="flex-1 py-2.5 rounded-xl bg-accent-primary text-bg-dark font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-accent-primary/20 pointer-events-none">
                                                                <span className="material-symbols-outlined text-[20px]">library_add</span>
                                                                <span className="text-base">{cartQty}</span>
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <div className={`w-full py-2.5 rounded-xl transition-all flex items-center justify-center gap-2 font-bold text-xs uppercase tracking-wider bg-bg-deep border border-border-dark text-text-muted pointer-events-none`}>
                                                            <span className="material-symbols-outlined text-[20px]">add_circle</span>
                                                            Agregar
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right Panel: Cart / Summary (Full Height Floating on Desktop) */}
            <div className={`flex flex-col min-h-0 bg-card-dark border-border-dark shadow-2xl relative ${activeTab === 'menu' ? 'hidden lg:flex' : 'flex flex-1'} lg:fixed lg:top-4 lg:right-4 lg:bottom-4 lg:w-[420px] xl:w-[460px] 2xl:w-[500px] lg:rounded-2xl lg:border lg:z-50`}>
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-bg-deep/30 shrink-0">
                    <div className="flex items-center gap-3">
                        {cartStep === 'info' && (
                            <button
                                onClick={() => setCartStep('items')}
                                className="p-1.5 hover:bg-white/5 rounded-lg text-accent-primary transition-colors"
                            >
                                <span className="material-symbols-outlined">arrow_back</span>
                            </button>
                        )}
                        <div>
                            <h3 className="font-bold text-white text-base">
                                {cartStep === 'items' ? 'Carrito' : 'Finalizar Pedido'}
                            </h3>
                            <p className="text-[10px] text-text-muted">
                                {cartStep === 'items'
                                    ? 'Revisa los items antes de confirmar'
                                    : 'Completa los datos de entrega y comentarios'
                                }
                            </p>
                        </div>
                    </div>
                    <span className="text-xs font-mono text-accent-primary bg-accent-primary/10 px-2 py-1 rounded-lg">
                        {orderItems.length} items
                    </span>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {orderItems.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-text-muted opacity-30 gap-3 py-12">
                            <span className="material-symbols-outlined text-6xl">shopping_basket</span>
                            <p className="text-sm font-medium">No hay productos aún</p>
                        </div>
                    ) : cartStep === 'items' ? (
                        // STEP 1: REVIEW ITEMS
                        <div className="space-y-4 animate-in fade-in slide-in-from-left-2 duration-300">
                            {orderItems.map((item, idx) => {
                                const recipe = getRecipeForProduct(item.product_id);
                                const removedNames = getRemovedNames(item.removed_ingredients || [], recipe);
                                const modsTotal = getModifiersTotal(item.modifiers || []);

                                return (
                                    <div key={`${item.product_id}-${idx}`} className="flex justify-between items-start gap-3 group border-b border-border-dark/30 pb-3 last:border-0 last:pb-0">
                                        <div
                                            className="flex-1 min-w-0 cursor-pointer hover:bg-white/5 p-2 -m-2 rounded-lg transition-colors group/edit"
                                            onClick={() => handleEditCartItem(idx)}
                                        >
                                            <div className="flex items-center gap-2">
                                                <p className="text-white text-sm font-bold truncate transition-colors">{item.product_name}</p>
                                                <span className="material-symbols-outlined text-[14px] text-accent-primary lg:opacity-0 lg:group-hover/edit:opacity-100 transition-opacity">edit</span>
                                            </div>
                                            <p className="text-text-muted text-[10px] font-mono">{formatPrice(item.unit_price)}</p>

                                            {/* Modifiers Display */}
                                            {(removedNames.length > 0 || (item.modifiers && item.modifiers.length > 0)) && (
                                                <div className="mt-1 flex flex-wrap gap-1">
                                                    {removedNames.map((name, i) => (
                                                        <span key={i} className="text-[9px] font-black uppercase text-status-alert bg-status-alert/10 px-1.5 py-0.5 rounded">
                                                            SIN {name}
                                                        </span>
                                                    ))}
                                                    {item.modifiers?.map((modId, i) => (
                                                        <span key={i} className="text-[9px] font-black uppercase text-accent-secondary bg-accent-secondary/10 px-1.5 py-0.5 rounded">
                                                            + {getModifierName(modId)}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                            {modsTotal > 0 && (
                                                <p className="text-accent-secondary text-[10px] font-mono mt-0.5">+ {formatPrice(modsTotal)} (Extras)</p>
                                            )}
                                            {item.comment && (
                                                <p className="text-[10px] text-text-muted mt-1 italic border-l-2 border-accent-primary/30 pl-1.5 flex gap-1">
                                                    <span className="material-symbols-outlined text-[10px]">sticky_note_2</span>
                                                    {item.comment}
                                                </p>
                                            )}
                                        </div>

                                        <div className="flex flex-col items-end gap-2">
                                            <div className="flex items-center gap-1.5 bg-bg-deep rounded-xl p-1 border border-border-dark shadow-inner">
                                                <button
                                                    onClick={() => handleUpdateQuantity(idx, -1)}
                                                    className="size-8 rounded-lg flex items-center justify-center text-text-muted hover:text-white hover:bg-white/5 transition-all text-xl"
                                                >−</button>
                                                <span className="text-white text-sm font-mono w-6 text-center font-bold">{item.quantity}</span>
                                                <button
                                                    onClick={() => handleUpdateQuantity(idx, 1)}
                                                    className="size-8 rounded-lg flex items-center justify-center text-accent-primary hover:bg-accent-primary/10 transition-all text-xl"
                                                >+</button>
                                            </div>

                                            <button
                                                onClick={() => handleRemoveItem(idx)}
                                                className="text-xs text-status-alert hover:underline opacity-60 hover:opacity-100 transition-opacity"
                                            >
                                                Eliminar
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        // STEP 2: FINALIZE (DELIVERY + COMMENTS)
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-2 duration-300">
                            {/* Delivery Customer Info */}
                            {deliveryType === 'delivery' && (
                                <DeliveryInfoForm
                                    value={deliveryDetails}
                                    onChange={setDeliveryDetails}
                                    errors={formErrors}
                                />
                            )}

                            {/* General Comment Input */}
                            <div className="space-y-2 px-1">
                                <div className="flex items-center gap-2 text-[10px] text-text-muted uppercase tracking-widest font-bold mb-1">
                                    <span className="material-symbols-outlined text-[16px]">sticky_note_2</span>
                                    Comentario General del Pedido
                                </div>
                                <textarea
                                    value={generalComment}
                                    onChange={(e) => setGeneralComment(e.target.value)}
                                    placeholder="Ej: Por favor cubiertos, sin servilletas, etc..."
                                    className="w-full bg-bg-deep border border-border-dark rounded-xl p-3 text-xs text-white placeholder-text-muted/50 focus:outline-none focus:border-accent-primary transition-colors resize-none h-24 shadow-inner"
                                />
                            </div>

                            <div className="bg-accent-primary/5 p-4 rounded-xl border border-accent-primary/20">
                                <h4 className="text-[10px] text-accent-primary uppercase tracking-widest font-black mb-2">Resumen de Cuenta</h4>
                                <div className="flex justify-between items-center text-white font-bold">
                                    <span className="text-xs">Subtotal ({orderItems.length} items)</span>
                                    <span className="text-sm font-mono">{formatPrice(calculateTotal())}</span>
                                </div>
                                <div className="flex justify-between items-center text-text-muted mt-1 text-[10px]">
                                    <span>Propinas / Otros</span>
                                    <span>A definir</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Total & Confirm - Stick to bottom */}
                <div className="p-4 border-t border-border-dark bg-bg-deep/80 backdrop-blur-md space-y-4">
                    <div className="flex justify-between items-center px-1">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-text-muted uppercase tracking-widest font-bold">Total a pagar</span>
                            <span className="text-2xl font-black text-white leading-none">{formatPrice(calculateTotal())}</span>
                        </div>
                        <div className="text-right">
                            <span className="text-[10px] text-text-muted uppercase tracking-widest font-bold">Impuestos incl.</span>
                            <p className="text-xs text-status-success font-medium">
                                {cartStep === 'items' ? 'Verificando productos...' : 'Listo para enviar'}
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={handleSubmit}
                        disabled={orderItems.length === 0 || isSubmitting}
                        className={`w-full py-4 rounded-2xl font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-2xl relative overflow-hidden group
                            ${orderItems.length === 0 || isSubmitting
                                ? 'bg-border-dark text-text-muted cursor-not-allowed opacity-50'
                                : 'bg-accent-primary text-bg-dark hover:brightness-110 active:scale-[0.98] shadow-accent-primary/30'}
                        `}
                    >
                        {isSubmitting ? (
                            <span className="material-symbols-outlined animate-spin">progress_activity</span>
                        ) : (
                            <>
                                <span className="material-symbols-outlined group-hover:scale-125 transition-transform">
                                    {cartStep === 'items' ? 'arrow_forward' : 'check_circle'}
                                </span>
                                {cartStep === 'items' ? 'Continuar' : 'Confirmar Orden'}
                            </>
                        )}
                    </button>
                </div>

                {/* Pulse effect overlay when enabled */}
                {!isSubmitting && orderItems.length > 0 && (
                    <span className="absolute inset-0 bg-white/10 animate-pulse pointer-events-none"></span>
                )}
            </div>

            {/* Floating Category Menu (Mobile Only) - Bottom Right FAB Style */}
            <div className={`lg:hidden fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3 pointer-events-none`}>
                {/* Backdrop for click-outside (optional, but good for UX) - Only covers if open */}
                {isCategoryMenuOpen && (
                    <div
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 pointer-events-auto"
                        onClick={() => setIsCategoryMenuOpen(false)}
                        style={{ zIndex: -1 }}
                    />
                )
                }

                {/* Categories List (Expands Upwards) */}
                <div className={`flex flex-col items-end gap-2 transition-all duration-300 origin-bottom pointer-events-auto pb-1 ${isCategoryMenuOpen ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-10 scale-90 pointer-events-none'}`}>
                    <div className="max-h-[60vh] overflow-y-auto flex flex-col items-end gap-2 p-1 no-scrollbar">
                        <button
                            onClick={() => { setSelectedCategoryId('all'); setIsCategoryMenuOpen(false); }}
                            className={`px-4 py-2.5 rounded-xl text-xs font-bold backdrop-blur-md shadow-lg transition-all border border-white/5 active:scale-95 ${selectedCategoryId === 'all' ? 'bg-accent-primary text-bg-dark border-accent-primary' : 'bg-bg-deep/80 text-white hover:bg-bg-deep'}`}
                        >
                            Todas
                        </button>
                        {categories.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => { setSelectedCategoryId(cat.id); setIsCategoryMenuOpen(false); }}
                                className={`px-4 py-2.5 rounded-xl text-xs font-bold backdrop-blur-md shadow-lg transition-all border border-white/5 active:scale-95 ${selectedCategoryId === cat.id ? 'bg-accent-primary text-bg-dark border-accent-primary' : 'bg-bg-deep/80 text-white hover:bg-bg-deep'}`}
                            >
                                {cat.name}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main FAB Toggle with Active Category Indicator */}
            <div className="flex items-center gap-3 pointer-events-auto">
                {!isCategoryMenuOpen && selectedCategoryId !== 'all' && (
                    <div className="bg-accent-primary/90 backdrop-blur-md text-bg-dark font-black text-[10px] uppercase tracking-wider px-3 py-1.5 rounded-lg shadow-lg animate-in slide-in-from-right-8 fade-in duration-300 border border-white/10">
                        {categories.find(c => c.id === selectedCategoryId)?.name}
                    </div>
                )}

                <button
                    onClick={() => setIsCategoryMenuOpen(!isCategoryMenuOpen)}
                    className={`size-12 rounded-2xl backdrop-blur-md shadow-2xl flex items-center justify-center transition-all active:scale-90 border border-white/10 ${isCategoryMenuOpen ? 'bg-accent-primary text-bg-dark' : 'bg-bg-deep/60 text-accent-primary hover:bg-bg-deep'}`}
                >
                    <span className={`material-symbols-outlined transition-transform duration-300 text-[24px] ${isCategoryMenuOpen ? 'rotate-[-90deg]' : 'rotate-0'}`}>
                        chevron_left
                    </span>
                </button>
            </div>

            {/* Modal de Modificadores */}
            {
                isModalOpen && selectedProductForMod && (
                    <ModifierModal
                        product={selectedProductForMod}
                        recipe={getRecipeForProduct(selectedProductForMod.id)}
                        modifiers={globalModifiers}
                        initialRemoved={editingCartItemIndex !== null ? orderItems[editingCartItemIndex].removed_ingredients : []}
                        initialModifiers={editingCartItemIndex !== null ? orderItems[editingCartItemIndex].modifiers : []}
                        initialComment={editingCartItemIndex !== null ? orderItems[editingCartItemIndex].comment : ''}
                        onClose={() => { setIsModalOpen(false); setSelectedProductForMod(null); setEditingCartItemIndex(null); }}
                        onConfirm={handleConfirmModifiers}
                    />
                )
            }
        </div >
    );
};

