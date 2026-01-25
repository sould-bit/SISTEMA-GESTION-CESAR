/**
 * Tipos TypeScript para el módulo de Ingredientes
 */

export interface Ingredient {
    id: string;
    company_id: number;
    name: string;
    sku: string;
    base_unit: string;
    current_cost: number;
    last_cost: number;
    yield_factor: number;
    category_id: number | null;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
    // Optional fields populated by backend list view
    stock?: number;
    calculated_cost?: number;
    total_inventory_value?: number;
    ingredient_type?: "RAW" | "PROCESSED" | "MERCHANDISE";
}

export interface IngredientCreate {
    name: string;
    sku: string;
    base_unit: string;
    current_cost?: number;
    yield_factor?: number;
    category_id?: number | null;
}

export interface IngredientUpdate {
    name?: string;
    sku?: string;
    base_unit?: string;
    current_cost?: number;
    yield_factor?: number;
    category_id?: number | null;
    is_active?: boolean;
}

export interface IngredientImpact {
    recipes_count: number;
    total_recipes_cost: number;
    avg_usage_per_recipe: number;
}
