import { useState, useEffect, useMemo } from 'react';
import { setupService } from '../setup/setup.service';

interface GlobalAuditHistoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRevertSuccess?: () => void;
}

export const GlobalAuditHistoryModal = ({ isOpen, onClose, onRevertSuccess }: GlobalAuditHistoryModalProps) => {
    const [history, setHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isReverting, setIsReverting] = useState<string | null>(null);

    // Filtros
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState<'all' | 'pos' | 'neg' | 'revert'>('all');

    const fetchHistory = async () => {
        if (!isOpen) return;
        setIsLoading(true);
        try {
            const data = await setupService.getGlobalAuditHistory(200);
            setHistory(data);
        } catch (error) {
            console.error("Failed to fetch global history", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) fetchHistory();
    }, [isOpen]);

    // Lógica de filtrado
    const filteredHistory = useMemo(() => {
        return history.filter(item => {
            const matchesSearch =
                (item.ingredient_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                (item.user_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                (item.reason?.toLowerCase() || '').includes(searchTerm.toLowerCase());

            const qty = Number(item.quantity);

            const isReversion =
                item.transaction_type?.includes('REVERT') ||
                item.transaction_type?.includes('ROLLBACK') ||
                item.transaction_type?.includes('DELETION');

            const matchesType =
                filterType === 'all' ||
                (filterType === 'pos' && qty > 0) ||
                (filterType === 'neg' && qty < 0) ||
                (filterType === 'revert' && isReversion);

            return matchesSearch && matchesType;
        });
    }, [history, searchTerm, filterType]);

    // Agrupación mejorada con totales diarios
    const groupedHistory = useMemo(() => {
        const groups: { [key: string]: { items: any[], stats: { pos: number, neg: number, rev: number } } } = {};

        filteredHistory.forEach(item => {
            const date = new Date(item.created_at);
            const dateKey = date.toLocaleDateString('es-ES', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            if (!groups[dateKey]) {
                groups[dateKey] = { items: [], stats: { pos: 0, neg: 0, rev: 0 } };
            }

            groups[dateKey].items.push(item);
            const qty = Number(item.quantity);
            const isRev = item.transaction_type?.includes('REVERT') || item.transaction_type?.includes('ROLLBACK');

            if (isRev) groups[dateKey].stats.rev += 1;
            else if (qty > 0) groups[dateKey].stats.pos += 1;
            else if (qty < 0) groups[dateKey].stats.neg += 1;
        });

        return groups;
    }, [filteredHistory]);


    const handleRevert = async (transactionId: string, ingredientName: string) => {
        if (!window.confirm(`¿Estás seguro de que deseas revertir el ajuste de "${ingredientName}"?`)) return;

        setIsReverting(transactionId);
        try {
            await setupService.revertTransaction(transactionId);
            await fetchHistory();
            if (onRevertSuccess) onRevertSuccess();
        } catch (error: any) {
            alert(error.response?.data?.detail || "Error al revertir");
        } finally {
            setIsReverting(null);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[70] p-0 md:p-4 animate-in fade-in duration-200">
            <div className="bg-card-dark border border-border-dark w-full max-w-5xl md:rounded-xl shadow-2xl overflow-hidden flex flex-col h-full md:max-h-[90vh] animate-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>

                {/* Header Superior */}
                <div className="p-6 border-b border-border-dark bg-white/5 shrink-0">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex gap-4 items-center">
                            <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center border border-orange-500/20">
                                <span className="material-symbols-outlined text-orange-400">summarize</span>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white tracking-tight">Kardex de Auditorías</h3>
                                <p className="text-xs text-text-muted">Control completo de movimientos manuales de inventario</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-1.5 rounded-md hover:bg-white/10 text-text-muted hover:text-white transition-all">
                            <span className="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    {/* Controles de Filtrado */}
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-muted text-lg">search</span>
                            <input
                                type="text"
                                placeholder="Buscar por insumo, usuario o motivo..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-lg py-2 pl-10 pr-4 text-sm text-white placeholder:text-text-muted focus:outline-none focus:border-orange-500/50 transition-all text-xs"
                            />
                        </div>
                        <div className="flex gap-1 bg-black/20 p-1 rounded-lg border border-white/10 shrink-0">
                            {[
                                { id: 'all', label: 'Todos', icon: 'list' },
                                { id: 'pos', label: 'Ingresos', icon: 'add_circle' },
                                { id: 'neg', label: 'Salidas', icon: 'remove_circle' },
                                { id: 'revert', label: 'Reversiones', icon: 'history' }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setFilterType(tab.id as any)}
                                    className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-all flex items-center gap-1.5 uppercase tracking-wider ${filterType === tab.id ? 'bg-orange-500 text-white' : 'text-text-muted hover:text-white'}`}
                                >
                                    <span className="material-symbols-outlined text-[14px]">{tab.icon}</span>
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Área de Datos */}
                <div className="flex-1 overflow-y-auto custom-scrollbar bg-bg-deep/50">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-full py-20 space-y-4">
                            <div className="w-10 h-10 border-2 border-orange-500/10 border-t-orange-500 rounded-full animate-spin"></div>
                            <span className="text-[10px] text-text-muted font-bold uppercase tracking-[0.2em]">Consultando Kardex...</span>
                        </div>
                    ) : filteredHistory.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full py-20 text-center px-10">
                            <span className="material-symbols-outlined text-4xl text-white/5 mb-3">manage_search</span>
                            <h4 className="text-white/40 font-bold text-sm uppercase">No hay resultados para este filtro</h4>
                        </div>
                    ) : (
                        <div className="p-4 space-y-10">
                            {Object.entries(groupedHistory).map(([date, group]) => (
                                <div key={date}>
                                    {/* Cabecera de Grupo con Totales */}
                                    <div className="sticky top-0 z-30 py-3 mb-4 bg-bg-deep/90 backdrop-blur-md border-b border-orange-500/20 px-2 flex justify-between items-center">
                                        <h4 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">{date}</h4>
                                        <div className="flex gap-4">
                                            <div className="flex items-center gap-1.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                                <span className="text-[9px] font-bold text-text-muted">{group.stats.pos} Registros</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                                                <span className="text-[9px] font-bold text-text-muted">{group.stats.neg} Ajustes</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                                                <span className="text-[9px] font-bold text-text-muted">{group.stats.rev} Reversiones</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Registros */}
                                    <div className="space-y-2">
                                        {group.items.map((log: any) => (
                                            <div key={log.id} className="bg-card-dark border border-white/5 rounded-lg overflow-hidden hover:border-white/20 transition-all">
                                                <div className="p-4 flex flex-col md:flex-row gap-4 items-start md:items-center">

                                                    {/* Info Tiempo y Tipo */}
                                                    <div className="flex items-center gap-3 shrink-0">
                                                        <div className="text-center w-12 border-r border-white/5 pr-3">
                                                            <div className="text-xs font-bold text-white uppercase">{new Date(log.created_at).getHours().toString().padStart(2, '0')}:{new Date(log.created_at).getMinutes().toString().padStart(2, '0')}</div>
                                                            <div className="text-[8px] text-text-muted font-bold tracking-tighter uppercase">Hora</div>
                                                        </div>
                                                        <div className={`p-1.5 rounded-md ${Number(log.quantity) > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                                            <span className="material-symbols-outlined text-sm">{Number(log.quantity) > 0 ? 'trending_up' : 'trending_down'}</span>
                                                        </div>
                                                    </div>

                                                    {/* Info Insumo y Stock */}
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-1">
                                                            <span className="font-bold text-white text-sm uppercase">{log.ingredient_name}</span>
                                                            <span className="text-[9px] font-bold text-text-muted bg-white/5 px-2 py-0.5 rounded border border-white/5">
                                                                {log.ingredient_unit}
                                                            </span>
                                                        </div>
                                                        <div className="flex flex-wrap items-center gap-4">
                                                            <div className="flex items-center gap-1.5">
                                                                <span className="text-[10px] text-white/40 font-bold uppercase tracking-tighter">Stock Final:</span>
                                                                <span className="text-[11px] font-black text-orange-400/80">{Number(log.balance_after || 0).toLocaleString()}</span>
                                                            </div>
                                                            <div className="flex items-center gap-1.5">
                                                                <span className="material-symbols-outlined text-[12px] text-text-muted">person</span>
                                                                <span className="text-[10px] text-text-muted font-bold capitalize">{log.user_name || 'Sistema'}</span>
                                                            </div>
                                                            {log.reference_id && (
                                                                <div className="text-[10px] text-text-muted bg-white/5 px-1.5 rounded flex items-center gap-1">
                                                                    <span className="material-symbols-outlined text-[10px]">tag</span>
                                                                    {log.reference_id}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Notas / Motivo FULL */}
                                                    <div className="w-full md:w-48 xl:w-64 border-t md:border-t-0 md:border-l border-white/5 pt-2 md:pt-0 md:pl-4 min-w-0">
                                                        <span className="text-[9px] text-text-muted font-bold uppercase block mb-0.5">Motivo / Notas:</span>
                                                        <p className="text-[11px] text-gray-400 break-words leading-tight italic">"{log.reason || 'Sin detalles registrados'}"</p>
                                                    </div>

                                                    {/* Variación y Acciones */}
                                                    <div className="flex items-center gap-4 shrink-0 self-end md:self-center">
                                                        <div className="flex flex-col items-end">
                                                            <div className={`text-base font-black font-mono leading-none ${Number(log.quantity) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                                {Number(log.quantity) > 0 ? '+' : ''}{Number(log.quantity).toLocaleString()}
                                                            </div>
                                                            <div className="flex items-center gap-1 mt-1">
                                                                {(log.transaction_type?.includes('REVERT') || log.transaction_type?.includes('ROLLBACK')) && (
                                                                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" title="Registro de Reversión"></span>
                                                                )}
                                                                <span className="text-[8px] font-bold text-text-muted uppercase">Variación</span>
                                                            </div>
                                                        </div>
                                                        {['ADJUST', 'ADJ'].includes(log.transaction_type) && (
                                                            <button
                                                                onClick={() => handleRevert(log.id, log.ingredient_name)}
                                                                disabled={!!isReverting}
                                                                className={`w-9 h-9 flex items-center justify-center rounded-lg border border-white/10 hover:border-rose-500 hover:bg-rose-500/10 text-text-muted hover:text-rose-400 transition-all ${isReverting === log.id ? 'animate-spin bg-rose-500 text-white' : ''}`}
                                                                title="Revertir este ajuste"
                                                            >
                                                                <span className="material-symbols-outlined text-base">{isReverting === log.id ? 'sync' : 'history_toggle_off'}</span>
                                                            </button>
                                                        )}
                                                    </div>

                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 bg-white/5 border-t border-border-dark flex justify-between items-center shrink-0">
                    <div className="flex gap-4">
                        <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-bold text-text-muted uppercase">Resultados:</span>
                            <span className="text-[11px] font-black text-white">{filteredHistory.length}</span>
                        </div>
                        <div className="flex items-center gap-1.5 border-l border-white/5 pl-4">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            <span className="text-[10px] font-bold text-text-muted uppercase">Conexión Segura</span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="px-8 py-2 rounded-lg bg-orange-500 text-white hover:bg-orange-600 transition-all font-black text-[10px] uppercase tracking-widest shadow-lg shadow-orange-500/20"
                    >
                        Cerrar Kardex
                    </button>
                </div>
            </div>
        </div>
    );
};
