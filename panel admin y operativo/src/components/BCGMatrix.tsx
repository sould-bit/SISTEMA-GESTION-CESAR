/**
 * BCGMatrix Component - Visualización de la Matriz BCG de Ingeniería de Menú
 * 
 * Cuadrantes:
 * - Stars (top-right): Alta popularidad + Alto margen
 * - Plowhorses (top-left): Alta popularidad + Bajo margen
 * - Puzzles (bottom-right): Baja popularidad + Alto margen
 * - Dogs (bottom-left): Baja popularidad + Bajo margen
 */

import { useState, useEffect, useMemo } from 'react';
import { api } from '../lib/api';

interface ProductMetrics {
    product_id: number;
    product_name: string;
    category: string;
    price: number;
    cost: number;
    quantity_sold: number;
    revenue: number;
    contribution_margin: number;
    food_cost_pct: number;
    popularity_pct: number;
    revenue_share: number;
    classification: 'star' | 'plowhorse' | 'puzzle' | 'dog';
}

interface BCGMatrixData {
    stars: ProductMetrics[];
    plowhorses: ProductMetrics[];
    puzzles: ProductMetrics[];
    dogs: ProductMetrics[];
}

interface ReportSummary {
    total_products: number;
    total_revenue: number;
    total_quantity_sold: number;
    avg_popularity_threshold: number;
    avg_margin_threshold: number;
}

interface MenuEngineeringReport {
    period: { start: string; end: string };
    summary: ReportSummary;
    classification_counts: { stars: number; plowhorses: number; puzzles: number; dogs: number };
    matrix: BCGMatrixData;
    all_products: ProductMetrics[];
}

const QUADRANT_CONFIG = {
    star: {
        label: 'Estrellas',
        color: 'amber',
        icon: 'star',
        description: 'Mantener y optimizar',
        bgClass: 'bg-amber-500/10 border-amber-500/30',
        textClass: 'text-amber-400',
        iconClass: 'text-amber-400',
    },
    plowhorse: {
        label: 'Caballos de Trabajo',
        color: 'blue',
        icon: 'trending_up',
        description: 'Reducir costos',
        bgClass: 'bg-blue-500/10 border-blue-500/30',
        textClass: 'text-blue-400',
        iconClass: 'text-blue-400',
    },
    puzzle: {
        label: 'Rompecabezas',
        color: 'purple',
        icon: 'extension',
        description: 'Promocionar más',
        bgClass: 'bg-purple-500/10 border-purple-500/30',
        textClass: 'text-purple-400',
        iconClass: 'text-purple-400',
    },
    dog: {
        label: 'Perros',
        color: 'red',
        icon: 'warning',
        description: 'Evaluar eliminación',
        bgClass: 'bg-red-500/10 border-red-500/30',
        textClass: 'text-red-400',
        iconClass: 'text-red-400',
    },
};

