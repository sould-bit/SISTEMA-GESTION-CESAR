import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { useState } from 'react';
import { useAppDispatch } from '@/stores/store';
import { setCredentials } from '@/stores/auth.slice';

const registerSchema = z.object({
    name: z.string().min(1, 'El nombre de empresa es requerido'),
    slug: z.string().min(1, 'El código es requerido'),
    owner_name: z.string().min(1, 'El nombre del propietario es requerido'),
    owner_email: z.string().email('Email inválido'),
    password: z.string().min(6, 'Mínimo 6 caracteres'),
    password_confirm: z.string(),
}).refine((data) => data.password === data.password_confirm, {
    message: "Las contraseñas no coinciden",
    path: ["password_confirm"],
});

type RegisterForm = z.infer<typeof registerSchema>;

export const RegisterPage = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successData, setSuccessData] = useState<{ username: string; company_slug: string; token: string; user_id: number; plan: string; company_id: number } | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<RegisterForm>({
        resolver: zodResolver(registerSchema),
    });

    const onSubmit = async (data: RegisterForm) => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.post('/auth/register', {
                company_name: data.name,
                company_slug: data.slug,
                owner_name: data.owner_name,
                owner_email: data.owner_email,
                password: data.password,
                plan: 'free'
            });

            // Guardar datos de éxito para mostrar al usuario
            setSuccessData({
                username: response.data.username,
                company_slug: response.data.company_slug,
                token: response.data.access_token,
                user_id: response.data.user_id,
                plan: response.data.plan,
                company_id: response.data.company_id || 0 // Backend might not send company_id directly in root, but let's check
            });

        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail;
            if (Array.isArray(detail)) {
                setError(detail[0].msg || 'Error de validación');
            } else {
                setError(detail || 'Error en el registro. Verifique que el código no exista.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleContinue = () => {
        if (!successData) return;

        // Auto-login
        dispatch(setCredentials({
            token: successData.token,
            user: {
                id: successData.user_id,
                username: successData.username,
                role: 'admin',
                company_id: successData.company_id
            }
        }));

        navigate('/admin/dashboard');
    };

    if (successData) {
        return (
            <AuthLayout>
                <div className="flex flex-col items-center mb-6 text-center">
                    <div className="h-16 w-16 bg-success-green/20 border border-success-green rounded-full flex items-center justify-center mb-4 animate-bounce">
                        <span className="material-symbols-outlined text-4xl text-success-green">check</span>
                    </div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">¡Registro Exitoso!</h1>
                    <p className="text-slate-400 text-sm">Tu cuenta empresarial ha sido creada.</p>
                </div>

                <div className="bg-asphalt-light/80 backdrop-blur-xl border border-asphalt-lighter rounded-2xl shadow-2xl p-8 max-w-md w-full">
                    <div className="space-y-4">
                        <div className="bg-asphalt p-4 rounded-lg border border-asphalt-lighter">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Tus Credenciales de Acceso</h3>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Código Empresa:</span>
                                    <span className="text-white font-mono font-bold">{successData.company_slug}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Usuario:</span>
                                    <span className="text-fastops-orange font-mono font-bold">{successData.username}</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-blue-500/10 border border-blue-500/20 p-3 rounded-lg flex gap-3 text-sm text-blue-200">
                            <span className="material-symbols-outlined text-[20px]">info</span>
                            <p>Guarda estos datos. Necesitarás el <strong>Código</strong> y <strong>Usuario</strong> para iniciar sesión en el futuro.</p>
                        </div>

                        <button
                            onClick={handleContinue}
                            className="w-full flex justify-center items-center py-3.5 px-4 rounded-lg shadow-lg text-sm font-bold text-white bg-success-green hover:bg-emerald-600 focus:outline-none transition-all transform hover:scale-[1.01] uppercase tracking-wider"
                        >
                            Ir al Dashboard
                            <span className="material-symbols-outlined ml-2 text-[18px]">arrow_forward</span>
                        </button>
                    </div>
                </div>
            </AuthLayout>
        );
    }

    return (
        <AuthLayout>
            <div className="flex flex-col items-center mb-6 text-center">
                <div className="h-16 w-16 bg-gradient-to-br from-asphalt-light to-asphalt border border-asphalt-lighter rounded-2xl flex items-center justify-center shadow-2xl shadow-fastops-orange/10 mb-4">
                    <span className="material-symbols-outlined text-4xl text-fastops-orange">rocket_launch</span>
                </div>
                <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">FastOps Platform</h1>
                <p className="text-slate-400 text-sm">Plataforma de Gestión para Restaurantes</p>
            </div>

            <div className="bg-asphalt-light/80 backdrop-blur-xl border border-asphalt-lighter rounded-2xl shadow-2xl overflow-hidden">
                <div className="px-8 pt-8 pb-2">
                    <h2 className="text-xl font-bold text-white">Registro de Empresa</h2>
                    <p className="text-slate-400 text-sm mt-1">Crea tu cuenta empresarial y comienza a operar.</p>
                </div>

                <div className="p-8 space-y-6">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                        {error && (
                            <div className="bg-alert-red/10 border border-alert-red text-alert-red px-4 py-2 rounded text-sm">
                                {error}
                            </div>
                        )}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="space-y-1.5 group">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="company-name">
                                    Nombre Empresa
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">storefront</span>
                                    </div>
                                    <input {...register('name')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="company-name" placeholder="ej. Test 2" type="text" />
                                </div>
                                {errors.name && <span className="text-red-500 text-xs">{errors.name.message}</span>}
                            </div>
                            <div className="space-y-1.5 group">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="company-code">
                                    Código (Slug)
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">link</span>
                                    </div>
                                    <input {...register('slug')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="company-code" placeholder="ej. test-segundo-nuevo" type="text" />
                                </div>
                                {errors.slug && <span className="text-red-500 text-xs">{errors.slug.message}</span>}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="owner-name">
                                    Propietario
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">person</span>
                                    </div>
                                    <input {...register('owner_name')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="owner-name" placeholder="Maria García" type="text" />
                                </div>
                                {errors.owner_name && <span className="text-red-500 text-xs">{errors.owner_name.message}</span>}
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="owner-email">
                                    Email Propietario
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">mail</span>
                                    </div>
                                    <input {...register('owner_email')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="owner-email" placeholder="maria@test.com" type="email" />
                                </div>
                                {errors.owner_email && <span className="text-red-500 text-xs">{errors.owner_email.message}</span>}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="password">
                                    Contraseña
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">lock</span>
                                    </div>
                                    <input {...register('password')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="password" placeholder="••••••••" type="password" />
                                </div>
                                {errors.password && <span className="text-red-500 text-xs">{errors.password.message}</span>}
                            </div>
                            <div className="space-y-1.5">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1" htmlFor="password-confirm">
                                    Confirmar
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span className="material-symbols-outlined text-slate-500 text-[20px]">verified_user</span>
                                    </div>
                                    <input {...register('password_confirm')} className="block w-full pl-10 pr-3 py-3 bg-asphalt border border-asphalt-lighter rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-fastops-orange focus:ring-1 focus:ring-fastops-orange transition-all sm:text-sm" id="password-confirm" placeholder="••••••••" type="password" />
                                </div>
                                {errors.password_confirm && <span className="text-red-500 text-xs">{errors.password_confirm.message}</span>}
                            </div>
                        </div>

                        <div className="pt-4">
                            <button
                                disabled={loading}
                                className="w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-lg shadow-[0_0_20px_rgba(255,107,0,0.2)] text-sm font-bold text-white bg-fastops-orange hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-fastops-orange focus:ring-offset-asphalt transition-all transform hover:scale-[1.01] uppercase tracking-wider disabled:opacity-50"
                                type="submit"
                            >
                                {loading ? 'Registrando...' : 'Registrar Empresa'}
                                <span className="material-symbols-outlined ml-2 text-[18px]">arrow_forward</span>
                            </button>
                        </div>
                    </form>

                    <div className="flex items-center justify-between pt-2 border-t border-asphalt-lighter/50">
                        <a className="text-sm font-medium text-slate-400 hover:text-fastops-orange transition-colors flex items-center gap-1" href="#">
                            <span className="material-symbols-outlined text-[16px]">help</span>
                            Ayuda
                        </a>
                        <Link to="/login" className="text-sm font-medium text-fastops-orange hover:text-orange-400 transition-colors">
                            ¿Ya tienes cuenta? Inicia Sesión
                        </Link>
                    </div>
                </div>
                <div className="bg-asphalt px-8 py-3 flex justify-between items-center text-[10px] text-slate-500 font-mono border-t border-asphalt-lighter">
                    <span>FastOps Register v1.0</span>
                    <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-success-green animate-pulse"></span>
                        <span>Servidor Activo</span>
                    </div>
                </div>
            </div>
        </AuthLayout>
    );
};
