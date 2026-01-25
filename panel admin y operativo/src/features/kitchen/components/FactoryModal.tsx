import React, { useState, useEffect } from 'react';
import { Ingredient, kitchenService } from '../kitchen.service';

interface FactoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    ingredients: Ingredient[];
    onSuccess: () => void;
}



export const FactoryModal: React.FC<FactoryModalProps> = ({
    isOpen,
    onClose,
    ingredients,
    onSuccess
}) => {
    const [inputs, setInputs] = useState<{ ingredient_id: string; quantity: string }[]>([{ ingredient_id: '', quantity: '' }]);
    const [outputMode, setOutputMode] = useState<'EXISTING' | 'NEW'>('EXISTING');

    // Output state
    const [outputId, setOutputId] = useState<string>('');
    const [outputQuantity, setOutputQuantity] = useState<string>('');
    const [outputNewName, setOutputNewName] = useState<string>('');
    const [outputNewUnit, setOutputNewUnit] = useState<string>('kg');
    // const [outputNewCategory, setOutputNewCategory] = useState<string>('');

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Initial reset
    useEffect(() => {
        if (isOpen) {
            setInputs([{ ingredient_id: '', quantity: '' }]);
            setOutputMode('EXISTING');
            setOutputId('');
            setOutputQuantity('');
            setOutputNewName('');
            setError(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    // Filtered lists
    const rawIngredients = ingredients.filter(i => i.ingredient_type === 'RAW' && i.is_active);
    const processedIngredients = ingredients.filter(i => i.ingredient_type === 'PROCESSED' && i.is_active);

    // Helper: Parse Spanish/LatAm number format (1.000 -> 1000, 1,5 -> 1.5)
    // If invalid, returns NaN
    const parseNumber = (val: string): number => {
        if (!val) return 0;
        // Remove dots (thousands separator)
        const cleanDots = val.replace(/\./g, '');
        // Replace comma with dot (decimal separator)
        const normalized = cleanDots.replace(',', '.');
        return parseFloat(normalized);
    };

    const handleAddInput = () => {
        setInputs([...inputs, { ingredient_id: '', quantity: '' }]);
    };

    const handleRemoveInput = (index: number) => {
        const newInputs = [...inputs];
        newInputs.splice(index, 1);
        setInputs(newInputs);
    };

    const handleInputChange = (index: number, field: keyof typeof inputs[0], value: any) => {
        const newInputs = [...inputs];
        newInputs[index] = { ...newInputs[index], [field]: value };
        setInputs(newInputs);
    };

    const handleSubmit = async () => {
        setError(null);

        // Parse Inputs
        const parsedInputs = inputs.map(i => ({
            ingredient_id: i.ingredient_id,
            quantity: parseNumber(i.quantity)
        }));

        // Validation
        const validInputs = parsedInputs.filter(i => i.ingredient_id && !isNaN(i.quantity) && i.quantity > 0);

        if (validInputs.length === 0) {
            setError("Agrega al menos un insumo válido (Cantidad > 0)");
            return;
        }

        const parsedOutputQty = parseNumber(outputQuantity);
        if (isNaN(parsedOutputQty) || parsedOutputQty <= 0) {
            setError("La cantidad producida debe ser válida y mayor a 0");
            return;
        }

        const payload: any = {
            inputs: validInputs.map(i => ({ ingredient_id: i.ingredient_id, quantity: i.quantity })),
            output_quantity: parsedOutputQty,
            output: {}
        };

        if (outputMode === 'EXISTING') {
            if (!outputId) {
                setError("Selecciona un insumo de destino o crea uno nuevo");
                return;
            }
            payload.output.ingredient_id = outputId;
        } else {
            if (!outputNewName) {
                setError("Ingresa el nombre del nuevo insumo");
                return;
            }
            payload.output.name = outputNewName;
            payload.output.base_unit = outputNewUnit;
            // if (outputNewCategory) payload.output.category_id = parseInt(outputNewCategory);
        }

        setIsSubmitting(true);
        try {
            await kitchenService.registerProduction(payload);
            // alert("Producción registrada correctamente");
            onSuccess();
            onClose();
        } catch (error: any) {
            console.error(error);
            let errorMessage = "Error al registrar producción";
            const detail = error.response?.data?.detail;

            if (typeof detail === 'string') {
                errorMessage = detail;
            } else if (Array.isArray(detail)) {
                // Handle Pydantic validation error array
                errorMessage = detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
            } else if (typeof detail === 'object' && detail !== null) {
                errorMessage = JSON.stringify(detail);
            } else if (error.message) {
                errorMessage = error.message;
            }

            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
            <div className="bg-card-dark border border-border-dark rounded-2xl w-full max-w-4xl max-h-[90vh] shadow-2xl flex flex-col">

                {/* Header */}
                <div className="p-6 border-b border-border-dark bg-white/5 flex justify-between items-center rounded-t-2xl">
                    <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-orange-500">factory</span>
                        Fábrica de Producción Interna
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="mb-6 bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-lg flex items-center gap-2">
                            <span className="material-symbols-outlined">error</span>
                            {error}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* LEFT: INPUTS */}
                        <div className="space-y-4 md:border-r border-border-dark md:pr-6">
                            <div className="flex justify-between items-center">
                                <h4 className="font-semibold text-gray-300 flex items-center gap-2">
                                    <span className="bg-orange-500/20 text-orange-400 w-6 h-6 rounded-full flex items-center justify-center text-xs">1</span>
                                    Insumos a Transformar
                                </h4>
                                <button
                                    onClick={handleAddInput}
                                    className="text-orange-400 hover:text-orange-300 text-sm font-medium flex items-center gap-1"
                                >
                                    <span className="material-symbols-outlined text-[18px]">add</span>
                                    Agregar Insumo
                                </button>
                            </div>

                            <div className="space-y-3">
                                {inputs.map((input, idx) => (
                                    <div key={idx} className="flex gap-2 items-end bg-bg-deep p-3 rounded-lg border border-border-dark">
                                        <div className="flex-1">
                                            <label className="block text-xs text-gray-500 mb-1">Materia Prima</label>
                                            <select
                                                value={input.ingredient_id}
                                                onChange={(e) => handleInputChange(idx, 'ingredient_id', e.target.value)}
                                                className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 outline-none"
                                            >
                                                <option value="">Seleccionar...</option>
                                                {rawIngredients.map(ing => (
                                                    <option key={ing.id} value={ing.id}>
                                                        {ing.name} ({ing.base_unit})
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="w-24">
                                            <label className="block text-xs text-gray-500 mb-1">Cant.</label>
                                            <input
                                                type="text"
                                                className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 outline-none"
                                                value={input.quantity}
                                                onChange={(e) => handleInputChange(idx, 'quantity', e.target.value)}
                                                placeholder="0.00"
                                            />
                                        </div>
                                        {inputs.length > 1 && (
                                            <button
                                                onClick={() => handleRemoveInput(idx)}
                                                className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                            >
                                                <span className="material-symbols-outlined text-[20px]">delete</span>
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* RIGHT: OUTPUT */}
                        <div className="space-y-6">
                            <h4 className="font-semibold text-gray-300 flex items-center gap-2">
                                <span className="bg-emerald-500/20 text-emerald-400 w-6 h-6 rounded-full flex items-center justify-center text-xs">2</span>
                                Producto Resultante
                            </h4>

                            <div className="flex bg-white/5 p-1 rounded-lg">
                                <button
                                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${outputMode === 'EXISTING' ? 'bg-orange-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                                    onClick={() => setOutputMode('EXISTING')}
                                >
                                    Existente
                                </button>
                                <button
                                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${outputMode === 'NEW' ? 'bg-orange-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                                    onClick={() => setOutputMode('NEW')}
                                >
                                    Nuevo Producto
                                </button>
                            </div>

                            <div className="p-5 border border-orange-500/30 bg-orange-500/5 rounded-xl space-y-5">
                                {outputMode === 'EXISTING' ? (
                                    <div>
                                        <label className="block text-sm font-medium text-orange-200 mb-1">Producto Procesado</label>
                                        <select
                                            value={outputId}
                                            onChange={(e) => setOutputId(e.target.value)}
                                            className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2.5 text-white focus:border-orange-500 outline-none"
                                        >
                                            <option value="">Buscar en catálogo...</option>
                                            {processedIngredients.map(ing => (
                                                <option key={ing.id} value={ing.id}>
                                                    {ing.name} ({ing.base_unit})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-orange-200 mb-1">Nombre del Nuevo Producto</label>
                                            <input
                                                type="text"
                                                value={outputNewName}
                                                onChange={(e) => setOutputNewName(e.target.value)}
                                                placeholder="Ej. Carne para Hamburguesa"
                                                className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2.5 text-white focus:border-orange-500 outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-orange-200 mb-1">Unidad Base</label>
                                            <select
                                                value={outputNewUnit}
                                                onChange={(e) => setOutputNewUnit(e.target.value)}
                                                className="w-full bg-card-dark border border-border-dark rounded-lg px-3 py-2.5 text-white focus:border-orange-500 outline-none"
                                            >
                                                <option value="kg">Kilogramos (kg)</option>
                                                <option value="und">Unidades (und)</option>
                                                <option value="lt">Litros (lt)</option>
                                                <option value="g">Gramos (g)</option>
                                            </select>
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-bold text-orange-400 mb-1">CANTIDAD PRODUCIDA</label>
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="text"
                                            className="w-full bg-card-dark border-2 border-orange-500/50 rounded-lg px-4 py-3 text-white text-xl font-bold focus:border-orange-500 outline-none"
                                            placeholder="0.00"
                                            value={outputQuantity}
                                            onChange={(e) => setOutputQuantity(e.target.value)}
                                        />
                                        <span className="text-sm font-medium text-gray-400 bg-white/5 px-3 py-3 rounded-lg min-w-[60px] text-center border border-white/10">
                                            {outputMode === 'EXISTING'
                                                ? (processedIngredients.find(i => i.id === outputId)?.base_unit || '-')
                                                : outputNewUnit}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-2">
                                        * Esta cantidad se sumará al inventario y el costo se promediará.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-border-dark bg-white/5 flex justify-end gap-3 rounded-b-2xl">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 text-gray-400 hover:text-white font-medium transition-colors"
                        disabled={isSubmitting}
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                        className="px-8 py-2.5 bg-orange-600 hover:bg-orange-500 text-white rounded-lg font-bold shadow-lg shadow-orange-500/20 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        {isSubmitting ? (
                            <span className="animate-spin material-symbols-outlined text-[20px]">progress_activity</span>
                        ) : (
                            <span className="material-symbols-outlined text-[20px]">settings_suggest</span>
                        )}
                        {isSubmitting ? 'Procesando...' : 'Registrar Producción'}
                    </button>
                </div>

            </div>
        </div>
    );
};
