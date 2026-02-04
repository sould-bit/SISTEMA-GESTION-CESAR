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

    // Financial Data
    const [productPrice, setProductPrice] = useState<number>(0);
    const [margin, setMargin] = useState({ percent: 0, value: 0 });
    const [foodCostPct, setFoodCostPct] = useState(0);

    useEffect(() => {
        if (!recipe?.id) return;
        loadEfficiency();
        if (recipe.product_id) loadProductFinancials();
    }, [recipe.id]);

    const loadProductFinancials = async () => {
        try {
            const product = await kitchenService.getProduct(recipe.product_id);
            if (product) {
                const price = Number(product.price);
                const cost = Number(recipe.total_cost);
                setProductPrice(price);

                if (price > 0) {
                    const marginValue = price - cost;
                    const marginPct = (marginValue / price) * 100;
                    const fcPct = (cost / price) * 100;

                    setMargin({ percent: marginPct, value: marginValue });
                    setFoodCostPct(fcPct);
                }
            }
        } catch (error) {
            console.error('Error loading product financials:', error);
        }
    };

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

            // Reload efficiency and financials after calibration
            loadEfficiency();
            loadProductFinancials();
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

    if (loading && !efficiencyData) {
        return (
            <div className="bg-card-dark border border-border-dark rounded-2xl p-6 animate-pulse">
                <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
                <div className="h-4 bg-gray-700 rounded w-2/3"></div>
            </div>
        );
    }

    // Determine overall status
    const criticalItems = efficiencyData?.recommendations.filter(r => r.efficiency < 0.9) || [];
    const isCritical = criticalItems.length > 0;
    const isLowMargin = margin.percent < 30; // 30% threshold for warning

    return (
        <div className="space-y-6">
            {/* 1. PROFITABILITY DASHBOARD */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">

                {/* Selling Price Card */}
                <div className="bg-card-dark border border-border-dark rounded-2xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <span className="material-symbols-outlined text-[80px] text-white">payments</span>
                    </div>
                    <p className="text-text-muted text-xs uppercase tracking-wider font-semibold mb-1">Precio de Venta</p>
                    <h3 className="text-2xl font-bold text-white font-mono">{formatCurrency(productPrice)}</h3>
                    <div className="mt-2 text-xs text-gray-400 flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">storefront</span>
                        Producto vinculado
                    </div>
                </div>

                {/* Total Cost Card */}
                <div className="bg-card-dark border border-border-dark rounded-2xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <span className="material-symbols-outlined text-[80px] text-amber-500">shopping_cart</span>
                    </div>
                    <p className="text-text-muted text-xs uppercase tracking-wider font-semibold mb-1">Costo Total (Materia Prima)</p>
                    <h3 className="text-2xl font-bold text-white font-mono">{formatCurrency(Number(recipe.total_cost))}</h3>
                    <div className="mt-2 text-xs flex items-center gap-1 text-amber-400">
                        <span className="material-symbols-outlined text-[14px]">restaurant_menu</span>
                        {recipe.items?.length || 0} ingredientes
                    </div>
                </div>

                {/* Gross Margin Card */}
                <div className={`bg-card-dark border rounded-2xl p-5 relative overflow-hidden group ${isLowMargin ? 'border-red-500/30' : 'border-emerald-500/30'}`}>
                    <div className={`absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity`}>
                        <span className={`material-symbols-outlined text-[80px] ${isLowMargin ? 'text-red-500' : 'text-emerald-500'}`}>trending_up</span>
                    </div>
                    <p className="text-text-muted text-xs uppercase tracking-wider font-semibold mb-1">Margen Bruto (Ganancia)</p>
                    <div className="flex items-baseline gap-2">
                        <h3 className={`text-2xl font-bold font-mono ${isLowMargin ? 'text-red-400' : 'text-emerald-400'}`}>
                            {formatCurrency(margin.value)}
                        </h3>
                        <span className={`text-sm font-bold ${isLowMargin ? 'text-red-500' : 'text-emerald-500'}`}>
                            {margin.percent.toFixed(1)}%
                        </span>
                    </div>
                    <div className="mt-2">
                        {isLowMargin ? (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-red-500/10 text-red-300 px-2 py-0.5 rounded border border-red-500/20">
                                <span className="material-symbols-outlined text-[12px]">warning</span>
                                Margen bajo (Meta {'>'} 30%)
                            </span>
                        ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/20">
                                <span className="material-symbols-outlined text-[12px]">check_circle</span>
                                Margen saludable
                            </span>
                        )}
                    </div>
                </div>

                {/* Food Cost % Card */}
                <div className="bg-card-dark border border-border-dark rounded-2xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <span className="material-symbols-outlined text-[80px] text-blue-500">pie_chart</span>
                    </div>
                    <p className="text-text-muted text-xs uppercase tracking-wider font-semibold mb-1">Food Cost %</p>
                    <div className="relative pt-2">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-2xl font-bold text-white font-mono">{foodCostPct.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full ${foodCostPct > 40 ? 'bg-red-500' : foodCostPct > 35 ? 'bg-amber-500' : 'bg-blue-500'}`}
                                style={{ width: `${Math.min(foodCostPct, 100)}%` }}
                            ></div>
                        </div>
                        <p className="text-[10px] text-gray-500 mt-2">
                            {foodCostPct > 40 ? '🔴 Costo muy alto. Revisa porciones o precios.' : '🔵 Costo dentro del rango aceptable.'}
                        </p>
                    </div>
                </div>
            </div>

            {/* 2. INTELLIGENCE & CALIBRATION (Existing Logic + UI Refresh) */}
            {efficiencyData && (
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
                                    Desviación Detectada
                                </span>
                            ) : (
                                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-sm font-medium border border-emerald-500/30 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[16px]">check_circle</span>
                                    Eficiencia Óptima
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Insights List */}
                        <div className="space-y-4">
                            {efficiencyData.recommendations.length === 0 ? (
                                <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl flex items-start gap-3">
                                    <span className="material-symbols-outlined text-emerald-400 mt-1">verified</span>
                                    <div>
                                        <p className="text-white font-medium text-sm">Ejecución Perfecta</p>
                                        <p className="text-emerald-400/70 text-xs">Tu cocina está siguiendo esta receta al pie de la letra.</p>
                                    </div>
                                </div>
                            ) : (
                                efficiencyData.recommendations.map((rec, idx) => (
                                    <div key={idx} className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-xl hover:bg-amber-500/10 transition-colors">
                                        <div className="flex items-start gap-3">
                                            <span className="material-symbols-outlined text-amber-400 mt-0.5">lightbulb</span>
                                            <div>
                                                <p className="text-amber-100 text-sm font-medium mb-1">Oportunidad de Mejora</p>
                                                <p className="text-gray-300 text-sm leading-relaxed">{rec.message}</p>
                                                <div className="mt-2 text-xs text-amber-400/80 font-mono bg-amber-500/10 inline-block px-1.5 py-0.5 rounded">
                                                    Eficiencia actual: {(rec.efficiency * 100).toFixed(0)}%
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Actions & Calibration */}
                        <div className="flex flex-col justify-center items-end space-y-4 border-l border-white/5 pl-6">
                            {isCritical && !calibrationResult && (
                                <div className="text-center w-full">
                                    <p className="text-gray-400 text-sm mb-4">
                                        Hemos detectado que el consumo real difiere de la receta estándar.
                                        <br />
                                        <span className="text-amber-400 text-xs">Ajustar la receta a la realidad te dará costos más precisos.</span>
                                    </p>
                                    <button
                                        onClick={handleCalibrate}
                                        disabled={calibrating}
                                        className="w-full py-3 bg-gradient-to-r from-accent-purple to-orange-600 hover:from-accent-purple/90 hover:to-orange-600/90 text-white rounded-xl shadow-lg shadow-orange-500/20 transition-all font-medium flex items-center justify-center gap-2 group"
                                    >
                                        {calibrating ? (
                                            <span className="material-symbols-outlined animate-spin">sync</span>
                                        ) : (
                                            <span className="material-symbols-outlined group-hover:rotate-12 transition-transform">auto_fix_high</span>
                                        )}
                                        Calibrar Receta Automáticamente
                                    </button>
                                </div>
                            )}

                            {calibrationResult && (
                                <div className="w-full bg-bg-deep border border-orange-500/30 rounded-xl p-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <h4 className="font-bold text-white mb-3 flex items-center gap-2">
                                        <span className="material-symbols-outlined text-emerald-400">price_check</span>
                                        Resultado de Calibración
                                    </h4>

                                    <div className="grid grid-cols-2 gap-4 text-sm mb-4 bg-black/20 p-3 rounded-lg">
                                        <div>
                                            <span className="block text-gray-500 text-xs uppercase tracking-wider">Costo Anterior</span>
                                            <span className="text-gray-400 font-mono line-through text-sm">{formatCurrency(calibrationResult.old_cost)}</span>
                                        </div>
                                        <div className="text-right">
                                            <span className="block text-emerald-400 text-xs uppercase tracking-wider font-bold">Nuevo Costo</span>
                                            <span className="text-white font-bold font-mono text-lg">{formatCurrency(calibrationResult.new_cost)}</span>
                                        </div>
                                    </div>

                                    {calibrationResult.suggested_price > calibrationResult.current_price && (
                                        <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-orange-200 font-medium text-xs">Sugerencia de Precio</span>
                                                <span className="text-orange-300 font-bold font-mono">{formatCurrency(calibrationResult.suggested_price)}</span>
                                            </div>
                                            <p className="text-[10px] text-orange-400/80 leading-relaxed mt-1">
                                                Para mantener tu margen del {(calibrationResult.old_margin_pct * 100).toFixed(0)}%.
                                                Si no ajustas, tu margen caerá al {(calibrationResult.new_margin_pct_if_static * 100).toFixed(0)}%.
                                            </p>
                                        </div>
                                    )}

                                    <div className="mt-4 pt-3 border-t border-white/5 text-center">
                                        <span className="text-emerald-400 text-xs flex items-center justify-center gap-1 font-medium">
                                            <span className="material-symbols-outlined text-[14px]">check_circle</span>
                                            Receta actualizada con éxito
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
