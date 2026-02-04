import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../../stores/store';
import { setCredentials } from '../../stores/auth.slice';
import { api } from '../../lib/api';

const loginSchema = z.object({
    email: z.string().email('Email inválido'),
    password: z.string().min(1, 'La contraseña es requerida'),
    remember: z.boolean().optional(),
});

type LoginForm = z.infer<typeof loginSchema>;

interface CompanyOption {
    name: string;
    slug: string;
    role: string;
}

export const LoginPage = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [companyOptions, setCompanyOptions] = useState<CompanyOption[] | null>(null);
    const [credentials, setCredentialsState] = useState<{ email: string, password: string } | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            remember: true
        }
    });

    const processLoginResponse = async (data: any) => {
        if (data.requires_selection && data.options) {
            // Multi-tenant scenario
            setCompanyOptions(data.options);
            return;
        }

        if (data.token) {
            // Direct login success
            // 1. Set minimal credentials first
            dispatch(setCredentials({
                token: data.token.access_token,
                user: {
                    id: 0, // Will be updated by /me
                    username: '', // Will be updated by /me
                    role: '',
                    company_id: 0
                }
            }));

            // 2. Fetch full user details
            try {
                const me = await api.get('/auth/me');
                dispatch(setCredentials({
                    token: data.token.access_token,
                    user: me.data
                }));
            } catch (e) {
                console.warn("No se pudo obtener info detallada del usuario", e);
            }

            navigate('/admin/dashboard');
        }
    };

    const onSubmit = async (formData: LoginForm) => {
        setLoading(true);
        setError(null);
        setCredentialsState({ email: formData.email, password: formData.password });

        try {
            const response = await api.post('/auth/login', {
                email: formData.email,
                password: formData.password
            });
            await processLoginResponse(response.data);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Error al iniciar sesión.');
        } finally {
            setLoading(false);
        }
    };

    const handleCompanySelect = async (slug: string) => {
        if (!credentials) return;
        setLoading(true);
        setError(null);

        try {
            // Re-login with specific company slug
            const response = await api.post('/auth/login', {
                email: credentials.email,
                password: credentials.password,
                company_slug: slug
            });
            await processLoginResponse(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al seleccionar empresa.');
        } finally {
            setLoading(false);
        }
    };

    // Render Company Selection Screen
    if (companyOptions) {
        return (
            <AuthLayout>
                <div className="flex flex-col items-center mb-8 text-center">
                    <div className="h-14 w-14 bg-gradient-to-br from-card-dark to-bg-deep border border-border-dark rounded-xl flex items-center justify-center shadow-xl shadow-accent-primary/10 mb-3">
                        <span className="material-symbols-outlined text-3xl text-accent-primary">domain</span>
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Elige tu destino</h1>
                    <p className="text-text-muted text-sm mt-1">Tu email está asociado a varias empresas.</p>
                </div>

                <div className="bg-card-dark/80 backdrop-blur-xl border border-border-dark rounded-2xl shadow-2xl p-6">
                    <div className="space-y-3">
                        {companyOptions.map((opt) => (
                            <button
                                key={opt.slug}
                                onClick={() => handleCompanySelect(opt.slug)}
                                disabled={loading}
                                className="w-full flex items-center justify-between p-4 bg-bg-deep border border-border-dark hover:border-accent-primary/50 hover:bg-white/5 rounded-xl transition-all group"
                            >
                                <div className="flex flex-col items-start">
                                    <span className="font-bold text-white group-hover:text-accent-primary transition-colors">{opt.name}</span>
                                    <span className="text-xs text-text-muted uppercase tracking-wider">{opt.role}</span>
                                </div>
                                <span className="material-symbols-outlined text-text-muted group-hover:translate-x-1 transition-transform">arrow_forward_ios</span>
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={() => { setCompanyOptions(null); setCredentialsState(null); }}
                        className="w-full mt-6 text-sm text-text-muted hover:text-white transition-colors"
                    >
                        ← Volver al login
                    </button>
                </div>
            </AuthLayout>
        );
    }

    // Render Normal Login Screen
    return (
        <AuthLayout>
            <div className="flex flex-col items-center mb-8 text-center">
                <div className="h-14 w-14 bg-gradient-to-br from-card-dark to-bg-deep border border-border-dark rounded-xl flex items-center justify-center shadow-xl shadow-accent-primary/10 mb-3">
                    <span className="material-symbols-outlined text-3xl text-accent-primary">restaurant_menu</span>
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-white">Bienvenido de nuevo</h1>
                <p className="text-text-muted text-sm mt-1">Ingresa a tu panel de control</p>
            </div>

            <div className="bg-card-dark/80 backdrop-blur-xl border border-border-dark rounded-2xl shadow-2xl p-8">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                    {error && (
                        <div className="bg-status-alert/10 border border-status-alert text-status-alert px-4 py-2 rounded text-sm mb-4">
                            {error}
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <label className="block text-xs font-semibold text-text-muted" htmlFor="email">
                            EMAIL
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-text-muted text-[20px]">alternate_email</span>
                            </div>
                            <input
                                {...register('email')}
                                className="block w-full pl-10 pr-3 py-2.5 bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all sm:text-sm"
                                id="email"
                                placeholder="tu@email.com"
                                type="email"
                                autoComplete="email"
                            />
                        </div>
                        {errors.email && <span className="text-red-500 text-xs">{errors.email.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="block text-xs font-semibold text-text-muted" htmlFor="password">
                            CONTRASEÑA
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-text-muted text-[20px]">lock_open</span>
                            </div>
                            <input
                                {...register('password')}
                                className="block w-full pl-10 pr-3 py-2.5 bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all sm:text-sm"
                                id="password"
                                placeholder="••••••••"
                                type="password"
                                autoComplete="current-password"
                            />
                        </div>
                        {errors.password && <span className="text-red-500 text-xs">{errors.password.message}</span>}
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center">
                            <input
                                {...register('remember')}
                                id="remember-me"
                                type="checkbox"
                                className="h-4 w-4 text-accent-primary focus:ring-accent-primary border-border-dark rounded bg-bg-deep"
                            />
                            <label htmlFor="remember-me" className="ml-2 block text-sm text-text-muted">
                                Recordarme
                            </label>
                        </div>
                        <div className="text-sm">
                            <a href="#" className="font-medium text-accent-primary hover:text-orange-400 transition-colors">
                                ¿Olvidaste tu contraseña?
                            </a>
                        </div>
                    </div>

                    <button
                        disabled={loading}
                        type="submit"
                        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-lg text-sm font-bold text-white bg-accent-primary hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary focus:ring-offset-bg-deep transition-all transform hover:scale-[1.01] uppercase tracking-wide disabled:opacity-50"
                    >
                        {loading ? 'Iniciando...' : 'Iniciar Sesión'}
                    </button>

                    <div className="mt-8 text-center">
                        <p className="text-text-muted text-sm">
                            ¿Nueva franquicia?{' '}
                            <a href="/genesis" className="text-accent-primary hover:text-orange-400 font-bold transition-colors">
                                Inicializar Protocolo Génesis
                            </a>
                        </p>
                    </div>


                </form>
            </div>

            <div className="mt-8 text-center">
                <p className="text-xs text-text-muted">
                    &copy; 2026 FastOps Technologies Inc. Todos los derechos reservados.
                </p>
            </div>
        </AuthLayout>
    );
};
