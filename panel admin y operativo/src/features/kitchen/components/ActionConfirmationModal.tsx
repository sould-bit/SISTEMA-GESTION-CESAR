import React from 'react';

interface ActionConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'warning' | 'info' | 'success';
    iconName?: string;
    children?: React.ReactNode;
}

export const ActionConfirmationModal: React.FC<ActionConfirmationModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    confirmText = 'Confirmar',
    cancelText = 'Cancelar',
    variant = 'danger',
    iconName,
    children
}) => {
    if (!isOpen) return null;

    // Defines styles based on variant
    const styles = {
        danger: {
            border: 'border-red-500/50',
            headerBorder: 'border-red-500/20',
            headerBg: 'bg-red-500/10',
            iconBg: 'bg-red-500/20',
            iconColor: 'text-red-500',
            buttonBg: 'bg-red-600 hover:bg-red-700 shadow-red-500/20',
            defaultIcon: 'delete_forever'
        },
        warning: {
            border: 'border-amber-500/50',
            headerBorder: 'border-amber-500/20',
            headerBg: 'bg-amber-500/10',
            iconBg: 'bg-amber-500/20',
            iconColor: 'text-amber-500',
            buttonBg: 'bg-amber-600 hover:bg-amber-700 shadow-amber-500/20',
            defaultIcon: 'warning'
        },
        info: {
            border: 'border-blue-500/50',
            headerBorder: 'border-blue-500/20',
            headerBg: 'bg-blue-500/10',
            iconBg: 'bg-blue-500/20',
            iconColor: 'text-blue-500',
            buttonBg: 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20',
            defaultIcon: 'info'
        },
        success: {
            border: 'border-emerald-500/50',
            headerBorder: 'border-emerald-500/20',
            headerBg: 'bg-emerald-500/10',
            iconBg: 'bg-emerald-500/20',
            iconColor: 'text-emerald-500',
            buttonBg: 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20',
            defaultIcon: 'check_circle'
        }
    };

    const currentStyle = styles[variant];
    const icon = iconName || currentStyle.defaultIcon;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[60] p-4 animate-in fade-in duration-200">
            <div className={`bg-card-dark border ${currentStyle.border} rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200`}>

                {/* Header */}
                <div className={`p-6 border-b ${currentStyle.headerBorder} ${currentStyle.headerBg}`}>
                    <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${currentStyle.iconBg} ${currentStyle.iconColor}`}>
                            <span className="material-symbols-outlined text-3xl">
                                {icon}
                            </span>
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white">
                                {title}
                            </h3>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 text-gray-300">
                    {children}
                </div>

                {/* Actions */}
                <div className="p-6 pt-0 flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 rounded-lg border border-border-dark text-gray-300 hover:bg-white/5 font-medium transition-colors"
                    >
                        {cancelText}
                    </button>
                    <button
                        onClick={() => {
                            onConfirm();
                            onClose();
                        }}
                        className={`px-6 py-2.5 rounded-lg text-white font-medium shadow-lg transition-colors flex items-center justify-center gap-2 ${currentStyle.buttonBg}`}
                    >
                        {variant !== 'info' && variant !== 'success' && (
                            <span className="material-symbols-outlined text-lg">{icon}</span>
                        )}
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};
