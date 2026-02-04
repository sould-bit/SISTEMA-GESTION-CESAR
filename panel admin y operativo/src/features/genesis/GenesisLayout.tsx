import { ReactNode } from 'react';
import { useAppSelector } from '../../stores/store';

interface GenesisLayoutProps {
    children: ReactNode;
}

export const GenesisLayout = ({ children }: GenesisLayoutProps) => {
    const currentStep = useAppSelector((state) => state.genesis.currentStep);

    // Calculate progress width based on current step (1-3)
    const progressWidth = `${((currentStep - 1) / 2) * 100}%`;

    return (
        <div className="bg-bg-deep min-h-screen flex flex-col font-sans text-white relative overflow-hidden">
            {/* Immersive Background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                <div className="absolute top-0 left-1/4 w-[800px] h-[800px] bg-accent-primary/5 rounded-full blur-[150px] animate-pulse"></div>
                <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-status-info/5 rounded-full blur-[120px]"></div>

                {/* Grid Pattern Overlay */}
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
                <div className="absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.95),rgba(15,23,42,0.95))]"></div>
            </div>

            {/* Header / Progress */}
            <header className="relative z-20 px-8 py-6 flex items-center justify-between border-b border-white/5 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 bg-gradient-to-br from-accent-primary to-orange-600 rounded-lg flex items-center justify-center shadow-lg shadow-accent-primary/20">
                        <span className="material-symbols-outlined text-white text-lg font-bold">bolt</span>
                    </div>
                    <div>
                        <h1 className="text-sm font-bold tracking-wider uppercase text-white/90">Protocolo Génesis</h1>
                        <p className="text-[10px] text-text-muted">Iniciando sistema operativo...</p>
                    </div>
                </div>

                {/* Steps Indicator */}
                <div className="hidden md:flex items-center gap-12">
                    {[1, 2, 3].map((step) => (
                        <div key={step} className={`flex items-center gap-2 ${step === currentStep ? 'text-accent-primary' : step < currentStep ? 'text-status-success' : 'text-white/20'}`}>
                            <div className={`
                                w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold border transition-all duration-500
                                ${step === currentStep
                                    ? 'border-accent-primary bg-accent-primary/10 shadow-[0_0_15px_rgba(255,107,0,0.3)]'
                                    : step < currentStep
                                        ? 'border-status-success bg-status-success/10 text-status-success'
                                        : 'border-white/10 bg-white/5'}
                            `}>
                                {step < currentStep ? <span className="material-symbols-outlined text-sm">check</span> : step}
                            </div>
                            <span className="text-xs font-semibold uppercase tracking-wider">
                                {step === 1 && 'Fundación'}
                                {step === 2 && 'Territorio'}
                                {step === 3 && 'Datos De Inicio'}
                            </span>
                        </div>
                    ))}
                </div>

                <div className="w-24"></div> {/* Spacer for balance */}
            </header>

            {/* Progress Line */}
            <div className="relative z-20 h-0.5 bg-white/5 w-full">
                <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-status-success via-accent-primary to-accent-primary transition-all duration-700 ease-out"
                    style={{ width: progressWidth }}
                ></div>
                {/* Glow effect at the tip of the progress bar */}
                <div
                    className="absolute top-1/2 -translate-y-1/2 h-1.5 w-24 bg-accent-primary blur-md transition-all duration-700 ease-out -ml-12"
                    style={{ left: progressWidth, opacity: progressWidth === '0%' ? 0 : 1 }}
                ></div>
            </div>

            {/* Main Content Area */}
            <main className="relative z-10 flex-1 flex flex-col items-center justify-center p-6 overflow-y-auto">
                <div className="w-full max-w-4xl mx-auto anime-fade-in">
                    {children}
                </div>
            </main>

            {/* Footer Status */}
            <footer className="relative z-20 py-3 px-8 border-t border-white/5 flex justify-between items-center text-[10px] font-mono text-text-muted/50">
                <span>TERMINAL_SESSION_ID: {Math.random().toString(36).substring(7).toUpperCase()}</span>
                <span className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse"></span>
                    SYSTEM_ONLINE
                </span>
            </footer>
        </div>
    );
};
