import { useAppDispatch, useAppSelector } from '../../stores/store';
import { setAccessDenied } from '../../stores/ui.slice';
import { useNavigate } from 'react-router-dom';

/**
 * Modal global que se muestra cuando se deniega el acceso a una acción o sección.
 * Proporciona feedback específico sobre qué permiso falta y qué acción se intentó.
 */
export const AccessDenied = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const {
        accessDenied,
        isAccessDeniedBlocking,
        requiredPermission,
        requiredPermissionCode,
        actionName
    } = useAppSelector(state => state.ui);

    if (!accessDenied) return null;

    const handleClose = () => {
        dispatch(setAccessDenied({ isOpen: false }));
        // Si era bloqueante y cerramos, forzamos salida al dashboard para evitar reaperturas infinitas
        if (isAccessDeniedBlocking) {
            navigate('/admin/dashboard');
        }
    };

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 overflow-y-auto">
            {/* Backdrop con desenfoque suave */}
            <div
                className="fixed inset-0 bg-bg-deep/90 backdrop-blur-md transition-opacity animate-in fade-in duration-500"
                onClick={!isAccessDeniedBlocking ? handleClose : undefined}
            />

            {/* Modal Container */}
            <div className="relative bg-card-dark border border-border-dark rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden transform transition-all animate-in fade-in zoom-in duration-300">

                {/* Header Alerta Premium */}
                <div className="bg-gradient-to-br from-status-alert/15 to-transparent p-8 border-b border-border-dark flex items-center gap-6">
                    <div className="size-16 rounded-2xl bg-status-alert/10 flex items-center justify-center border border-status-alert/20 shadow-inner">
                        <span className="material-symbols-outlined text-status-alert text-4xl animate-pulse">lock_person</span>
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-white tracking-tight leading-none">Acceso Restringido</h2>
                        <p className="text-status-alert text-xs font-bold uppercase tracking-[0.2em] mt-2 opacity-80">Protocolo de Seguridad Activo</p>
                    </div>
                </div>

                {/* Body */}
                <div className="p-8">
                    <p className="text-text-muted text-sm leading-relaxed mb-8">
                        Tu perfil actual no cuenta con las autorizaciones necesarias para ejecutar esta operación.
                        Para mantener la integridad del sistema, esta acción ha sido bloqueada.
                    </p>

                    <div className="space-y-4">
                        {/* Acción intentada */}
                        <div className="bg-bg-deep/50 rounded-2xl p-5 border border-border-dark">
                            <span className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-2 block">Operación Intentada</span>
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-text-muted text-xl">near_me</span>
                                <p className="text-base text-gray-100 font-semibold tracking-tight">
                                    {actionName || "Operación no definida"}
                                </p>
                            </div>
                        </div>

                        {/* Permiso técnico */}
                        {(requiredPermission || requiredPermissionCode) && (
                            <div className="bg-status-alert/5 rounded-2xl p-5 border border-status-alert/10 relative overflow-hidden group">
                                <span className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-2 block">Recurso Requerido</span>
                                <div className="flex items-center gap-3">
                                    <span className="material-symbols-outlined text-status-alert text-xl">key</span>
                                    <p className="text-base text-status-alert font-bold">
                                        {requiredPermission || "Permiso Administrativo"}
                                    </p>
                                </div>
                                {requiredPermissionCode && (
                                    <div className="mt-3 flex items-center gap-2">
                                        <span className="text-[10px] font-mono text-gray-500 bg-black/40 px-2 py-0.5 rounded uppercase letter-spacing-widest">
                                            ID Técnico: {requiredPermissionCode}
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Guía de resolución */}
                    <div className="mt-8 flex items-start gap-4 p-5 rounded-2xl bg-accent-primary/5 border border-accent-primary/10">
                        <div className="mt-1 flex items-center justify-center size-8 rounded-full bg-accent-primary/20">
                            <span className="material-symbols-outlined text-accent-primary text-xl">help</span>
                        </div>
                        <div className="space-y-1">
                            <h4 className="text-sm font-bold text-white">¿Cómo solucionar esto?</h4>
                            <p className="text-xs text-text-muted leading-relaxed">
                                Solicita a tu supervisor o administrador que asigne el código <span className="text-accent-primary font-mono bg-accent-primary/10 px-1 rounded">{requiredPermissionCode || 'específico'}</span> a tu rol.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Acciones */}
                <div className="bg-bg-deep/50 p-6 flex flex-col sm:flex-row gap-3 border-t border-border-dark">
                    <button
                        onClick={() => navigate('/admin/dashboard')}
                        className="flex-1 py-4 px-6 bg-white/5 hover:bg-white/10 text-white text-xs font-bold rounded-xl transition-all uppercase tracking-widest border border-border-dark"
                    >
                        Panel Principal
                    </button>
                    <button
                        onClick={handleClose}
                        className="flex-1 py-4 px-6 bg-gradient-to-br from-status-alert to-orange-600 hover:scale-[1.02] text-white text-xs font-black rounded-xl transition-all shadow-xl shadow-status-alert/20 uppercase tracking-widest"
                    >
                        {isAccessDeniedBlocking ? 'Cerrar Sección' : 'Cerrar Notificación'}
                    </button>
                </div>
            </div>
        </div>
    );
};
