import { useState, useEffect } from 'react';
import { tablesService, Table } from './tables.service';
import { useNavigate } from 'react-router-dom';

export const TablesPage = () => {
    const [tables, setTables] = useState<Table[]>([]);
    const [loading, setLoading] = useState(true);
    const [setupCount, setSetupCount] = useState(10);
    const navigate = useNavigate();

    const fetchTables = async () => {
        try {
            setLoading(true);
            const data = await tablesService.getTables();
            setTables(data);
        } catch (error) {
            console.error("Error fetching tables", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTables();
    }, []);

    const handleSetup = async () => {
        try {
            await tablesService.setupTables(setupCount);
            await fetchTables();
        } catch (error) {
            console.error("Error setting up tables", error);
            alert("Error al configurar mesas");
        }
    };

    const handleTableClick = (table: Table) => {
        console.log("Mesa seleccionada:", table);
        navigate('/admin/orders/new', {
            state: {
                tableId: table.id,
                tableNumber: table.table_number,
                branchId: table.branch_id
            }
        });
    };

    if (loading) return <div className="p-8 text-white">Cargando mesas...</div>;

    // View: Setup (if no tables)
    if (tables.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8">
                <div className="bg-card-dark p-8 rounded-2xl border border-border-dark max-w-md w-full text-center">
                    <div className="size-16 bg-accent-primary/10 rounded-full flex items-center justify-center text-accent-primary mx-auto mb-6">
                        <span className="material-symbols-outlined text-3xl">table_restaurant</span>
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Configuración Inicial</h2>
                    <p className="text-text-muted mb-6">
                        No hay mesas configuradas en esta sucursal.
                        ¿Cuántas mesas deseas habilitar?
                    </p>

                    <div className="flex gap-4 mb-6">
                        <input
                            type="number"
                            min="1"
                            max="50"
                            value={setupCount}
                            onChange={(e) => setSetupCount(Number(e.target.value))}
                            className="w-full bg-input-bg border border-input-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-accent-primary"
                        />
                    </div>

                    <button
                        onClick={handleSetup}
                        className="w-full bg-accent-primary hover:bg-accent-primary/90 text-white font-bold py-3 rounded-lg transition-all"
                    >
                        Generar Mesas
                    </button>
                </div>
            </div>
        );
    }

    // View: Grid
    return (
        <div className="p-6 h-full flex flex-col">
            <header className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Mesas</h1>
                    <p className="text-text-muted text-sm">Gestión de sala y órdenes</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={fetchTables} className="p-2 text-text-muted hover:text-white bg-card-dark rounded-lg border border-border-dark">
                        <span className="material-symbols-outlined">refresh</span>
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 overflow-y-auto pb-20">
                {tables.map(table => (
                    <div
                        key={table.id}
                        onClick={() => handleTableClick(table)}
                        className={`
                            relative aspect-square rounded-2xl border-2 flex flex-col items-center justify-center cursor-pointer transition-all hover:scale-105 active:scale-95
                            ${table.status === 'occupied'
                                ? 'bg-status-alert/10 border-status-alert text-status-alert'
                                : 'bg-card-dark border-border-dark text-text-muted hover:border-accent-primary hover:text-accent-primary'
                            }
                        `}
                    >
                        <span className="material-symbols-outlined text-4xl mb-2">table_restaurant</span>
                        <span className="text-xl font-bold">Mesa {table.table_number}</span>
                        <span className="text-xs uppercase tracking-wider font-semibold mt-1">
                            {table.status === 'occupied' ? 'Ocupada' : 'Libre'}
                        </span>

                        {table.status === 'occupied' && (
                            <div className="absolute top-2 right-2 size-3 bg-status-alert rounded-full animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
