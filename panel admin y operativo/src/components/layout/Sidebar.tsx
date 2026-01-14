import { Link, useLocation } from 'react-router-dom';

const menuItems = [
    { name: 'Orders', path: '/admin/orders', icon: 'receipt_long' },
    { name: 'Inventory', path: '/admin/inventory', icon: 'inventory_2' },
    { name: 'Ingredients', path: '/admin/ingredients', icon: 'nutrition' },
    { name: 'Menu Engineering', path: '/admin/menu-engineering', icon: 'analytics' },
    { name: 'Engineering', path: '/admin/setup', icon: 'construction' },
    { name: 'Staff', path: '/admin/staff', icon: 'group' },
    { name: 'Analytics', path: '/admin/analytics', icon: 'monitoring' },
    { name: 'Settings', path: '/admin/settings', icon: 'settings' },
];

export const Sidebar = () => {
    const location = useLocation();

    return (
        <aside className="hidden lg:flex flex-col w-64 h-full border-r border-border-dark bg-[#0B1120] shrink-0 font-sans">
            <div className="flex flex-col h-full p-4">
                {/* Logo Area */}
                <div className="flex items-center gap-3 px-2 mb-8 mt-2">
                    <div className="bg-accent-orange/10 flex items-center justify-center rounded-lg size-10 text-accent-orange">
                        <span className="material-symbols-outlined">fastfood</span>
                    </div>
                    <div className="flex flex-col">
                        <h1 className="text-white text-lg font-bold leading-none tracking-tight">FastFood OS</h1>
                        <p className="text-text-muted text-xs font-normal mt-1">Manager View</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex flex-col gap-1.5 flex-1">
                    {menuItems.map((item) => {
                        const isActive = location.pathname === item.path || (item.path !== '/admin/dashboard' && location.pathname.startsWith(item.path));

                        // Handle Dashboard separately or as default? For now, if path is /admin/dashboard, maybe highlight Analytics or add Dashboard item
                        // Adding "Dashboard" manually to top if needed, or mapping items. 
                        // The design has 'Orders' as first item. I'll stick to the design's specific items for now.

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`
                                    flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all
                                    ${isActive
                                        ? 'bg-accent-orange/10 text-accent-orange border border-accent-orange/20 shadow-[0_0_10px_rgba(255,107,0,0.1)]'
                                        : 'text-text-muted hover:text-white hover:bg-white/5'
                                    }
                                `}
                            >
                                <span className={`material-symbols-outlined ${isActive ? 'fill-1' : ''}`}>
                                    {item.icon}
                                </span>
                                <span className="text-sm font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* System Status */}
                <div className="mt-4 px-3 py-3 rounded-lg bg-card-dark/50 border border-border-dark">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-text-muted font-medium">System Status</span>
                        <span className="flex size-2 rounded-full bg-status-success animate-pulse"></span>
                    </div>
                    <p className="text-xs text-status-success font-mono">Sync: Live</p>
                    <p className="text-[10px] text-gray-500 font-mono mt-1">v2.4.0-stable</p>
                </div>
            </div>
        </aside>
    );
};
