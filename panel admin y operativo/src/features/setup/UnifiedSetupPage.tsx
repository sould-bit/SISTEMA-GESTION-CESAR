import { useState, useEffect } from 'react';
import { useSetupData } from './hooks/useSetupData';
import { useProductForm } from './hooks/useProductForm';
import { SetupNavigation } from './components/SetupNavigation';
import { BeverageForm } from './components/BeverageForm';
import { StandardForm } from './components/StandardForm';
import { ModifierForm } from './components/ModifierForm';
import { setupService, RecipeItemRow } from './setup.service';
import { type Ingredient as KitchenIngredient } from '@/features/kitchen/kitchen.service';

export const UnifiedSetupPage = () => {
    // --- Global Data Hook ---
    const {
        viewMode, setViewMode,
        categories, ingredients, products, modifiers,
        isLoading, refreshData
    } = useSetupData();

    // --- Selection State ---
    const [selectedCategory, setSelectedCategory] = useState<any>(null);
    const [recipeItems, setRecipeItems] = useState<RecipeItemRow[]>([]);

    // --- Form Logic Hook ---
    const {
        productForm, setProductForm,
        isSaving, fileInputRef,
        handleFileChange, handleSave: saveProduct,
        selectedProduct, handleSelectProduct, handleDelete, resetForm
    } = useProductForm(viewMode, refreshData, selectedCategory, products);

    // Aliases for different form modes (since all use the same unified hook logic)
    const handleSaveStandard = saveProduct;
    // Modifiers might need separate logic or use the same hook
    // (Assuming ModifierForm expects a specific signature, checking usage temporarily aliased)
    const handleSaveModifier = async (data: any) => {
        // Placeholder if distinct logic is needed, or reuse saveProduct if compatible
        console.warn("Modifier save logic not fully integrated yet");
    };

    // --- Category Selection Logic ---
    useEffect(() => {
        // Auto-select category based on viewMode if needed (e.g. Materia Prima)
        if (viewMode === 'INSUMOS') {
            const rawCat = categories.find(c => c.name.toLowerCase() === 'materia prima');
            if (rawCat) setSelectedCategory(rawCat);
        } else if (viewMode === 'BEBIDAS') {
            // Strict enforcement: ONLY "Venta Directa"
            const bevCat = categories.find(c =>
                c.name.toLowerCase().includes('venta directa')
            );
            if (bevCat) setSelectedCategory(bevCat);
            else setSelectedCategory(null);
        } else {
            setSelectedCategory(null);
        }
    }, [viewMode, categories]);

    if (isLoading) {
        return <div className="text-white p-10 flex justify-center">Cargando datos del sistema...</div>;
    }

    return (
        <div className="min-h-screen bg-[#1a1a1a] text-gray-100 font-sans selection:bg-accent-orange/30">
            {/* Background Gradients */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-accent-orange/5 rounded-full blur-[120px] mix-blend-screen" />
                <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[120px] mix-blend-screen" />
            </div>

            <div className="relative z-10 max-w-7xl mx-auto p-4 md:p-8 space-y-8">

                {/* HEADLINE */}
                <div className="text-center space-y-2 mb-12">
                    <h1 className="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500 tracking-tight">
                        Ingeniería de Menú
                    </h1>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto font-light">
                        Diseña tu oferta gastronómica, gestiona costos y controla tu inventario desde un solo lugar.
                    </p>
                </div>

                {/* NAVIGATION (Visible if HOME) */}
                {viewMode === 'HOME' && (
                    <SetupNavigation onSelect={setViewMode} />
                )}

                {/* BEBIDAS MODULE */}
                {viewMode === 'BEBIDAS' && (
                    <BeverageForm
                        productForm={productForm}
                        setProductForm={setProductForm}
                        fileInputRef={fileInputRef}
                        handleFileChange={handleFileChange}
                        handleSave={saveProduct}
                        onCancel={() => setViewMode('HOME')}
                        isSaving={isSaving}
                        products={products
                            .filter(p => !p.category_id || p.category_name !== 'Materia Prima')
                            .map(p => {
                                // Enrich with stock from linked ingredient (Single Source of Truth)
                                const linkedIng = (ingredients as unknown as KitchenIngredient[]).find(i =>
                                    i.name.trim().toLowerCase() === p.name.trim().toLowerCase()
                                );
                                return {
                                    ...p,
                                    stock: linkedIng?.stock ?? p.stock ?? 0
                                };
                            })
                        }
                        selectedProduct={selectedProduct}
                        onSelectProduct={(p) => {
                            // Enrich with ingredient cost/stock if available (Bridge 1:1)
                            const linkedIng = (ingredients as unknown as KitchenIngredient[]).find(i =>
                                i.name.trim().toLowerCase() === p.name.trim().toLowerCase()
                            );

                            let finalCost = p.cost; // Default
                            let finalStock = p.stock;

                            if (linkedIng) {
                                console.log(`[DEBUG-SETUP] Linked Ingredient found for ${p.name}:`, {
                                    id: linkedIng.id,
                                    stock: linkedIng.stock,
                                    calc_cost: linkedIng.calculated_cost,
                                    curr_cost: linkedIng.current_cost,
                                    total_val: linkedIng.total_inventory_value
                                });

                                finalStock = linkedIng.stock;
                                // Use Backend calculated Effective Cost
                                if (linkedIng.calculated_cost && linkedIng.calculated_cost > 0) {
                                    finalCost = linkedIng.calculated_cost;
                                    console.log("[DEBUG-SETUP] Using Backend Effective Cost:", finalCost);
                                } else {
                                    finalCost = linkedIng.current_cost;
                                    console.log("[DEBUG-SETUP] Fallback to Current Cost:", finalCost);
                                }
                            } else {
                                console.log(`[DEBUG-SETUP] No Linked Ingredient found for ${p.name}`);
                            }

                            const enriched = {
                                ...p,
                                cost: finalCost || 0,
                                stock: finalStock || 0
                            };
                            handleSelectProduct(enriched);
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        allIngredients={ingredients as any}
                        onDelete={handleDelete}
                        onCancelEdit={resetForm}
                    />
                )}

                {/* MODIFIERS MODULE */}
                {viewMode === 'EXTRAS' && (
                    <div>
                        <button onClick={() => setViewMode('HOME')} className="mb-4 text-sm text-gray-500 hover:text-white underline">
                            &larr; Volver
                        </button>
                        <ModifierForm
                            modifiers={modifiers}
                            handleSaveModifier={handleSaveModifier}
                            isSaving={isSaving}
                            recipeItems={recipeItems}
                            setRecipeItems={setRecipeItems}
                            ingredients={ingredients}
                        />
                    </div>
                )}

                {/* STANDARD FORM (INSUMOS / CARTA) */}
                {(viewMode === 'INSUMOS' || viewMode === 'CARTA') && (
                    <div className="space-y-4">
                        <button onClick={() => setViewMode('HOME')} className="text-sm text-gray-500 hover:text-white underline">
                            &larr; Volver al Menú
                        </button>

                        <StandardForm
                            viewMode={viewMode}
                            productForm={productForm}
                            setProductForm={setProductForm}
                            selectedCategory={selectedCategory}
                            handleSave={handleSaveStandard}
                            isSaving={isSaving}
                            recipeItems={recipeItems}
                            setRecipeItems={setRecipeItems}
                            ingredients={ingredients}
                        />

                        {/* PRODUCT GRID FOR STANDARD MODES */}
                        <div className="mt-8 pt-8 border-t border-gray-800">
                            <h3 className="text-xl font-bold text-gray-500 mb-4">
                                {viewMode === 'INSUMOS' ? 'Insumos Registrados' : 'Platos Registrados'}
                            </h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                                {products
                                    .filter(p => {
                                        if (viewMode === 'INSUMOS') return p.category_id === selectedCategory?.id; // Rough filter
                                        return p.category_id !== categories.find(c => c.name === 'Materia Prima')?.id;
                                    })
                                    .slice(0, 12)
                                    .map(p => (
                                        <div key={p.id} className="bg-gray-800 p-3 rounded text-sm">
                                            <div className="font-bold text-white truncate">{p.name}</div>
                                            <div className="text-gray-500">${p.price}</div>
                                        </div>
                                    ))}
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
};
