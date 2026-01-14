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
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface IngredientCreate {
    name: string;
    sku: string;
    base_unit: 'kg' | 'lt' | 'und' | 'g' | 'ml';
    current_cost: number;
    yield_factor?: number;
    category_id?: number;
}

export interface IngredientUpdate {
    name?: string;
    sku?: string;
    base_unit?: 'kg' | 'lt' | 'und' | 'g' | 'ml';
    current_cost?: number;
    yield_factor?: number;
    category_id?: number;
    is_active?: boolean;
}

export interface RecipeItem {
    ingredient_id: string;
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
    id: string;
    product_id: number;
    name: string;
    version: number;
    is_active: boolean;
    batch_yield: number;
    total_cost: number;
    preparation_time: number;
    items: RecipeItem[];
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

    getIngredients: async (search?: string): Promise<Ingredient[]> => {
        const params = search ? { search } : {};
        const { data } = await api.get<Ingredient[]>('/ingredients/', { params });
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

    updateIngredientCost: async (id: string, newCost: number, reason?: string): Promise<Ingredient> => {
        const { data } = await api.post<Ingredient>(`/ingredients/${id}/update-cost`, {
            new_cost: newCost,
            reason
        });
        return data;
    },

    // ─────────────────────────────────────────
    // 2. RECIPES (Constructor de Recetas)
    // ─────────────────────────────────────────

    getRecipes: async (productId?: number): Promise<Recipe[]> => {
        const params = productId ? { product_id: productId } : {};
        const { data } = await api.get<Recipe[]>('/recipes/', { params });
        return data;
    },

    getRecipe: async (id: string): Promise<Recipe> => {
        const { data } = await api.get<Recipe>(`/recipes/${id}`);
        return data;
    },

    createRecipe: async (payload: RecipePayload): Promise<Recipe> => {
        const { data } = await api.post<Recipe>('/recipes/', payload);
        return data;
    },

    updateRecipe: async (id: string, payload: Partial<RecipePayload>): Promise<Recipe> => {
        const { data } = await api.patch<Recipe>(`/recipes/${id}`, payload);
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
};

export default kitchenService;
