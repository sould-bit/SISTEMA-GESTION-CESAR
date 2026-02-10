import { useState, useEffect } from 'react';
import { kitchenService, Ingredient, IngredientCostHistory } from '../kitchen.service';
import { formatCurrency, formatDate } from '@/utils/formatters';

interface InventoryHistoryModalProps {
    item: Ingredient;
    isOpen: boolean;
    onClose: () => void;
}

export const InventoryHistoryModal = ({ item, isOpen, onClose }: InventoryHistoryModalProps) => {
    const [history, setHistory] = useState<IngredientCostHistory[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen && item) {
            loadHistory();
        }
    }, [isOpen, item]);

    const loadHistory = async () => {
        setLoading(true);
        try {
            const data = await kitchenService.getIngredientHistory(item.id);
            setHistory(data);
        } catch (error) {
            console.error('Error loading history:', error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-bg-card border border-border-dark w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-bg-deep/50">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-amber-500">history</span>
                            Historial de Costos
                        </h3>
                        <p className="text-sm text-text-muted">{item.name} ({item.sku})</p>
                    </div>
                    <button onClick={onClose} className="text-text-muted hover:text-white transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="max-h-[60vh] overflow-y-auto p-4">
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
                        </div>
                    ) : history.length === 0 ? (
                        <div className="text-center py-12 text-text-muted">
                            <span className="material-symbols-outlined text-4xl mb-2 opacity-20">history_toggle_off</span>
                            <p>No hay historial de cambios de costo para este insumo.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {history.map((record, idx) => {
                                const isIncrease = record.new_cost > record.previous_cost;
                                return (
                                    <div key={idx} className="flex gap-4 p-3 rounded-lg bg-bg-deep/30 border border-white/5">
                                        <div className={`mt-1 p-2 rounded-full h-fit ${isIncrease ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                                            <span className="material-symbols-outlined text-lg">
                                                {isIncrease ? 'trending_up' : 'trending_down'}
                                            </span>
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="font-medium text-white text-sm">
                                                        Actualización de Costo
                                                    </p>
                                                    <p className="text-xs text-text-muted mt-0.5">
                                                        {formatDate(record.created_at)}
                                                    </p>
                                                </div>
                                                <div className="text-right">
                                                    <div className="flex items-center gap-2 text-sm font-mono">
                                                        <span className="text-text-muted line-through text-xs">
                                                            {formatCurrency(record.previous_cost)}
                                                        </span>
                                                        <span className="material-symbols-outlined text-[10px] text-text-muted">arrow_forward</span>
                                                        <span className={`font-bold ${isIncrease ? 'text-red-400' : 'text-emerald-400'}`}>
                                                            {formatCurrency(record.new_cost)}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            {record.reason && (
                                                <div className="mt-2 text-xs bg-white/5 p-2 rounded text-gray-300 italic">
                                                    "{record.reason}"
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-border-dark bg-bg-deep/50 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors text-sm font-medium"
                    >
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    );
};

interface GlobalAuditHistoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRevertSuccess?: () => void;
    initialFilter?: 'all' | 'audit';
}

export const GlobalAuditHistoryModal = ({ isOpen, onClose, initialFilter = 'all' }: GlobalAuditHistoryModalProps) => {
    // Placeholder component since no backend endpoint exists for global history yet
    // This allows the app to compile and run without crashing

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-bg-card border border-border-dark w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 min-h-[500px] flex flex-col">
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-bg-deep/50">
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-rose-500">gavel</span>
                            Auditoría Global
                        </h3>
                        <p className="text-sm text-text-muted">Registro de todas las operaciones</p>
                    </div>
                    <button onClick={onClose} className="text-text-muted hover:text-white transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                    <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-6">
                        <span className="material-symbols-outlined text-5xl text-text-muted opacity-50">engineering</span>
                    </div>
                    <h4 className="text-xl font-bold text-white mb-2">En Construcción</h4>
                    <p className="text-text-muted max-w-md mx-auto">
                        La vista global de auditoría estará disponible en la próxima actualización.
                        Por ahora, puedes ver el historial individual de cada insumo desde su tarjeta.
                    </p>

                    <div className="mt-8 flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-5 py-2.5 bg-accent-primary text-white rounded-lg font-medium hover:bg-orange-600 transition-colors"
                        >
                            Entendido
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
