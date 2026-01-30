import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAppDispatch, useAppSelector } from '../../../stores/store';
import { updateAuth, setStep, completeGenesis } from '../../../stores/genesis.slice';
import { startOnboarding } from '../../../stores/onboarding.slice';
import { TextInput } from '../../../components/ui/TextInput';
import { submitGenesis } from '../genesis.service';
import { useNavigate } from 'react-router-dom';

const authSchema = z.object({
    fullName: z.string().min(3, 'Nombre requerido'),
    username: z.string()
        .min(3, 'Usuario requerido')
        .regex(/^[a-zA-Z0-9._-]+$/, 'Solo letras, números, puntos y guiones (sin espacios)'),
    adminEmail: z.string().email('Email inválido'),
    adminPassword: z.string().min(6, 'Mínimo 6 caracteres')
});

type AuthForm = z.infer<typeof authSchema>;

export const Step3Auth = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const genesisState = useAppSelector(state => state.genesis);
    const auth = genesisState.auth;

    // Derived from Step 1
    const companySlug = genesisState.foundation.companyName.toLowerCase().replace(/[^a-z0-9-]/g, '-');

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<AuthForm>({
        resolver: zodResolver(authSchema),
        defaultValues: {
            fullName: auth.fullName || genesisState.foundation.ownerName, // Pre-fill with owner name if available
            username: auth.username,
            adminEmail: auth.adminEmail,
            adminPassword: auth.adminPassword
        }
    });

    const onSubmit = async (data: AuthForm) => {
        setError(null);
        setIsLoading(true);

        // 1. Update local Redux state first so service has latest data
        dispatch(updateAuth(data));

        // We construct a temporary full state because redux update might be async/batched
        const tempState = {
            ...genesisState,
            auth: { ...genesisState.auth, ...data }
        };

        try {
            await submitGenesis(tempState, dispatch);
            dispatch(completeGenesis());

            // Start Onboarding Flow
            dispatch(startOnboarding());

            // Redirect to Staff Page for first step (Create Users)
            navigate('/admin/staff');
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Error al establecer el protocolo');
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-8">
            <div className="text-center mb-4">
                <h2 className="text-3xl font-bold text-white mb-2">Credenciales de Acceso</h2>
                <p className="text-text-muted">Configura tu usuario administrador. Tu email será tu llave maestra.</p>
            </div>

            <div className="max-w-md mx-auto w-full bg-card-dark p-8 rounded-2xl border border-border-dark shadow-xl">
                <div className="mb-6 flex justify-center">
                    <div className="w-20 h-20 bg-accent-orange/10 rounded-full flex items-center justify-center border border-accent-orange/20">
                        <span className="material-symbols-outlined text-4xl text-accent-orange">badge</span>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 bg-red-500/20 border border-red-500/50 text-red-100 p-3 rounded-lg text-sm flex items-center gap-2">
                        <span className="material-symbols-outlined text-base">warning</span>
                        {error}
                    </div>
                )}

                {/* Display generated Company Slug */}
                <div className="mb-6 bg-bg-deep p-4 rounded-xl border border-white/10 text-center">
                    <p className="text-xs text-text-muted uppercase tracking-widest mb-1">Identificador de Negocio</p>
                    <p className="text-xl font-mono text-accent-orange font-bold tracking-wider">{companySlug}</p>
                    <p className="text-[10px] text-text-muted mt-2">Este código distingue tu empresa en el sistema.</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <TextInput
                        label="Nombre Completo"
                        icon="person"
                        placeholder="Ej. Tony Stark"
                        {...register('fullName')}
                        error={errors.fullName?.message}
                    />

                    <TextInput
                        label="Nombre de Usuario"
                        icon="account_circle"
                        placeholder="Ej. ironman"
                        {...register('username')}
                        error={errors.username?.message}
                    />

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
                                    <span>Registrar</span>
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
