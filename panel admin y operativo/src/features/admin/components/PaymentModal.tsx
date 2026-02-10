
import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Order } from '../types';
import { api } from '../../../lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface PaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    order: Order | null;
}

export const PaymentModal = ({ isOpen, onClose, order }: PaymentModalProps) => {
    const [method, setMethod] = useState<'cash' | 'card' | 'transfer' | 'nequi' | 'daviplata'>('cash');
    const [amount, setAmount] = useState<string>('');
    const queryClient = useQueryClient();

    const paymentMutation = useMutation({
        mutationFn: async (data: any) => {
            return await api.post('/payments/', data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['activeOrders'] });
            onClose();
            setAmount('');
        }
    });

    if (!order) return null;

    const totalPaid = order.payments?.reduce((acc, p) => acc + (p.status === 'completed' ? Number(p.amount) : 0), 0) || 0;
    const balance = order.total - totalPaid;

    const handleSetFullAmount = () => setAmount(balance.toString());

    return (
        <Transition show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-[60]" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-md" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-3xl bg-bg-dark border border-border-dark p-8 shadow-2xl transition-all">
                                <div className="text-center mb-8">
                                    <div className="w-16 h-16 bg-status-success/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-status-success/20">
                                        <span className="material-symbols-outlined text-status-success text-3xl">payments</span>
                                    </div>
                                    <Dialog.Title as="h3" className="text-2xl font-black text-white">
                                        Registrar Pago
                                    </Dialog.Title>
                                    <p className="text-text-muted mt-2">Pedido {order.order_number}</p>
                                </div>

                                <div className="bg-bg-deep rounded-2xl p-6 border border-border-dark mb-8">
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-text-muted font-bold uppercase tracking-widest">Saldo Pendiente</span>
                                        <button
                                            onClick={handleSetFullAmount}
                                            className="text-[10px] text-accent-primary hover:underline font-bold"
                                        >
                                            PAGAR TODO
                                        </button>
                                    </div>
                                    <div className="text-4xl font-black text-white">
                                        ${balance.toLocaleString()}
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div>
                                        <label className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3 block">Monto a Pagar</label>
                                        <div className="relative">
                                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted font-bold text-xl">$</span>
                                            <input
                                                type="number"
                                                value={amount}
                                                onChange={(e) => setAmount(e.target.value)}
                                                placeholder="0.00"
                                                className="w-full bg-bg-deep border border-border-dark focus:border-accent-primary rounded-xl py-4 pl-10 pr-4 text-white text-xl font-bold outline-none transition-all"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3 block">Método de Pago</label>
                                        <div className="grid grid-cols-3 gap-3">
                                            {[
                                                { id: 'cash', label: 'Efectivo', icon: 'payments' },
                                                { id: 'card', label: 'Tarjeta', icon: 'credit_card' },
                                                { id: 'nequi', label: 'Nequi', icon: 'smartphone' },
                                                { id: 'daviplata', label: 'Daviplata', icon: 'account_balance_wallet' },
                                                { id: 'transfer', label: 'Transf.', icon: 'sync_alt' },
                                            ].map((m) => (
                                                <button
                                                    key={m.id}
                                                    onClick={() => setMethod(m.id as any)}
                                                    className={`
                                                        flex flex-col items-center gap-2 p-3 rounded-xl border transition-all
                                                        ${method === m.id
                                                            ? 'bg-accent-primary border-accent-primary text-bg-deep font-bold shadow-lg scale-105'
                                                            : 'bg-bg-deep border-border-dark text-text-muted hover:border-text-muted hover:text-white'}
                                                    `}
                                                >
                                                    <span className="material-symbols-outlined text-[20px]">{m.icon}</span>
                                                    <span className="text-[10px] uppercase">{m.label}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex gap-4 pt-4">
                                        <button
                                            onClick={onClose}
                                            className="grow bg-bg-deep hover:bg-border-dark text-white font-bold py-4 rounded-2xl transition-all border border-border-dark"
                                        >
                                            Cancelar
                                        </button>
                                        <button
                                            disabled={!amount || Number(amount) <= 0 || paymentMutation.isPending}
                                            onClick={() => paymentMutation.mutate({
                                                order_id: order.id,
                                                amount: Number(amount),
                                                method: method,
                                                status: 'completed'
                                            })}
                                            className="grow-[2] bg-accent-primary hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-bg-deep font-black py-4 rounded-2xl transition-all shadow-xl shadow-accent-primary/20 flex items-center justify-center gap-2"
                                        >
                                            {paymentMutation.isPending ? (
                                                <span className="animate-spin material-symbols-outlined">sync</span>
                                            ) : (
                                                <span className="material-symbols-outlined">check_circle</span>
                                            )}
                                            CONFIRMAR PAGO
                                        </button>
                                    </div>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
};
