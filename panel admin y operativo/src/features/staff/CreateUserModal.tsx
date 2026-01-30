import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { StaffService, Role, User } from './staff.service';
import { api } from '../../lib/api';

interface Branch {
    id: number;
    name: string;
    code: string;
    is_main: boolean;
}

const userSchema = z.object({
    full_name: z.string().min(3, 'Nombre requerido'),
    username: z.string().min(3, 'Usuario requerido').regex(/^[a-zA-Z0-9._-]+$/, 'Solo letras, números, puntos y guiones'),
    email: z.string().email('Email inválido'),
    password: z.string().optional(),
    role_id: z.string().uuid('Rol requerido'),
    branch_id: z.string().optional()
});

type UserForm = z.infer<typeof userSchema>;

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    userToEdit?: User | null;
}

export const CreateUserModal = ({ isOpen, onClose, onSuccess, userToEdit }: Props) => {
    const [roles, setRoles] = useState<Role[]>([]);
    const [branches, setBranches] = useState<Branch[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors }, reset } = useForm<UserForm>({
        resolver: zodResolver(userSchema.refine(data => {
            if (!userToEdit && (!data.password || data.password.length < 6)) {
                return false;
            }
            if (data.password && data.password.length > 0 && data.password.length < 6) {
                return false;
            }
            return true;
        }, {
            message: "Contraseña requerida (min 6 caracteres)",
            path: ["password"]
        }))
    });

    useEffect(() => {
        if (isOpen) {
            loadRoles();
            loadBranches();
            setError(null);
            if (userToEdit) {
                reset({
                    full_name: userToEdit.full_name,
                    username: userToEdit.username,
                    email: userToEdit.email,
                    role_id: userToEdit.role_id,
                    branch_id: userToEdit.branch_id?.toString() || '',
                    password: ''
                });
            } else {
                reset({
                    full_name: '',
                    username: '',
                    email: '',
                    password: '',
                    role_id: '',
                    branch_id: ''
                });
            }
        }
    }, [isOpen, userToEdit]);

    const loadRoles = async () => {
        try {
            const data = await StaffService.getRoles();
            setRoles(data);
        } catch (err: any) {
            console.error(err);
            if (err.response && err.response.status === 403) {
                setError("No tienes permiso para ver los roles. Contacta al administrador.");
            } else {
                setError("Error al cargar roles");
            }
        }
    };

    const loadBranches = async () => {
        try {
            const response = await api.get('/branches');
            setBranches(response.data.items || []);
        } catch (err: any) {
            console.error('Error loading branches:', err);
        }
    };

    const onSubmit = async (data: UserForm) => {
        setLoading(true);
        setError(null);
        try {
            const payload = {
                ...data,
                branch_id: data.branch_id ? parseInt(data.branch_id) : null,
                password: data.password || undefined // Send undefined if empty to avoid updating password
            };

            if (userToEdit) {
                await StaffService.updateUser(userToEdit.id, payload);
            } else {
                await StaffService.createUser(payload as any);
            }

            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al guardar usuario');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-[#1A2333] border border-border-dark rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-fade-in-up">
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-[#0B1120]">
                    <h3 className="text-lg font-bold text-white">
                        {userToEdit ? 'Editar Usuario' : 'Nuevo Miembro del Staff'}
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm">error</span>
                            {error}
                        </div>
                    )}

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Nombre Completo</label>
                        <div className="relative">
                            <span className="absolute left-3 top-2.5 text-gray-500 material-symbols-outlined text-sm">person</span>
                            <input
                                {...register('full_name')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg pl-9 pr-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-accent-orange transition-colors"
                                placeholder="Ej: Juan Pérez"
                            />
                        </div>
                        {errors.full_name && <p className="text-xs text-red-400 mt-1">{errors.full_name.message}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Usuario</label>
                            <input
                                {...register('username')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-accent-orange transition-colors"
                                placeholder="juan.perez"
                            />
                            {errors.username && <p className="text-xs text-red-400 mt-1">{errors.username.message}</p>}
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Rol</label>
                            <select
                                {...register('role_id')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange transition-colors appearance-none"
                            >
                                <option value="">Seleccionar...</option>
                                {roles.map(role => (
                                    <option key={role.id} value={role.id}>{role.name}</option>
                                ))}
                            </select>
                            {errors.role_id && <p className="text-xs text-red-400 mt-1">{errors.role_id.message}</p>}
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Email</label>
                        <div className="relative">
                            <span className="absolute left-3 top-2.5 text-gray-500 material-symbols-outlined text-sm">mail</span>
                            <input
                                type="email"
                                {...register('email')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg pl-9 pr-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-accent-orange transition-colors"
                                placeholder="juan@empresa.com"
                            />
                        </div>
                        {errors.email && <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>}
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">
                            {userToEdit ? 'Nueva Contraseña (Opcional)' : 'Contraseña'}
                        </label>
                        <div className="relative">
                            <span className="absolute left-3 top-2.5 text-gray-500 material-symbols-outlined text-sm">lock</span>
                            <input
                                type="password"
                                {...register('password')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg pl-9 pr-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-accent-orange transition-colors"
                                placeholder={userToEdit ? "Dejar en blanco para mantener actual" : "******"}
                            />
                        </div>
                        {errors.password && <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>}
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Sucursal</label>
                        <div className="relative">
                            <span className="absolute left-3 top-2.5 text-gray-500 material-symbols-outlined text-sm">store</span>
                            <select
                                {...register('branch_id')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg pl-9 pr-3 py-2 text-white focus:outline-none focus:border-accent-orange transition-colors appearance-none"
                            >
                                <option value="">Todas las sucursales (acceso global)</option>
                                {branches.map(branch => (
                                    <option key={branch.id} value={branch.id.toString()}>
                                        {branch.name} ({branch.code}){branch.is_main ? ' ⭐' : ''}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Si no seleccionas sucursal, el usuario tendrá acceso a todas.</p>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-accent-orange to-orange-600 text-white hover:opacity-90 disabled:opacity-50 shadow-lg shadow-orange-500/20 transition-all"
                        >
                            {loading ? (userToEdit ? 'Guardando...' : 'Creando...') : (userToEdit ? 'Guardar Cambios' : 'Crear Usuario')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
