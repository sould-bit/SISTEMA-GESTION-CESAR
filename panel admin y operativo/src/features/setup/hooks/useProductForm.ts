import { useState, useRef, useEffect, ChangeEvent } from 'react';
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

    const [selectedProduct, setSelectedProduct] = useState<any>(null);
    const [isSaving, setIsSaving] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Reset form when viewMode changes
    useEffect(() => {
        resetForm();
    }, [viewMode]);

    const handleSelectProduct = (product: any) => {
        // ... (same as before)
        setSelectedProduct(product);
        setProductForm({
            name: product.name,
            price: product.price || '',
            cost: product.cost || '',
            stock: product.stock || '',
            unit: product.unit || 'UNIDAD',
            description: product.description || '',
            sku: product.sku || '',
            image_url: product.image_url || '',
        });
    };




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

    const handleDelete = async () => {
        if (!selectedProduct) return;
        if (!confirm('¿Estás seguro de eliminar este producto? Esta acción no se puede deshacer.')) return;

        setIsSaving(true);
        try {
            if (viewMode === 'BEBIDAS') {
                await setupService.deleteBeverage(selectedProduct.id);
            } else {
                // TODO: standard delete if needed
                alert("Eliminar no implementado para este modo");
                setIsSaving(false);
                return;
            }
            await refreshData();
            resetForm();
            alert("Eliminado correctamente");
        } catch (error) {
            console.error(error);
            alert("Error al eliminar");
        } finally {
            setIsSaving(false);
        }
    };

    const resetForm = () => {
        setSelectedProduct(null);
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

            // Check duplicates (Client side check)
            // Exclude current product if editing
            const isDuplicate = existingProducts.some(p =>
                p.name.trim().toLowerCase() === cleanName.toLowerCase() &&
                (!selectedProduct || Number(p.id) !== Number(selectedProduct.id))
            );

            if (isDuplicate) {
                alert("Ya existe un producto con este nombre. Por favor usa otro.");
                setIsSaving(false);
                return;
            }

            if (viewMode === 'BEBIDAS') {
                // Auto-generate SKU if not provided
                const finalSku = productForm.sku ? productForm.sku : `BEV-${Math.floor(Date.now() / 1000).toString(36).toUpperCase()}`;

                const payload: BeveragePayload = {
                    name: cleanName,
                    category_id: selectedCategory?.id,
                    cost: Number(productForm.cost),
                    sale_price: Number(productForm.price),
                    initial_stock: Number(productForm.stock),
                    unit: 'BOTELLA',
                    image_url: productForm.image_url,
                    supplier: productForm.supplier,
                    description: 'Bebida Venta Directa',
                    sku: finalSku
                };

                if (!user?.branch_id) {
                    alert('Error: Usuario no tiene sucursal asignada.');
                    setIsSaving(false);
                    return;
                }

                if (selectedProduct) {
                    // Update
                    await setupService.updateBeverage(selectedProduct.id, payload, user.branch_id);
                } else {
                    // Create
                    await setupService.createBeverage(payload, user.branch_id);
                }
            } else {
                // Standard logic
                const payload = {
                    ...productForm,
                    category_id: selectedCategory?.id
                };
                if (viewMode === 'INSUMOS') {
                    // Ingredient update not fully implemented in this refactor step, assumes create
                    await setupService.createIngredient(payload);
                } else {
                    // Product update not fully implemented in this refactor step
                    await setupService.createProduct(payload);
                }
            }

            await refreshData();
            resetForm();
            alert("Guardado correctamente");
        } catch (error: any) {
            console.error(error);
            if (error.response?.status === 500) {
                alert("Error del servidor. Posiblemente el nombre ya existe o hay un problema interno.");
            } else if (error.response?.status === 401) {
                alert("Sesión expirada. Por favor recarga la página.");
            } else {
                alert("Error al guardar. Verifica la consola para más detalles.");
            }
        } finally {
            setIsSaving(false);
        }
    };

    return {
        productForm,
        setProductForm,
        selectedProduct,
        handleSelectProduct,
        handleDelete,
        isSaving,
        fileInputRef,
        handleFileChange,
        handleSave,
        resetForm
    };
};
