import { useAppDispatch, useAppSelector } from '../../stores/store';
import { advanceStep, finishOnboarding } from '../../stores/onboarding.slice';
import { useNavigate } from 'react-router-dom';

export const OnboardingGuide = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const { isActive, currentStep } = useAppSelector(state => state.onboarding);

    if (!isActive) return null;

    const steps = {
        'create_users': {
            title: "Paso 1: Tu equipo",
            description: "Registra a tus empleados (meseros, cocineros, cajeros). Asígnales un usuario y una contraseña temporal.",
            actionText: "Ir a Roles",
            action: () => {
                dispatch(advanceStep('create_roles'));
                navigate('/admin/staff'); // Explicit navigation if needed, though usually already there
            },
            icon: "group_add"
        },
        'create_roles': {
            title: "Paso 2: Roles y Permisos",
            description: "Define exactamente qué puede hacer cada rol. Puedes ajustar los permisos predeterminados o crear nuevos roles.",
            actionText: "Ir a Permisos",
            action: () => dispatch(advanceStep('assign_permissions')),
            icon: "admin_panel_settings"
        },
        'assign_permissions': {
            title: "Paso 3: Permisos",
            description: "Asegúrate de que cada rol tenga solo los accesos necesarios.",
            actionText: "Ir a Sucursales",
            action: () => {
                dispatch(advanceStep('create_branches'));
                navigate('/admin/branches');
            },
            icon: "lock_person"
        },
        'create_branches': {
            title: "Paso 4: Sucursales",
            description: "Esta sección es para gestionar tus sucursales en caso de que te expandas o lo requieras.",
            actionText: "Finalizar Tour",
            action: () => {
                dispatch(finishOnboarding());
                navigate('/admin/dashboard');
            },
            icon: "store"
        },
        'finished': {
            title: "¡Listo!",
            description: "Has completado la configuración inicial.",
            actionText: "Cerrar",
            action: () => dispatch(finishOnboarding()),
            icon: "check_circle"
        }
    };

    const currentConfig = steps[currentStep] || steps['finished'];

    return (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm w-full animate-slide-in-right">
            <div className="bg-[#1A1F2E] border border-accent-primary/30 p-6 rounded-2xl shadow-2xl relative overflow-hidden backdrop-blur-xl">
                {/* Glow effect */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-accent-primary/10 rounded-full blur-2xl -mr-16 -mt-16 pointer-events-none"></div>

                <div className="flex items-start gap-4 mb-4 relative z-10">
                    <div className="size-12 rounded-xl bg-accent-primary/20 flex items-center justify-center shrink-0 border border-accent-primary/20">
                        <span className="material-symbols-outlined text-accent-primary text-2xl">
                            {currentConfig.icon}
                        </span>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white mb-1">
                            {currentConfig.title}
                        </h3>
                        <p className="text-sm text-gray-400 leading-relaxed">
                            {currentConfig.description}
                        </p>
                    </div>
                </div>

                <div className="flex gap-3 justify-end relative z-10 transition-all">
                    <button
                        onClick={() => dispatch(finishOnboarding())}
                        className="px-4 py-2 text-xs font-medium text-gray-500 hover:text-white transition-colors"
                    >
                        Omitir
                    </button>
                    <button
                        onClick={currentConfig.action}
                        className="px-5 py-2 bg-accent-primary hover:bg-orange-500 text-white text-sm font-bold rounded-lg shadow-lg shadow-orange-500/20 transition-all flex items-center gap-2"
                    >
                        {currentConfig.actionText}
                        <span className="material-symbols-outlined text-base">arrow_forward</span>
                    </button>
                </div>
            </div>
        </div>
    );
};
