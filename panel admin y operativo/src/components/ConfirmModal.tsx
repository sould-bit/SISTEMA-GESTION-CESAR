/**
 * Modal de confirmación personalizado.
 * Reemplaza window.confirm() y window.alert() para evitar el título "localhost says".
 * Usa branding de la app (FastOps) y estilos coherentes.
 */

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';

export interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm?: (value?: string) => void | Promise<void>;
    variant?: 'confirm' | 'alert' | 'danger';
}

const APP_NAME = 'FastOps Manager';

export const ConfirmModal = ({
    isOpen,
    onClose,
    title = APP_NAME,
    message,
    confirmText = 'Aceptar',
    cancelText = 'Cancelar',
    onConfirm,
    variant = 'confirm',
}: ConfirmModalProps) => {
    const isAlert = variant === 'alert' || !onConfirm;
    const isDanger = variant === 'danger';

    const handleConfirm = async () => {
        if (onConfirm) await onConfirm();
        onClose();
    };

    const confirmBtnClass = isDanger
        ? 'bg-status-alert hover:bg-status-alert/90 text-white'
        : 'bg-accent-primary hover:bg-accent-primary/90 text-bg-dark';

    return (
        <Transition show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-[60]" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-200"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-150"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 flex items-center justify-center p-4">
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-200"
                        enterFrom="opacity-0 scale-95"
                        enterTo="opacity-100 scale-100"
                        leave="ease-in duration-150"
                        leaveFrom="opacity-100 scale-100"
                        leaveTo="opacity-0 scale-95"
                    >
                        <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-bg-dark border border-border-dark p-6 shadow-2xl">
                            <Dialog.Title as="h3" className="text-lg font-bold text-white mb-1" id="confirm-modal-title">
                                {title}
                            </Dialog.Title>
                            <p className="text-text-muted text-sm leading-relaxed mb-6">{message}</p>

                            <div className="flex gap-3 justify-end">
                                {!isAlert && (
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="px-4 py-2 text-sm font-medium text-text-muted hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                    >
                                        {cancelText}
                                    </button>
                                )}
                                <button
                                    type="button"
                                    onClick={handleConfirm}
                                    disabled={false}
                                    className={`px-4 py-2 text-sm font-bold rounded-lg transition-colors disabled:opacity-50 ${confirmBtnClass}`}
                                >
                                    {confirmText}
                                </button>
                            </div>
                        </Dialog.Panel>
                    </Transition.Child>
                </div>
            </Dialog>
        </Transition>
    );
};
