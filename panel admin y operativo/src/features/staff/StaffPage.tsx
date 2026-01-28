import { useState, useEffect } from 'react';
import { StaffService, User, Role } from './staff.service';
import { CreateUserModal } from './CreateUserModal';
import { RoleEditorModal } from './RoleEditorModal';

export const StaffPage = () => {
    const [roles, setRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'users' | 'roles'>('users');

    // Modals
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
    const [editingRoleId, setEditingRoleId] = useState<string | undefined>(undefined);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [usersData, rolesData] = await Promise.all([
                StaffService.getUsers(),
                StaffService.getRoles()
            ]);
            setUsers(usersData);
            setRoles(rolesData);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateRole = () => {
        setEditingRoleId(undefined);
        setIsRoleModalOpen(true);
    };

    const handleEditRole = (role: Role) => {
        if (role.is_system && role.code === 'admin') {
            alert("El rol de Administrador Principal no se puede editar por seguridad.");
            return;
        }
        setEditingRoleId(role.id);
        setIsRoleModalOpen(true);
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
            loadData();
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
                    Nueva Configuración
                </button>
                {viewMode === 'users' ? (
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 bg-accent-orange text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20"
                    >
                        <span className="material-symbols-outlined">add</span>
                        Nuevo Miembro
                    </button>
                ) : (
                    <button
                        onClick={handleCreateRole}
                        className="flex items-center gap-2 bg-accent-orange text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20"
                    >
                        <span className="material-symbols-outlined">security</span>
                        Crear Rol
                    </button>
                )}
            </div>
        </div>

            {/* TABS */ }
    <div className="flex border-b border-border-dark">
        <button
            onClick={() => setViewMode('users')}
            className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${viewMode === 'users'
                    ? 'border-accent-orange text-white'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
        >
            Usuarios
        </button>
        <button
            onClick={() => setViewMode('roles')}
            className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${viewMode === 'roles'
                    ? 'border-accent-orange text-white'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
        >
            Roles y Permisos
        </button>
    </div>

    {
        loading ? (
            <div className="text-text-muted">Cargando datos...</div>
        ) : viewMode === 'users' ? (
            // VIEW: USERS
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
        ) : (
            // VIEW: ROLES
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {roles.map(role => (
                    <div
                        key={role.id}
                        onClick={() => handleEditRole(role)}
                        className="bg-card-dark border border-border-dark rounded-xl p-6 hover:border-accent-orange/50 transition-all cursor-pointer group relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="material-symbols-outlined text-accent-orange">edit_square</span>
                        </div>

                        <div className="size-12 rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center mb-4 border border-white/5">
                            <span className="material-symbols-outlined text-white text-2xl">
                                {role.code === 'admin' ? 'admin_panel_settings' :
                                    role.code === 'manager' ? 'manage_accounts' :
                                        role.code === 'cashier' ? 'point_of_sale' :
                                            role.code === 'cook' ? 'skillet' :
                                                role.code === 'server' ? 'restaurant' : 'badge'}
                            </span>
                        </div>

                        <h3 className="text-xl font-bold text-white mb-1">{role.name}</h3>
                        <p className="text-text-muted text-sm line-clamp-2 mb-4 h-10">
                            {role.description || "Sin descripción"}
                        </p>

                        <div className="flex items-center gap-4 text-xs font-medium text-gray-500">
                            <div className="flex items-center gap-1">
                                <span className="material-symbols-outlined text-[16px]">group</span>
                                {users.filter(u => u.role_id === role.id || u.role === role.code).length} Usuarios
                            </div>
                            <div className="flex items-center gap-1">
                                <span className="material-symbols-outlined text-[16px]">lock</span>
                                Configurable
                            </div>
                        </div>
                    </div>
                ))}

                {/* New Role Card */}
                <button
                    onClick={handleCreateRole}
                    className="bg-[#0B1120] border border-border-dark border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-4 hover:bg-white/5 transition-colors group text-gray-400 hover:text-accent-orange hover:border-accent-orange/50 aspect-[4/3] md:aspect-auto"
                >
                    <div className="size-14 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <span className="material-symbols-outlined text-3xl">add</span>
                    </div>
                    <span className="font-semibold">Crear Nuevo Rol</span>
                </button>
            </div>
        )
    }

            <CreateUserModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSuccess={loadData}
            />

            <RoleEditorModal 
                isOpen={isRoleModalOpen}
                roleId={editingRoleId}
                onClose={() => setIsRoleModalOpen(false)}
                onSuccess={loadData}
            />
        </div >
    );
};
