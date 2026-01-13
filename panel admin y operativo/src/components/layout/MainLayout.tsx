import { Outlet } from 'react-router-dom';

export const MainLayout = () => {
    return (
        <div className="min-h-screen bg-asphalt text-base-content font-sans flex">
            {/* Sidebar Placeholder */}
            <aside className="w-64 bg-asphalt-light border-r border-asphalt-lighter hidden md:flex flex-col">
                <div className="h-16 flex items-center px-6 border-b border-asphalt-lighter">
                    <span className="text-xl font-bold text-white tracking-tight">FastOps</span>
                </div>
                <nav className="flex-1 p-4">
                    <p className="text-sm text-slate-500">Menu Sidebar</p>
                </nav>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-16 bg-asphalt/50 backdrop-blur-md border-b border-asphalt-lighter flex items-center px-6 justify-between sticky top-0 z-20">
                    <h2 className="text-lg font-semibold text-white">Dashboard</h2>
                    <div className="w-8 h-8 rounded-full bg-asphalt-lighter flex items-center justify-center text-xs text-white">
                        UA
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 p-6 overflow-auto">
                    <div className="max-w-7xl mx-auto">
                        <Outlet /> {/* Aqui se renderizan las rutas hijas */}
                    </div>
                </main>
            </div>
        </div>
    );
};
