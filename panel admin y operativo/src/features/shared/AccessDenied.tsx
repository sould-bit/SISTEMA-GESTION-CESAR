
import { useAppDispatch } from '../../stores/store';
import { setAccessDenied } from '../../stores/ui.slice';
import { useNavigate } from 'react-router-dom';

interface ValidationProps {
    isBlocking?: boolean;
}

export const AccessDenied = ({ isBlocking = false }: ValidationProps) => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();

    const handleDismiss = () => {
        dispatch(setAccessDenied(false));
    };

    const handleGoHome = () => {
        dispatch(setAccessDenied(false));
        navigate('/admin/dashboard');
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-deep/90 backdrop-blur-sm animate-fade-in">
            <div className="bg-card-dark border border-border-dark p-8 rounded-2xl shadow-2xl max-w-md w-full text-center relative overflow-hidden">

                {/* Background Decoration */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-red-500 to-orange-500"></div>
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-red-500/10 rounded-full blur-2xl"></div>

                {/* Icon */}
                <div className="mx-auto size-20 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                    <span className="material-symbols-outlined text-4xl text-red-500">
                        lock_person
                    </span>
                </div>

                {/* Content */}
                <h2 className="text-2xl font-bold text-white mb-2">
                    Acceso Restringido
                </h2>
                <p className="text-text-muted mb-8 text-sm leading-relaxed">
                    No tienes los permisos necesarios para acceder a esta sección.
                    Si crees que es un error, contacta al administrador del sistema.
                </p>

                {/* Actions */}
                <div className="flex flex-col gap-3">
                    <button
                        onClick={handleGoHome}
                        className="w-full py-3 px-4 bg-white text-bg-deep font-bold rounded-xl hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
                    >
                        <span className="material-symbols-outlined text-xl">home</span>
                        Volver al Inicio
                    </button>

                    {!isBlocking && (
                        <button
                            onClick={handleDismiss}
                            className="w-full py-3 px-4 bg-transparent border border-border-dark text-text-muted font-medium rounded-xl hover:bg-white/5 transition-colors text-sm"
                        >
                            Cerrar mensaje
                        </button>
                    )}
                </div>

                <div className="mt-6 text-xs text-gray-600 font-mono">
                    E_ACCESS_DENIED_403
                </div>
            </div>
        </div>
    );
};
