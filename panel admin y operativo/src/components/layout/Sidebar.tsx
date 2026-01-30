/**
 * Sidebar Component - Updated with Kitchen Management Submenu
 */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface MenuItem {
    name: string;
    path: string;
    icon: string;
    submenu?: { name: string; path: string; icon: string }[];
}

const menuItems: MenuItem[] = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: 'dashboard' },
    { name: 'Orders', path: '/admin/orders', icon: 'receipt_long' },
    { name: 'Inventory', path: '/admin/inventory', icon: 'inventory_2' },
    {
        name: 'Cocina & Menú',
        path: '/kitchen',
        icon: 'restaurant',
        submenu: [
            //{ name: 'Insumos', path: '/kitchen/ingredients', icon: 'nutrition' },

            //{ name: 'Recetas', path: '/kitchen/recipes', icon: 'menu_book' },
            { name: 'Ingeniería de Menú', path: '/kitchen/menu-engineering', icon: 'analytics' },
            { name: '🍺 PANEL DE CONTROL', path: '/admin/setup', icon: 'tune' },
        ]
    },
    { name: 'Staff', path: '/admin/staff', icon: 'group' },
    { name: 'Sucursales', path: '/admin/branches', icon: 'store' },
    { name: 'Analytics', path: '/admin/analytics', icon: 'monitoring' },
    { name: 'Settings', path: '/admin/settings', icon: 'settings' },
];

export const Sidebar = () => {
    const location = useLocation();
    const [expandedMenus, setExpandedMenus] = useState<string[]>(['/kitchen']);

    const toggleSubmenu = (path: string) => {
        setExpandedMenus(prev =>
            prev.includes(path)
                ? prev.filter(p => p !== path)
                : [...prev, path]
        );
    };

    const isPathActive = (path: string) => {
        return location.pathname === path || location.pathname.startsWith(path + '/');
    };

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
                <nav className="flex flex-col gap-1 flex-1">
                    {menuItems.map((item) => {
                        const isActive = isPathActive(item.path);
                        const isExpanded = expandedMenus.includes(item.path);
                        const hasSubmenu = item.submenu && item.submenu.length > 0;

                        return (
                            <div key={item.path}>
                                {hasSubmenu ? (
                                    // Parent with submenu
                                    <button
                                        onClick={() => toggleSubmenu(item.path)}
                                        className={`
                                            w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg transition-all
                                            ${isActive
                                                ? 'bg-accent-orange/10 text-accent-orange border border-accent-orange/20'
                                                : 'text-text-muted hover:text-white hover:bg-white/5'
                                            }
                                        `}
                                    >
                                        <div className="flex items-center gap-3">
                                            <span className={`material-symbols-outlined ${isActive ? 'fill-1' : ''}`}>
                                                {item.icon}
                                            </span>
                                            <span className="text-sm font-medium">{item.name}</span>
                                        </div>
                                        <span className={`material-symbols-outlined text-[18px] transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                                            expand_more
                                        </span>
                                    </button>
                                ) : (
                                    // Regular link
                                    <Link
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
                                )}

                                {/* Submenu */}
                                {hasSubmenu && isExpanded && (
                                    <div className="ml-4 mt-1 space-y-1 border-l border-border-dark pl-3">
                                        {item.submenu!.map((subItem) => {
                                            const isSubActive = location.pathname === subItem.path;
                                            return (
                                                <Link
                                                    key={subItem.path}
                                                    to={subItem.path}
                                                    className={`
                                                        flex items-center gap-2 px-3 py-2 rounded-lg transition-all text-sm
                                                        ${isSubActive
                                                            ? 'bg-accent-orange/10 text-accent-orange'
                                                            : 'text-text-muted hover:text-white hover:bg-white/5'
                                                        }
                                                    `}
                                                >
                                                    <span className="material-symbols-outlined text-[18px]">
                                                        {subItem.icon}
                                                    </span>
                                                    <span>{subItem.name}</span>
                                                </Link>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
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
                    <p className="text-[10px] text-gray-500 font-mono mt-1">v4.1-menu-engineering</p>
                </div>
            </div>
        </aside>
    );
};
