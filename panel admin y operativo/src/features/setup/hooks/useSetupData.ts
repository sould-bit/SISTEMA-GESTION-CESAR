import { useState, useEffect } from 'react';
import { setupService, Category, Product, MacroType } from '../setup.service';

const withTimeout = <T>(promise: Promise<T>, name: string, ms = 10000): Promise<T> => {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            console.error(`❌ [TIMEOUT] ${name} took longer than ${ms}ms`);
            reject(new Error(`${name} timed out`));
        }, ms);

        console.log(`⏳ [START] Loading ${name}...`);
        promise
            .then((data) => {
                clearTimeout(timer);
                console.log(`✅ [SUCCESS] ${name} loaded (${Array.isArray(data) ? data.length : 'OK'} items)`);
                resolve(data);
            })
            .catch((err) => {
                clearTimeout(timer);
                console.error(`❌ [ERROR] ${name} failed:`, err);
                reject(err);
            });
    });
};

export const useSetupData = () => {
    const [viewMode, setViewMode] = useState<MacroType>('HOME');
    const [categories, setCategories] = useState<Category[]>([]);
    const [ingredients, setIngredients] = useState<Product[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [modifiers, setModifiers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    const loadData = async () => {
        setIsLoading(true);
        setLoadError(null);
        console.log("🚀 [SETUP] Starting unified data load...");
        const startTime = Date.now();

        try {
            // Use Promise.allSettled so one failure doesn't block the others from being saved
            const results = await Promise.allSettled([
                withTimeout(setupService.getCategories(), 'Categories'),
                withTimeout(setupService.getIngredients(), 'Ingredients'),
                withTimeout(setupService.getProducts(), 'Products')
            ]);

            // Process results
            const [catsResult, ingsResult, prodsResult] = results;

            if (catsResult.status === 'fulfilled') setCategories(catsResult.value);
            else console.error("Failed Categories:", catsResult.reason);

            if (ingsResult.status === 'fulfilled') setIngredients(ingsResult.value);
            else console.error("Failed Ingredients:", ingsResult.reason);

            if (prodsResult.status === 'fulfilled') setProducts(prodsResult.value);
            else console.error("Failed Products:", prodsResult.reason);

            console.log(`🏁 [SETUP] Load complete in ${Date.now() - startTime}ms`);

            // Non-blocking modifiers
            setupService.getModifiers()
                .then(mods => setModifiers(mods))
                .catch(err => console.warn("Background load: Modifiers failed", err));

        } catch (error: any) {
            console.error('🔥 [SETUP] Critical Load Error:', error);
            setLoadError(error.message || "Error desconocido");
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
        loadError,
        refreshData
    };
};
