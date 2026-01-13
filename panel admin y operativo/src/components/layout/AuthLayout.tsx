import { ReactNode } from 'react';

interface AuthLayoutProps {
    children: ReactNode;
}

export const AuthLayout = ({ children }: AuthLayoutProps) => {
    return (
        <div className="bg-asphalt min-h-screen flex items-center justify-center font-sans text-white relative overflow-hidden">
            <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-fastops-orange/5 rounded-full blur-[120px]"></div>
                <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] bg-info-blue/5 rounded-full blur-[100px]"></div>
            </div>
            <main className="w-full max-w-xl p-6 relative z-10">
                {children}
                <p className="text-center text-slate-600 text-xs mt-8">
                    © 2026 FastOps Technologies Inc. Todos los derechos reservados.
                </p>
            </main>
        </div>
    );
};
