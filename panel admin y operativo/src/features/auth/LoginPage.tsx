
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../../stores/store';
import { setCredentials } from '../../stores/auth.slice';
import { api } from '../../lib/api';
import { useState } from 'react';

const loginSchema = z.object({
    company_code: z.string().min(1, 'El código de empresa es requerido'),
    username: z.string().min(1, 'El usuario es requerido'),
    password: z.string().min(1, 'La contraseña es requerida'),
    remember: z.boolean().optional(),
});

type LoginForm = z.infer<typeof loginSchema>;

export const LoginPage = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            remember: true
        }
    });

    const onSubmit = async (data: LoginForm) => {
        setLoading(true);
        setError(null);
        try {
            // CORRECCION: Usar /auth/login y enviar company_slug
            const response = await api.post('/auth/login', {
                username: data.username,
                password: data.password,
                company_slug: data.company_code
            });

            dispatch(setCredentials({
                token: response.data.access_token,
                user: {
                    id: response.data.user_id || 0,
                    username: data.username,
                    role: 'admin',
                    company_id: response.data.company_id || 0
                }
            }));

            // Intentar obtener datos completos del usuarios
            try {
                const me = await api.get('/auth/me');
                dispatch(setCredentials({
                    token: response.data.access_token,
                    user: me.data
                }));
            } catch (e) {
                console.warn("No se pudo obtener info detallada del usuario", e);
            }

            navigate('/admin/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Error al iniciar sesión. Verifique sus credenciales.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <AuthLayout>
            <div className="flex flex-col items-center mb-8 text-center">
                <div className="h-14 w-14 bg-gradient-to-br from-card-dark to-bg-deep border border-border-dark rounded-xl flex items-center justify-center shadow-xl shadow-accent-orange/10 mb-3">
                    <span className="material-symbols-outlined text-3xl text-accent-orange">restaurant_menu</span>
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

                    <div className="space-y-1.5 group">
                        <label className="block text-xs font-semibold text-text-muted " htmlFor="company-code">
                            CÓDIGO DE EMPRESA
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-text-muted text-[20px]">domain</span>
                            </div>
                            <input
                                {...register('company_code')}
                                className="block w-full pl-10 pr-3 py-2.5 bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted focus:outline-none focus:border-accent-orange focus:ring-1 focus:ring-accent-orange transition-all sm:text-sm"
                                id="company-code"
                                placeholder="ej. mi-restaurante"
                                type="text"
                            />
                        </div>
                        {errors.company_code && <span className="text-red-500 text-xs">{errors.company_code.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="block text-xs font-semibold text-text-muted" htmlFor="username">
                            USUARIO
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-text-muted text-[20px]">person</span>
                            </div>
                            <input
                                {...register('username')}
                                className="block w-full pl-10 pr-3 py-2.5 bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted focus:outline-none focus:border-accent-orange focus:ring-1 focus:ring-accent-orange transition-all sm:text-sm"
                                id="username"
                                placeholder="Ingrese su usuario"
                                type="text"
                            />
                        </div>
                        {errors.username && <span className="text-red-500 text-xs">{errors.username.message}</span>}
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
                                className="block w-full pl-10 pr-3 py-2.5 bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted focus:outline-none focus:border-accent-orange focus:ring-1 focus:ring-accent-orange transition-all sm:text-sm"
                                id="password"
                                placeholder="••••••••"
                                type="password"
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
                                className="h-4 w-4 text-accent-orange focus:ring-accent-orange border-border-dark rounded bg-bg-deep"
                            />
                            <label htmlFor="remember-me" className="ml-2 block text-sm text-text-muted">
                                Recordarme
                            </label>
                        </div>
                        <div className="text-sm">
                            <a href="#" className="font-medium text-accent-orange hover:text-orange-400 transition-colors">
                                ¿Olvidaste tu contraseña?
                            </a>
                        </div>
                    </div>

                    <button
                        disabled={loading}
                        type="submit"
                        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-lg text-sm font-bold text-white bg-accent-orange hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-orange focus:ring-offset-bg-deep transition-all transform hover:scale-[1.01] uppercase tracking-wide disabled:opacity-50"
                    >
                        {loading ? 'Iniciando...' : 'Iniciar Sesión'}
                    </button>

                    <div className="mt-8 text-center">
                        <p className="text-text-muted text-sm">
                            ¿Nueva franquicia?{' '}
                            <a href="/genesis" className="text-accent-orange hover:text-orange-400 font-bold transition-colors">
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
