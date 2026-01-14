import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAppDispatch, useAppSelector } from '../../../stores/store';
import { updateCommand, setStep, completeGenesis } from '../../../stores/genesis.slice';
import { TextInput } from '../../../components/ui/TextInput';
import { submitGenesis } from '../genesis.service';
import { useNavigate } from 'react-router-dom';

const commandSchema = z.object({
    adminEmail: z.string().email('Email inválido'),
    adminPassword: z.string().min(6, 'Mínimo 6 caracteres')
});

type CommandForm = z.infer<typeof commandSchema>;

const ROLES = [
    {
        id: 'architect',
        title: 'Arquitecto',
        description: 'Acceso total al sistema. Puede configurar parámetros globales.',
        icon: 'manage_accounts',
        color: 'text-accent-orange',
        bg: 'bg-accent-orange/10',
        border: 'border-accent-orange',
        locked: true
    },
    {
        id: 'commander',
        title: 'Comandante',
        description: 'Gestión de sucursal, reportes y anulación de ventas.',
        icon: 'military_tech',
        color: 'text-status-info',
        bg: 'bg-status-info/10',
        border: 'border-status-info',
        locked: false
    },
    {
        id: 'operator',
        title: 'Operador',
        description: 'Acceso a punto de venta (POS) y cierre de caja básico.',
        icon: 'point_of_sale',
        color: 'text-status-success',
        bg: 'bg-status-success/10',
        border: 'border-status-success',
        locked: false
    }
];

export const Step3Command = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const genesisState = useAppSelector(state => state.genesis);
    const command = genesisState.command;
    
    const [activeRoles, setActiveRoles] = useState<string[]>(command.roles);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<CommandForm>({
        resolver: zodResolver(commandSchema),
        defaultValues: {
            adminEmail: command.adminEmail,
            adminPassword: command.adminPassword
        }
    });

    const toggleRole = (roleId: string, locked: boolean) => {
        if (locked) return;
        setActiveRoles(prev =>
            prev.includes(roleId)
                ? prev.filter(r => r !== roleId)
                : [...prev, roleId]
        );
    };

    const onSubmit = async (data: CommandForm) => {
        setError(null);
        setIsLoading(true);

        // 1. Update local Redux state first so service has latest data
        dispatch(updateCommand({ ...data, roles: activeRoles }));
        
        // We construct a temporary full state because redux update might be async/batched
        const tempState = {
            ...genesisState,
            command: { ...genesisState.command, ...data, roles: activeRoles }
        };

        try {
            await submitGenesis(tempState, dispatch);
            dispatch(completeGenesis());
            
            // Redirect to Setup Wizard
            navigate('/admin/setup'); 
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Error al establecer el protocolo');
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-8">
            <div className="text-center mb-4">
                <h2 className="text-3xl font-bold text-white mb-2">Matriz de Mando</h2>
                <p className="text-text-muted">Define la jerarquía y crea tu credencial maestra de acceso.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {ROLES.map((role) => {
                    const isActive = activeRoles.includes(role.id);
                    return (
                        <div
                            key={role.id}
                            onClick={() => toggleRole(role.id, role.locked)}
                            className={`
                                relative p-6 rounded-2xl border transition-all duration-300 cursor-pointer overflow-hidden group
                                ${isActive ? `${role.bg} ${role.border}` : 'bg-card-dark border-border-dark opacity-60 grayscale hover:grayscale-0 hover:opacity-100'}
                            `}
                        >
                            <div className="absolute top-3 right-3">
                                {role.locked ? (
                                    <span className="material-symbols-outlined text-white/50 text-sm">lock</span>
                                ) : (
                                    <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${isActive ? 'bg-white border-transparent' : 'border-white/30'}`}>
                                        {isActive && <span className="material-symbols-outlined text-[12px] text-black font-bold">check</span>}
                                    </div>
                                )}
                            </div>

                            <span className={`material-symbols-outlined text-4xl mb-4 ${role.color} transition-transform group-hover:scale-110`}>{role.icon}</span>
                            <h3 className={`text-lg font-bold text-white mb-2`}>{role.title}</h3>
                            <p className="text-xs text-text-muted leading-relaxed">{role.description}</p>

                            {isActive && <div className={`absolute bottom-0 left-0 w-full h-1 ${role.color.replace('text-', 'bg-')}`}></div>}
                        </div>
                    );
                })}
            </div>

            <div className="max-w-md mx-auto w-full mt-4 bg-card-dark p-6 rounded-2xl border border-border-dark shadow-xl">
                <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Credencial Maestra</h4>
                
                {error && (
                    <div className="mb-4 bg-red-500/20 border border-red-500/50 text-red-100 p-3 rounded-lg text-sm flex items-center gap-2">
                        <span className="material-symbols-outlined text-base">warning</span>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <TextInput
                        label="Email Administrativo"
                        icon="alternate_email"
                        type="email"
                        placeholder="admin@imperio.com"
                        {...register('adminEmail')}
                        error={errors.adminEmail?.message}
                    />
                    <TextInput
                        label="Contraseña Segura"
                        icon="lock"
                        type="password"
                        placeholder="••••••••"
                        {...register('adminPassword')}
                        error={errors.adminPassword?.message}
                    />

                    <div className="pt-4 flex gap-4">
                        <button
                            type="button"
                            onClick={() => dispatch(setStep(2))}
                            disabled={isLoading}
                            className="bg-bg-deep hover:bg-white/5 text-white py-3 px-6 rounded-xl border border-white/10 transition-colors text-sm disabled:opacity-50"
                        >
                            Atrás
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="flex-1 bg-accent-orange hover:bg-orange-500 text-white font-bold py-3 px-8 rounded-xl shadow-[0_4px_20px_rgba(255,107,0,0.3)] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                            ) : (
                                <>
                                    <span>Establecer Protocolo</span>
                                    <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform text-sm">rocket_launch</span>
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
