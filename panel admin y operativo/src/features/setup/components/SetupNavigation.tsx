import { Package, UtensilsCrossed, Cookie, Beer } from 'lucide-react';
import { MacroType } from '../setup.service';
import { useNavigate } from 'react-router-dom';

const CARDS = [
    {
        id: 'INSUMOS',
        label: 'Despensa & Insumos',
        icon: Package,
        color: 'text-emerald-400',
        bgIcon: 'bg-emerald-500/10',
        border: 'hover:border-emerald-500/50',
        gradient: 'from-emerald-500/5 to-transparent',
        desc: 'Gestiona la materia prima, costos base y proveedores.',
        navigateTo: '/kitchen/ingredients?tab=RAW'
    },
    {
        id: 'PRODUCCION',
        label: 'Producción Interna',
        icon: Package,
        color: 'text-orange-400',
        bgIcon: 'bg-orange-500/10',
        border: 'hover:border-orange-500/50',
        gradient: 'from-orange-500/5 to-transparent',
        desc: 'Transforma insumos en productos semielaborados. Mise en place.',
        navigateTo: '/kitchen/ingredients?tab=PROCESSED'
    },
    {
        id: 'CARTA',
        label: 'Platos de Carta',
        icon: UtensilsCrossed,
        color: 'text-amber-400',
        bgIcon: 'bg-amber-500/10',
        border: 'hover:border-amber-500/50',
        gradient: 'from-amber-500/5 to-transparent',
        desc: 'Diseña recetas para tus productos y calcula costos automáticamente.',
        navigateTo: '/kitchen/recipes'
    },
    {
        id: 'BEBIDAS',
        label: 'Bebidas & Cafetería',
        icon: Beer,
        color: 'text-blue-400',
        bgIcon: 'bg-blue-500/10',
        border: 'hover:border-blue-500/50',
        gradient: 'from-blue-500/5 to-transparent',
        desc: 'Productos de venta directa 1:1. Crea producto + inventario automáticamente.',
        navigateTo: null
    },
    {
        id: 'EXTRAS',
        label: 'Modificadores & Extras',
        icon: Cookie,
        color: 'text-purple-400',
        bgIcon: 'bg-purple-500/10',
        border: 'hover:border-purple-500/50',
        gradient: 'from-purple-500/5 to-transparent',
        desc: 'Adicionales, salsas y opciones personalizables para tus platos.',
        navigateTo: null
    }
];

interface SetupNavigationProps {
    onSelect: (id: MacroType) => void;
}

export const SetupNavigation = ({ onSelect }: SetupNavigationProps) => {
    const navigate = useNavigate();

    const handleClick = (card: any) => {
        if (card.navigateTo) {
            navigate(card.navigateTo);
        } else {
            onSelect(card.id as MacroType);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto px-4">
            {CARDS.map((card) => (
                <div
                    key={card.id}
                    onClick={() => handleClick(card)}
                    className={`group relative bg-card-dark border border-border-dark p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 overflow-hidden ${card.border}`}
                >
                    <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                    <div className="relative z-10 flex flex-col h-full">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 duration-300 ${card.bgIcon}`}>
                            <card.icon className={card.color} size={24} />
                        </div>
                        <h3 className={`text-xl font-bold mb-2 text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-400 transition-all`}>
                            {card.label}
                        </h3>
                        <p className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">
                            {card.desc}
                        </p>
                    </div>
                </div>
            ))}
        </div>
    );
};
