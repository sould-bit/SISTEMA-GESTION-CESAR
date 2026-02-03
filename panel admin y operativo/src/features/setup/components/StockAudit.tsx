import { ArrowLeft, ChevronRight, UtensilsCrossed, SlidersHorizontal, Check, Box, Zap, PackageSearch, AlertTriangle, RefreshCcw, Save } from 'lucide-react';
import { useState, useMemo } from 'react';
import { useSetupData } from '../hooks/useSetupData';
import { setupService } from '../setup.service';

interface StockAuditProps {
    onBack: () => void;
    initialType?: 'FLASH' | 'FULL';
    initialSelection?: string[];
}

type AuditMode = 'SELECT_TYPE' | 'SELECTION_LIST' | 'WIZARD' | 'SUMMARY';

export const StockAudit = ({ onBack, initialType, initialSelection }: StockAuditProps) => {
    const { ingredients, refreshData } = useSetupData();
    const [auditMode, setAuditMode] = useState<AuditMode>(initialType ? 'SELECTION_LIST' : 'SELECT_TYPE');
    const [auditType, setAuditType] = useState<'FLASH' | 'FULL'>(initialType || 'FLASH');

    // Selection State
    const [selectedItemIds, setSelectedItemIds] = useState<Set<string>>(
        initialSelection ? new Set(initialSelection) : new Set()
    );

    // Audit Execution State
    const [wizardDetails, setWizardDetails] = useState<{
        queue: string[]; // Array of IDs to audit
        currentIndex: number;
        results: Record<string, number>; // ID -> Physical Count
    }>({ queue: [], currentIndex: 0, results: {} });

    const [isSubmitting, setIsSubmitting] = useState(false);

    // 1. FILTERING & DATA PREP
    const filteredIngredients = useMemo(() => {
        if (auditType === 'FULL') return ingredients;

        const initialSet = new Set(initialSelection || []);

        // Flash: Critical or Low Stock OR Explicitly Selected
        return ingredients.filter(item => {
            if (item.id && initialSet.has(item.id)) return true; // Always show selected

            const minStock = Number(item.min_stock) || 0;
            const stock = Number(item.stock) || 0;
            return stock <= minStock * 1.5; // Critical (<= min) or Low (<= 1.5x min)
        });
    }, [ingredients, auditType, initialSelection]);

    // 2. HANDLERS
    const handleStartSelection = (type: 'FLASH' | 'FULL') => {
        setAuditType(type);
        setAuditMode('SELECTION_LIST');
        if (type === 'FLASH') {
            setSelectedItemIds(new Set());
        } else {
            setSelectedItemIds(new Set());
        }
    };

    const toggleSelection = (id: string) => {
        const newSet = new Set(selectedItemIds);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setSelectedItemIds(newSet);
    };

    const toggleSelectAll = () => {
        if (selectedItemIds.size === filteredIngredients.length) {
            setSelectedItemIds(new Set());
        } else {
            setSelectedItemIds(new Set(filteredIngredients.map(i => i.id!)));
        }
    };

    const startWizard = () => {
        const queue = Array.from(selectedItemIds);
        if (queue.length === 0) return;
        setWizardDetails({
            queue,
            currentIndex: 0,
            results: {}
        });
        setAuditMode('WIZARD');
    };

    const submitCurrentWizardStep = (count: number) => {
        const currentId = wizardDetails.queue[wizardDetails.currentIndex];

        setWizardDetails(prev => ({
            ...prev,
            results: { ...prev.results, [currentId]: count },
            currentIndex: prev.currentIndex + 1
        }));

        // Check if finished
        if (wizardDetails.currentIndex >= wizardDetails.queue.length - 1) {
            setAuditMode('SUMMARY');
        }
    };

    const currentWizardItem = useMemo(() => {
        if (auditMode !== 'WIZARD') return null;
        const id = wizardDetails.queue[wizardDetails.currentIndex];
        return ingredients.find(i => i.id === id);
    }, [auditMode, wizardDetails, ingredients]);

    const handleCommitAudit = async () => {
        setIsSubmitting(true);
        try {
            const promises = Object.entries(wizardDetails.results).map(async ([id, count]) => {
                const item = ingredients.find(i => i.id === id);
                if (!item) return;

                const currentStock = Number(item.stock) || 0;
                const diff = count - currentStock;

                await setupService.updateIngredientStock(
                    id,
                    count,
                    'ADJUST',
                    `Auditoría ${auditType}: ${diff >= 0 ? '+' : ''}${diff.toFixed(2)}`
                );
            });

            await Promise.all(promises);
            await refreshData();
            onBack(); // Go back to inventory
        } catch (error) {
            console.error("Audit Commit Failed", error);
            // Show error toast?
        } finally {
            setIsSubmitting(false);
        }
    };

    // Calculate Summary Stats
    const summaryData = useMemo(() => {
        let totalVarianceValue = 0;
        const rows = Object.entries(wizardDetails.results).map(([id, physicalCount]) => {
            const item = ingredients.find(i => i.id === id);
            if (!item) return null;
            const currentStock = Number(item.stock) || 0;
            const diff = physicalCount - currentStock;
            const price = Number(item.price) || 0;
            const varianceValue = diff * price;
            totalVarianceValue += varianceValue;

            // Healthy Logic (5%)
            const variancePercent = currentStock !== 0 ? Math.abs(diff / currentStock) : (diff !== 0 ? 1 : 0);
            const isHealthy = variancePercent <= 0.05;

            return {
                item,
                currentStock,
                physicalCount,
                diff,
                varianceValue,
                isHealthy
            };
        }).filter((r): r is NonNullable<typeof r> => r !== null);

        return { rows, totalVarianceValue };
    }, [wizardDetails.results, ingredients]);


    return (
        <div className="bg-slate-900 text-white font-sans min-h-screen flex flex-col selection:bg-orange-500 selection:text-white absolute inset-0 z-50 overflow-hidden">

            {/* HEADER */}
            <header className="border-b border-slate-700 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 flex-none">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button onClick={onBack} className="bg-slate-800 hover:bg-slate-700 p-2 rounded-lg text-slate-400 hover:text-white transition-colors">
                            <ArrowLeft size={20} />
                        </button>
                        <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-2 flex items-center justify-center">
                            <Box className="text-orange-500" size={24} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight leading-none text-white">FastOps</h1>
                            <p className="text-xs text-slate-400 font-medium">Auditoría de Stock</p>
                        </div>
                    </div>
                    {/* Status Indicator */}
                    <div className="hidden md:flex items-center gap-2 text-xs font-semibold text-slate-400 bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
                        {auditMode === 'WIZARD' ? (
                            <>
                                <span className="relative flex h-2 w-2 mr-1">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-500 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                                </span>
                                Auditoría en Curso
                            </>
                        ) : (
                            <span className="text-slate-500">Modo Selección</span>
                        )}
                    </div>
                </div>
            </header>

            <main className="flex-grow p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-8 flex flex-col overflow-y-auto custom-scrollbar">

                {/* 1. SELECT TYPE */}
                {auditMode === 'SELECT_TYPE' && (
                    <section className="animate-in fade-in slide-in-from-bottom-4 duration-500 m-auto w-full max-w-4xl">
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Flash Audit */}
                            <button
                                onClick={() => handleStartSelection('FLASH')}
                                className="group relative flex flex-col items-start p-8 rounded-2xl border-2 border-slate-700 bg-slate-800 hover:border-orange-500 hover:bg-slate-700/50 transition-all duration-300 text-left shadow-lg overflow-hidden"
                            >
                                <Zap size={120} className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity transform rotate-12 text-orange-500" />
                                <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-yellow-400/20 to-orange-500/20 text-yellow-500 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform ring-1 ring-white/10">
                                    <Zap size={32} />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">Flash Audit</h3>
                                <p className="text-slate-400 text-sm mb-6">
                                    Verificación rápida de insumos en estado <strong className="text-orange-400">Crítico</strong> o <strong className="text-yellow-400">Bajo Stock</strong>.
                                </p>
                                <span className="flex items-center text-orange-500 font-bold text-sm bg-orange-500/10 px-4 py-2 rounded-lg group-hover:bg-orange-500 group-hover:text-white transition-colors">
                                    SELECCIONAR ITEMS <ChevronRight size={18} className="ml-2" />
                                </span>
                            </button>

                            {/* Full Inventory */}
                            <button
                                onClick={() => handleStartSelection('FULL')}
                                className="group relative flex flex-col items-start p-8 rounded-2xl border-2 border-slate-700 bg-slate-800 hover:border-blue-500 hover:bg-slate-700/50 transition-all duration-300 text-left shadow-lg overflow-hidden"
                            >
                                <PackageSearch size={120} className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity transform -rotate-12 text-blue-500" />
                                <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-400/20 to-indigo-500/20 text-blue-500 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform ring-1 ring-white/10">
                                    <PackageSearch size={32} />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">Inventario Completo</h3>
                                <p className="text-slate-400 text-sm mb-6">
                                    Auditoría exhaustiva de todos los insumos activos.
                                </p>
                                <span className="flex items-center text-blue-500 font-bold text-sm bg-blue-500/10 px-4 py-2 rounded-lg group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    SELECCIONAR ITEMS <ChevronRight size={18} className="ml-2" />
                                </span>
                            </button>
                        </div>
                    </section>
                )}

                {/* 2. SELECTION LIST */}
                {auditMode === 'SELECTION_LIST' && (
                    <section className="animate-in fade-in duration-500 flex flex-col h-full max-h-full">
                        <div className="flex items-center justify-between mb-6 flex-none">
                            <h2 className="text-xl font-bold text-white">
                                Selecciona items para {auditType === 'FLASH' ? 'Flash Audit' : 'Auditoría Completa'}
                            </h2>
                            <button
                                onClick={toggleSelectAll}
                                className="text-sm text-indigo-400 hover:text-indigo-300 font-medium"
                            >
                                {selectedItemIds.size === filteredIngredients.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
                            </button>
                        </div>

                        <div className="flex-grow overflow-y-auto custom-scrollbar bg-slate-800/50 rounded-2xl border border-slate-700 p-2">
                            {filteredIngredients.length === 0 ? (
                                <div className="h-64 flex flex-col items-center justify-center text-slate-500">
                                    <Check size={48} className="mb-4 opacity-20" />
                                    <p>No hay items que coincidan con el criterio.</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {filteredIngredients.map(item => (
                                        <div
                                            key={item.id}
                                            onClick={() => toggleSelection(item.id!)}
                                            className={`p-4 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${selectedItemIds.has(item.id!)
                                                ? 'bg-indigo-500/10 border-indigo-500/50 shadow-sm'
                                                : 'bg-slate-800 border-slate-700 hover:bg-slate-700'
                                                }`}
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`w-6 h-6 rounded-md border flex items-center justify-center transition-colors ${selectedItemIds.has(item.id!) ? 'bg-indigo-500 border-indigo-500' : 'border-slate-600 bg-slate-900'
                                                    }`}>
                                                    {selectedItemIds.has(item.id!) && <Check size={14} className="text-white" />}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-white">{item.name}</p>
                                                    <p className="text-xs text-slate-400 font-mono">
                                                        Actual: {Number(item.stock).toLocaleString('es-MX', { maximumFractionDigits: 2 })} {item.unit} | Min: {Number(item.min_stock).toLocaleString('es-MX', { maximumFractionDigits: 2 })}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className={`text-xs px-2 py-1 rounded font-bold uppercase ${(item.stock || 0) <= (Number(item.min_stock) || 0) ? 'text-red-400 bg-red-400/10' :
                                                (item.stock || 0) <= (Number(item.min_stock) || 0) * 1.5 ? 'text-yellow-400 bg-yellow-400/10' :
                                                    'text-emerald-400 bg-emerald-400/10'
                                                }`}>
                                                {(item.stock || 0) <= (Number(item.min_stock) || 0) ? 'Crítico' :
                                                    (item.stock || 0) <= (Number(item.min_stock) || 0) * 1.5 ? 'Bajo' : 'OK'}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="mt-6 flex justify-end flex-none">
                            <button
                                onClick={startWizard}
                                disabled={selectedItemIds.size === 0}
                                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-indigo-600/20 flex items-center gap-2 transition-all w-full md:w-auto justify-center"
                            >
                                COMENZAR AUDITORÍA ({selectedItemIds.size}) <ChevronRight size={20} />
                            </button>
                        </div>
                    </section>
                )}


                {/* 3. WIZARD */}
                {auditMode === 'WIZARD' && currentWizardItem && (
                    <div className="m-auto w-full max-w-lg h-full flex flex-col justify-center animate-in fade-in zoom-in-95 duration-500">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                <UtensilsCrossed className="text-orange-500" />
                                En Progreso
                            </h2>
                            <span className="text-[10px] tracking-wider uppercase bg-orange-500 text-slate-900 px-2 py-1 rounded font-bold shadow-[0_0_10px_rgba(255,107,0,0.4)]">En Vivo</span>
                        </div>

                        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 flex flex-col shadow-2xl relative overflow-hidden group">
                            {/* Progress Bar */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-slate-700">
                                <div
                                    className="h-full bg-orange-500 transition-all duration-300"
                                    style={{ width: `${((wizardDetails.currentIndex) / wizardDetails.queue.length) * 100}%` }}
                                ></div>
                            </div>

                            <div className="flex justify-between items-center mb-8 mt-2">
                                <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
                                    Item {wizardDetails.currentIndex + 1} / {wizardDetails.queue.length}
                                </span>
                                <span className="bg-slate-900 text-slate-400 text-xs px-2 py-1 rounded border border-slate-700 font-mono">
                                    SKU: {currentWizardItem.sku || 'N/A'}
                                </span>
                            </div>

                            <div className="flex-grow flex flex-col justify-center items-center text-center space-y-6 z-10">
                                <div className="w-24 h-24 rounded-full bg-slate-900 border-4 border-slate-700 flex items-center justify-center relative shadow-lg">
                                    <Box size={40} className="text-slate-300" />
                                </div>
                                <div>
                                    <h3 className="text-2xl font-bold text-white leading-tight">{currentWizardItem.name}</h3>
                                    <p className="text-slate-400 text-sm mt-2">
                                        Unidad: <span className="text-orange-500 font-bold">{currentWizardItem.unit}</span>
                                    </p>
                                    <p className="text-xs text-slate-600 mt-1">
                                        Stock Esperado (Ciego): <span className="blur-sm hover:blur-none transition-all cursor-pointer select-none">{currentWizardItem.stock}</span>
                                    </p>
                                </div>

                                <div className="w-full max-w-xs mx-auto">
                                    <AuditInput
                                        onConfirm={submitCurrentWizardStep}
                                        unit={currentWizardItem.unit}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 4. SUMMARY */}
                {auditMode === 'SUMMARY' && (
                    <section className="flex flex-col h-full animate-in fade-in slide-in-from-bottom-8 duration-500">
                        <div className="flex items-center justify-between mb-4 flex-none">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <SlidersHorizontal size={20} className="text-blue-500" />
                                Resumen de Auditoría
                            </h2>
                        </div>

                        <div className="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden shadow-xl flex-grow flex flex-col">
                            <div className="overflow-x-auto custom-scrollbar flex-grow">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-slate-900/50 border-b border-slate-700 text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                                            <th className="p-4 pl-6">Insumo</th>
                                            <th className="p-4 text-right">Teórico</th>
                                            <th className="p-4 text-right">Físico</th>
                                            <th className="p-4 text-center">Diferencia</th>
                                            <th className="p-4 text-center">Estado</th>
                                            <th className="p-4 text-right">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700 text-sm">
                                        {summaryData.rows.map((row, idx) => (
                                            <tr key={idx} className="hover:bg-white/5 transition-colors">
                                                <td className="p-4 pl-6 font-medium text-white">
                                                    {row?.item?.name}
                                                </td>
                                                <td className="p-4 text-right text-slate-400 font-mono">
                                                    {Number(row?.currentStock)?.toFixed(2)}
                                                </td>
                                                <td className="p-4 text-right text-white font-bold font-mono">
                                                    {row?.physicalCount}
                                                </td>
                                                <td className="p-4 text-center">
                                                    <span className={`font-mono font-bold px-2 py-1 rounded ${row?.diff === 0 ? 'text-slate-500' :
                                                        row?.diff > 0 ? 'text-emerald-400 bg-emerald-400/10' : 'text-red-400 bg-red-400/10'
                                                        }`}>
                                                        {row?.diff > 0 ? '+' : ''}{row?.diff?.toFixed(2)}
                                                    </span>
                                                </td>
                                                <td className="p-4 text-center">
                                                    {row?.isHealthy ? (
                                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold border border-emerald-500/20">
                                                            <Check size={10} /> OK
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 text-[10px] font-bold border border-red-500/20">
                                                            <AlertTriangle size={10} /> DESVÍO
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="p-4 text-right">
                                                    <button
                                                        onClick={() => {
                                                            const newCount = prompt(`Re-contar ${row?.item?.name}`, row?.physicalCount.toString());
                                                            if (newCount !== null && !isNaN(Number(newCount))) {
                                                                setWizardDetails(prev => ({
                                                                    ...prev,
                                                                    results: { ...prev.results, [row!.item!.id!]: Number(newCount) }
                                                                }));
                                                            }
                                                        }}
                                                        className="text-indigo-400 hover:text-white p-2 bg-slate-700/50 hover:bg-indigo-600 rounded-lg transition-all"
                                                        title="Corregir Conteo"
                                                    >
                                                        <RefreshCcw size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="bg-slate-900 border-t border-slate-700 p-6 flex flex-col sm:flex-row justify-between items-center gap-4 flex-none">
                                <div className="text-sm text-slate-400">
                                    Total Items Auditados: <strong className="text-white">{summaryData.rows.length}</strong>
                                </div>
                                <button
                                    onClick={handleCommitAudit}
                                    disabled={isSubmitting}
                                    className="w-full sm:w-auto bg-emerald-500 hover:bg-emerald-600 text-white px-8 py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? (
                                        <span className="animate-pulse">Guardando...</span>
                                    ) : (
                                        <>
                                            <Save size={20} /> CONFIRMAR Y GUARDAR
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </section>
                )}

            </main>
        </div>
    );
};

// Helper Component for Wizard Input
const AuditInput = ({ onConfirm, unit }: { onConfirm: (val: number) => void, unit?: string }) => {
    const [val, setVal] = useState('');

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (val === '') return;
        onConfirm(Number(val));
        setVal('');
    };

    return (
        <form onSubmit={handleSubmit} className="w-full">
            <div className="relative">
                <input
                    autoFocus
                    className="w-full bg-slate-900 border-2 border-slate-700 focus:border-orange-500 focus:ring-0 focus:shadow-[0_0_20px_rgba(255,107,0,0.2)] rounded-2xl text-center text-5xl font-bold text-white py-6 placeholder-slate-800 transition-all outline-none"
                    placeholder="?"
                    type="number"
                    step="0.01"
                    value={val}
                    onChange={(e) => setVal(e.target.value)}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 pointer-events-none text-sm font-bold truncate max-w-[50px]">{unit}</span>
            </div>
            <button
                type="submit"
                disabled={val === ''}
                className="w-full mt-6 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3.5 rounded-xl font-bold text-sm uppercase tracking-wide shadow-lg shadow-orange-500/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
            >
                Confirmar <Check size={18} />
            </button>
        </form>
    );
};
