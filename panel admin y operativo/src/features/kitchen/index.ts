// Kitchen Module - Barrel Exports
export { kitchenService } from './kitchen.service';
export type {
    Ingredient,
    IngredientCreate,
    IngredientUpdate,
    Recipe,
    RecipeItem,
    RecipePayload,
    MenuEngineeringProduct,
    MenuEngineeringReport,
    CostSimulation
} from './kitchen.service';

export { IngredientManager } from './components/IngredientManager';
export { ImprovedRecipeBuilder } from './components/ImprovedRecipeBuilder';
export { MenuMatrix } from './components/MenuMatrix';
export { RecipesPage } from './components/RecipesPage';
