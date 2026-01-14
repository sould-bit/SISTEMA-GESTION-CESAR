import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAppDispatch, useAppSelector } from '../../../stores/store';
import { updateTerritory, setStep } from '../../../stores/genesis.slice';
import { TextInput } from '../../../components/ui/TextInput';

const territorySchema = z.object({
    branchName: z.string().min(3, 'Nombre de sede requerido'),
    address: z.string().min(5, 'Dirección requerida'),
    phone: z.string().min(7, 'Teléfono requerido')
});

type TerritoryForm = z.infer<typeof territorySchema>;

export const Step2Territory = () => {
    const dispatch = useAppDispatch();
    const territory = useAppSelector(state => state.genesis.territory);
    const [isPinDragging, setIsPinDragging] = useState(false);

    const { register, handleSubmit, formState: { errors } } = useForm<TerritoryForm>({
        resolver: zodResolver(territorySchema),
        defaultValues: {
            branchName: territory.branchName,
            address: territory.address,
            phone: territory.phone
        }
    });

    const onSubmit = (data: TerritoryForm) => {
        dispatch(updateTerritory(data));
        dispatch(setStep(3));
    };

    return (
        <div className="flex flex-col md:flex-row gap-8 items-stretch min-h-[500px]">
            {/* Left: Map Interface */}
            <div className="flex-1 bg-card-dark rounded-2xl overflow-hidden border border-border-dark relative group h-[400px] md:h-auto">
                {/* Static Map Image / Placeholder - Using a dark map style image */}
                <div
                    className="absolute inset-0 bg-cover bg-center opacity-60 group-hover:opacity-80 transition-opacity duration-500"
                    style={{ backgroundImage: "url('https://api.mapbox.com/styles/v1/mapbox/dark-v10/static/-74.006,40.7128,12,0/800x600?access_token=Pk.xyz')" }}
                >
                    {/* Fallback solid color if image fails or for better contrast */}
                    <div className="absolute inset-0 bg-bg-deep/40 mix-blend-multiply"></div>
                </div>

                {/* Map Grid Overlay */}
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10"></div>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-[80%] h-[80%] border border-accent-orange/20 rounded-lg flex items-center justify-center relative">
                        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-accent-orange"></div>
                        <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-accent-orange"></div>
                        <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-accent-orange"></div>
                        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-accent-orange"></div>
                    </div>
                </div>

                {/* Draggable Pin */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 cursor-move z-20 hover:scale-110 transition-transform">
                    <div className="relative">
                        <span className="material-symbols-outlined text-4xl text-accent-orange drop-shadow-[0_0_15px_rgba(255,107,0,0.8)]">location_on</span>
                        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-4 h-1 bg-black/50 blur-sm rounded-full"></div>
                    </div>
                </div>

                {/* Overlay Text */}
                <div className="absolute bottom-4 left-4 right-4 bg-bg-deep/90 backdrop-blur border border-white/10 rounded-lg p-3">
                    <p className="text-xs text-text-muted flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm animate-bounce text-accent-orange">touch_app</span>
                        Arrastra el pin para ajustar las coordenadas de tu base.
                    </p>
                </div>
            </div>

            {/* Right: Branch Form */}
            <div className="flex-1 flex flex-col justify-center max-w-md w-full mx-auto">
                <div className="mb-6">
                    <h2 className="text-3xl font-bold text-white mb-2">Nexo Territorial</h2>
                    <p className="text-text-muted">Establece la ubicación física de tu primera sucursal operativa.</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                    <TextInput
                        label="Nombre de la Sede"
                        icon="store"
                        placeholder="Ej. Sede Central - Norte"
                        {...register('branchName')}
                        error={errors.branchName?.message}
                        autoFocus
                    />

                    <TextInput
                        label="Dirección Física"
                        icon="location_on"
                        placeholder="Ej. Av. Principal #123"
                        {...register('address')}
                        error={errors.address?.message}
                    />

                    <TextInput
                        label="Teléfono de Contacto"
                        icon="call"
                        placeholder="Ej. +57 300 123 4567"
                        {...register('phone')}
                        error={errors.phone?.message}
                    />

                    <div className="pt-6 flex gap-4">
                        <button
                            type="button"
                            onClick={() => dispatch(setStep(1))}
                            className="bg-card-dark hover:bg-white/5 text-white py-4 px-6 rounded-xl border border-white/10 transition-colors"
                        >
                            Volver
                        </button>
                        <button
                            type="submit"
                            className="flex-1 bg-accent-orange hover:bg-orange-500 text-white font-bold py-4 px-8 rounded-xl shadow-[0_4px_20px_rgba(255,107,0,0.3)] hover:shadow-[0_4px_30px_rgba(255,107,0,0.5)] transition-all transform hover:-translate-y-1 flex items-center justify-center gap-3 group"
                        >
                            <span className="tracking-widest uppercase text-sm">Establecer Base</span>
                            <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">my_location</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
