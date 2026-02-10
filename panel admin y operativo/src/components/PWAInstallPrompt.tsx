import { useState } from 'react';
import { usePWAInstall } from '../hooks/usePWAInstall';
import { Download, X } from 'lucide-react';

export const PWAInstallPrompt = () => {
    const { isInstallable, installPWA } = usePWAInstall();
    const [isVisible, setIsVisible] = useState(true);

    // Si no es instalable o el usuario cerró el aviso, no mostrar nada
    if (!isInstallable || !isVisible) return null;

    return (
        <div className="fixed bottom-4 left-4 right-4 z-[9999] md:left-auto md:w-96 animate-in slide-in-from-bottom-5 fade-in duration-300">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-4 text-white flex items-center gap-4">
                <div className="bg-indigo-600 p-3 rounded-xl">
                    <Download size={24} />
                </div>

                <div className="flex-1">
                    <p className="font-bold text-sm">Instalar FastOps</p>
                    <p className="text-xs text-slate-400">Instala la app para recibir notificaciones y acceso rápido.</p>
                </div>

                <div className="flex flex-col gap-2">
                    <button
                        onClick={installPWA}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors"
                    >
                        Instalar
                    </button>
                    <button
                        onClick={() => setIsVisible(false)}
                        className="text-slate-500 hover:text-white transition-colors"
                    >
                        <X size={16} className="mx-auto" />
                    </button>
                </div>
            </div>
        </div>
    );
};

