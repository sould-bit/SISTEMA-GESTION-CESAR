/**
 * Sidebar Component - Updated with Kitchen Management Submenu
 */

import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { usePWAInstall } from '../../hooks/usePWAInstall';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useAppDispatch, useAppSelector } from '../../stores/store';
import { setSidebarOpen, setSidebarCollapsed } from '../../stores/ui.slice';

interface MenuItem {
    name: string;
    path: string;
    icon: string;
    submenu?: { name: string; path: string; icon: string }[];
}

const menuItems: MenuItem[] = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: 'dashboard' },
    { name: 'Mesas', path: '/admin/tables', icon: 'table_restaurant' },
    { name: 'Orders', path: '/admin/orders', icon: 'receipt_long' },
    { name: 'Inventory', path: '/admin/inventory', icon: 'inventory_2' },
    {
        name: 'Cocina & Menú',
        path: '/kitchen',
        icon: 'restaurant',
        submenu: [
            { name: 'Ingeniería de Menú', path: '/kitchen/menu-engineering', icon: 'analytics' },
            { name: '🍺 PANEL DE CONTROL', path: '/admin/setup', icon: 'tune' },
        ]
    },
    { name: 'Staff', path: '/admin/staff', icon: 'group' },
    { name: 'Sucursales', path: '/admin/branches', icon: 'store' },
];

