import { useState, useEffect } from 'react';
import { setupService, Category, Product, MacroType } from '../setup.service';

export const useSetupData = () => {
    const [viewMode, setViewMode] = useState<MacroType>('HOME');
    const [categories, setCategories] = useState<Category[]>([]);
    const [ingredients, setIngredients] = useState<Product[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [modifiers, setModifiers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [cats, ings, prods, mods] = await Promise.all([
                setupService.getCategories(),
                setupService.getIngredients(),
                setupService.getProducts(),
                setupService.getModifiers()
            ]);
            setCategories(cats);
            setIngredients(ings);
            setProducts(prods);
            setModifiers(mods);
        } catch (error) {
            console.error('Error loading setup data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const refreshData = loadData;

    return {
        viewMode,
        setViewMode,
        categories,
        ingredients,
        products,
        modifiers,
        isLoading,
        refreshData
    };
};