export const BCGMatrix = () => {
    const [report, setReport] = useState<MenuEngineeringReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedQuadrant, setSelectedQuadrant] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'matrix' | 'table'>('matrix');

    useEffect(() => {
        const fetchReport = async () => {
            setLoading(true);
            try {
                const response = await api.get<MenuEngineeringReport>('/reports/menu-engineering/');
                setReport(response.data);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Error al cargar reporte');
            } finally {
                setLoading(false);
            }
        };
        fetchReport();
    }, []);

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    };

    const selectedProducts = useMemo(() => {
        if (!report || !selectedQuadrant) return [];
        return report.matrix[selectedQuadrant as keyof BCGMatrixData] || [];
    }, [report, selectedQuadrant]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-6 py-4 rounded-xl">
                {error}
            </div>
        );
    }

    if (!report) return null;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-accent-primary">analytics</span>
                        Ingeniería de Menú
                    </h1>
                    <p className="text-text-muted text-sm">
                        Análisis BCG • Últimos 30 días • {report.summary.total_products} productos
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode('matrix')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${viewMode === 'matrix' ? 'bg-accent-primary text-white' : 'bg-card-dark text-text-muted hover:text-white'}`}
                    >
                        <span className="material-symbols-outlined text-[18px] align-middle mr-1">grid_view</span>
                        Matriz
                    </button>
                    <button
                        onClick={() => setViewMode('table')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-accent-primary text-white' : 'bg-card-dark text-text-muted hover:text-white'}`}
                    >
                        <span className="material-symbols-outlined text-[18px] align-middle mr-1">table_rows</span>
                        Tabla
                    </button>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(QUADRANT_CONFIG).map(([key, config]) => (
                    <button
                        key={key}
                        onClick={() => setSelectedQuadrant(selectedQuadrant === key ? null : key)}
                        className={`p-4 rounded-xl border transition-all ${config.bgClass} ${selectedQuadrant === key ? 'ring-2 ring-white/50 scale-[1.02]' : 'hover:scale-[1.01]'}`}
                    >
                        <div className="flex items-center justify-between mb-2">
                            <span className={`material-symbols-outlined ${config.iconClass}`}>{config.icon}</span>
                            <span className={`text-2xl font-bold ${config.textClass}`}>
                                {report.classification_counts[key as keyof typeof report.classification_counts]}
                            </span>
                        </div>
                        <div className={`text-sm font-medium ${config.textClass}`}>{config.label}</div>
                        <div className="text-xs text-text-muted">{config.description}</div>
                    </button>
                ))}
            </div>

            {viewMode === 'matrix' ? (
                /* BCG Matrix Visual */
                <div className="bg-card-dark border border-border-dark rounded-2xl p-6">
                    <div className="grid grid-cols-2 gap-4 aspect-square max-w-2xl mx-auto">
                        {/* Top Row: Plowhorses | Stars */}
                        <QuadrantCell
                            products={report.matrix.plowhorses}
                            config={QUADRANT_CONFIG.plowhorse}
                        />
                        <QuadrantCell
                            products={report.matrix.stars}
                            config={QUADRANT_CONFIG.star}
                        />
                        {/* Bottom Row: Dogs | Puzzles */}
                        <QuadrantCell
                            products={report.matrix.dogs}
                            config={QUADRANT_CONFIG.dog}
                        />
                        <QuadrantCell
                            products={report.matrix.puzzles}
                            config={QUADRANT_CONFIG.puzzle}
                        />
                    </div>
                    {/* Axis Labels */}
                    <div className="flex justify-between mt-4 text-xs text-text-muted">
                        <span>← Bajo Margen</span>
                        <span className="font-medium">RENTABILIDAD</span>
                        <span>Alto Margen →</span>
                    </div>
                    <div className="flex flex-col items-center -mt-2 text-xs text-text-muted">
                        <span className="rotate-0">↑ Alta Popularidad</span>
                        <span className="font-medium my-2">POPULARIDAD</span>
                        <span className="rotate-0">↓ Baja Popularidad</span>
                    </div>
                </div>
            ) : (
                /* Table View */
                <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-bg-deep border-b border-border-dark">
                                <tr>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Producto</th>
                                    <th className="px-4 py-3 text-left text-text-muted font-medium text-xs uppercase">Clasificación</th>
                                    <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Ventas</th>
                                    <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Revenue</th>
                                    <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Margen</th>
                                    <th className="px-4 py-3 text-right text-text-muted font-medium text-xs uppercase">Food Cost</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark">
                                {report.all_products.map((product) => {
                                    const config = QUADRANT_CONFIG[product.classification];
                                    return (
                                        <tr key={product.product_id} className="hover:bg-white/5">
                                            <td className="px-4 py-3">
                                                <div className="font-medium text-white">{product.product_name}</div>
                                                <div className="text-xs text-text-muted">{product.category}</div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bgClass} ${config.textClass}`}>
                                                    <span className="material-symbols-outlined text-[14px]">{config.icon}</span>
                                                    {config.label}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-right font-mono text-gray-300">
                                                {product.quantity_sold}
                                            </td>
                                            <td className="px-4 py-3 text-right font-mono text-emerald-400">
                                                {formatCurrency(product.revenue)}
                                            </td>
                                            <td className="px-4 py-3 text-right font-mono text-white">
                                                {formatCurrency(product.contribution_margin)}
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                <span className={`font-mono ${product.food_cost_pct > 35 ? 'text-red-400' : product.food_cost_pct > 28 ? 'text-amber-400' : 'text-emerald-400'}`}>
                                                    {product.food_cost_pct.toFixed(1)}%
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Selected Quadrant Detail */}
            {selectedQuadrant && selectedProducts.length > 0 && (
                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        {QUADRANT_CONFIG[selectedQuadrant as keyof typeof QUADRANT_CONFIG].label}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {selectedProducts.slice(0, 6).map((product) => (
                            <div key={product.product_id} className="bg-bg-deep rounded-lg p-3">
                                <div className="font-medium text-white text-sm">{product.product_name}</div>
                                <div className="text-xs text-text-muted mt-1">
                                    {product.quantity_sold} vendidos • {formatCurrency(product.revenue)}
                                </div>
                                <div className="flex justify-between mt-2 text-xs">
                                    <span className="text-text-muted">Margen:</span>
                                    <span className="text-emerald-400 font-mono">{formatCurrency(product.contribution_margin)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// Quadrant Cell Component
const QuadrantCell = ({ products, config }: {
    products: ProductMetrics[];
    config: typeof QUADRANT_CONFIG.star;
}) => (
    <div className={`${config.bgClass} rounded-xl p-4 flex flex-col`}>
        <div className="flex items-center justify-between mb-2">
            <span className={`material-symbols-outlined text-2xl ${config.iconClass}`}>{config.icon}</span>
            <span className={`text-lg font-bold ${config.textClass}`}>{products.length}</span>
        </div>
        <div className={`font-semibold ${config.textClass} text-sm`}>{config.label}</div>
        <div className="text-xs text-text-muted mb-3">{config.description}</div>
        <div className="flex-1 space-y-1 overflow-hidden">
            {products.slice(0, 3).map((p) => (
                <div key={p.product_id} className="text-xs text-white/80 truncate">
                    • {p.product_name}
                </div>
            ))}
            {products.length > 3 && (
                <div className="text-xs text-text-muted">+{products.length - 3} más</div>
            )}
        </div>
    </div>
);