export const Sidebar = () => {
    const location = useLocation();
    const dispatch = useAppDispatch();
    const isOpen = useAppSelector(state => state.ui.sidebarOpen);
    const isCollapsed = useAppSelector(state => state.ui.sidebarCollapsed);
    const isDesktop = useMediaQuery('(min-width: 1024px)');
    const { isInstallable, installPWA } = usePWAInstall();
    const [expandedMenus, setExpandedMenus] = useState<string[]>(['/kitchen']);

    // Close sidebar on path change (for mobile)
    useEffect(() => {
        if (!isDesktop) {
            dispatch(setSidebarOpen(false));
        }
    }, [location.pathname, dispatch, isDesktop]);

    const toggleSubmenu = (path: string) => {
        if (isCollapsed && isDesktop) {
            dispatch(setSidebarCollapsed(false));
            if (!expandedMenus.includes(path)) {
                setExpandedMenus(prev => [...prev, path]);
            }
            return;
        }
        setExpandedMenus(prev =>
            prev.includes(path)
                ? prev.filter(p => p !== path)
                : [...prev, path]
        );
    };

    const isPathActive = (path: string) => {
        return location.pathname === path || location.pathname.startsWith(path + '/');
    };

    const isCompact = isCollapsed || !isDesktop;

    return (
        <>
            {/* Mobile Overlay */}
            {!isDesktop && isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
                    onClick={() => dispatch(setSidebarOpen(false))}
                />
            )}

            <motion.aside
                initial={false}
                animate={{
                    width: isDesktop ? (isCollapsed ? 82 : 256) : 72,
                    x: isDesktop ? 0 : (isOpen ? 0 : -72)
                }}
                onMouseEnter={() => isDesktop && dispatch(setSidebarCollapsed(false))}
                onMouseLeave={() => isDesktop && dispatch(setSidebarCollapsed(true))}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className={`
                    fixed inset-y-0 left-0 z-50 bg-[#0B1120] border-r border-border-dark flex flex-col shrink-0 font-sans
                    lg:static lg:z-auto cursor-default
                `}
            >
                <div className="flex flex-col h-full relative overflow-hidden">

                    <div className="flex flex-col h-full p-4 pt-[max(1rem,env(safe-area-inset-top))] lg:pt-4 overflow-y-auto overflow-x-hidden custom-scrollbar">
                        {/* Logo Area */}
                        <div className={`flex items-center gap-3 px-2 mb-8 mt-0 transition-all duration-300 ${isCompact ? 'justify-center' : ''}`}>
                            <div className="bg-accent-primary/10 flex items-center justify-center rounded-lg size-10 text-accent-primary shrink-0">
                                <span className="material-symbols-outlined shrink-0">fastfood</span>
                            </div>
                            <AnimatePresence>
                                {!isCompact && (
                                    <motion.div
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                        className="flex flex-col whitespace-nowrap"
                                    >
                                        <h1 className="text-white text-lg font-bold leading-none tracking-tight">FastFood OS</h1>
                                        <p className="text-text-muted text-xs font-normal mt-1">Manager View</p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
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
                                            <button
                                                onClick={() => toggleSubmenu(item.path)}
                                                className={`
                                                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all relative overflow-hidden group
                                                    ${isCompact ? 'justify-center' : 'justify-between'}
                                                    ${isActive
                                                        ? 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20 shadow-[0_4px_12px_-4px_rgba(234,88,12,0.1)]'
                                                        : 'text-text-muted hover:text-white hover:bg-white/5'
                                                    }
                                                `}
                                                title={isCompact ? item.name : undefined}
                                            >
                                                {/* Active Indicator Bar */}
                                                {isActive && (
                                                    <motion.div
                                                        layoutId="active-nav"
                                                        className="absolute left-0 w-1 h-3/5 bg-accent-primary rounded-r-full"
                                                    />
                                                )}

                                                <div className="flex items-center gap-3 min-w-0">
                                                    <span className={`material-symbols-outlined shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'fill-1' : ''}`}>
                                                        {item.icon}
                                                    </span>
                                                    {!isCompact && (
                                                        <motion.span
                                                            initial={{ opacity: 0, x: -5 }}
                                                            animate={{ opacity: 1, x: 0 }}
                                                            className="text-sm font-medium truncate"
                                                        >
                                                            {item.name}
                                                        </motion.span>
                                                    )}
                                                </div>
                                                {!isCompact && (
                                                    <span className={`material-symbols-outlined text-[18px] transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                                                        expand_more
                                                    </span>
                                                )}
                                            </button>
                                        ) : (
                                            <Link
                                                to={item.path}
                                                className={`
                                                    flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all relative overflow-hidden group
                                                    ${isCompact ? 'justify-center' : ''}
                                                    ${isActive
                                                        ? 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20 shadow-[0_4px_12px_-4px_rgba(234,88,12,0.1)]'
                                                        : 'text-text-muted hover:text-white hover:bg-white/5'
                                                    }
                                                `}
                                                title={isCompact ? item.name : undefined}
                                            >
                                                {/* Active Indicator Bar */}
                                                {isActive && (
                                                    <motion.div
                                                        layoutId="active-nav"
                                                        className="absolute left-0 w-1 h-3/5 bg-accent-primary rounded-r-full"
                                                    />
                                                )}

                                                <span className={`material-symbols-outlined shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'fill-1' : ''}`}>
                                                    {item.icon}
                                                </span>
                                                {!isCompact && (
                                                    <motion.span
                                                        initial={{ opacity: 0, x: -5 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        className="text-sm font-medium truncate"
                                                    >
                                                        {item.name}
                                                    </motion.span>
                                                )}
                                            </Link>
                                        )}

                                        {/* Submenu */}
                                        {hasSubmenu && isExpanded && !isCompact && (
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
                                                                    ? 'bg-accent-primary/10 text-accent-primary'
                                                                    : 'text-text-muted hover:text-white hover:bg-white/5'
                                                                }
                                                            `}
                                                        >
                                                            <span className="material-symbols-outlined text-[18px] shrink-0">
                                                                {subItem.icon}
                                                            </span>
                                                            <span className="truncate">{subItem.name}</span>
                                                        </Link>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}

                            {/* PWA Persistent Install Button */}
                            {isInstallable && (
                                <button
                                    onClick={installPWA}
                                    className={`
                                        mt-4 flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30 hover:text-indigo-300 group
                                        ${isCompact ? 'justify-center border-none bg-transparent hover:bg-indigo-600/10' : ''}
                                    `}
                                    title={isCompact ? "Instalar Aplicación" : undefined}
                                >
                                    <span className="material-symbols-outlined group-hover:scale-110 transition-transform shrink-0">
                                        download_for_offline
                                    </span>
                                    {!isCompact && <span className="text-sm font-bold whitespace-nowrap">Instalar Aplicación</span>}
                                </button>
                            )}
                        </nav>

                        {/* System Status */}
                        <div className={`mt-4 mb-[max(0.5rem,env(safe-area-inset-bottom))] lg:mb-0 px-3 py-3 rounded-lg bg-card-dark/50 border border-border-dark transition-all duration-300 ${isCompact ? 'bg-transparent border-none flex flex-col items-center py-1' : ''}`}>
                            <div className={`flex items-center justify-between mb-2 w-full ${isCompact ? 'justify-center mb-0' : ''}`}>
                                {!isCompact && <span className="text-xs text-text-muted font-medium">System Status</span>}
                                <span className={`flex size-2 rounded-full bg-status-success animate-pulse ${isCompact ? 'size-2' : ''}`}></span>
                            </div>
                            {!isCompact && (
                                <>
                                    <p className="text-xs text-status-success font-mono">Sync: Live</p>
                                    <p className="text-[10px] text-gray-500 font-mono mt-1 whitespace-nowrap">v4.1-menu-engineering</p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </motion.aside>
        </>
    );
};
