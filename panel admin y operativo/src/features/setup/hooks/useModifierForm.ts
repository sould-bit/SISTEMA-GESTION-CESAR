import { useState, useCallback } from 'react';
import { setupService, ProductModifier, RecipeItem } from '../setup.service';

interface ModifierFormData {
    name: string;
    description: string;
    extra_price: string;
}

const initialForm: ModifierFormData = {
    name: '',
    description: '',
    extra_price: '0'
};

export const useModifierForm = (
    onRefresh: () => Promise<void>
) => {
    const [form, setForm] = useState<ModifierFormData>(initialForm);
    const [isSaving, setIsSaving] = useState(false);
    const [selectedModifier, setSelectedModifier] = useState<ProductModifier | null>(null);
    const [recipeItems, setRecipeItems] = useState<any[]>([]);

    const resetForm = useCallback(() => {
        setForm(initialForm);
        setSelectedModifier(null);
        setRecipeItems([]);
    }, []);

    const handleSelectModifier = useCallback((mod: ProductModifier) => {
        setSelectedModifier(mod);
        setForm({
            name: mod.name,
            description: mod.description || '',
            extra_price: mod.extra_price.toString()
        });

        // Transform backend recipe items to the frontend format used by RecipeBuilder
        if (mod.recipe_items) {
            const formattedItems = mod.recipe_items.map(ri => ({
                ingredientId: ri.ingredient_product_id,
                name: ri.ingredient?.name || 'Insumo desconocido',
                cost: ri.ingredient?.price || 0,
                quantity: ri.quantity,
                unit: ri.unit
            }));
            setRecipeItems(formattedItems);
        } else {
            setRecipeItems([]);
        }
    }, []);

    const handleSave = async () => {
        if (!form.name.trim()) {
            alert("El nombre es requerido");
            return;
        }

        setIsSaving(true);
        try {
            const payload: Partial<ProductModifier> = {
                name: form.name.trim(),
                description: form.description.trim(),
                extra_price: Number(form.extra_price) || 0,
            };

            let savedMod: ProductModifier;

            if (selectedModifier) {
                // Update basic info
                savedMod = await setupService.updateModifier(selectedModifier.id, payload);
            } else {
                // Create
                savedMod = await setupService.createModifier(payload);
            }

            // Save recipe items if any
            // Transform frontend format to backend RecipeItem
            const backendRecipeItems: RecipeItem[] = recipeItems.map(ri => ({
                ingredient_product_id: ri.ingredientId,
                quantity: ri.quantity,
                unit: ri.unit
            }));

            await setupService.updateModifierRecipe(savedMod.id, backendRecipeItems);

            await onRefresh();
            resetForm();
            alert(selectedModifier ? "Modificador actualizado correctamente" : "Modificador creado correctamente");
        } catch (error: any) {
            console.error('Error saving modifier:', error);
            const detail = error.response?.data?.detail || error.message;
            alert(`Error al guardar: ${detail}`);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("¿Estás seguro de desactivar este modificador?")) return;

        setIsSaving(true);
        try {
            await setupService.updateModifier(id, { is_active: false });
            await onRefresh();
            if (selectedModifier?.id === id) resetForm();
        } catch (error: any) {
            console.error('Error deleting modifier:', error);
            alert("Error al desactivar el modificador");
        } finally {
            setIsSaving(false);
        }
    };

    return {
        form,
        setForm,
        isSaving,
        selectedModifier,
        recipeItems,
        setRecipeItems,
        handleSelectModifier,
        handleSave,
        handleDelete,
        resetForm
    };
};
