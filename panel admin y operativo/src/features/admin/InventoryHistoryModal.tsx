import { useState, useEffect } from 'react';
import { setupService } from '../setup/setup.service';

interface InventoryHistoryModalProps {
    item: any;
    isOpen: boolean;
    onClose: () => void;
}

export const InventoryHistoryModal = ({ item, isOpen, onClose }: InventoryHistoryModalProps) => {
    const [history, setHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            if (!item || !isOpen) return;
            setIsLoading(true);
            try {
                const data = await setupService.getIngredientHistory(item.id);
                setHistory(data);
            } catch (error) {
                console.error("Failed to fetch history", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchHistory();
    }, [item, isOpen]);

    if (!isOpen || !item) return null;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[70] p-4 animate-in fade-in duration-200">
            <div className="bg-card-dark border border-border-dark rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="p-6 border-b border-border-dark bg-white/5 flex justify-between items-center shrink-0">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="material-symbols-outlined text-orange-400">history</span>
                            Historial de Movimientos
                        </h3>
                        <p className="text-sm text-text-muted mt-1">{item.name}</p>
                    </div>
                    <button onClick={onClose} className="text-text-muted hover:text-white transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-0 md:p-2">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-48 space-y-3">
                            <span className="material-symbols-outlined animate-spin text-orange-500 text-3xl">progress_activity</span>
                            <span className="text-text-muted text-sm">Cargando historial...</span>
                        </div>
                    ) : history.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-48 text-text-muted">
                            <span className="material-symbols-outlined text-4xl mb-2 opacity-50">event_busy</span>
                            <p>No hay movimientos registrados.</p>
                        </div>
                    ) : (
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-text-muted uppercase bg-bg-deep sticky top-0 z-10 border-b border-border-dark">
                                <tr>
                                    <th className="px-6 py-3 font-semibold">Fecha</th>
                                    <th className="px-6 py-3 font-semibold">Tipo</th>
                                    <th className="px-6 py-3 font-semibold">Cantidad</th>
                                    <th className="px-6 py-3 font-semibold">Motivo / Detalle</th>
                                    <th className="px-6 py-3 font-semibold text-right">Usuario</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark">
                                {history.map((log: any, index: number) => (
                                    <tr key={index} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-3 text-text-muted whitespace-nowrap">
                                            {new Date(log.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-3">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${['PURCHASE', 'IN'].includes(log.transaction_type) ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                                                ['ADJUST', 'ADJ'].includes(log.transaction_type) ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' :
                                                    ['USAGE', 'OUT', 'WASTE'].includes(log.transaction_type) ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                                                        'bg-white/5 text-text-muted border-white/10'
                                                }`}>
                                                {['PURCHASE', 'IN'].includes(log.transaction_type) ? 'ENTRADA / COMPRA' :
                                                    ['ADJUST', 'ADJ'].includes(log.transaction_type) ? 'AJUSTE / AUDITORÍA' :
                                                        log.transaction_type === 'USAGE' ? 'CONSUMO' :
                                                            log.transaction_type === 'OUT' ? 'SALIDA' :
                                                                log.transaction_type === 'WASTE' ? 'MERMA' : log.transaction_type}
                                            </span>
                                        </td>
                                        <td className={`px-6 py-3 font-mono font-bold ${Number(log.quantity) > 0 ? 'text-emerald-400' : 'text-rose-400'
                                            }`}>
                                            {Number(log.quantity) > 0 ? '+' : ''}{Number(log.quantity)} {item.unit}
                                        </td>
                                        <td className="px-6 py-3 text-white max-w-[200px] truncate" title={log.reason}>
                                            {log.reason || '-'}
                                        </td>
                                        <td className="px-6 py-3 text-right text-text-muted text-xs">
                                            {log.user_name || 'Sistema'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border-dark bg-bg-deep flex justify-between items-center shrink-0">
                    <span className="text-xs text-text-muted">
                        * Solo se muestran los últimos 20 movimientos.
                    </span>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg border border-border-dark text-white hover:bg-white/5 transition-colors font-medium text-sm"
                    >
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    );
};
