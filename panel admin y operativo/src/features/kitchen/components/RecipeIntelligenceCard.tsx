import { useState, useEffect } from 'react';
import { kitchenService, CalibrationResult, RecipeEfficiency, Recipe } from '../kitchen.service';

interface Props {
    recipe: Recipe;
    onCalibrateComplete?: (result: CalibrationResult) => void;
}

export const RecipeIntelligenceCard = ({ recipe, onCalibrateComplete }: Props) => {
    const [loading, setLoading] = useState(false);
    const [efficiencyData, setEfficiencyData] = useState<RecipeEfficiency | null>(null);
    const [calibrationResult, setCalibrationResult] = useState<CalibrationResult | null>(null);
    const [calibrating, setCalibrating] = useState(false);

    useEffect(() => {
        if (!recipe?.id) return;
        loadEfficiency();
    }, [recipe.id]);

    const loadEfficiency = async () => {
        setLoading(true);
        try {
            const data = await kitchenService.getRecipeEfficiency(recipe.id.toString());
            setEfficiencyData(data);
        } catch (error) {
            console.error('Error loading recipe efficiency:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCalibrate = async () => {
        if (!efficiencyData || !efficiencyData.recommendations.length) return;

        if (!confirm('¿Estás seguro de calibrar esta receta? Esto actualizará las cantidades brutas basada en el consumo real.')) return;

        setCalibrating(true);
        try {
            const itemsToCalibrate = efficiencyData.recommendations.map(r => ({
                ingredient_id: r.ingredient_id,
                new_quantity: r.suggested_quantity
            }));

            const result = await kitchenService.calibrateRecipe(recipe.id.toString(), itemsToCalibrate);
            setCalibrationResult(result);
            if (onCalibrateComplete) onCalibrateComplete(result);

            // Reload efficiency
            loadEfficiency();
        } catch (error) {
            console.error('Error calibrating:', error);
            alert('Error al calibrar la receta');
        } finally {
            setCalibrating(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(value);
    };

    if (loading) {
        return (
            <div className="bg-card-dark border border-border-dark rounded-2xl p-6 animate-pulse">
                <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
                <div className="h-4 bg-gray-700 rounded w-2/3"></div>
            </div>
        );
    }

    if (!efficiencyData) {
        return null; // Or empty state
    }

    // Determine overall status
    const criticalItems = efficiencyData.recommendations.filter(r => r.efficiency < 0.9);
    const isCritical = criticalItems.length > 0;

    return (
        <div className="bg-card-dark border border-border-dark rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-accent-purple">psychology</span>
                        Inteligencia de Cocina (Live)
                    </h3>
                    <p className="text-text-muted text-sm">Análisis de consumo real vs receta estándar</p>
                </div>
                <div>
                    {isCritical ? (
                        <span className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm font-medium border border-red-500/30 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[16px]">warning</span>
                            Desviación Alta
                        </span>
                    ) : (
                        <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-sm font-medium border border-emerald-500/30 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[16px]">check_circle</span>
                            Eficiencia Óptima
                        </span>
                    )}
                </div>
            </div>

            {/* Main Insights Canvas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left: Alerts & Messages */}
                <div className="space-y-4">
                    {efficiencyData.recommendations.length === 0 ? (
                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-200 text-sm">
                            Tu cocina está siguiendo esta receta a la perfección. ¡Buen trabajo!
                        </div>
                    ) : (
                        efficiencyData.recommendations.map((rec, idx) => {
                            // Find ingredient Name from recipe items if possible, or use ID
                            // Warning: recipe.items might not match perfectly if recommendations include removed items? Unlikely.
                            // The backend message usually contains text "Tu receta dice X pero cocina usa Y".
                            return (
                                <div key={idx} className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                    <div className="flex items-start gap-3">
                                        <span className="material-symbols-outlined text-amber-400 mt-0.5">lightbulb</span>
                                        <div>
                                            <p className="text-amber-100 text-sm font-medium mb-1">Insight Generado</p>
                                            <p className="text-gray-300 text-sm">{rec.message}</p>
                                            <div className="mt-2 text-xs text-amber-400/80">
                                                Eficiencia: {(rec.efficiency * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Right: Actions & Calibration */}
                <div className="flex flex-col justify-center items-end space-y-4">
                    {isCritical && !calibrationResult && (
                        <div className="text-center w-full">
                            <p className="text-gray-400 text-sm mb-3">
                                Se detectaron diferencias consistentes. ¿Deseas ajustar la receta a la realidad?
                            </p>
                            <button
                                onClick={handleCalibrate}
                                disabled={calibrating}
                                className="w-full py-3 bg-gradient-to-r from-accent-purple to-indigo-600 hover:from-accent-purple/90 hover:to-indigo-600/90 text-white rounded-xl shadow-lg shadow-indigo-500/20 transition-all font-medium flex items-center justify-center gap-2"
                            >
                                {calibrating ? (
                                    <span className="material-symbols-outlined animate-spin">sync</span>
                                ) : (
                                    <span className="material-symbols-outlined">auto_fix_high</span>
                                )}
                                Calibrar Receta Automáticamente
                            </button>
                        </div>
                    )}

                    {/* Calibration Result (Price Suggestion) */}
                    {calibrationResult && (
                        <div className="w-full bg-bg-deep border border-indigo-500/30 rounded-xl p-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <h4 className="font-bold text-white mb-3 flex items-center gap-2">
                                <span className="material-symbols-outlined text-emerald-400">price_check</span>
                                Resultado de Calibración
                            </h4>

                            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                                <div>
                                    <span className="block text-gray-500 text-xs">Costo Anterior</span>
                                    <span className="text-gray-300 font-mono line-through">{formatCurrency(calibrationResult.old_cost)}</span>
                                </div>
                                <div className="text-right">
                                    <span className="block text-gray-500 text-xs">Nuevo Costo</span>
                                    <span className="text-white font-bold font-mono">{formatCurrency(calibrationResult.new_cost)}</span>
                                </div>
                            </div>

                            {calibrationResult.suggested_price > calibrationResult.current_price && (
                                <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-3">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-indigo-200 font-medium">Precio Sugerido</span>
                                        <span className="text-indigo-300 font-bold font-mono text-lg">{formatCurrency(calibrationResult.suggested_price)}</span>
                                    </div>
                                    <p className="text-xs text-indigo-400/80 leading-relaxed">
                                        Para mantener tu margen del {(calibrationResult.old_margin_pct * 100).toFixed(0)}%, deberías subir el precio.
                                        <br />
                                        Si mantienes {formatCurrency(calibrationResult.current_price)}, tu margen bajará al {(calibrationResult.new_margin_pct_if_static * 100).toFixed(0)}%.
                                    </p>
                                </div>
                            )}

                            <div className="mt-3 text-center">
                                <span className="text-emerald-400 text-xs flex items-center justify-center gap-1">
                                    <span className="material-symbols-outlined text-[14px]">check</span>
                                    Receta Actualizada Exitosamente
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
