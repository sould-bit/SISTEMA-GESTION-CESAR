import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { StaffService, Role } from './staff.service';

const createUserSchema = z.object({
    full_name: z.string().min(3, 'Nombre requerido'),
    username: z.string().min(3, 'Usuario requerido').regex(/^[a-zA-Z0-9._-]+$/, 'Solo letras, números, puntos y guiones'),
    email: z.string().email('Email inválido'),
    password: z.string().min(6, 'Mínimo 6 caracteres'),
    role_id: z.string().uuid('Rol requerido')
});

type CreateUserForm = z.infer<typeof createUserSchema>;

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const CreateUserModal = ({ isOpen, onClose, onSuccess }: Props) => {
    const [roles, setRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors }, reset } = useForm<CreateUserForm>({
        resolver: zodResolver(createUserSchema)
    });

    useEffect(() => {
        if (isOpen) {
            loadRoles();
            reset();
            setError(null);
        }
    }, [isOpen]);

    const loadRoles = async () => {
        try {
            const data = await StaffService.getRoles();
            setRoles(data);
        } catch (err) {
            console.error(err);
            setError("Error al cargar roles");
        }
    };

    const onSubmit = async (data: CreateUserForm) => {
        setLoading(true);
        setError(null);
        try {
            await StaffService.createUser(data);
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al crear usuario');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-[#1A2333] border border-border-dark rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-[#0B1120]">
                    <h3 className="text-lg font-bold text-white">Nuevo Miembro del Staff</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg">
                            {error}
                        </div>
                    )}

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Nombre Completo</label>
                        <input
                            {...register('full_name')}
                            className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="Ej: Juan Pérez"
                        />
                        {errors.full_name && <p className="text-xs text-red-400">{errors.full_name.message}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Usuario</label>
                            <input
                                {...register('username')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                                placeholder="juan.perez"
                            />
                            {errors.username && <p className="text-xs text-red-400">{errors.username.message}</p>}
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Rol</label>
                            <select
                                {...register('role_id')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            >
                                <option value="">Seleccionar...</option>
                                {roles.map(role => (
                                    <option key={role.id} value={role.id}>{role.name}</option>
                                ))}
                            </select>
                            {errors.role_id && <p className="text-xs text-red-400">{errors.role_id.message}</p>}
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Email</label>
                        <input
                            type="email"
                            {...register('email')}
                            className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="juan@empresa.com"
                        />
                        {errors.email && <p className="text-xs text-red-400">{errors.email.message}</p>}
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Contraseña</label>
                        <input
                            type="password"
                            {...register('password')}
                            className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="******"
                        />
                        {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-accent-orange to-orange-600 text-white hover:opacity-90 disabled:opacity-50"
                        >
                            {loading ? 'Creando...' : 'Crear Usuario'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
