/**
 * Kitchen Service - Centralized API layer for Kitchen Management
 * 
 * Handles:
 * - Ingredients (Materia Prima)
 * - Recipes (Constructor de Recetas Vivas)
 * - Menu Engineering (BCG Matrix)
 */

import { api } from '@/lib/api';

// ============================================
// TYPES - Aligned with Backend V4.1
// ============================================

export interface ProductSummary {
    id: number;
    name: string;
    price: number;
    stock: number;
    category_id?: number;
    category_name?: string;
}

export interface Category {
    id: number;
    name: string;
    description?: string;
    is_active: boolean;
}

export interface ProductCreate {
    name: string;
    price: number;
    category_id?: number;
    description?: string;
    stock?: number;
    image_url?: string;
}

export interface Ingredient {
    id: string;
    name: string;
    sku: string;
    base_unit: 'kg' | 'lt' | 'und' | 'g' | 'ml';
    current_cost: number;
    last_cost: number;
    yield_factor: number; // Merma (0.90 = 90% aprovechable)
    category_id?: number;
    company_id: number;
    ingredient_type: 'RAW' | 'PROCESSED' | 'MERCHANDISE';
    is_active: boolean;
    stock?: number;
    total_inventory_value?: number;
    calculated_cost?: number;
    created_at?: string;
    updated_at?: string;
}

export interface IngredientCostHistory {
    id: string;
    previous_cost: number;
    new_cost: number;
    reason?: string;
    user_id?: number;
    created_at: string;
}

export interface IngredientBatch {
    id: string;
    quantity_initial: number;
    quantity_remaining: number;
    cost_per_unit: number;
    total_cost: number;
    acquired_at: string;
    is_active: boolean;
    supplier?: string;
}

export interface IngredientCreate {
    name: string;
    sku: string;
    base_unit: 'kg' | 'lt' | 'und' | 'g' | 'ml';
    current_cost: number;
    ingredient_type: 'RAW' | 'PROCESSED';
    yield_factor?: number;
    category_id?: number;
}

export interface IngredientUpdate {
    name?: string;
    sku?: string;
    base_unit?: 'kg' | 'lt' | 'und' | 'g' | 'ml';
    current_cost?: number;
    ingredient_type?: 'RAW' | 'PROCESSED';
    yield_factor?: number;
    category_id?: number;
    is_active?: boolean;
}

export interface RecipeItem {
    id?: string; // Add ID if present
    ingredient_id: string;
    ingredient_name?: string; // Populate from backend
    gross_quantity: number;
    measure_unit: string;
    // Calculated fields
    net_quantity?: number;
    calculated_cost?: number;
}

export interface RecipePayload {
    product_id: number;
    name: string;
    preparation_time?: number;
    items: RecipeItem[];
}

export interface Recipe {
    id: number;  // INTEGER in database
    product_id: number;
    product_name?: string; // Populate from backend
    product_image_url?: string; // Product image URL
    category_id?: number;  // Category of the product
    category_name?: string; // Category name for grouping
    name: string;
    version: number;
    is_active: boolean;
    batch_yield: number;
    total_cost: number;
    preparation_time: number;
    recipe_type: 'REAL' | 'AUTO' | 'PROCESSED';  // Type of recipe
    items: RecipeItem[];
    items_count?: number; // Count from backend for list views
}

export interface MenuEngineeringProduct {
    product_id: number;
    product_name: string;
    category: string;
    price: number;
    cost: number;
    quantity_sold: number;
    revenue: number;
    contribution_margin: number;
    food_cost_pct: number;
    popularity_pct: number;
    revenue_share: number;
    classification: 'star' | 'plowhorse' | 'puzzle' | 'dog';
}

