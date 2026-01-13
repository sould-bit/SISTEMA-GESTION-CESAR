import { useAppDispatch } from '@/stores/store';
import { logout } from '@/stores/auth.slice';
import { useNavigate } from 'react-router-dom';

export const DashboardPage = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();

    const handleLogout = () => {
        dispatch(logout());
        navigate('/login');
    };

    return (
        <div className="space-y-6 p-6">
            <header>
                <h1 className="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
                <p className="text-slate-400">Vista general de tu negocio</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Demo Card */}
                <div className="bg-asphalt-light border border-asphalt-lighter p-6 rounded-xl shadow-sm">
                    <h3 className="text-lg font-semibold text-white mb-2">Estado del Sistema</h3>
                    <p className="text-emerald-400 font-medium flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        Operativo
                    </p>
                </div>

                <div className="bg-asphalt-light border border-asphalt-lighter p-6 rounded-xl shadow-sm">
                    <h3 className="text-lg font-semibold text-white mb-2">Ventas del Día</h3>
                    <p className="text-2xl font-bold text-white">$ 0.00</p>
                </div>
            </div>

            <div className="mt-10 border-t border-asphalt-lighter pt-6">
                <p className="text-sm text-slate-500 mb-4">Zona de Pruebas</p>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-4 py-2 bg-asphalt-light border border-alert-red/30 text-alert-red rounded-lg hover:bg-alert-red hover:text-white transition-all text-sm font-medium"
                >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    Cerrar Sesión
                </button>
            </div>
        </div>
    );
};
