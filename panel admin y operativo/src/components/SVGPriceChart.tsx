import React, { useMemo } from 'react';

interface DataPoint {
    date: string;
    price: number;
}

interface SVGPriceChartProps {
    data: DataPoint[];
    height?: number;
    width?: string;
    lineColor?: string;
    fillColor?: string;
}

export const SVGPriceChart: React.FC<SVGPriceChartProps> = ({
    data,
    height = 300,
    width = '100%',
    lineColor = '#10B981', // Emerald-500
    fillColor = 'rgba(16, 185, 129, 0.1)',
}) => {
    if (!data || data.length === 0) {
        return <div className="h-full flex items-center justify-center text-gray-500">Sin datos históricos</div>;
    }

    // Sort data by date
    const sortedData = useMemo(() =>
        [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()),
        [data]);

    // Calculate dimensions and scales
    const padding = 40;
    const chartHeight = height - padding * 2;
    // We assume 100% width, but for SVG ViewBox we need a fixed logic number. 
    // Let's use 800 for internal coord system.
    const viewBoxWidth = 800;
    const chartWidth = viewBoxWidth - padding * 2;

    const minPrice = Math.min(...sortedData.map(d => d.price)) * 0.9;
    const maxPrice = Math.max(...sortedData.map(d => d.price)) * 1.1;
    const priceRange = maxPrice - minPrice || 1; // Prevent division by zero

    const minDate = new Date(sortedData[0].date).getTime();
    const maxDate = new Date(sortedData[sortedData.length - 1].date).getTime();
    const dateRange = maxDate - minDate || 1;

    // Helper to map data to coordinates
    const getX = (dateStr: string) => {
        const date = new Date(dateStr).getTime();
        return padding + ((date - minDate) / dateRange) * chartWidth;
    };

    const getY = (price: number) => {
        return padding + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
    };

    // Generate Path
    const points = sortedData.map(d => `${getX(d.date)},${getY(d.price)}`).join(' ');
    const areaPath = `
        M ${padding},${height - padding} 
        L ${points.split(' ')[0]} 
        L ${points} 
        L ${getX(sortedData[sortedData.length - 1].date)},${height - padding} 
        Z
    `;

    return (
        <div className="w-full" style={{ height }}>
            <svg viewBox={`0 0 ${viewBoxWidth} ${height}`} className="w-full h-full overflow-visible">
                {/* Grid Lines (Horizontal) */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                    const y = padding + chartHeight * ratio;
                    const price = maxPrice - (priceRange * ratio);
                    return (
                        <g key={ratio}>
                            <line
                                x1={padding}
                                y1={y}
                                x2={viewBoxWidth - padding}
                                y2={y}
                                stroke="#374151"
                                strokeDasharray="4 4"
                                strokeWidth="0.5"
                            />
                            <text
                                x={padding - 10}
                                y={y + 4}
                                textAnchor="end"
                                fill="#9CA3AF"
                                fontSize="10"
                            >
                                ${Math.round(price)}
                            </text>
                        </g>
                    );
                })}

                {/* Area Fill */}
                <path d={areaPath} fill={fillColor} />

                {/* Line */}
                <polyline
                    fill="none"
                    stroke={lineColor}
                    strokeWidth="2"
                    points={points}
                />

                {/* Data Points */}
                {sortedData.map((d, i) => (
                    <circle
                        key={i}
                        cx={getX(d.date)}
                        cy={getY(d.price)}
                        r="3"
                        fill="#1F2937"
                        stroke={lineColor}
                        strokeWidth="2"
                    />
                ))}

                {/* Date Labels (Start and End) */}
                <text x={padding} y={height - padding + 20} fill="#9CA3AF" fontSize="10" textAnchor="middle">
                    {new Date(minDate).toLocaleDateString()}
                </text>
                <text x={viewBoxWidth - padding} y={height - padding + 20} fill="#9CA3AF" fontSize="10" textAnchor="middle">
                    {new Date(maxDate).toLocaleDateString()}
                </text>

            </svg>
        </div>
    );
};
