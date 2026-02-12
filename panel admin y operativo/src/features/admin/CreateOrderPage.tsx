import { useState, useRef } from 'react';
import { useAppSelector } from '../../stores/store';
import { useNavigate, useLocation } from 'react-router-dom';
import { ModifierModal } from './ModifierModal';
import { DeliveryInfoForm } from './DeliveryInfoForm';
import { Product } from '../setup/setup.service';
import { DeliveryDetails } from './createOrder.machine';
import { useMachine } from '@xstate/react';
import { createOrderMachine } from './createOrder.machine';
import { inspector } from '../../lib/inspector';


export const CreateOrderPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { tableId, tableNumber, branchId, deliveryType, orderId } = location.state || {};

    const { user } = useAppSelector(state => state.auth);

    const [state, send] = useMachine(createOrderMachine, {
        input: {
            tableId,
            tableNumber,
            branchId,
            deliveryType: deliveryType || 'dine_in',
            existingOrderId: orderId,
            permissions: user?.permissions || []
        },
        inspect: inspector?.inspect
    });

    const {
        products,
        categories,
        recipes,
        globalModifiers,
        orderItems,
        deliveryDetails,
        searchTerm,
        selectedCategoryId,
        selectedProductForMod,
        editingCartItemIndex,
        generalComment,
        existingItems,
        stockError
    } = state.context;

    const isLoading = state.matches('loading');
    const isSubmitting = state.matches('submitting');
    const isModalOpen = state.matches('customizing');
    const cartStep = state.matches('ordering.menu') ? 'items'
        : state.matches('ordering.reviewing') ? 'items'
            : state.matches('ordering.info') ? 'info' : 'items';

    // Local UI states only (not domain/business logic)
    const [activeTab, setActiveTab] = useState<'menu' | 'cart'>('menu');
    const [expandedProductIds, setExpandedProductIds] = useState<Set<number>>(new Set());
    const [formErrors, setFormErrors] = useState<Partial<Record<string, string>>>({});
    const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false);

    // Handlers
    const handleAddToCart = (product: Product) => send({ type: 'ADD_ITEM', product });
    const handleUpdateQuantity = (index: number, delta: number) => send({ type: 'UPDATE_QUANTITY', index, delta });
    const handleRemoveItem = (index: number) => send({ type: 'REMOVE_ITEM', index });

    const handleUpdateExistingQuantity = (itemId: number, quantity: number) =>
        send({ type: 'UPDATE_EXISTING_QUANTITY', itemId, quantity });
    const handleRemoveExistingItem = (itemId: number) =>
        send({ type: 'REMOVE_EXISTING_ITEM', itemId });

    const handleModifierConfirm = (removed: string[], mods: number[], comment?: string) =>
        send({ type: 'CONFIRM_MODS', removed, mods, comment });
    const handleModifierClose = () => send({ type: 'CLOSE_MODAL' });

    const handleEditCartItem = (index: number) => {
        const item = orderItems[index];
        const product = products.find(p => p.id === item.product_id);
        if (product) send({ type: 'OPEN_MODAL', product, index });
    };

    const handleProductClick = (product: Product) => {
        send({ type: 'OPEN_MODAL', product });
    };

    const handleAddProduct = (product: Product) => send({ type: 'ADD_ITEM', product });
    const handleRemoveOneProduct = (productId: number) => {
        const index = [...orderItems].reverse().findIndex(item => item.product_id === productId);
        if (index !== -1) {
            const actualIndex = orderItems.length - 1 - index;
            send({ type: 'UPDATE_QUANTITY', index: actualIndex, delta: -1 });
        }
    };

    const handleUpdateDeliveryInfo = (details: Partial<DeliveryDetails>) =>
        send({ type: 'SET_DELIVERY_INFO', details });

    const handleUpdateGeneralComment = (comment: string) =>
        send({ type: 'SET_GENERAL_COMMENT', comment });

    const handleClearStockError = () => send({ type: 'CLEAR_STOCK_ERROR' });

    const handleSubmit = () => {
        if (cartStep === 'items') {
            send({ type: 'NEXT_STEP' });
        } else {
            if (deliveryType !== 'dine_in') {
                const errors: Partial<Record<string, string>> = {};
                if (!deliveryDetails.customer_name) errors.customer_name = 'El nombre es obligatorio';
                if (!deliveryDetails.customer_phone) errors.customer_phone = 'El teléfono es obligatorio';
                if (deliveryType === 'delivery' && !deliveryDetails.delivery_address) {
                    errors.delivery_address = 'La dirección es obligatoria';
                }

                if (Object.keys(errors).length > 0) {
                    setFormErrors(errors);
                    return;
                }
            }
            setFormErrors({});
            send({ type: 'SUBMIT' });
        }
    };

    const setSearchTerm = (term: string) => send({ type: 'SET_SEARCH', term });
    const setSelectedCategoryId = (id: number | 'all') => send({ type: 'SELECT_CATEGORY', categoryId: id });
    const setCartStep = (step: 'items' | 'info') => {
        if (step === 'items') send({ type: 'PREV_STEP' });
        else send({ type: 'NEXT_STEP' });
    };


    const toggleProduct = (productId: number) => {
        setExpandedProductIds((prev: Set<number>) => {
            const next = new Set(prev);
            if (next.has(productId)) {
                next.delete(productId);
            } else {
                next.add(productId);
            }
            return next;
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

    const endPress = (product: Product, e?: React.PointerEvent) => {
        if (pressTimer.current) {
            clearTimeout(pressTimer.current);
            pressTimer.current = null;
            if (!isLongPress.current) {
                // Only handle short press if we didn't click a button (to avoid double actions)
                const target = e?.target as HTMLElement;
                if (!target?.closest('button')) {
                    handleAddToCart(product);
                }
            }
        }
    }

    const getRecipeForProduct = (productId: number) => {
        return recipes.find(r => r.product_id === productId);
    };

    const filteredProducts = products.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = selectedCategoryId === 'all' || Number(p.category_id) === Number(selectedCategoryId);
        return matchesSearch && matchesCategory;
    });

    // Total calculation
    const calculateTotal = () => {
        const newItemsTotal = orderItems.reduce((acc, item) => {
            const modsPrice = getModifiersTotal(item.modifiers || []);
            return acc + (item.unit_price + modsPrice) * item.quantity;
        }, 0);
        const existingTotal = existingItems.reduce((acc, item) => acc + (Number(item.quantity) * Number(item.unit_price || 0)), 0);
        return newItemsTotal + existingTotal;
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price);
    };

    const getModifierName = (modId: number | string) => {
        return globalModifiers.find(m => String(m.id) === String(modId))?.name || 'Extra Desconocido';
    };

    const getModifiersTotal = (modIds: number[]) => {
        return modIds.reduce((acc, modId) => {
            const mod = globalModifiers.find(m => Number(m.id) === Number(modId));
            return acc + (mod ? Number(mod.extra_price) : 0);
        }, 0);
    };

    const getRemovedNames = (removedIds: string[], recipe: any) => {
        if (!recipe || !recipe.items) return [];
        return removedIds.map(id => {
            const item = recipe.items.find((i: any) =>
                String(i.ingredient_id) === String(id) ||
                String(i.ingredient_product_id) === String(id)
            );
            return item ? item.ingredient_name : 'Desconocido';
        });
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-bg-dark flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <span className="material-symbols-outlined text-accent-primary animate-spin text-4xl">progress_activity</span>
                    <p className="text-text-muted animate-pulse font-medium">Cargando menú...</p>
                </div>
            </div>
        );
    }

    // UI variables
    const orderStatus = state.context.existingOrderStatus;

    return (
        <>
            <div className="flex flex-col h-screen bg-bg-dark text-white overflow-hidden p-4 lg:pr-[400px] xl:pr-[440px] 2xl:pr-[480px]">
                {/* Header / Table Info */}
                <div className="flex justify-between items-center mb-4 shrink-0">
                    <div>
                        <h1 className="text-xl sm:text-2xl font-bold text-white leading-tight">
                            {orderId ? 'Agregar Productos' : 'Nueva Orden'}
                        </h1>
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
                    <div className="space-y-3 mb-4 shrink-0 mt-2 lg:mt-0">
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
                                        <div
                                            key={product.id}
                                            className={`group relative bg-card-dark p-4 rounded-2xl border-2 transition-all flex flex-col h-full shadow-lg ${cartQty > 0 ? 'border-accent-primary bg-accent-primary/5' : 'border-border-dark hover:border-accent-primary/30'} select-none touch-manipulation cursor-pointer`}
                                            onContextMenu={(e) => e.preventDefault()}
                                            onPointerDown={() => startPress(product)}
                                            onPointerUp={(e) => endPress(product, e)}
                                            onPointerLeave={cancelPress}
                                            onPointerCancel={cancelPress}
                                        >
                                            {cartQty > 0 && (
                                                <div className="absolute -top-2 -right-2 size-7 bg-accent-primary text-bg-dark rounded-full flex items-center justify-center font-bold text-sm ring-4 ring-bg-deep shadow-xl z-30 animate-in zoom-in">
                                                    {cartQty}
                                                </div>
                                            )}

                                            <div className="flex-1 flex flex-col min-w-0 mb-4 relative z-20">
                                                <div className="flex justify-between items-start gap-2 mb-2">
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="font-bold text-white text-base leading-tight group-hover:text-accent-primary transition-colors line-clamp-2 min-h-[2.5rem]">{product.name}</h3>
                                                        <span className="text-status-success font-mono text-lg font-black mt-1">
                                                            {formatPrice(product.price)}
                                                        </span>
                                                    </div>

                                                    {/* Ingredients Toggle Icon - Explicitly outside the main click handler's logic if needed, but here it's on top */}
                                                    {recipe && recipe.items && recipe.items.length > 0 && (
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); toggleProduct(product.id); }}
                                                            onPointerDown={(e) => e.stopPropagation()}
                                                            onPointerUp={(e) => e.stopPropagation()}
                                                            className={`size-8 rounded-lg flex items-center justify-center transition-all ${expandedProductIds.has(product.id) ? 'bg-accent-secondary text-bg-dark' : 'bg-white/5 text-accent-secondary hover:bg-white/10'} border border-accent-secondary/20 shadow-sm`}
                                                            title={expandedProductIds.has(product.id) ? 'Ocultar ingredientes' : 'Ver ingredientes'}
                                                        >
                                                            <span className="material-symbols-outlined text-[20px]">
                                                                {expandedProductIds.has(product.id) ? 'keyboard_arrow_up' : 'list_alt'}
                                                            </span>
                                                        </button>
                                                    )}
                                                </div>

                                                {/* Expanded Ingredients List */}
                                                {recipe && recipe.items && expandedProductIds.has(product.id) && (
                                                    <div className="text-[11px] text-text-muted/80 leading-relaxed animate-in slide-in-from-top-1 fade-in duration-200 bg-bg-deep/30 p-2 rounded-lg border border-border-dark/30 mt-1 mb-2 pointer-events-none">
                                                        <ul className="space-y-1">
                                                            {recipe.items.map((i: any, idx: number) => (
                                                                <li key={idx} className="flex justify-between items-center gap-2 border-b border-white/5 last:border-0 pb-1 last:pb-0">
                                                                    <span className="truncate">{i.ingredient_name}</span>
                                                                    {i.quantity > 0 && <span className="text-[9px] opacity-50 shrink-0 font-mono">{i.quantity} {i.unit}</span>}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {!expandedProductIds.has(product.id) && (
                                                    <p className="text-xs text-text-muted/50 italic leading-relaxed mt-2 line-clamp-2 pointer-events-none">
                                                        {product.description || 'Sin descripción'}
                                                    </p>
                                                )}
                                            </div>

                                            {/* Actions Footer */}
                                            <div className="mt-auto pt-3 border-t border-border-dark/40 relative z-30">
                                                <div className="flex items-center gap-2">
                                                    {cartQty > 0 ? (
                                                        <>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleRemoveOneProduct(product.id);
                                                                    if (navigator.vibrate) navigator.vibrate(50);
                                                                }}
                                                                className="size-10 rounded-xl bg-bg-deep border border-border-dark flex items-center justify-center text-status-alert hover:bg-status-alert/10 hover:border-status-alert/30 transition-all active:scale-95 shadow-inner"
                                                            >
                                                                <span className="material-symbols-outlined text-[20px]">remove</span>
                                                            </button>

                                                            <div className="flex-1 h-10 rounded-xl bg-accent-primary text-bg-dark font-black text-base flex items-center justify-center gap-2 shadow-lg shadow-accent-primary/20 pointer-events-none">
                                                                <span className="material-symbols-outlined text-[18px]">shopping_cart</span>
                                                                <span>{cartQty}</span>
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleAddProduct(product);
                                                                if (navigator.vibrate) navigator.vibrate(50);
                                                            }}
                                                            className="group/btn w-full h-10 rounded-xl transition-all flex items-center justify-center gap-2 font-black text-[10px] uppercase tracking-widest bg-bg-deep border border-border-dark text-text-muted hover:border-accent-primary/50 hover:bg-accent-primary/5 hover:text-white"
                                                        >
                                                            <span className="material-symbols-outlined text-[20px] group-hover/btn:text-accent-primary transition-colors">add_circle</span>
                                                            Agregar
                                                        </button>
                                                    )}
                                                </div>

                                                <div className="mt-2 flex items-center justify-center gap-1 opacity-40 group-hover:opacity-100 transition-opacity pointer-events-none">
                                                    <span className="material-symbols-outlined text-[12px] text-accent-primary">touch_app</span>
                                                    <span className="text-[8px] text-text-muted font-bold uppercase tracking-tighter">Mantén para personalizar</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div >

            {/* Right Panel: Cart / Summary (Full Height Floating on Desktop) */}
            < div className={`flex flex-col min-h-0 bg-card-dark border-border-dark shadow-2xl relative ${activeTab === 'menu' ? 'hidden lg:flex' : 'flex flex-1'} lg:fixed lg:top-4 lg:right-4 lg:bottom-4 lg:w-[380px] xl:w-[420px] 2xl:w-[460px] lg:rounded-2xl lg:border lg:z-50`}>
                <div className="p-4 pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4 border-b border-border-dark flex justify-between items-center bg-bg-deep/30 shrink-0">
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
                            {/* Existing Items (Editable if not ready/delivered) */}
                            {existingItems.length > 0 && (
                                <div className="space-y-3 relative">
                                    <div className="flex items-center gap-2 mb-2 sticky top-0 bg-bg-dark/95 backdrop-blur-sm z-10 py-1">
                                        <span className="h-[1px] flex-1 bg-border-dark"></span>
                                        <span className="text-[10px] font-black uppercase tracking-widest text-text-muted flex items-center gap-1.5">
                                            <span className="material-symbols-outlined text-[14px] text-accent-secondary">check_circle</span>
                                            En Pedido Actual
                                        </span>
                                        <span className="h-[1px] flex-1 bg-border-dark"></span>
                                    </div>

                                    {existingItems.map((item, idx) => {
                                        const canEditItem = ['pending', 'confirmed', 'preparing'].includes(orderStatus || '');

                                        return (
                                            <div key={`exist-${item.id}-${idx}`} className={`flex justify-between items-start gap-3 p-3 rounded-xl border transition-all ${canEditItem ? 'bg-card-dark border-border-dark/50 shadow-sm' : 'bg-card-dark/40 border-border-dark/30 opacity-80'}`}>
                                                <div className="flex-1 min-w-0">
                                                    <p className={`text-white text-sm font-bold truncate ${!canEditItem ? 'line-through decoration-white/20 opacity-60' : ''}`}>
                                                        {item.product_name}
                                                    </p>
                                                    <p className="text-text-muted text-[10px] font-mono">{formatPrice(item.unit_price)}</p>

                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {orderStatus === 'pending' && (
                                                            <span className="text-[8px] font-black uppercase text-blue-400 bg-blue-400/5 px-1.5 py-0.5 rounded border border-blue-400/20">Por Confirmar</span>
                                                        )}
                                                        {orderStatus === 'confirmed' && (
                                                            <span className="text-[8px] font-black uppercase text-status-success bg-status-success/5 px-1.5 py-0.5 rounded border border-status-success/20">Confirmado</span>
                                                        )}
                                                        {orderStatus === 'preparing' && (
                                                            <span className="text-[8px] font-black uppercase text-accent-secondary bg-accent-secondary/5 px-1.5 py-0.5 rounded border border-accent-secondary/10">En Cocina</span>
                                                        )}
                                                        {!canEditItem && (
                                                            <span className="text-[8px] font-black uppercase text-text-muted bg-white/5 px-1.5 py-0.5 rounded">Listo / Entregado</span>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex flex-col items-end gap-2">
                                                    {canEditItem ? (
                                                        <div className="flex items-center gap-1.5 bg-bg-deep rounded-xl p-1 border border-border-dark shadow-inner">
                                                            <button
                                                                onClick={() => handleUpdateExistingQuantity(item.id, Number(item.quantity) - 1)}
                                                                className="size-8 rounded-lg flex items-center justify-center text-text-muted hover:text-white hover:bg-white/5 transition-all text-xl"
                                                            >−</button>
                                                            <span className="text-white text-sm font-mono w-6 text-center font-bold">{Math.floor(item.quantity)}</span>
                                                            <button
                                                                onClick={() => handleUpdateExistingQuantity(item.id, Number(item.quantity) + 1)}
                                                                className="size-8 rounded-lg flex items-center justify-center text-accent-primary hover:bg-accent-primary/10 transition-all text-xl"
                                                            >+</button>
                                                        </div>
                                                    ) : (
                                                        <div className="size-9 rounded-lg bg-bg-deep border border-border-dark/30 flex items-center justify-center text-xs font-bold text-accent-secondary">
                                                            x{Math.floor(item.quantity)}
                                                        </div>
                                                    )}

                                                    {canEditItem && (
                                                        <button
                                                            onClick={() => handleRemoveExistingItem(item.id)}
                                                            className="text-[10px] text-status-alert hover:underline opacity-60 hover:opacity-100 transition-opacity flex items-center gap-1"
                                                        >
                                                            <span className="material-symbols-outlined text-[12px]">delete</span>
                                                            Eliminar
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}

                                    <div className="h-4"></div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        <span className="text-[10px] font-black uppercase tracking-widest text-accent-primary flex items-center gap-1.5">
                                            <span className="material-symbols-outlined text-[14px]">add_shopping_cart</span>
                                            Nuevos Productos
                                        </span>
                                        <span className="h-[1px] flex-1 bg-accent-primary/20"></span>
                                    </div>
                                </div>
                            )}

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
                                    onChange={handleUpdateDeliveryInfo}
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
                                    onChange={(e) => handleUpdateGeneralComment(e.target.value)}
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
                <div className="p-4 pb-[max(1rem,calc(1rem+env(safe-area-inset-bottom)))] lg:pb-4 border-t border-border-dark bg-bg-deep/80 backdrop-blur-md space-y-4">
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
                                {cartStep === 'items' ? 'Continuar' : (orderId ? 'Agregar al Pedido' : 'Confirmar Orden')}
                            </>
                        )}
                    </button>
                </div>

                {/* Pulse effect overlay when enabled */}
                {
                    !isSubmitting && orderItems.length > 0 && (
                        <span className="absolute inset-0 bg-white/10 animate-pulse pointer-events-none"></span>
                    )
                }
            </div >

            {/* Floating Quick Action / Category Menu Container (Mobile Only) */}
            < div className={`lg:hidden fixed right-4 z-50 flex flex-col items-end gap-3 pointer-events-none bottom-[max(1rem,calc(1rem+env(safe-area-inset-bottom)))]`}>
                {/* Backdrop for click-outside */}
                {
                    isCategoryMenuOpen && (
                        <div
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 pointer-events-auto"
                            onClick={() => setIsCategoryMenuOpen(false)}
                            style={{ zIndex: -1 }}
                        />
                    )
                }

                {/* Primary Navigation / Tab Switcher FAB */}
                <div className="flex flex-col items-end gap-3 pointer-events-auto">
                    {/* Cart/Menu Toggle Button */}
                    <button
                        onClick={() => setActiveTab(activeTab === 'menu' ? 'cart' : 'menu')}
                        className={`size-14 rounded-2xl shadow-2xl flex items-center justify-center transition-all active:scale-95 border-2 relative
                            ${activeTab === 'cart'
                                ? 'bg-accent-primary text-bg-dark border-accent-primary'
                                : 'bg-bg-deep/80 text-accent-primary border-white/10 backdrop-blur-md'}`}
                    >
                        <span className="material-symbols-outlined text-[28px]">
                            {activeTab === 'menu' ? 'shopping_cart' : 'restaurant_menu'}
                        </span>
                        {activeTab === 'menu' && orderItems.length > 0 && (
                            <span className="absolute -top-2 -left-2 size-6 bg-status-alert text-white rounded-full flex items-center justify-center text-[10px] font-black border-2 border-bg-deep ring-2 ring-status-alert/20 animate-bounce">
                                {orderItems.reduce((acc, curr) => acc + curr.quantity, 0)}
                            </span>
                        )}
                    </button>

                    {/* Main Action FAB (Continue/Confirm) - Only shows if we have items */}
                    {(orderItems.length > 0 || existingItems.length > 0) && (
                        <button
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className={`size-14 rounded-full shadow-2xl flex items-center justify-center transition-all active:scale-95 border-2 animate-in zoom-in slide-in-from-bottom-4 duration-300
                                ${cartStep === 'info'
                                    ? 'bg-status-success text-white border-status-success shadow-status-success/30'
                                    : 'bg-accent-secondary text-bg-dark border-accent-secondary shadow-accent-secondary/30'}`}
                        >
                            {isSubmitting ? (
                                <span className="material-symbols-outlined animate-spin">progress_activity</span>
                            ) : (
                                <span className="material-symbols-outlined text-[28px]">
                                    {cartStep === 'items' ? 'arrow_forward' : 'check_circle'}
                                </span>
                            )}
                        </button>
                    )}
                </div>

                {/* Categories List (Expands Upwards) */}
                <div className={`flex flex-col items-end gap-2 transition-all duration-300 origin-bottom pointer-events-auto ${isCategoryMenuOpen ? 'opacity-100 translate-y-0 scale-100 max-h-[60vh]' : 'opacity-0 translate-y-10 scale-90 pointer-events-none max-h-0 overflow-hidden'}`}>
                    <div className="max-h-[50vh] overflow-y-auto flex flex-col items-end gap-2 p-1 no-scrollbar pr-1">
                        <button
                            onClick={() => { setSelectedCategoryId('all'); setIsCategoryMenuOpen(false); }}
                            className={`px-4 py-2.5 rounded-xl text-xs font-bold backdrop-blur-md shadow-lg transition-all border border-white/5 active:scale-95 ${selectedCategoryId === 'all' ? 'bg-accent-primary text-bg-dark border-accent-primary' : 'bg-bg-deep/80 text-white hover:bg-bg-deep'}`}
                        >
                            Todas las Categorías
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

                {/* Category FAB Toggle */}
                <div className="flex items-center gap-3 pointer-events-auto mt-2">
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
                            {isCategoryMenuOpen ? 'close' : 'filter_list'}
                        </span>
                    </button>
                </div>
            </div >

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
                        onClose={handleModifierClose}
                        onConfirm={handleModifierConfirm}
                    />
                )
            }

            {/* Modal de Error de Stock */}
            {stockError && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-bg-card border border-border-subtle rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-300">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-red-500/20 to-orange-500/20 px-6 py-5 border-b border-border-subtle">
                            <div className="flex items-center gap-3">
                                <div className="size-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-red-400 text-[28px]">inventory_2</span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Stock Insuficiente</h3>
                                    <p className="text-text-muted text-sm">No hay inventario disponible</p>
                                </div>
                            </div>
                        </div>

                        {/* Body */}
                        <div className="p-6">
                            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4">
                                <p className="text-red-200 text-sm leading-relaxed">
                                    {stockError.message}
                                </p>
                            </div>

                            {stockError.ingredient && (
                                <div className="flex items-center gap-3 bg-bg-elevated rounded-xl p-4 mb-4">
                                    <span className="material-symbols-outlined text-amber-400">warning</span>
                                    <div>
                                        <p className="text-sm text-text-muted">Ingrediente faltante:</p>
                                        <p className="text-white font-semibold">{stockError.ingredient}</p>
                                    </div>
                                </div>
                            )}

                            <p className="text-text-muted text-sm leading-relaxed">
                                Para continuar, debes registrar una compra de este insumo o ajustar el inventario.
                            </p>
                        </div>

                        {/* Footer */}
                        <div className="px-6 pb-6 flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={handleClearStockError}
                                className="flex-1 px-4 py-3 rounded-xl text-text-secondary font-medium bg-bg-elevated hover:bg-bg-elevated/80 transition-colors"
                            >
                                Cerrar
                            </button>
                            <button
                                onClick={() => {
                                    handleClearStockError();
                                    if (stockError.ingredientType === 'MERCHANDISE') {
                                        navigate('/admin/setup?tab=BEBIDAS&subtab=INVENTORY');
                                    } else if (stockError.ingredientType === 'PROCESSED') {
                                        navigate('/kitchen/ingredients?tab=PROCESSED');
                                    } else if (stockError.ingredientType === 'PRODUCT') {
                                        navigate('/admin/inventory');
                                    } else {
                                        navigate('/kitchen/ingredients?tab=RAW');
                                    }
                                }}
                                className="flex-1 px-4 py-3 rounded-xl text-white font-bold bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transition-all flex items-center justify-center gap-2 shadow-lg"
                            >
                                <span className="material-symbols-outlined text-[20px]">inventory_2</span>
                                {stockError.ingredientType === 'MERCHANDISE' ? 'Ir a Venta Directa' :
                                    stockError.ingredientType === 'PROCESSED' ? 'Ir a Producción' :
                                        stockError.ingredientType === 'PRODUCT' ? 'Ir a Inventario General' :
                                            'Ir a Insumos'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

