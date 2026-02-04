import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAppDispatch, useAppSelector } from '../../../stores/store';
import { updateFoundation, setStep } from '../../../stores/genesis.slice';
import { TextInput } from '../../../components/ui/TextInput';
import { useState } from 'react';

const foundationSchema = z.object({
    companyName: z.string().min(2, 'El nombre es muy corto'),
    nitRut: z.string().min(5, 'Identificador legal requerido'),
    ownerName: z.string().min(3, 'Nombre del fundador requerido'),
    phone: z.string().min(7, 'Teléfono requerido')
});

type FoundationForm = z.infer<typeof foundationSchema>;

export const Step1Foundation = () => {
    const dispatch = useAppDispatch();
    const foundation = useAppSelector(state => state.genesis.foundation);
    const [logoPreview, setLogoPreview] = useState<string | null>(null);

    const { register, handleSubmit, formState: { errors } } = useForm<FoundationForm>({
        resolver: zodResolver(foundationSchema),
        defaultValues: {
            companyName: foundation.companyName,
            nitRut: foundation.nitRut,
            ownerName: foundation.ownerName,
            phone: foundation.phone
        }
    });

    const onSubmit = (data: FoundationForm) => {
        dispatch(updateFoundation({ ...data, logo: logoPreview || undefined }));
        dispatch(setStep(2));
    };

    const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setLogoPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="flex flex-col md:flex-row gap-12 items-center justify-center min-h-[500px]">
            {/* Left: Logo Uploader */}
            <div className="flex-1 flex flex-col items-center justify-center">
                <div className="relative group cursor-pointer">
                    <input
                        type="file"
                        accept="image/*"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        onChange={handleLogoUpload}
                    />

                    {/* Animated Circles */}
                    <div className="absolute inset-0 bg-accent-primary/20 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500 animate-pulse"></div>

                    <div className={`
                        w-48 h-48 rounded-full border-2 border-dashed flex flex-col items-center justify-center relative z-20 bg-bg-deep/50 backdrop-blur-sm transition-all duration-300
                        ${logoPreview ? 'border-accent-primary' : 'border-white/20 group-hover:border-accent-primary'}
                    `}>
                        {logoPreview ? (
                            <img src={logoPreview} alt="Logo" className="w-full h-full object-cover rounded-full p-2" />
                        ) : (
                            <>
                                <span className="material-symbols-outlined text-4xl text-white/50 group-hover:text-accent-primary transition-colors mb-2">upload_file</span>
                                <span className="text-xs text-white/50 uppercase tracking-widest font-bold group-hover:text-white transition-colors">Subir Insignia</span>
                            </>
                        )}
                        {!logoPreview && (
                            <div className="absolute inset-0 rounded-full border border-accent-primary/0 group-hover:border-accent-primary/50 scale-110 transition-all duration-500"></div>
                        )}
                    </div>
                </div>
                <p className="mt-6 text-sm text-text-muted text-center max-w-[200px]">
                    El emblema que representará tu organización en todo el sistema.
                </p>
            </div>

            {/* Right: Form */}
            <div className="flex-1 w-full max-w-md">
                <div className="mb-8">
                    <h2 className="text-3xl font-bold text-white mb-2">Fundación</h2>
                    <p className="text-text-muted">Establece la identidad legal y comercial de tu nuevo imperio.</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <TextInput
                        label="Nombre de la Organización"
                        icon="business"
                        placeholder="Ej. Corporación Stark"
                        {...register('companyName')}
                        error={errors.companyName?.message}
                        autoFocus
                    />

                    <TextInput
                        label="Identificador Legal (NIT/RUT)"
                        icon="badge"
                        placeholder="Ej. 900.123.456-7"
                        {...register('nitRut')}
                        error={errors.nitRut?.message}
                    />

                    <TextInput
                        label="Nombre del Fundador"
                        icon="person"
                        placeholder="Ej. Tony Stark"
                        {...register('ownerName')}
                        error={errors.ownerName?.message}
                    />

                    <TextInput
                        label="Teléfono de Contacto"
                        icon="call"
                        placeholder="Ej. +57 300 123 4567"
                        {...register('phone')}
                        error={errors.phone?.message}
                    />

                    <div className="pt-8">
                        <button
                            type="submit"
                            className="w-full bg-accent-primary hover:bg-orange-500 text-white font-bold py-4 px-8 rounded-xl shadow-[0_4px_20px_rgba(255,107,0,0.3)] hover:shadow-[0_4px_30px_rgba(255,107,0,0.5)] transition-all transform hover:-translate-y-1 flex items-center justify-center gap-3 group"
                        >
                            <span className="tracking-widest uppercase text-sm">Establecer Cimientos</span>
                            <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
