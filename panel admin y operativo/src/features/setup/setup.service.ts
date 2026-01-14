import { api } from '../../lib/api';

// Interfaces based on backend schemas
export interface Product {
    id: number;
    name: string;
    price: number;
    stock: number;
    category_id?: number;
    category_name?: string;
    is_active: boolean;
    image_url?: string;
    description?: string;
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
    ingredient_product_id: number;
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
    ingredient_product_id: number;
    quantity: number;
    unit: string;
    ingredient?: Product; // Expanded by backend
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
        // Ideally filter by category_id of 'Materia Prima'
        // For now, get all and filter client side or assume we'll build a specific endpoint later
        // Optimally: await api.get('/products/?category_id=...');
        const res = await api.get('/products/');
        // We can't easily filter by category name without joining or separate call unless backend supports it
        // We'll rely on the UI to match IDs for now, or fetch all.
        // Let's assume we filter on frontend by the known category ID.
        return res.data;
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
    }
};
