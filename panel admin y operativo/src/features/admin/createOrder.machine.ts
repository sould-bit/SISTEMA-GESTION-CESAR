import { createMachine, assign, fromPromise, setup } from 'xstate';
import { setupService, Product, Category, ProductModifier } from '../setup/setup.service';
import { api } from '../../lib/api';

export interface OrderItem {
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    modifiers?: number[];
    removed_ingredients?: string[];
    comment?: string;
}

export interface DeliveryDetails {
    customer_name: string;
    customer_phone: string;
    delivery_address: string;
    delivery_notes: string;
}

export interface CreateOrderContext {
    // Data
    products: Product[];
    categories: Category[];
    recipes: any[];
    globalModifiers: ProductModifier[];
    permissions: string[]; // Sincronizado desde Redux

    // State
    orderItems: OrderItem[];
    existingItems: any[];
    existingOrderStatus: string | null;
    deliveryDetails: DeliveryDetails;
    searchTerm: string;
    selectedCategoryId: number | 'all';
    generalComment: string;

    // UI selection
    selectedProductForMod: Product | null;
    editingCartItemIndex: number | null;

    // External Info
    tableId?: number;
    tableNumber?: string;
    branchId: number;
    deliveryType: 'dine_in' | 'takeaway' | 'delivery';
    existingOrderId?: number;

    // Errors/Loading
    error: string | null;
    stockError: { message: string; ingredient?: string; ingredientType?: string } | null;
    isAwaitingCancellation?: boolean;
}

export type CreateOrderEvent =
    | { type: 'SET_SEARCH'; term: string }
    | { type: 'SELECT_CATEGORY'; categoryId: number | 'all' }
    | { type: 'ADD_ITEM'; product: Product; removed?: string[]; mods?: number[]; comment?: string }
    | { type: 'UPDATE_QUANTITY'; index: number; delta: number }
    | { type: 'REMOVE_ITEM'; index: number }
    | { type: 'OPEN_MODAL'; product: Product; index?: number }
    | { type: 'CLOSE_MODAL' }
    | { type: 'CONFIRM_MODS'; removed: string[]; mods: number[]; comment?: string }
    | { type: 'SET_DELIVERY_INFO'; details: Partial<DeliveryDetails> }
    | { type: 'SET_GENERAL_COMMENT'; comment: string }
    | { type: 'CLEAR_STOCK_ERROR' }
    | { type: 'NEXT_STEP' }
    | { type: 'PREV_STEP' }
    | { type: 'SUBMIT' }
    | { type: 'RETRY' }
    | { type: 'UPDATE_EXISTING_QUANTITY'; itemId: number; quantity: number }
    | { type: 'REMOVE_EXISTING_ITEM'; itemId: number };

