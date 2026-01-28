import { useState, useEffect } from 'react';
import { StaffService, User } from './staff.service';
import { CreateUserModal } from './CreateUserModal';

export const StaffPage = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        setLoading(true);
        try {
            const data = await StaffService.getUsers();
            setUsers(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async (user: User) => {
        // Validación de protección: No permitir desactivar al admin
        if (
            user.role === 'admin' ||
            user.role === 'owner' ||
            user.username === 'admin' ||
            (user.role_name && user.role_name.toLowerCase() === 'administrador')
        ) {
            alert("No puedes desactivar al usuario administrador principal.");
            return;
        }

        const action = user.is_active ? 'desactivar' : 'activar';
        if (!confirm(`¿Estás seguro de ${action} este usuario?`)) return;

        try {
            await StaffService.updateUser(user.id, { is_active: !user.is_active });
            loadUsers();
        } catch (error) {
            console.error(error);
            alert("Error actualizando estado del usuario");
        }
    };

    const handleFixRoles = async () => {
        setLoading(true);
        try {
            await StaffService.fixRoles();
            alert("Roles restaurados correctamente. Ahora puedes crear usuarios con roles.");
        } catch (error) {
            alert("Error restaurando roles");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 space-y-6 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Gestión del Personal</h1>
                    <p className="text-text-muted">Administra usuarios y roles</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleFixRoles}
                        className="flex items-center gap-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                        title="Si no aparecen roles, usa este botón"
                    >
                        <span className="material-symbols-outlined text-[18px]">build_circle</span>
                        Reparar Roles
                    </button>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 bg-accent-orange text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors"
                    >
                        <span className="material-symbols-outlined">add</span>
                        Nuevo Miembro
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="text-text-muted">Cargando personal...</div>
            ) : (
                <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-[#0B1120] text-gray-400 text-sm font-medium">
                            <tr>
                                <th className="px-6 py-3">Nombre</th>
                                <th className="px-6 py-3">Email</th>
                                <th className="px-6 py-3">Rol</th>
                                <th className="px-6 py-3">Estado</th>
                                <th className="px-6 py-3">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {users.map((user) => (
                                <tr key={user.id} className="hover:bg-white/5 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="size-8 rounded-full bg-accent-orange/20 flex items-center justify-center text-accent-orange font-bold">
                                                {user.username.charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <div className="font-medium text-white">{user.full_name || user.username}</div>
                                                <div className="text-xs text-text-muted">@{user.username}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-300">{user.email}</td>
                                    <td className="px-6 py-4">
                                        <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
                                            {user.role_name || user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-xs font-medium border ${user.is_active
                                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                                            : 'bg-red-500/10 text-red-400 border-red-500/20'
                                            }`}>
                                            {user.is_active ? 'Activo' : 'Inactivo'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex gap-2">
                                            {/* Ocultar botón de bloqueo si es admin */}
                                            {user.role !== 'admin' && user.role !== 'owner' && (user.role_name && user.role_name.toLowerCase() !== 'administrador') ? (
                                                <button
                                                    onClick={() => handleToggleStatus(user)}
                                                    className={`p-1 rounded transition-colors ${user.is_active
                                                        ? 'hover:bg-red-500/20 text-red-400'
                                                        : 'hover:bg-green-500/20 text-green-400'
                                                        }`}
                                                    title={user.is_active ? "Desactivar usuario" : "Activar usuario"}
                                                >
                                                    <span className="material-symbols-outlined text-[20px]">
                                                        {user.is_active ? 'block' : 'check_circle'}
                                                    </span>
                                                </button>
                                            ) : (
                                                <span className="text-gray-600 text-xs italic px-2">Protegido</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {users.length === 0 && (
                        <div className="p-8 text-center text-text-muted">
                            No hay usuarios registrados.
                        </div>
                    )}
                </div>
            )}

            <CreateUserModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={loadUsers}
            />
        </div>
    );
};
