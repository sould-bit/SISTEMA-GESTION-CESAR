/**
 * Hook para gestionar ingredientes desde la API
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import { Ingredient, IngredientCreate, IngredientUpdate } from '../types/ingredient';

interface UseIngredientsReturn {
    ingredients: Ingredient[];
    loading: boolean;
    error: string | null;
    fetchIngredients: () => Promise<void>;
    createIngredient: (data: IngredientCreate) => Promise<Ingredient>;
    updateIngredient: (id: string, data: IngredientUpdate) => Promise<Ingredient>;
    deleteIngredient: (id: string) => Promise<void>;
    updateCost: (id: string, newCost: number, useWeightedAverage?: boolean) => Promise<Ingredient>;
}

export const useIngredients = (): UseIngredientsReturn => {
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchIngredients = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get<Ingredient[]>('/ingredients/');
            setIngredients(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al cargar ingredientes');
        } finally {
            setLoading(false);
        }
    }, []);

    const createIngredient = async (data: IngredientCreate): Promise<Ingredient> => {
        const response = await api.post<Ingredient>('/ingredients/', data);
        setIngredients((prev) => [...prev, response.data]);
        return response.data;
    };

    const updateIngredient = async (id: string, data: IngredientUpdate): Promise<Ingredient> => {
        const response = await api.patch<Ingredient>(`/ingredients/${id}`, data);
        setIngredients((prev) =>
            prev.map((ing) => (ing.id === id ? response.data : ing))
        );
        return response.data;
    };

    const deleteIngredient = async (id: string): Promise<void> => {
        await api.delete(`/ingredients/${id}`);
        setIngredients((prev) => prev.filter((ing) => ing.id !== id));
    };

    const updateCost = async (
        id: string,
        newCost: number,
        useWeightedAverage = true
    ): Promise<Ingredient> => {
        const response = await api.post<Ingredient>(`/ingredients/${id}/update-cost`, {
            new_cost: newCost,
            use_weighted_average: useWeightedAverage,
        });
        setIngredients((prev) =>
            prev.map((ing) => (ing.id === id ? response.data : ing))
        );
        return response.data;
    };

    useEffect(() => {
        fetchIngredients();
    }, [fetchIngredients]);

    return {
        ingredients,
        loading,
        error,
        fetchIngredients,
        createIngredient,
        updateIngredient,
        deleteIngredient,
        updateCost,
    };
};