export const createOrderMachine = setup({
    types: {
        context: {} as CreateOrderContext,
        events: {} as CreateOrderEvent,
        input: {} as {
            tableId?: number;
            tableNumber?: string;
            branchId: number;
            deliveryType: 'dine_in' | 'takeaway' | 'delivery';
            existingOrderId?: number;
            permissions: string[];
        },
    },
    guards: {
        canCreateOrder: ({ context }) => context.permissions.includes('orders.update'),
        canCancelDirectly: ({ context }) => context.permissions.includes('orders.cancel'),
        canRequestCancellation: ({ context }) =>
            context.permissions.includes('orders.update') && !context.permissions.includes('orders.cancel'),
    },
    actions: {
        updateExistingQuantity: assign({
            existingItems: ({ context, event }) => {
                if (event.type !== 'UPDATE_EXISTING_QUANTITY') return context.existingItems;
                if (event.quantity <= 0) {
                    return context.existingItems.filter(i => i.id !== event.itemId);
                }
                return context.existingItems.map(item =>
                    item.id === event.itemId ? { ...item, quantity: event.quantity } : item
                );
            }
        }),
        removeExistingItem: assign({
            existingItems: ({ context, event }) => {
                if (event.type !== 'REMOVE_EXISTING_ITEM') return context.existingItems;
                return context.existingItems.filter(i => i.id !== event.itemId);
            }
        }),
        handleConfirmMods: assign({
            orderItems: ({ context, event }) => {
                if (event.type !== 'CONFIRM_MODS' || !context.selectedProductForMod) return context.orderItems;

                const { removed, mods, comment } = event;

                if (context.editingCartItemIndex !== null) {
                    const newItems = [...context.orderItems];
                    newItems[context.editingCartItemIndex] = {
                        ...newItems[context.editingCartItemIndex],
                        removed_ingredients: removed,
                        modifiers: mods,
                        comment: comment
                    };
                    return newItems;
                } else {
                    return [...context.orderItems, {
                        product_id: context.selectedProductForMod.id,
                        product_name: context.selectedProductForMod.name,
                        quantity: 1,
                        unit_price: Number(context.selectedProductForMod.price),
                        removed_ingredients: removed,
                        modifiers: mods,
                        comment: comment || ''
                    }];
                }
            }
        }),
        addItem: assign({
            orderItems: ({ context, event }) => {
                if (event.type !== 'ADD_ITEM') return context.orderItems;
                const { product, removed = [], mods = [], comment = '' } = event;

                const existingIndex = context.orderItems.findIndex(item =>
                    item.product_id === product.id &&
                    JSON.stringify([...(item.removed_ingredients || [])].sort()) === JSON.stringify([...removed].sort()) &&
                    JSON.stringify([...(item.modifiers || [])].sort()) === JSON.stringify([...mods].sort()) &&
                    (item.comment || '') === comment
                );

                if (existingIndex >= 0) {
                    const newItems = [...context.orderItems];
                    newItems[existingIndex] = {
                        ...newItems[existingIndex],
                        quantity: newItems[existingIndex].quantity + 1
                    };
                    return newItems;
                }

                return [...context.orderItems, {
                    product_id: product.id,
                    product_name: product.name,
                    quantity: 1,
                    unit_price: product.price,
                    removed_ingredients: removed,
                    modifiers: mods,
                    comment
                }];
            }
        }),
        updateQuantity: assign({
            orderItems: ({ context, event }) => {
                if (event.type !== 'UPDATE_QUANTITY') return context.orderItems;
                return context.orderItems.map((item, idx) => {
                    if (idx === event.index) {
                        return { ...item, quantity: Math.max(0, item.quantity + event.delta) };
                    }
                    return item;
                }).filter(item => item.quantity > 0);
            }
        }),
        removeItem: assign({
            orderItems: ({ context, event }) => {
                if (event.type !== 'REMOVE_ITEM') return context.orderItems;
                return context.orderItems.filter((_, idx) => idx !== event.index);
            }
        }),
    },
    actors: {
        loadData: fromPromise(async ({ input }: { input: { existingOrderId?: number } }) => {
            const [productsData, recipesData, categoriesData, modifiersData] = await Promise.all([
                setupService.getProducts(),
                setupService.getRecipes(),
                setupService.getCategories(),
                setupService.getModifiers()
            ]);

            let existingItems = [];
            let existingOrderStatus = null;
            let existingNotes = '';
            let existingCustomerNotes = '';

            if (input.existingOrderId) {
                try {
                    const orderRes = await api.get(`/orders/${input.existingOrderId}`);
                    existingItems = orderRes.data.items || [];
                    existingOrderStatus = orderRes.data.status;
                    existingNotes = orderRes.data.notes || '';
                    existingCustomerNotes = orderRes.data.customer_notes || '';
                } catch (e) {
                    console.error('Error fetching existing order:', e);
                }
            }

            return {
                products: productsData.filter(p => p.is_active && p.category_name?.toLowerCase() !== 'materia prima'),
                categories: categoriesData.filter(c => c.name.toLowerCase() !== 'materia prima'),
                recipes: recipesData,
                globalModifiers: modifiersData.filter(m => m.is_active),
                existingItems,
                existingOrderStatus,
                existingNotes,
                existingCustomerNotes
            };
        }),
        submitOrder: fromPromise(async ({ input }: { input: { context: CreateOrderContext } }) => {
            const { context } = input;
            const items = context.orderItems.map((item: OrderItem) => ({
                product_id: item.product_id,
                quantity: item.quantity,
                modifiers: item.modifiers,
                removed_ingredients: item.removed_ingredients,
                notes: item.comment
            }));

            if (context.existingOrderId) {
                await api.post(`/orders/${context.existingOrderId}/items`, items);
            } else {
                const payload = {
                    branch_id: context.branchId || 1,
                    table_id: context.tableId,
                    delivery_type: context.deliveryType || 'dine_in',
                    items,
                    delivery_customer_name: context.deliveryDetails.customer_name,
                    delivery_customer_phone: context.deliveryDetails.customer_phone,
                    delivery_address: context.deliveryDetails.delivery_address,
                    delivery_notes: context.deliveryDetails.delivery_notes,
                    notes: ''
                };
                await api.post('/orders/', payload);
            }
        })
    }
}).createMachine({
    /** @xstate-layout N4IgpgJg5mDOIC5QGMBOYCGAXMB5VEYqAdADYD2GEAlgHZQDEE5tYxdAbuQNZtqY58hEhSp0oCTuWTZqLANoAGALpLliUAAdysaljm0NIAB6IATGYAsxAMw2A7AFYAjGYBsADkdmbixwBoQAE9Ee0tHYnc3N3sPNxdFaIBfJMD+bDwCIjJKGnoGIlRyEk1SbAAzYoBbYnTBLJFc8UlaLhl9BRU1I21dDsMkE3MrWwcXdy8fP0CQhABORzdiRTnnGOdHObNFG1cUtPQMoWzi4XEGAGUAUQAVAH1rgEEAJQBhAAluwd69AyNTBCuez2WyWBweRRWDw2DweMwzRAwxTENyWOYLVGuSweOao-YgOqZYTEU5Ec7XAAyV1e91ejxuVwA4rhngBNL5aHS-Fj-RCuRbLMyORTOVZo+w2OaWBEIMweayi9H2CzQxKrfGE44kUmoc6PAAi+ruAEkGQBZDkgH79XmAuXWGyeYEOR3OSzw4J8jwgsLo2EbR3Yxw2DWHerEnXnACqAAV9fSrncAIpRx4AORupvZKh6XJtgwB-JstidcTB0UskJlzhsZjmxEVUrRlmVeNSBLDRJODXOzyuZtwADVE6b+5brX8C3yzPZkbtvXF7G5EjZLG5qz4zMRfbjFB5nLEwZZQwIu9qe-lcDGrmm7gP4xTx3nJ6BC3Ni5Y0XN94k3K4Nh4Mr7rYiigYolZWBY9hzPYJ5HA0JIXowsbxgydxXAAGsaFyZmmjLJqmGZZk+fQvkMdrOB4yxOt4qr2Ae0qeoCNZLHWSrRLC7ohu2moIZG+R9gOw7oVhOHGnhJrmiR3IDK+fIbPWS7erOKzOAe0LVjs9byuiWyOJsoFWHB4bdmcAn9kOiaYdhuH4aOFrOOo3zPjyU7MXK277jOIoODEYIylKH5gXu7oLPuczGWeiFmVAxBVGAtAAK4MGmmH3DhVwxtJ+ZyfMuK2N6+kWG475WAETFuD425gau7ruqiZiRVq0VkvQxDoBw1BgAA7ucqUYelDJZTmzmka5uU1iMZj8up3q1t4MqVaxNWfpBDVNXxSHtWAnU9ecMZ9oODxDdlZGFokW6OkKta1k48Qyo4YTLGBy6WJRUrxBtEZbXQlSXFGABCZqmqd43kUKyJqddlb6cKjjutWYLFqi6J1ooS6eJ+X2ma1sW-eQDAHVcR0ZcNTmcmNsnkZNETfr6VhqdBlUPUuxDCqBr3vWujjY+eMXsLQf3XPc+pXBSxrDmyJppgAYrgoNU4W2IghClWhbWaLOIt7rEDpWxxAs+nerzLW6m1+OXLcdyMjeVzPI8FJ3K8uBmmaN43ArtpujEuuFX4ficbCD1rrYumfosf4wo1PGds1yCJbAWDkFU1AAF7nK8FK4Ncd64A+ntuZRH5fj+0T-o4gFMZs9aayVy5yt6Cwm-HifJ2nGe4LLxrPGauf6hcBcTe+xCfn6zi-uXlezBY1iQl+y6wu+cI8zHp7NbAiUAEYp1g+j5MwrAC1wvC1LHCEb9veh7xIUjtAYaiD+Dy4NkWMP6X4jGzGplbbqsMRLtsXEyoTYXx3tfAoqAiglDKFgSoqAai8WJKAq+zRb6yE6KoEaFMZK2ncJDV+fh37w00tiEeb0-LLhRlsE2hRigMD7DcNkj8ASogiDYdmdh+Q+G9AFWEkQ-5SjmHuDYKwaGQLoZnK4Lxjq4FeAAaXQs8Z4LJmGIE-MiNc0MZz7hxEuICcRiBSjWBCAC3F2y0HIIQeAgxEFEFzJTW0ABadcTFnEm1EHkKA9icFuQRkxJwIJhTQjXAsGssITb8S8aNHxuVoQ+kKvDSqMJ9YynCPWFY6IYZvVWJCCJW14pJW8TlcisIIixCcIk7hKSKobG3GsCsmxI5hDyfzDqXVer0CKWdeS6JIiVXhuKNcB4XGzD-FRaa0RWG4hrM01e8Fvr83xl0sGhZgxbnAmMSqaxvxzBlGEawbFVhyisDBd8zcE5JxTunTp0TikAj8V-GsDZ2ZFxFOPUCEU5kmRIMg3e4hlmKzUR6L+apljkM2AeTY7huIHDXufRKyBkBwGsdgu5ajwgj36aubR709FMTUjCBs5DojKlxKtMRUCAW2mxDXMYvhFi7FRrwqikp6numUtsFeKQgA */
    id: 'createOrder',
    context: ({ input }) => ({
        products: [],
        categories: [],
        recipes: [],
        globalModifiers: [],
        orderItems: [],
        existingItems: [],
        existingOrderStatus: null,
        deliveryDetails: {
            customer_name: '',
            customer_phone: '',
            delivery_address: '',
            delivery_notes: ''
        },
        searchTerm: '',
        permissions: input.permissions || [],
        selectedCategoryId: 'all',
        generalComment: '',
        selectedProductForMod: null,
        editingCartItemIndex: null,
        branchId: input.branchId,
        tableId: input.tableId,
        tableNumber: input.tableNumber,
        deliveryType: input.deliveryType,
        existingOrderId: input.existingOrderId,
        error: null,
        stockError: null
    }),
    initial: 'loading',
    states: {
        loading: {
            invoke: {
                src: 'loadData',
                input: ({ context }) => ({ existingOrderId: context.existingOrderId }),
                onDone: {
                    target: 'ordering',
                    actions: assign({
                        products: ({ event }) => event.output.products,
                        categories: ({ event }) => event.output.categories,
                        recipes: ({ event }) => event.output.recipes,
                        globalModifiers: ({ event }) => event.output.globalModifiers,
                        existingItems: ({ event }) => event.output.existingItems,
                        existingOrderStatus: ({ event }) => event.output.existingOrderStatus,
                        generalComment: ({ context, event }) => event.output.existingNotes || context.generalComment,
                        deliveryDetails: ({ context, event }) => ({
                            ...context.deliveryDetails,
                            delivery_notes: event.output.existingCustomerNotes || context.deliveryDetails.delivery_notes
                        })
                    })
                },
                onError: {
                    target: 'error',
                    actions: assign({ error: ({ event }) => (event.error as Error).message })
                }
            }
        },
        ordering: {
            initial: 'menu',
            on: {
                SET_SEARCH: {
                    actions: assign({ searchTerm: ({ event }) => event.term })
                },
                SELECT_CATEGORY: {
                    actions: assign({ selectedCategoryId: ({ event }) => event.categoryId })
                },
                ADD_ITEM: {
                    actions: 'addItem'
                },
                UPDATE_QUANTITY: {
                    actions: 'updateQuantity'
                },
                REMOVE_ITEM: {
                    actions: 'removeItem'
                },
                OPEN_MODAL: {
                    target: 'customizing',
                    actions: assign({
                        selectedProductForMod: ({ event }) => event.product,
                        editingCartItemIndex: ({ event }) => event.index ?? null
                    })
                },
                UPDATE_EXISTING_QUANTITY: {
                    actions: 'updateExistingQuantity'
                },
                REMOVE_EXISTING_ITEM: [
                    {
                        guard: 'canCancelDirectly',
                        actions: 'removeExistingItem'
                    },
                    {
                        guard: 'canRequestCancellation',
                        actions: assign({ isAwaitingCancellation: true })
                    }
                ]
            },
            states: {
                menu: {
                    on: {
                        NEXT_STEP: {
                            target: 'reviewing',
                            guard: ({ context }) => context.orderItems.length > 0
                        }
                    }
                },
                reviewing: {
                    on: {
                        NEXT_STEP: 'info',
                        PREV_STEP: 'menu'
                    }
                },
                info: {
                    on: {
                        SUBMIT: {
                            target: '#createOrder.submitting',
                            guard: 'canCreateOrder'
                        },
                        PREV_STEP: 'reviewing',
                        SET_DELIVERY_INFO: {
                            actions: assign({
                                deliveryDetails: ({ context, event }) => ({
                                    ...context.deliveryDetails,
                                    ...event.details
                                })
                            })
                        },
                        SET_GENERAL_COMMENT: {
                            actions: assign({ generalComment: ({ event }) => event.comment })
                        }
                    }
                }
            }
        },
        customizing: {
            on: {
                CLOSE_MODAL: {
                    target: 'ordering.menu',
                    actions: assign({
                        selectedProductForMod: null,
                        editingCartItemIndex: null
                    })
                },
                CONFIRM_MODS: {
                    target: 'ordering.menu',
                    actions: ['handleConfirmMods', assign({
                        selectedProductForMod: null,
                        editingCartItemIndex: null
                    })]
                }
            }
        },
        submitting: {
            invoke: {
                src: 'submitOrder',
                input: ({ context }) => ({ context }),
                onDone: {
                    target: 'success'
                },
                onError: {
                    target: 'error',
                    actions: assign({
                        error: ({ event }) => (event.error as any)?.response?.data?.detail || (event.error as Error).message,
                        stockError: ({ event }) => {
                            const detail = (event.error as any)?.response?.data?.detail || '';
                            if (detail.includes('insuficiente')) {
                                const match = detail.match(/insuficiente\s+(.+)\.\s*Disponible/i);
                                const matchType = detail.match(/Tipo:\s*(?:IngredientType\.)?(\w+)/i);
                                return {
                                    message: detail,
                                    ingredient: match ? match[1].trim() : undefined,
                                    ingredientType: matchType ? matchType[1].trim() : 'RAW'
                                };
                            }
                            return null;
                        }
                    })
                }
            }
        },
        success: {
            type: 'final'
        },
        error: {
            on: {
                RETRY: 'ordering.info',
                CLEAR_STOCK_ERROR: {
                    actions: assign({ stockError: null })
                }
            }
        }
    }
});
