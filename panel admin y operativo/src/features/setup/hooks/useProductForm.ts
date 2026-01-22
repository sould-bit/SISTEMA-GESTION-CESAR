import { useState, useRef, ChangeEvent } from 'react';
import { Product, BeveragePayload, setupService, MacroType } from '../setup.service';
import { useAppSelector } from '../../../stores/store';

export const useProductForm = (
    viewMode: MacroType,
    refreshData: () => Promise<void>,
    selectedCategory?: any,
    existingProducts: Product[] = []
) => {
    const { user } = useAppSelector(state => state.auth);
    const [productForm, setProductForm] = useState<any>({
        name: '',
        price: '',
        cost: '',
        stock: '',
        unit: 'UNIDAD',
        description: '',
        sku: '',
        minStock: '',
        supplier: '',
        categoryName: '',
        hasRecipe: false,
        image_url: '',
        totalCost: ''
    });

    const [isSaving, setIsSaving] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            try {
                const url = await setupService.uploadImage(file);
                setProductForm((prev: any) => ({ ...prev, image_url: url }));
            } catch (error) {
                console.error("Upload failed", error);
                alert("Error subiendo imagen");
            }
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const cleanName = productForm.name.trim();
            if (!cleanName) {
                alert("El nombre es requerido");
                setIsSaving(false);
                return;
            }

            // Check duplicates (Client side check) - Compare trimmed & ignore case
            // Also check INACTIVE products because DB constraint is likely unique on name regardless of status
            const isDuplicate = existingProducts.some(p =>
                p.name.trim().toLowerCase() === cleanName.toLowerCase()
            );

            if (isDuplicate) {
                alert("Ya existe un producto con este nombre. Por favor usa otro.");
                setIsSaving(false);
                return;
            }

            if (viewMode === 'BEBIDAS') {
                // Try to find a default category for beverages if none selected
                // This logic might need to be robust; assuming 'Bebidas' or 'General' exists or logic is handled
                // ideally we pass a 'defaultCategoryId' to the hook, but let's try to grab it from selectedCategory if passed or just send as is
                // If backend requires category_id, we must provide it.
                // NOTE: 'selectedCategory' in hook props might be null for BEBIDAS mode as per UnifiedSetupPage logic.

                // We will rely on setupService.createBeverage to handle default category logic server side OR 
                // we should pass it. 
                // Let's add 'category_id' to payload if available.
                const payload: BeveragePayload = {
                    name: cleanName, // Send TRIMMED name
                    category_id: selectedCategory?.id, // If we passed a default category

                    cost: Number(productForm.cost),
                    sale_price: Number(productForm.price),
                    initial_stock: Number(productForm.stock),
                    unit: 'BOTELLA', // Default for beverages
                    image_url: productForm.image_url,
                    supplier: productForm.supplier,
                    description: 'Bebida Venta Directa'
                };
                // We need branchId. Check how it was handled before. 
                // It was passing '1'.
                if (!user?.branch_id) {
                    alert('Error: Usuario no tiene sucursal asignada.');
                    setIsSaving(false);
                    return;
                }
                await setupService.createBeverage(payload, user.branch_id);
            } else {
                // Standard logic (Insumos/Carta)
                // ... Implementation similar to existing handleNewProduct
                // For simplified refactor, we might iterate this later.
                // Assuming standard creation:
                const payload = {
                    ...productForm,
                    category_id: selectedCategory?.id
                };
                if (viewMode === 'INSUMOS') {
                    await setupService.createIngredient(payload);
                } else {
                    await setupService.createProduct(payload);
                }
            }

            await refreshData();
            // Reset form
            setProductForm({
                name: '',
                price: '',
                cost: '',
                stock: '',
                unit: 'UNIDAD',
                description: '',
                sku: '',
                minStock: '',
                supplier: '',
                categoryName: '',
                hasRecipe: false,
                image_url: '',
                totalCost: ''
            });
            alert("Guardado correctamente");
        } catch (error) {
            console.error(error);
            alert("Error al guardar");
        } finally {
            setIsSaving(false);
        }
    };

    return {
        productForm,
        setProductForm,
        isSaving,
        fileInputRef,
        handleFileChange,
        handleSave
    };
};
