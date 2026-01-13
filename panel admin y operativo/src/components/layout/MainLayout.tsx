import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const MainLayout = () => {
    return (
        <div className="h-screen w-full bg-bg-deep text-text-body font-sans flex overflow-hidden">
            {/* Sidebar */}
            <div className="hidden lg:flex flex-col h-full shrink-0">
                <Sidebar />
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 h-full relative">
                <Header />

                {/* Scrollable Page Content */}
                <main className="flex-1 overflow-y-auto bg-bg-deep p-6">
                    <div className="max-w-[1600px] mx-auto h-full">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};
