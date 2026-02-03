import { useState, useCallback } from 'react';
import { setupService, Product } from '../setup.service';

interface IngredientFormData {
    name: string;
    cost: string; // Map to price in product table for Ingredients
    stock: string;
    unit: string;
    sku: string;
    minStock: string;
    description: string;
}

const initialForm: IngredientFormData = {
    name: '',
    cost: '0',
    stock: '0',
    unit: 'UNIDAD',
    sku: '',
    minStock: '0',
    description: 'Ingrediente'
};

export const useIngredientForm = (
    onRefresh: () => Promise<void>
) => {
    const [form, setForm] = useState<IngredientFormData>(initialForm);
    const [isSaving, setIsSaving] = useState(false);
    const [selectedIngredient, setSelectedIngredient] = useState<Product | null>(null);

    const resetForm = useCallback(() => {
        setForm(initialForm);
        setSelectedIngredient(null);
    }, []);

    const handleSelectIngredient = useCallback((ing: Product) => {
        setSelectedIngredient(ing);
        setForm({
            name: ing.name,
            cost: ing.price.toString(),
            stock: ing.stock.toString(),
            unit: (ing as any).unit || 'UNIDAD',
            sku: (ing as any).sku || '',
            minStock: (ing as any).min_stock?.toString() || '0',
            description: ing.description || 'Ingrediente'
        });
    }, []);

    const handleSave = async () => {
        if (!form.name.trim()) {
            alert("El nombre es requerido");
            return;
        }

        setIsSaving(true);
        try {
            const payload: Partial<Product> = {
                name: form.name.trim(),
                price: Number(form.cost), // Price stores cost for ingredients
                stock: Number(form.stock),
                description: form.description,
                unit: form.unit,
                sku: form.sku || `ING-${Math.floor(Date.now() / 1000).toString(36).toUpperCase()}`
            };

            if (selectedIngredient) {
                await setupService.updateProduct(selectedIngredient.id, payload);
            } else {
                await setupService.createIngredient(payload);
            }

            await onRefresh();
            resetForm();
            alert(selectedIngredient ? "Insumo actualizado correctamente" : "Insumo creado correctamente");
        } catch (error: any) {
            console.error('Error saving ingredient:', error);
            const detail = error.response?.data?.detail || error.message;
            alert(`Error al guardar: ${detail}`);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("¿Estás seguro de desactivar este insumo?")) return;

        setIsSaving(true);
        try {
            await setupService.updateProduct(id, { is_active: false });
            await onRefresh();
            if (selectedIngredient?.id === id) resetForm();
        } catch (error: any) {
            console.error('Error deleting ingredient:', error);
            alert("Error al desactivar el insumo");
        } finally {
            setIsSaving(false);
        }
    };

    return {
        form,
        setForm,
        isSaving,
        selectedIngredient,
        handleSelectIngredient,
        handleSave,
        handleDelete,
        resetForm
    };
};
