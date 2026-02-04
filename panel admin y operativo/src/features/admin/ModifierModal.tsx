import { useState } from 'react';
import { Product, ProductModifier } from '../setup/setup.service';

interface ModifierModalProps {
    product: Product;
    recipe: any; // Recipe with items
    modifiers: ProductModifier[]; // Available global modifiers
    onClose: () => void;
    onConfirm: (removedIngredients: string[], selectedModifiers: number[], comment?: string) => void;
    initialRemoved?: string[];
    initialModifiers?: number[];
    initialComment?: string;
}

export const ModifierModal = ({
    product,
    recipe,
    modifiers,
    onClose,
    onConfirm,
    initialRemoved = [],
    initialModifiers = [],
    initialComment = ''
}: ModifierModalProps) => {
    // State for base ingredients (checked = keep, unchecked = remove)
    // We store IDs of REMOVED ingredients to send to backend
    // Since recipe items might use ingredient_id (UUID) or ingredient_product_id (Int),
    // we need to handle both. Setup service normalizes to strings? Or we use what we have.
    // Backend expects strings in removed_ingredients.

    const [removedIngredients, setRemovedIngredients] = useState<Set<string>>(new Set(initialRemoved));

    // State for modifiers: Map of ModifierID -> Quantity
    // Backend expects strictly a list of IDs. If quantity > 1, we repeat the ID?
    // Backend OrderService: "Counter(user_item.modifiers)" -> yes, repeats.
    // So we manage counts here and flatten to list on confirm.
    const [selectedMods, setSelectedMods] = useState<Map<number, number>>(() => {
        const map = new Map();
        initialModifiers.forEach(id => {
            map.set(id, (map.get(id) || 0) + 1);
        });
        return map;
    });

    const [comment, setComment] = useState(initialComment);

    const handleToggleIngredient = (id: string | number) => {
        const idStr = String(id);
        setRemovedIngredients(prev => {
            const next = new Set(prev);
            if (next.has(idStr)) {
                next.delete(idStr); // Re-add ingredient (un-remove)
            } else {
                next.add(idStr); // Remove ingredient
            }
            return next;
        });
    };

    const handleUpdateModifier = (modId: number, delta: number) => {
        setSelectedMods(prev => {
            const next = new Map(prev);
            const current = next.get(modId) || 0;
            const newQty = Math.max(0, current + delta);
            if (newQty === 0) {
                next.delete(modId);
            } else {
                next.set(modId, newQty);
            }
            return next;
        });
    };

    const handleConfirm = () => {
        // Flatten modifiers map to list of IDs
        const modList: number[] = [];
        selectedMods.forEach((qty, id) => {
            for (let i = 0; i < qty; i++) {
                modList.push(id);
            }
        });

        onConfirm(Array.from(removedIngredients), modList, comment);
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-card-dark w-full max-w-md rounded-2xl border border-border-dark shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="p-4 border-b border-border-dark flex justify-between items-center bg-bg-deep/50 rounded-t-2xl">
                    <div>
                        <h3 className="text-lg font-bold text-white leading-none">{product.name}</h3>
                        <p className="text-xs text-text-muted mt-1">Personaliza tu pedido</p>
                    </div>
                    <button onClick={onClose} className="p-2 -mr-2 text-text-muted hover:text-white transition-colors rounded-full hover:bg-white/10">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">

                    {/* Sección 1: Ingredientes Base (Remover) */}
                    {recipe && recipe.items && recipe.items.length > 0 && (
                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-accent-primary uppercase tracking-widest border-b border-white/10 pb-1">
                                Ingredientes Base
                            </h4>
                            <div className="space-y-2">
                                {recipe.items.map((item: any, idx: number) => {
                                    const id = item.ingredient_id || item.ingredient_product_id;
                                    const idStr = String(id);
                                    const isRemoved = removedIngredients.has(idStr);

                                    return (
                                        <div
                                            key={idx}
                                            onClick={() => handleToggleIngredient(id)}
                                            className={`flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer select-none group
                                                ${!isRemoved
                                                    ? 'bg-bg-deep border-accent-secondary/30 hover:border-accent-secondary'
                                                    : 'bg-bg-dark border-border-dark opacity-60 grayscale'
                                                }`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`size-5 rounded flex items-center justify-center border transition-colors ${!isRemoved ? 'bg-accent-secondary border-accent-secondary' : 'border-text-muted'}`}>
                                                    {!isRemoved && <span className="material-symbols-outlined text-bg-dark text-sm font-bold">check</span>}
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className={`text-sm font-medium transition-colors ${!isRemoved ? 'text-white' : 'text-text-muted line-through'}`}>
                                                        {item.ingredient_name || 'Ingrediente'}
                                                    </span>
                                                    {!isRemoved && (
                                                        <span className="text-[10px] text-accent-secondary/80 font-mono">
                                                            {Number(item.gross_quantity)} {item.measure_unit}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            {isRemoved && (
                                                <span className="text-xs font-bold text-status-alert px-2 py-0.5 bg-status-alert/10 rounded">SIN</span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Sección 2: Extras (Modificadores) */}
                    {modifiers && modifiers.length > 0 && (
                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-accent-secondary uppercase tracking-widest border-b border-white/10 pb-1">
                                Extras & Adiciones
                            </h4>
                            <div className="grid grid-cols-1 gap-2">
                                {modifiers.map(mod => {
                                    const qty = selectedMods.get(mod.id) || 0;

                                    return (
                                        <div key={mod.id} className={`flex items-center justify-between p-3 rounded-xl border transition-all ${qty > 0 ? 'bg-accent-primary/5 border-accent-primary' : 'bg-bg-deep/50 border-border-dark'}`}>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-bold text-white">{mod.name}</span>
                                                <span className="text-xs text-accent-primary font-mono font-bold">
                                                    +{formatPrice(mod.extra_price)}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-3 bg-bg-dark rounded-lg p-1 border border-border-dark/50">
                                                <button
                                                    onClick={() => handleUpdateModifier(mod.id, -1)}
                                                    className={`size-8 flex items-center justify-center rounded transition-colors ${qty > 0 ? 'text-white hover:bg-white/10' : 'text-text-muted cursor-not-allowed opacity-50'}`}
                                                    disabled={qty === 0}
                                                >
                                                    <span className="material-symbols-outlined text-lg">remove</span>
                                                </button>
                                                <span className={`w-4 text-center font-mono font-bold ${qty > 0 ? 'text-white' : 'text-text-muted'}`}>{qty}</span>
                                                <button
                                                    onClick={() => handleUpdateModifier(mod.id, 1)}
                                                    className="size-8 flex items-center justify-center rounded text-accent-primary hover:bg-accent-primary/10 transition-colors"
                                                >
                                                    <span className="material-symbols-outlined text-lg">add</span>
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {!recipe?.items?.length && !modifiers?.length && (
                        <div className="text-center py-8 text-text-muted">
                            <p>Este producto no tiene opciones de personalización.</p>
                        </div>
                    )}

                    {/* Sección 3: Nota/Comentario del ítem */}
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-text-muted uppercase tracking-widest block">
                            Notas del producto
                        </label>

                        {/* Traceability Warning */}
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 flex gap-3">
                            <span className="material-symbols-outlined text-blue-400 text-xl shrink-0">info</span>
                            <div className="space-y-1">
                                <p className="text-xs font-bold text-blue-200">Importante: Trazabilidad</p>
                                <p className="text-[11px] text-blue-200/80 leading-tight">
                                    Usa este campo <strong>SOLO</strong> para instrucciones de preparación (ej: término de la carne).
                                    <br /><br />
                                    Si el cliente quiere <strong>quitar ingredientes</strong> (ej: sin cebolla) o <strong>agregar extras</strong>,
                                    usa los botones de arriba. Si lo escribes aquí, <strong>el inventario no se descontará correctamente</strong>.
                                </p>
                            </div>
                        </div>

                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Ej: Término medio, partido en dos..."
                            className="w-full bg-bg-deep border border-border-dark rounded-xl p-3 text-sm text-white placeholder-text-muted/50 focus:outline-none focus:border-accent-primary transition-colors resize-none h-24"
                        />
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border-dark bg-bg-deep/80 backdrop-blur rounded-b-2xl">
                    <button
                        onClick={handleConfirm}
                        className="w-full py-3 bg-accent-primary text-bg-dark rounded-xl font-bold uppercase tracking-widest shadow-lg shadow-accent-primary/20 hover:brightness-110 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                    >
                        <span className="material-symbols-outlined">check_circle</span>
                        Confirmar Modificaciones
                    </button>
                </div>
            </div>
        </div>
    );
};
