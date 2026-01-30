import { useState, useEffect } from 'react';
import { BranchService, Branch } from './branch.service';
import { BranchModal } from './BranchModal';

export const BranchesPage = () => {
    const [branches, setBranches] = useState<Branch[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showInactive, setShowInactive] = useState(false);

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBranch, setEditingBranch] = useState<Branch | null>(null);

    useEffect(() => {
        loadBranches();
    }, [showInactive]);

    const loadBranches = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await BranchService.list(showInactive);
            setBranches(data.items);
        } catch (err: any) {
            console.error('Error loading branches:', err);
            if (err.response?.status === 403) {
                setError('No tienes permisos para ver las sucursales.');
            } else {
                setError('Error al cargar sucursales');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = () => {
        setEditingBranch(null);
        setIsModalOpen(true);
    };

    const handleEdit = (branch: Branch) => {
        setEditingBranch(branch);
        setIsModalOpen(true);
    };

    const handleDelete = async (branch: Branch) => {
        if (!confirm(`¿Estás seguro de desactivar la sucursal "${branch.name}"?`)) return;

        try {
            await BranchService.delete(branch.id);
            loadBranches();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error al eliminar sucursal');
        }
    };

    const handleSetMain = async (branch: Branch) => {
        if (branch.is_main) return;

        try {
            await BranchService.setAsMain(branch.id);
            loadBranches();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Error al establecer sucursal principal');
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <span className="material-symbols-outlined text-accent-orange text-3xl">store</span>
                        Sucursales
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Gestiona las sucursales de tu empresa
                    </p>
                </div>
                <button
                    onClick={handleCreate}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-orange to-orange-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                    <span className="material-symbols-outlined">add</span>
                    Nueva Sucursal
                </button>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={showInactive}
                        onChange={(e) => setShowInactive(e.target.checked)}
                        className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-accent-orange"
                    />
                    Mostrar inactivas
                </label>
            </div>

            {/* Error */}
            {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg">
                    {error}
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-orange"></div>
                </div>
            )}

            {/* Branches Grid */}
            {!loading && !error && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {branches.map(branch => (
                        <div
                            key={branch.id}
                            className={`bg-[#1A2333] border rounded-xl p-5 transition-all hover:border-accent-orange/50 ${branch.is_active ? 'border-border-dark' : 'border-red-500/30 opacity-60'
                                }`}
                        >
                            {/* Header */}
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${branch.is_main ? 'bg-yellow-500/20' : 'bg-accent-orange/20'}`}>
                                        <span className={`material-symbols-outlined ${branch.is_main ? 'text-yellow-500' : 'text-accent-orange'}`}>
                                            {branch.is_main ? 'star' : 'store'}
                                        </span>
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-white flex items-center gap-2">
                                            {branch.name}
                                            {branch.is_main && (
                                                <span className="text-xs bg-yellow-500/20 text-yellow-500 px-2 py-0.5 rounded">
                                                    Principal
                                                </span>
                                            )}
                                        </h3>
                                        <span className="text-xs text-gray-500 font-mono">{branch.code}</span>
                                    </div>
                                </div>
                                {!branch.is_active && (
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">
                                        Inactiva
                                    </span>
                                )}
                            </div>

                            {/* Info */}
                            <div className="space-y-2 text-sm mb-4">
                                {branch.address && (
                                    <div className="flex items-center gap-2 text-gray-400">
                                        <span className="material-symbols-outlined text-base">location_on</span>
                                        {branch.address}
                                    </div>
                                )}
                                {branch.phone && (
                                    <div className="flex items-center gap-2 text-gray-400">
                                        <span className="material-symbols-outlined text-base">phone</span>
                                        {branch.phone}
                                    </div>
                                )}
                                <div className="flex items-center gap-2 text-gray-400">
                                    <span className="material-symbols-outlined text-base">group</span>
                                    {branch.user_count} usuario{branch.user_count !== 1 ? 's' : ''}
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-2 pt-3 border-t border-border-dark">
                                <button
                                    onClick={() => handleEdit(branch)}
                                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                >
                                    <span className="material-symbols-outlined text-base">edit</span>
                                    Editar
                                </button>
                                {!branch.is_main && (
                                    <button
                                        onClick={() => handleSetMain(branch)}
                                        className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-yellow-500 hover:bg-yellow-500/10 rounded-lg transition-colors"
                                        title="Establecer como principal"
                                    >
                                        <span className="material-symbols-outlined text-base">star</span>
                                        Principal
                                    </button>
                                )}
                                {branch.is_active && !branch.is_main && (
                                    <button
                                        onClick={() => handleDelete(branch)}
                                        className="flex items-center justify-center gap-1 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                        title="Desactivar"
                                    >
                                        <span className="material-symbols-outlined text-base">delete</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}

                    {branches.length === 0 && (
                        <div className="col-span-full text-center py-12 text-gray-500">
                            <span className="material-symbols-outlined text-5xl mb-3 block">store</span>
                            <p>No hay sucursales registradas</p>
                            <button
                                onClick={handleCreate}
                                className="mt-4 text-accent-orange hover:underline"
                            >
                                Crear primera sucursal
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Modal */}
            <BranchModal
                isOpen={isModalOpen}
                branch={editingBranch}
                onClose={() => setIsModalOpen(false)}
                onSuccess={loadBranches}
            />
        </div>
    );
};

export default BranchesPage;
