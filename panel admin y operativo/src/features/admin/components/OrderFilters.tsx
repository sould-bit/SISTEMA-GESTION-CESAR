
interface OrderFiltersProps {
    currentFilter: string;
    onFilterChange: (filter: 'all' | 'dine_in' | 'takeaway' | 'delivery') => void;
    ordersCount: Record<string, number>;
}

export const OrderFilters = ({ currentFilter, onFilterChange, ordersCount }: OrderFiltersProps) => {
    const filters = [
        { id: 'all', label: 'Todos', icon: 'list_alt' },
        { id: 'dine_in', label: 'Mesas', icon: 'table_restaurant' },
        { id: 'takeaway', label: 'Llevar', icon: 'shopping_bag' },
        { id: 'delivery', label: 'Domicilio', icon: 'delivery_dining' },
    ];

    return (
        <div className="flex bg-bg-deep p-1 rounded-xl border border-border-dark space-x-1">
            {filters.map((filter) => (
                <button
                    key={filter.id}
                    onClick={() => onFilterChange(filter.id as any)}
                    className={`
                        flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                        ${currentFilter === filter.id
                            ? 'bg-accent-primary text-bg-deep shadow-lg'
                            : 'text-text-muted hover:text-white hover:bg-card-dark'}
                    `}
                >
                    <span className="material-symbols-outlined text-[18px]">{filter.icon}</span>
                    {filter.label}
                    <span className={`
                        ml-1 text-[10px] px-1.5 py-0.5 rounded-full
                        ${currentFilter === filter.id ? 'bg-bg-deep/20 text-bg-deep' : 'bg-bg-deep text-text-muted'}
                    `}>
                        {ordersCount[filter.id] || 0}
                    </span>
                </button>
            ))}
        </div>
    );
};