export interface MenuEngineeringReport {
    period: { start: string; end: string };
    summary: {
        total_products: number;
        total_revenue: number;
        total_quantity_sold: number;
        avg_popularity_threshold: number;
        avg_margin_threshold: number;
    };
    classification_counts: {
        stars: number;
        plowhorses: number;
        puzzles: number;
        dogs: number;
    };
    matrix: {
        stars: MenuEngineeringProduct[];
        plowhorses: MenuEngineeringProduct[];
        puzzles: MenuEngineeringProduct[];
        dogs: MenuEngineeringProduct[];
    };
    all_products: MenuEngineeringProduct[];
}

export interface CostSimulation {
    items: RecipeItem[];
    projected_cost: number;
    suggested_price: number;
    margin_percent: number;
}

// ============================================
// SERVICE - Kitchen API
// ============================================

export const kitchenService = {
    // ─────────────────────────────────────────
    // 1. INGREDIENTS (Materia Prima / Insumos)
    // ─────────────────────────────────────────

    getIngredients: async (search?: string, ingredientType?: string, activeOnly: boolean = true): Promise<Ingredient[]> => {
        const params: any = {};
        if (search) params.search = search;
        if (ingredientType) params.ingredient_type = ingredientType;
        params.active_only = activeOnly;

        const { data } = await api.get<Ingredient[]>('/ingredients/', { params });
        return data;
    },

    // Products
    getProducts: async (search?: string): Promise<ProductSummary[]> => {
        const params: any = {};
        if (search) params.search = search;
        const { data } = await api.get<ProductSummary[]>('/products', { params });
        return data;
    },

    getProduct: async (id: number): Promise<ProductSummary> => {
        const { data } = await api.get<ProductSummary>(`/products/${id}`);
        return data;
    },

    createProduct: async (product: ProductCreate): Promise<ProductSummary> => {
        const { data } = await api.post<ProductSummary>('/products/', product);
        return data;
    },

    // Categories
    getCategories: async (): Promise<Category[]> => {
        const { data } = await api.get<Category[]>('/categories/');
        return data;
    },

    createCategory: async (name: string, description?: string): Promise<Category> => {
        const { data } = await api.post<Category>('/categories/', {
            name,
            description: description || '',
            is_active: true
        });
        return data;
    },

    updateCategory: async (id: number, name: string, description?: string, is_active: boolean = true): Promise<Category> => {
        const payload: any = { name, is_active };
        if (description !== undefined) {
            payload.description = description;
        }
        console.log(`[updateCategory] Payload for ID ${id}:`, payload);
        const { data } = await api.put<Category>(`/categories/${id}`, payload);
        return data;
    },

    getIngredient: async (id: string): Promise<Ingredient> => {
        const { data } = await api.get<Ingredient>(`/ingredients/${id}`);
        return data;
    },

    createIngredient: async (payload: IngredientCreate): Promise<Ingredient> => {
        const { data } = await api.post<Ingredient>('/ingredients/', payload);
        return data;
    },

    updateIngredient: async (id: string, payload: IngredientUpdate): Promise<Ingredient> => {
        const { data } = await api.patch<Ingredient>(`/ingredients/${id}`, payload);
        return data;
    },

    deleteIngredient: async (id: string): Promise<void> => {
        await api.delete(`/ingredients/${id}`);
    },

    async updateIngredientCost(id: string, new_cost: number, reason?: string) {
        const response = await api.post(`/ingredients/${id}/update-cost`, {
            new_cost,
            reason
        });
        return response.data;
    },

    async updateIngredientStock(id: string, quantity: number, transaction_type: 'IN' | 'OUT' | 'ADJUST', reason?: string, cost_per_unit?: number, supplier?: string) {
        const response = await api.post(`/ingredients/${id}/stock`, {
            quantity,
            transaction_type,
            reason,
            cost_per_unit,
            supplier
        });
        return response.data;
    },

    async getIngredientBatches(id: string, activeOnly: boolean = true): Promise<IngredientBatch[]> {
        const params = { active_only: activeOnly };
        const { data } = await api.get<IngredientBatch[]>(`/ingredients/${id}/batches`, { params });
        return data;
    },

    async getIngredientHistory(id: string): Promise<IngredientCostHistory[]> {
        const { data } = await api.get<IngredientCostHistory[]>(`/ingredients/${id}/history`);
        return data;
    },

    async updateBatch(batchId: string, updates: {
        quantity_initial?: number;
        quantity_remaining?: number;
        cost_per_unit?: number;
        total_cost?: number;
        supplier?: string;
        is_active?: boolean
    }): Promise<IngredientBatch> {
        const { data } = await api.patch<IngredientBatch>(`/ingredients/batches/${batchId}`, updates);
        return data;
    },

    async deleteBatch(batchId: string): Promise<void> {
        await api.delete(`/ingredients/batches/${batchId}`);
    },

    // ─────────────────────────────────────────
    // 2. RECIPES (Constructor de Recetas)
    // ─────────────────────────────────────────

    getRecipes: async (productId?: number): Promise<Recipe[]> => {
        const params = productId ? { product_id: productId } : {};
        const { data } = await api.get<Recipe[]>('/recipes', { params });
        return data;
    },

    getRecipe: async (id: string): Promise<Recipe> => {
        const { data } = await api.get<Recipe>(`/recipes/${id}`);
        return data;
    },

    createRecipe: async (payload: RecipePayload): Promise<Recipe> => {
        const { data } = await api.post<Recipe>('/recipes', payload);
        return data;
    },

    updateRecipe: async (id: string, payload: Partial<RecipePayload>): Promise<Recipe> => {
        const { data } = await api.put<Recipe>(`/recipes/${id}`, payload);
        return data;
    },

    updateRecipeItems: async (id: string, items: RecipePayload['items']): Promise<Recipe> => {
        const { data } = await api.put<Recipe>(`/recipes/${id}/items`, { items });
        return data;
    },

    deleteRecipe: async (id: string): Promise<void> => {
        await api.delete(`/recipes/${id}`);
    },

    // Simulate cost before saving
    simulateRecipeCost: async (items: RecipeItem[]): Promise<CostSimulation> => {
        const { data } = await api.post<CostSimulation>('/recipes/simulate', { items });
        return data;
    },

    // Recalculate recipe cost (after ingredient price changes)
    recalculateRecipeCost: async (id: string): Promise<Recipe> => {
        const { data } = await api.post<Recipe>(`/recipes/${id}/recalculate`);
        return data;
    },

    // Upload image for recipe/product
    uploadImage: async (file: File): Promise<string> => {
        console.log('📤 [UPLOAD] Starting image upload...');
        console.log('📤 [UPLOAD] File:', {
            name: file.name,
            type: file.type,
            size: `${(file.size / 1024).toFixed(2)} KB`
        });

        const formData = new FormData();
        formData.append('file', file);

        try {
            const { data } = await api.post<{ url: string; filename: string }>('/uploads/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            console.log('✅ [UPLOAD] Success! Response:', data);
            console.log('✅ [UPLOAD] Image URL:', data.url);
            return data.url;
        } catch (error: any) {
            console.error('❌ [UPLOAD] Failed!', error);
            console.error('❌ [UPLOAD] Error details:', {
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                message: error.message
            });
            throw error;
        }
    },

    // Update product image
    updateProductImage: async (productId: number, imageUrl: string): Promise<void> => {
        console.log('🖼️ [UPDATE_IMAGE] Updating product image...');
        console.log('🖼️ [UPDATE_IMAGE] Product ID:', productId);
        console.log('🖼️ [UPDATE_IMAGE] Image URL:', imageUrl);

        try {
            await api.patch(`/products/${productId}`, { image_url: imageUrl });
            console.log('✅ [UPDATE_IMAGE] Product image updated successfully!');
        } catch (error: any) {
            console.error('❌ [UPDATE_IMAGE] Failed!', error);
            console.error('❌ [UPDATE_IMAGE] Error details:', {
                status: error.response?.status,
                data: error.response?.data
            });
            throw error;
        }
    },

    // ─────────────────────────────────────────
    // 3. MENU ENGINEERING (BCG Matrix)
    // ─────────────────────────────────────────

    getMenuEngineeringReport: async (params?: {
        branch_id?: number;
        start_date?: string;
        end_date?: string;
        category_id?: number;
    }): Promise<MenuEngineeringReport> => {
        const { data } = await api.get<MenuEngineeringReport>('/reports/menu-engineering/', { params });
        return data;
    },

    getMenuRecommendations: async (): Promise<{
        recommendations: Array<{
            product: string;
            classification: string;
            severity: string;
            action: string;
            reason: string;
        }>
    }> => {
        const { data } = await api.get('/reports/menu-engineering/recommendations');
        return data;
    },

    getMenuSummary: async (): Promise<{
        period_days: number;
        total_products: number;
        total_revenue: number;
        classification: { stars: number; plowhorses: number; puzzles: number; dogs: number };
        top_stars: Array<{ name: string; revenue: number }>;
        urgent_dogs: Array<{ name: string; food_cost_pct: number }>;
    }> => {
        const { data } = await api.get('/reports/menu-engineering/summary');
        return data;
    },

    // ─────────────────────────────────────────
    // 4. INTELLIGENCE (Live Recipe & Calibration)
    // ─────────────────────────────────────────

    getRecipeEfficiency: async (recipeId: string): Promise<RecipeEfficiency> => {
        const { data } = await api.get<RecipeEfficiency>(`/intelligence/recipe-efficiency/${recipeId}`);
        // Ensure recommendations is always an array
        if (!data.recommendations) data.recommendations = [];
        return data;
    },

    calibrateRecipe: async (recipeId: string, items: { ingredient_id: string; new_quantity: number }[]): Promise<CalibrationResult> => {
        const { data } = await api.post<CalibrationResult>(`/intelligence/calibrate-recipe/${recipeId}`, { items });
        return data;
    },

    // ─────────────────────────────────────────
    // 5. PRODUCTION (Transformations)
    // ─────────────────────────────────────────

    registerProduction: async (payload: {
        inputs: { ingredient_id: string; quantity: number }[];
        output: {
            ingredient_id?: string;
            name?: string;
            base_unit?: string;
            category_id?: number;
        };
        output_quantity: number;
        notes?: string;
    }): Promise<any> => {
        const { data } = await api.post('/kitchen/production/', payload); // Adjusted endpoint
        return data;
    },

    getProductionByBatch: async (batchId: string): Promise<ProductionDetail> => {
        const { data } = await api.get<ProductionDetail>(`/kitchen/production/batch/${batchId}`);
        return data;
    }
};

export interface ProductionInputDetail {
    ingredient_name: string;
    quantity: number;
    unit: string;
    cost_allocated: number;
    cost_per_unit: number;
}

export interface ProductionDetail {
    id: string;
    date: string;
    inputs: ProductionInputDetail[];
    output_quantity: number;
    notes?: string;
}

export interface RecipeEfficiency {
    recipe_id: string;
    items: {
        ingredient_id: string;
        theoretical_usage: number;
        real_usage: number;
        discrepancy: number;
        efficiency: number;
        message?: string;
        suggested_quantity?: number;
        last_audit_date?: string;
    }[];
    recommendations: {
        ingredient_id: string;
        efficiency: number;
        message: string;
        suggested_quantity: number;
    }[];
}

export interface CalibrationResult {
    status: string;
    items_updated: number;
    old_cost: number;
    new_cost: number;
    cost_increase: number;
    current_price: number;
    suggested_price: number;
    old_margin_pct: number;
    new_margin_pct_if_static: number;
}

export default kitchenService;
