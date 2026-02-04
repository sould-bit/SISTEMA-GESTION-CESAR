
import { useState, useEffect } from 'react';
import { StaffService, Role, Permission, PermissionCategory } from './staff.service';

interface Props {
    isOpen: boolean;
    roleId?: string; // If provided, edit mode. If null, create mode.
    onClose: () => void;
    onSuccess: () => void;
}

export const RoleEditorModal = ({ isOpen, roleId, onClose, onSuccess }: Props) => {
    const [role, setRole] = useState<Role | null>(null);
    const [categories, setCategories] = useState<PermissionCategory[]>([]);
    const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
    const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(new Set());

    // Form state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (isOpen) {
            loadMetaData();
            if (roleId) {
                loadRoleData(roleId);
            } else {
                resetForm();
            }
        }
    }, [isOpen, roleId]);

    const resetForm = () => {
        setRole(null);
        setName('');
        setDescription('');
        setSelectedPermissions(new Set());
    };

    const loadMetaData = async () => {
        try {
            const [cats, perms] = await Promise.all([
                StaffService.getCategories(),
                StaffService.getPermissions()
            ]);
            setCategories(cats);
            setAllPermissions(perms);
        } catch (error) {
            console.error("Error loading permission metadata", error);
        }
    };

    const loadRoleData = async (id: string) => {
        setLoading(true);
        try {
            const data = await StaffService.getRoleDetails(id);
            setRole(data);
            setName(data.name);
            setDescription(data.description || '');

            // Populate selected permissions
            const initialPerms = new Set<string>();
            if (data.permissions) {
                data.permissions.forEach(p => initialPerms.add(p.id));
            }
            setSelectedPermissions(initialPerms);
        } catch (error) {
            console.error("Error loading role details", error);
            onClose();
        } finally {
            setLoading(false);
        }
    };

    const handleTogglePermission = (permId: string) => {
        const next = new Set(selectedPermissions);
        if (next.has(permId)) {
            next.delete(permId);
        } else {
            next.add(permId);
        }
        setSelectedPermissions(next);
    };

    const handleToggleCategory = (catId: string, permissionsInCategory: Permission[]) => {
        const next = new Set(selectedPermissions);
        // Check if all permissions in this category are already selected
        const allSelected = permissionsInCategory.every(p => next.has(p.id));

        if (allSelected) {
            // Unselect all
            permissionsInCategory.forEach(p => next.delete(p.id));
        } else {
            // Select all
            permissionsInCategory.forEach(p => next.add(p.id));
        }
        setSelectedPermissions(next);
    };

    const handleSubmit = async () => {
        if (!name) return alert("El nombre es requerido");
        setSaving(true);
        try {
            let currentRoleId = roleId;

            if (roleId) {
                // UPDATE ROLE
                await StaffService.updateRole(roleId, { name, description });
            } else {
                // CREATE ROLE
                const newRole = await StaffService.createRole({
                    name,
                    code: name.toLowerCase().replace(/\s+/g, '_'), // Simple slug generation
                    description,
                    permission_ids: Array.from(selectedPermissions)
                });
                currentRoleId = newRole.id;
            }

            // Sync Permissions (Only needed for update, Create handles it in one go if designed so, 
            // but our Update logic might need diffing. For simplicity in Create we sent IDs.
            // For Update, we need to sync manually or use a batch endpoint if available.
            // Current StaffService.createRole accepts permission_ids, so Create is fine.
            // Update DOES NOT accept permission_ids in DTO. We must manually sync.
            // Wait! The user asked for "assign permissions".

            if (roleId && role) {
                // Differential update for permissions
                // This is slow if done one by one, ideally backend supports bulk update.
                // Assuming we have to do it one by one based on current service methods.

                const oldPerms = new Set(role.permissions?.map(p => p.id) || []);
                const newPerms = selectedPermissions;

                // To Add
                const toAdd = Array.from(newPerms).filter(x => !oldPerms.has(x));
                // To Remove
                const toRemove = Array.from(oldPerms).filter(x => !newPerms.has(x));

                // Execute sequentially to avoid race conditions/errors in backend
                for (const pid of toAdd) {
                    await StaffService.assignPermission(roleId, pid);
                }

                for (const pid of toRemove) {
                    await StaffService.revokePermission(roleId, pid);
                }
            }

            onSuccess();
            onClose();
        } catch (error) {
            console.error("Error saving role", error);
            alert("Error guardando el rol");
        } finally {
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-[#1A2333] border border-border-dark rounded-xl shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden">
                {/* HEAD */}
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-[#0B1120]">
                    <div>
                        <h3 className="text-lg font-bold text-white">
                            {roleId ? 'Editar Rol' : 'Crear Nuevo Rol'}
                        </h3>
                        <p className="text-sm text-text-muted">Define los permisos para este puesto</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* BODY (Scrollable) */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-white">Cargando datos...</div>
                    ) : (
                        <>
                            {/* Basic Info */}
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Nombre del Rol</label>
                                    <input
                                        value={name}
                                        onChange={e => setName(e.target.value)}
                                        className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-4 py-3 text-white focus:outline-none focus:border-accent-primary transition-colors"
                                        placeholder="Ej: Supervisor de Barra"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Descripción Breve</label>
                                    <input
                                        value={description}
                                        onChange={e => setDescription(e.target.value)}
                                        className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-4 py-3 text-white focus:outline-none focus:border-accent-primary transition-colors"
                                        placeholder="Descripción de responsabilidades..."
                                    />
                                </div>
                            </div>

                            {/* Permissions Grid */}
                            <div className="space-y-4">
                                <h4 className="text-white font-semibold flex items-center gap-2">
                                    <span className="material-symbols-outlined text-accent-primary">lock_open</span>
                                    Permisos y Accesos
                                </h4>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {categories.map(cat => {
                                        const catPerms = allPermissions.filter(p => p.category_id === cat.id);
                                        if (catPerms.length === 0) return null;

                                        const allSelected = catPerms.every(p => selectedPermissions.has(p.id));
                                        const someSelected = catPerms.some(p => selectedPermissions.has(p.id));

                                        return (
                                            <div key={cat.id} className="bg-[#0B1120]/50 border border-border-dark rounded-xl overflow-hidden hover:border-gray-600 transition-colors">
                                                {/* Category Header */}
                                                <div
                                                    className="px-4 py-3 flex items-center justify-between cursor-pointer bg-white/5 active:bg-white/10"
                                                    onClick={() => handleToggleCategory(cat.id, catPerms)}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div
                                                            className="size-8 rounded-lg flex items-center justify-center text-white"
                                                            style={{ backgroundColor: cat.color || '#607D8B' }}
                                                        >
                                                            <span className="material-symbols-outlined text-lg">{cat.icon || 'settings'}</span>
                                                        </div>
                                                        <span className="font-medium text-gray-200">{cat.name}</span>
                                                    </div>
                                                    <div className={`size-5 rounded border flex items-center justify-center transition-colors ${allSelected ? 'bg-accent-primary border-accent-primary' :
                                                        someSelected ? 'bg-accent-primary/50 border-accent-primary' : 'border-gray-500'
                                                        }`}>
                                                        {allSelected && <span className="material-symbols-outlined text-xs text-black font-bold">check</span>}
                                                        {someSelected && !allSelected && <div className="w-2 h-0.5 bg-white rounded-full"></div>}
                                                    </div>
                                                </div>

                                                {/* Permissions List */}
                                                <div className="p-3 space-y-1">
                                                    {catPerms.map(perm => {
                                                        const isSelected = selectedPermissions.has(perm.id);
                                                        return (
                                                            <div
                                                                key={perm.id}
                                                                onClick={() => handleTogglePermission(perm.id)}
                                                                className={`flex items-start gap-3 p-2 rounded-lg cursor-pointer transition-all ${isSelected ? 'bg-accent-primary/10' : 'hover:bg-white/5'
                                                                    }`}
                                                            >
                                                                <div className={`mt-0.5 size-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors ${isSelected ? 'bg-accent-primary border-accent-primary' : 'border-gray-600'
                                                                    }`}>
                                                                    {isSelected && <span className="material-symbols-outlined text-[10px] text-black font-bold">check</span>}
                                                                </div>
                                                                <div>
                                                                    <div className={`text-sm font-medium ${isSelected ? 'text-accent-primary' : 'text-gray-400'}`}>
                                                                        {perm.name}
                                                                    </div>
                                                                    {perm.description && (
                                                                        <div className="text-[10px] text-gray-500 line-clamp-1">{perm.description}</div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* FOOTER */}
                <div className="p-4 border-t border-border-dark flex justify-end gap-3 bg-[#0B1120]">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors font-medium"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={saving}
                        className="px-6 py-2 rounded-lg bg-accent-primary text-white font-medium hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20 disabled:opacity-50 flex items-center gap-2"
                    >
                        {saving && <span className="material-symbols-outlined animate-spin text-sm">progress_activity</span>}
                        {saving ? 'Guardando...' : 'Guardar Cambios'}
                    </button>
                </div>
            </div>
        </div>
    );
};
