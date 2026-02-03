import { api } from '../../lib/api';


export type MacroType = 'HOME' | 'INSUMOS' | 'PRODUCCION' | 'CARTA' | 'BEBIDAS' | 'EXTRAS';

export interface RecipeItemRow {
    ingredientId: number | string;
    name: string;
    cost: number;
    quantity: number;
    unit: string;
}

export interface Product {
    id: number | any;
    name: string;
    price: number;
    stock: number;
    category_id?: number;
    category_name?: string;
    is_active: boolean;
    image_url?: string;
    description?: string;
    unit?: string;
    sku?: string;
    min_stock?: number;
}

export interface Ingredient extends Product {
    // Ingredients are just products, but we might add UI specific fields
    unit?: string; // For recipe context
}

export interface Category {
    id: number;
    name: string;
    description?: string;
}

export interface RecipeItem {
    ingredient_product_id?: number | null;
    ingredient_id?: string | null;
    quantity: number;
    unit: string;
}

export interface RecipePayload {
    product_id: number;
    name: string;
    description?: string;
    items: RecipeItem[];
}

export interface ModifierRecipeItem {
    id: number;
    modifier_id: number;
    ingredient_product_id?: number | null;
    ingredient_id?: string | null;
    quantity: number;
    unit: string;
    ingredient?: Product; // Expanded by backend (Legacy)
    ingredient_ref?: any; // Expanded by backend (New V4.1)
}

export interface ProductModifier {
    id: number;
    company_id: number;
    name: string;
    description?: string;
    extra_price: number;
    is_active: boolean;
    recipe_items?: ModifierRecipeItem[];
}

// NEW: Beverage creation payload (1:1 Bridge Pattern)
export interface BeveragePayload {
    name: string;
    cost: number;         // Costo compra (para Ingredient)
    sale_price: number;   // Precio venta (para Product)
    initial_stock: number;
    unit: string;
    image_url?: string;
    category_id?: number;
    description?: string;
    sku?: string;
    supplier?: string;
    category_name?: string;
}

export interface BeverageResponse {
    product: Product;
    ingredient: any; // Simplified, backend returns full ingredient
    recipe: any;
    message: string;
}

const INGREDIENT_CATEGORY_NAME = 'Materia Prima';

