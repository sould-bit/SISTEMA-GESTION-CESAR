import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingCart,
  ChefHat,
  Package,
  Settings,
  Menu,
  X,
  LogOut,
  User
} from 'lucide-react';
import { cn } from '../utils';

const SidebarItem = ({ to, icon: Icon, label, onClick }: { to: string; icon: any; label: string; onClick?: () => void }) => (
  <NavLink
    to={to}
    onClick={onClick}
    className={({ isActive }) =>
      cn(
        "flex items-center space-x-3 px-4 py-3 text-gray-600 hover:bg-orange-50 hover:text-primary transition-colors rounded-lg",
        isActive && "bg-orange-100 text-primary font-medium"
      )
    }
  >
    <Icon size={20} />
    <span>{label}</span>
  </NavLink>
);

export const MainLayout: React.FC = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    // Implement logout logic here
    console.log('Logging out...');
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:static lg:transform-none",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-4 border-b h-16">
            <h1 className="text-xl font-bold text-primary">FastOps V</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <X size={24} />
            </button>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <SidebarItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
            <SidebarItem to="/orders" icon={ShoppingCart} label="Pedidos" />
            <SidebarItem to="/kitchen" icon={ChefHat} label="Cocina" />
            <SidebarItem to="/inventory" icon={Package} label="Inventario" />
            <SidebarItem to="/products" icon={Menu} label="Productos" />
            <SidebarItem to="/settings" icon={Settings} label="Configuración" />
          </nav>

          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-3 px-4 py-3 mb-2">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-primary">
                <User size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">Usuario</p>
                <p className="text-xs text-gray-500 truncate">Admin</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-3 w-full px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut size={20} />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-4 h-16 bg-white border-b border-gray-200 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700"
          >
            <Menu size={24} />
          </button>
          <span className="font-semibold text-gray-900">FastOps V</span>
          <div className="w-6" /> {/* Spacer */}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
