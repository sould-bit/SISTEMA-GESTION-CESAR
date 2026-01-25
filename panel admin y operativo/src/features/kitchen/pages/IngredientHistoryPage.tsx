import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { kitchenService, Ingredient, IngredientCostHistory, IngredientBatch } from '../kitchen.service';
import { SVGPriceChart } from '@/components/SVGPriceChart';
import { HelpIcon } from '@/components/ui/Tooltip';

export const IngredientHistoryPage = () => {
    const { id } = useParams<{ id: string }>();
    const [ingredient, setIngredient] = useState<Ingredient | null>(null);
    const [history, setHistory] = useState<IngredientCostHistory[]>([]);
    const [activeBatches, setActiveBatches] = useState<IngredientBatch[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            loadData();
        }
    }, [id]);

    const loadData = async () => {
        setLoading(true);
        try {
            if (!id) return;
            const [ingData, histData, batchesData] = await Promise.all([
                kitchenService.getIngredient(id),
                kitchenService.getIngredientHistory(id),
                kitchenService.getIngredientBatches(id, true) // Active only
            ]);
            setIngredient(ingData);
            setHistory(histData);
            setActiveBatches(batchesData);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error loading data');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleString('es-CO');
    };

    if (loading) return <div className="p-8 text-white flex justify-center">Cargando historial...</div>;
    if (error) return <div className="p-8 text-red-500">Error: {error}</div>;
    if (!ingredient) return <div className="p-8 text-white">Ingrediente no encontrado</div>;

    // Prepare data for chart
    const chartData = history.map(h => ({
        date: h.created_at,
        price: h.new_cost
    })).reverse(); // Oldest first for chart logic

    // Add current cost as the latest point if history doesn't cover it (optional, but good for context)
    // Actually history should record the latest change, so it should be there.

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link to="/kitchen/ingredients" className="p-2 bg-card-dark rounded-full hover:bg-white/10 transition-colors text-white">
                    <span className="material-symbols-outlined">arrow_back</span>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-emerald-400">query_stats</span>
                        Historial de Costos: {ingredient.name}
                    </h1>
                    <p className="text-text-muted text-sm">SKU: {ingredient.sku} — Unidad: {ingredient.base_unit}</p>
                </div>
            </div>

            {/* Analysis Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Visual Chart */}
                <div className="lg:col-span-2 bg-card-dark border border-border-dark rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Tendencia de Precio</h3>
                    <div className="h-[350px] bg-bg-deep rounded-lg p-4 border border-border-dark">
                        <SVGPriceChart data={chartData} height={320} lineColor="#34D399" fillColor="rgba(52, 211, 153, 0.1)" />
                    </div>
                </div>

                {/* KPI Cards */}
                <div className="space-y-4">
                    <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                        <div className="text-text-muted text-xs uppercase">Costo Actual</div>
                        <div className="text-3xl font-bold text-white font-mono mt-2">
                            {formatCurrency(ingredient.current_cost)}
                        </div>
                        <div className="text-xs text-emerald-400 mt-1 flex items-center">
                            <span className="material-symbols-outlined text-xs mr-1">check_circle</span>
                            Precio Vigente
                        </div>
                    </div>

                    <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                        <div className="text-text-muted text-xs uppercase">Variación Total</div>
                        <div className={`text-2xl font-bold font-mono mt-2 ${history.length > 1
                            ? (history[0].new_cost > history[history.length - 1].new_cost ? 'text-red-400' : 'text-emerald-400')
                            : 'text-white'
                            }`}>
                            {history.length > 0
                                ? formatCurrency(history[0].new_cost - history[history.length - 1].new_cost)
                                : '$0'}
                        </div>
                        <p className="text-xs text-text-muted mt-2">Desde el primer registro</p>
                    </div>

                    <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                        <h4 className="text-white font-medium mb-3">Analítica</h4>
                        <ul className="space-y-2 text-sm text-text-muted">
                            <li className="flex justify-between">
                                <span>Registros:</span>
                                <span className="text-white">{history.length}</span>
                            </li>
                            <li className="flex justify-between">
                                <span>Último cambio:</span>
                                <span className="text-white">{history.length > 0 ? new Date(history[0].created_at).toLocaleDateString() : 'N/A'}</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Active Batches Section */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-border-dark flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Lotes de Compra Activos</h3>
                    <div className="text-sm text-text-muted">
                        Método: <span className="text-accent-orange font-bold">FIFO</span> (Primero en entrar, primero en salir)
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-3 text-left text-text-muted font-medium text-xs uppercase">Fecha de Compra</th>
                                <th className="px-6 py-3 text-left text-text-muted font-medium text-xs uppercase">Proveedor</th>
                                <th className="px-6 py-3 text-center text-text-muted font-medium text-xs uppercase">Cantidad Inicial</th>
                                <th className="px-6 py-3 text-center text-text-muted font-medium text-xs uppercase">
                                    Restante
                                    <HelpIcon text="Cantidad disponible de este lote específico." />
                                </th>
                                <th className="px-6 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo Unitario</th>
                                <th className="px-6 py-3 text-center text-text-muted font-medium text-xs uppercase">Estado</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {activeBatches.map((batch) => (
                                <tr key={batch.id} className="hover:bg-white/5">
                                    <td className="px-6 py-3 text-white">
                                        {formatDate(batch.acquired_at)}
                                    </td>
                                    <td className="px-6 py-3 text-white">
                                        {batch.supplier || <span className="text-text-muted italic">-</span>}
                                    </td>
                                    <td className="px-6 py-3 text-center text-text-muted font-mono">
                                        {batch.quantity_initial}
                                    </td>
                                    <td className="px-6 py-3 text-center font-mono">
                                        <span className={`px-2 py-1 rounded ${batch.quantity_remaining > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-text-muted'}`}>
                                            {batch.quantity_remaining}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3 text-right text-white font-mono">
                                        {formatCurrency(batch.cost_per_unit)}
                                    </td>
                                    <td className="px-6 py-3 text-center">
                                        <span className="text-xs text-emerald-400 flex items-center justify-center gap-1">
                                            <span className="material-symbols-outlined text-[14px]">check_circle</span>
                                            Activo
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {activeBatches.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-text-muted">
                                        No hay lotes activos. El stock actual no está asociado a lotes de compra específicos.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* History Table */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-border-dark">
                    <h3 className="text-lg font-semibold text-white">Registro de Cambios</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-bg-deep border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-3 text-left text-text-muted font-medium text-xs uppercase">Fecha</th>
                                <th className="px-6 py-3 text-right text-text-muted font-medium text-xs uppercase">Costo Anterior</th>
                                <th className="px-6 py-3 text-right text-text-muted font-medium text-xs uppercase">Nuevo Costo</th>
                                <th className="px-6 py-3 text-left text-text-muted font-medium text-xs uppercase pl-10">Razón</th>
                                <th className="px-6 py-3 text-left text-text-muted font-medium text-xs uppercase">Usuario</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {history.map((record) => {
                                const change = record.new_cost - record.previous_cost;
                                return (
                                    <tr key={record.id} className="hover:bg-white/5">
                                        <td className="px-6 py-3 text-white">
                                            {formatDate(record.created_at)}
                                        </td>
                                        <td className="px-6 py-3 text-right text-text-muted font-mono">
                                            {formatCurrency(record.previous_cost)}
                                        </td>
                                        <td className="px-6 py-3 text-right text-white font-bold font-mono">
                                            {formatCurrency(record.new_cost)}
                                            <span className={`ml-2 text-xs ${change > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                                {change > 0 ? '▲' : '▼'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-3 pl-10 text-white">
                                            {record.reason || <span className="text-text-muted italic">Sin razón</span>}
                                        </td>
                                        <td className="px-6 py-3 text-text-muted text-xs">
                                            ID: {record.user_id || 'System'}
                                        </td>
                                    </tr>
                                );
                            })}
                            {history.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-text-muted">
                                        No hay historial de cambios registrado.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