export const setupService = {
    // --- Categories ---
    async getCategories(): Promise<Category[]> {
        const res = await api.get('/categories/');
        return res.data;
    },

    async ensureIngredientCategory(): Promise<number> {
        // 1. Check if exists locally/fetched
        let categories = await this.getCategories();
        let existing = categories.find(c => c.name.toLowerCase() === INGREDIENT_CATEGORY_NAME.toLowerCase());
        if (existing) return existing.id;

        // 2. Try to create
        try {
            const res = await api.post('/categories/', {
                name: INGREDIENT_CATEGORY_NAME,
                description: 'Insumos básicos para recetas',
                is_active: true
            });
            return res.data.id;
        } catch (error: any) {
            // 3. Handle race condition (Duplicate entry)
            // If creation failed but category exists (due to race condition), fetch again
            if (error.response && error.response.status === 400) {
                categories = await this.getCategories();
                existing = categories.find(c => c.name.toLowerCase() === INGREDIENT_CATEGORY_NAME.toLowerCase());
                if (existing) return existing.id;
            }
            throw error;
        }
    },

    async createCategory(name: string, description: string = ''): Promise<Category> {
        const res = await api.post('/categories/', {
            name,
            description, // Now uses the passed description (tag)
            is_active: true
        });
        return res.data;
    },

    async updateCategory(id: number, data: Partial<Category>): Promise<Category> {
        const res = await api.put(`/categories/${id}`, data);
        return res.data;
    },

    // --- Ingredients (Products) ---
    async createIngredient(data: Partial<Product>): Promise<Product> {
        const categoryId = await this.ensureIngredientCategory();
        const payload = {
            ...data,
            category_id: categoryId,
            price: Number(data.price) || 0, // Insumos might verify price > 0
            stock: Number(data.stock) || 0,
            tax_rate: 0,
            is_active: true,
            description: 'Ingrediente'
        };
        const res = await api.post('/products/', payload);
        return res.data;
    },

    async getIngredients(): Promise<Product[]> {
        // Use the dedicated Ingredients endpoint to get Stock/WAC data
        const res = await api.get('/ingredients/');
        // Normalize response to match Product interface expectations (price, unit)
        return res.data.map((ing: any) => ({
            ...ing,
            price: Number(ing.current_cost) || 0,
            unit: ing.base_unit || 'UNIDAD'
        }));
    },

    // --- Products (Menu) ---
    async createProduct(data: Partial<Product>): Promise<Product> {
        const payload = {
            ...data,
            price: Number(data.price) || 0,
            stock: Number(data.stock) || 0,
            tax_rate: 0,
            is_active: true
        };
        const res = await api.post('/products/', payload);
        return res.data;
    },

    async updateProduct(id: number, data: Partial<Product>): Promise<Product> {
        // Ensure numbers
        const payload = {
            ...data,
            price: Number(data.price) || 0,
            stock: Number(data.stock) || 0
        };
        const res = await api.put(`/products/${id}`, payload);
        return res.data;
    },

    async getProducts(): Promise<Product[]> {
        const res = await api.get('/products/');
        return res.data;
    },

    // --- Recipes ---
    async createRecipe(payload: RecipePayload): Promise<void> {
        await api.post('/recipes/', payload);
    },

    async getRecipes(): Promise<any[]> {
        const res = await api.get('/recipes/');
        return res.data;
    },

    async getRecipeByProduct(productId: number): Promise<any> {
        try {
            const res = await api.get(`/recipes/by-product/${productId}`);
            return res.data;
        } catch (error: any) {
            if (error.response && error.response.status === 404) {
                return null;
            }
            throw error;
        }
    },

    async updateRecipeItems(recipeId: number, items: RecipeItem[]): Promise<void> {
        await api.put(`/recipes/${recipeId}/items`, { items });
    },

    async uploadImage(file: File): Promise<string> {
        const formData = new FormData();
        formData.append('file', file);
        const res = await api.post('/uploads/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return res.data.url;
    },

    // --- Modifiers (Extras) ---
    async getModifiers(): Promise<ProductModifier[]> {
        const res = await api.get('/modifiers/');
        return res.data;
    },

    async createModifier(data: Partial<ProductModifier>): Promise<ProductModifier> {
        const payload = {
            ...data,
            extra_price: Number(data.extra_price) || 0,
            is_active: true
        };
        const res = await api.post('/modifiers/', payload);
        return res.data;
    },

    async updateModifier(id: number, data: Partial<ProductModifier>): Promise<ProductModifier> {
        const payload = {
            ...data,
            extra_price: Number(data.extra_price) || 0
        };
        const res = await api.put(`/modifiers/${id}`, payload);
        return res.data;
    },

    async updateModifierRecipe(modifierId: number, items: RecipeItem[]): Promise<ProductModifier> {
        const res = await api.put(`/modifiers/${modifierId}/recipe`, items);
        return res.data;
    },

    // NEW: Beverages / Merchandise (1:1 Bridge Pattern)
    async createBeverage(data: BeveragePayload, branchId: number): Promise<BeverageResponse> {
        const res = await api.post(`/products/beverage?branch_id=${branchId}`, data);
        return res.data;
    },

    async updateBeverage(id: number, data: BeveragePayload, branchId: number): Promise<BeverageResponse> {
        // Use cascade endpoint that updates Product + Ingredient
        const payload = {
            name: data.name,
            cost: data.cost,
            sale_price: data.sale_price,
            image_url: data.image_url,
            category_id: data.category_id,
            sku: data.sku,
            supplier: data.supplier
        };
        console.log('[updateBeverage] Request:', { id, branchId, payload });
        const res = await api.put(`/products/beverage/${id}?branch_id=${branchId}`, payload);
        console.log('[updateBeverage] Response:', res.data);
        return res.data;
    },

    async deleteBeverage(id: number): Promise<void> {
        // Use cascade endpoint that soft-deletes Product + Ingredient + Batches
        await api.delete(`/products/beverage/${id}`);
    },

    async updateIngredientStock(ingredientId: string, quantity: number, type: 'IN' | 'OUT' | 'ADJ' | 'ADJUST', reason?: string): Promise<any> {
        const payload = {
            quantity: Number(quantity),
            transaction_type: type,
            reason
        };
        const res = await api.post(`/ingredients/${ingredientId}/stock`, payload);
        return res.data;
    },

    async updateIngredientSettings(ingredientId: string, minStock: number, maxStock?: number): Promise<any> {
        const payload = {
            min_stock: Number(minStock),
            max_stock: maxStock ? Number(maxStock) : undefined
        };
        const res = await api.patch(`/ingredients/${ingredientId}/inventory`, payload);
        return res.data;
    },

    async getIngredientHistory(ingredientId: string | number, limit: number = 20): Promise<any[]> {
        const res = await api.get(`/ingredients/${ingredientId}/history`, { params: { limit } });
        return res.data;
    },

    async getGlobalAuditHistory(limit: number = 100): Promise<any[]> {
        const res = await api.get(`/ingredients/audits/history`, { params: { limit } });
        return res.data;
    },

    async revertTransaction(transactionId: string, reason: string): Promise<any> {
        const res = await api.post(`/ingredients/transactions/${transactionId}/revert`, { reason });
        return res.data;
    }
};
