/**
 * MenuEngineeringPage - Página principal del módulo de Ingeniería de Menú
 * 
 * Incluye:
 * - Matriz BCG interactiva
 * - Pestañas para diferentes vistas
 * - Acceso a Insumos y Recetas
 */

import { useState } from 'react';
import { BCGMatrix } from '../../components/BCGMatrix';
import { Link } from 'react-router-dom';

type TabType = 'matrix' | 'ingredients' | 'recipes';

export const MenuEngineeringPage = () => {
    const [activeTab, setActiveTab] = useState<TabType>('matrix');

    const tabs: { id: TabType; label: string; icon: string }[] = [
        { id: 'matrix', label: 'Matriz BCG', icon: 'analytics' },
        { id: 'ingredients', label: 'Insumos', icon: 'nutrition' },
        { id: 'recipes', label: 'Recetas', icon: 'restaurant' },
    ];

    return (
        <div className="space-y-6">
            {/* Header with Tabs */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${activeTab === tab.id
                                    ? 'bg-accent-orange text-white shadow-lg shadow-accent-orange/20'
                                    : 'bg-card-dark text-text-muted hover:text-white border border-border-dark'
                                }`}
                        >
                            <span className="material-symbols-outlined text-[20px]">{tab.icon}</span>
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Quick Actions */}
                <div className="flex gap-2">
                    <Link
                        to="/admin/ingredients"
                        className="flex items-center gap-2 px-4 py-2 bg-card-dark border border-border-dark rounded-lg text-text-muted hover:text-white transition-colors text-sm"
                    >
                        <span className="material-symbols-outlined text-[18px]">add</span>
                        Nuevo Insumo
                    </Link>
                </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'matrix' && <BCGMatrix />}

            {activeTab === 'ingredients' && (
                <div className="bg-card-dark border border-border-dark rounded-xl p-8 text-center">
                    <span className="material-symbols-outlined text-6xl text-text-muted mb-4">nutrition</span>
                    <h3 className="text-xl font-semibold text-white mb-2">Gestión de Insumos</h3>
                    <p className="text-text-muted mb-4">Administra las materias primas para tus recetas</p>
                    <Link
                        to="/admin/ingredients"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-accent-orange hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Ir a Insumos
                        <span className="material-symbols-outlined">arrow_forward</span>
                    </Link>
                </div>
            )}

            {activeTab === 'recipes' && (
                <div className="bg-card-dark border border-border-dark rounded-xl p-8 text-center">
                    <span className="material-symbols-outlined text-6xl text-text-muted mb-4">restaurant</span>
                    <h3 className="text-xl font-semibold text-white mb-2">Constructor de Recetas</h3>
                    <p className="text-text-muted mb-4">Crea y gestiona las recetas de tus productos</p>
                    <Link
                        to="/admin/setup"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-accent-orange hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Ir a Recetas
                        <span className="material-symbols-outlined">arrow_forward</span>
                    </Link>
                </div>
            )}
        </div>
    );
};
