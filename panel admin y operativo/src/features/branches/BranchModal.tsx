import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { BranchService, Branch, BranchCreate } from './branch.service';

const branchSchema = z.object({
    name: z.string().min(2, 'Nombre requerido (mín. 2 caracteres)'),
    code: z.string().min(2, 'Código requerido').max(20).regex(/^[A-Z0-9_-]+$/, 'Solo mayúsculas, números, guiones'),
    address: z.string().optional(),
    phone: z.string().optional(),
    is_main: z.boolean()
});

type BranchForm = z.infer<typeof branchSchema>;

interface Props {
    isOpen: boolean;
    branch: Branch | null; // null = create mode, Branch = edit mode
    onClose: () => void;
    onSuccess: () => void;
}

export const BranchModal = ({ isOpen, branch, onClose, onSuccess }: Props) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const isEditing = branch !== null;

    const { register, handleSubmit, formState: { errors }, reset, setValue } = useForm<BranchForm>({
        resolver: zodResolver(branchSchema),
        defaultValues: {
            is_main: false
        }
    });

    useEffect(() => {
        if (isOpen) {
            setError(null);
            if (branch) {
                // Edit mode - populate form
                setValue('name', branch.name);
                setValue('code', branch.code);
                setValue('address', branch.address || '');
                setValue('phone', branch.phone || '');
                setValue('is_main', branch.is_main);
            } else {
                // Create mode - reset form
                reset({
                    name: '',
                    code: '',
                    address: '',
                    phone: '',
                    is_main: false
                });
            }
        }
    }, [isOpen, branch]);

    const onSubmit = async (data: BranchForm) => {
        setLoading(true);
        setError(null);
        try {
            if (isEditing) {
                await BranchService.update(branch.id, data);
            } else {
                await BranchService.create(data as BranchCreate);
            }
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || `Error al ${isEditing ? 'actualizar' : 'crear'} sucursal`);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-[#1A2333] border border-border-dark rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-[#0B1120]">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-accent-orange">store</span>
                        {isEditing ? 'Editar Sucursal' : 'Nueva Sucursal'}
                    </h3>
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

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Nombre</label>
                            <input
                                {...register('name')}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                                placeholder="Sucursal Centro"
                            />
                            {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-gray-400">Código</label>
                            <input
                                {...register('code', {
                                    onChange: (e) => {
                                        e.target.value = e.target.value.toUpperCase();
                                    }
                                })}
                                className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white uppercase focus:outline-none focus:border-accent-orange"
                                placeholder="CENTRO"
                            />
                            {errors.code && <p className="text-xs text-red-400">{errors.code.message}</p>}
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Dirección</label>
                        <input
                            {...register('address')}
                            className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="Calle 80 #45-23"
                        />
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-medium text-gray-400">Teléfono</label>
                        <input
                            {...register('phone')}
                            className="w-full bg-[#0B1120] border border-border-dark rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-orange"
                            placeholder="+57 300 123 4567"
                        />
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-[#0B1120] rounded-lg border border-border-dark">
                        <input
                            type="checkbox"
                            {...register('is_main')}
                            id="is_main"
                            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-accent-orange focus:ring-accent-orange"
                        />
                        <label htmlFor="is_main" className="text-sm text-gray-300 flex items-center gap-2">
                            <span className="material-symbols-outlined text-yellow-500 text-lg">star</span>
                            Sucursal Principal
                        </label>
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
                            {loading ? 'Guardando...' : (isEditing ? 'Guardar Cambios' : 'Crear Sucursal')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
