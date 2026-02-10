import React from 'react';

interface DeliveryDetails {
    customer_name: string;
    customer_phone: string;
    delivery_address: string;
    delivery_notes: string;
}

interface DeliveryInfoFormProps {
    value: DeliveryDetails;
    onChange: (details: DeliveryDetails) => void;
    errors: Partial<Record<keyof DeliveryDetails, string>>;
}

export const DeliveryInfoForm: React.FC<DeliveryInfoFormProps> = ({ value, onChange, errors }) => {
    const handleChange = (field: keyof DeliveryDetails, newValue: string) => {
        onChange({ ...value, [field]: newValue });
    };

    return (
        <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="bg-bg-deep/50 p-4 rounded-xl border border-border-dark space-y-3 shadow-inner">
                <h4 className="text-[10px] text-accent-primary uppercase tracking-widest font-black mb-1 flex items-center gap-2">
                    <span className="material-symbols-outlined text-[14px]">local_shipping</span>
                    Datos de Entrega
                </h4>

                {/* Customer Name */}
                <div className="space-y-1">
                    <label className="text-[9px] text-text-muted uppercase tracking-wider font-bold ml-1">Nombre Completo</label>
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-muted text-[16px]">person</span>
                        <input
                            type="text"
                            value={value.customer_name}
                            onChange={(e) => handleChange('customer_name', e.target.value)}
                            placeholder="Ej: Juan Pérez"
                            className={`w-full bg-bg-deep border rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-text-muted/50 focus:outline-none transition-colors ${errors.customer_name ? 'border-status-alert' : 'border-border-dark focus:border-accent-primary'}`}
                        />
                    </div>
                    {errors.customer_name && <p className="text-[8px] text-status-alert font-bold ml-1">{errors.customer_name}</p>}
                </div>

                {/* Phone */}
                <div className="space-y-1">
                    <label className="text-[9px] text-text-muted uppercase tracking-wider font-bold ml-1">Teléfono / WhatsApp</label>
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-muted text-[16px]">phone</span>
                        <input
                            type="tel"
                            value={value.customer_phone}
                            onChange={(e) => handleChange('customer_phone', e.target.value)}
                            placeholder="Ej: 300 123 4567"
                            className={`w-full bg-bg-deep border rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-text-muted/50 focus:outline-none transition-colors ${errors.customer_phone ? 'border-status-alert' : 'border-border-dark focus:border-accent-primary'}`}
                        />
                    </div>
                    {errors.customer_phone && <p className="text-[8px] text-status-alert font-bold ml-1">{errors.customer_phone}</p>}
                </div>

                {/* Address */}
                <div className="space-y-1">
                    <label className="text-[9px] text-text-muted uppercase tracking-wider font-bold ml-1">Dirección Exacta</label>
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-muted text-[16px]">location_on</span>
                        <input
                            type="text"
                            value={value.delivery_address}
                            onChange={(e) => handleChange('delivery_address', e.target.value)}
                            placeholder="Ej: Calle 123 #45-67 Barrio Central"
                            className={`w-full bg-bg-deep border rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-text-muted/50 focus:outline-none transition-colors ${errors.delivery_address ? 'border-status-alert' : 'border-border-dark focus:border-accent-primary'}`}
                        />
                    </div>
                    {errors.delivery_address && <p className="text-[8px] text-status-alert font-bold ml-1">{errors.delivery_address}</p>}
                </div>

                {/* Delivery Notes */}
                <div className="space-y-1">
                    <label className="text-[9px] text-text-muted uppercase tracking-wider font-bold ml-1">Instrucciones de entrega</label>
                    <textarea
                        value={value.delivery_notes}
                        onChange={(e) => handleChange('delivery_notes', e.target.value)}
                        placeholder="Ej: Casa blanca, tocar timbre fuerte, dejar en portería..."
                        className="w-full bg-bg-deep border border-border-dark rounded-xl p-2.5 text-xs text-white placeholder-text-muted/50 focus:outline-none focus:border-accent-primary transition-colors resize-none h-16"
                    />
                </div>
            </div>
        </div>
    );
};
