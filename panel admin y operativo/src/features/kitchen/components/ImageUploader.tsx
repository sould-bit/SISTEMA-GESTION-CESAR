import { useState, useRef, useCallback } from 'react';
import { kitchenService } from '../kitchen.service';

interface ImageUploaderProps {
    currentImageUrl?: string;
    onImageUploaded: (url: string) => void;
    onError?: (error: string) => void;
    label?: string;
    className?: string;
}

export const ImageUploader = ({
    currentImageUrl,
    onImageUploaded,
    onError,
    label = 'Imagen del Producto',
    className = ''
}: ImageUploaderProps) => {
    const [uploading, setUploading] = useState(false);
    const [preview, setPreview] = useState<string | null>(currentImageUrl || null);
    const [dragActive, setDragActive] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleUpload = useCallback(async (file: File) => {
        console.log('🖼️ [ImageUploader] handleUpload called');
        console.log('🖼️ [ImageUploader] File received:', {
            name: file.name,
            type: file.type,
            size: `${(file.size / 1024).toFixed(2)} KB`
        });

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            console.error('❌ [ImageUploader] Invalid file type:', file.type);
            onError?.('Formato no permitido. Use JPG, PNG, WEBP o GIF');
            return;
        }

        // Validate file size (max 5MB)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            console.error('❌ [ImageUploader] File too large:', file.size);
            onError?.('La imagen es muy grande. Máximo 5MB');
            return;
        }

        console.log('🖼️ [ImageUploader] Validation passed, starting upload...');
        setUploading(true);
        try {
            // Create local preview immediately
            const localPreview = URL.createObjectURL(file);
            setPreview(localPreview);
            console.log('🖼️ [ImageUploader] Local preview created');

            // Upload to server
            console.log('🖼️ [ImageUploader] Calling kitchenService.uploadImage...');
            const imageUrl = await kitchenService.uploadImage(file);
            console.log('✅ [ImageUploader] Upload successful! URL:', imageUrl);

            onImageUploaded(imageUrl);
            console.log('✅ [ImageUploader] onImageUploaded callback called with:', imageUrl);

            // Update preview with server URL
            setPreview(imageUrl);
        } catch (error: any) {
            console.error('❌ [ImageUploader] Upload failed:', error);
            onError?.(error.message || 'Error al subir imagen');
            setPreview(currentImageUrl || null);
        } finally {
            setUploading(false);
            console.log('🖼️ [ImageUploader] Upload process finished');
        }
    }, [currentImageUrl, onImageUploaded, onError]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            handleUpload(file);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const file = e.dataTransfer.files?.[0];
        if (file) {
            handleUpload(file);
        }
    };

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleRemove = () => {
        setPreview(null);
        onImageUploaded('');
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <div className={`space-y-2 ${className}`}>
            <label className="block text-sm font-medium text-gray-300">
                {label}
            </label>

            <div
                onClick={handleClick}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`
                    relative group cursor-pointer
                    border-2 border-dashed rounded-xl
                    transition-all duration-300
                    ${dragActive
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-border-dark hover:border-purple-500/50 bg-card-darker'
                    }
                    ${uploading ? 'pointer-events-none opacity-70' : ''}
                `}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                    onChange={handleFileChange}
                    className="hidden"
                />

                {preview ? (
                    // Preview Mode
                    <div className="relative aspect-video overflow-hidden rounded-xl">
                        <img
                            src={preview.startsWith('blob:') ? preview : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${preview}`}
                            alt="Preview"
                            className="w-full h-full object-cover"
                        />

                        {/* Overlay on hover */}
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-4">
                            <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); handleClick(); }}
                                className="p-3 bg-white/20 backdrop-blur-sm rounded-full hover:bg-white/30 transition-colors"
                            >
                                <span className="material-symbols-outlined text-white">edit</span>
                            </button>
                            <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); handleRemove(); }}
                                className="p-3 bg-red-500/50 backdrop-blur-sm rounded-full hover:bg-red-500/70 transition-colors"
                            >
                                <span className="material-symbols-outlined text-white">delete</span>
                            </button>
                        </div>
                    </div>
                ) : (
                    // Upload Mode
                    <div className="aspect-video flex flex-col items-center justify-center p-8">
                        {uploading ? (
                            <>
                                <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                                <span className="text-gray-400">Subiendo imagen...</span>
                            </>
                        ) : (
                            <>
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined text-3xl text-purple-400">add_photo_alternate</span>
                                </div>
                                <p className="text-gray-300 font-medium mb-1">
                                    Arrastra una imagen o haz clic
                                </p>
                                <p className="text-gray-500 text-sm">
                                    JPG, PNG, WEBP • Máx. 5MB
                                </p>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
