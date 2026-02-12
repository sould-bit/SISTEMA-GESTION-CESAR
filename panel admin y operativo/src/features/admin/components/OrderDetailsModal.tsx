import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Order, OrderStatus } from '../types';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { API_URL } from '../../../config/env';
import { useAppSelector } from '../../../stores/store';
import { useOrderPermissions } from '../../../hooks/useOrderPermissions';
import { api } from '../../../lib/api';
import { ConfirmModal } from '../../../components/ConfirmModal';
import { useMachine } from '@xstate/react';
import { orderWorkflowMachine } from '../orderWorkflow.machine';

interface OrderDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    order: Order | null;
    onStatusChange: (orderId: number, newStatus: OrderStatus) => void;
    onOpenPayment: (order: Order) => void;
    onAddItems?: (order: Order) => void;
    onOrderUpdated?: () => void;
}

export const OrderDetailsModal = ({ isOpen, onClose, order, onStatusChange, onOpenPayment, onAddItems, onOrderUpdated }: OrderDetailsModalProps) => {
    const { user, token } = useAppSelector((state) => state.auth);
    const permissions = user?.permissions ?? [];

    const {
        canCancel,
        canProcessCancellation,
        canRequestCancellation,
        canOpenPayment,
    } = useOrderPermissions();

    const [wfState, send] = useMachine(orderWorkflowMachine, {
        input: {
            orderId: order?.id || 0,
            status: order?.status || 'pending',
            permissions: permissions
        }
    });

    const [isCancelling, setIsCancelling] = useState(false);
    const [cancellationReason, setCancellationReason] = useState('');
    const [isSubmittingCancel, setIsSubmittingCancel] = useState(false);
    const [isDenying, setIsDenying] = useState(false);
    const [denialReason, setDenialReason] = useState('');
    const [confirmModal, setConfirmModal] = useState<{ message: string; onConfirm: () => Promise<void> } | null>(null);
    const [alertModal, setAlertModal] = useState<{ message: string } | null>(null);

    // Sync machine completion with UI refresh
    useEffect(() => {
        if (wfState.matches('idle') && onOrderUpdated) {
            onOrderUpdated();
        }
    }, [wfState.value, onOrderUpdated]);

    const handleRequestCancellation = async () => {
        if (cancellationReason.trim().length < 5) {
            setAlertModal({ message: "El motivo debe tener al menos 5 caracteres" });
            return;
        }
        if (!order) return;

        setIsSubmittingCancel(true);
        try {
            await api.post(`/orders/${order.id}/cancel-request`, { reason: cancellationReason });
            setIsCancelling(false);
            setCancellationReason('');
            if (onOrderUpdated) onOrderUpdated();
            onClose();
        } catch (error) {
            console.error('Error requesting cancellation:', error);
            setAlertModal({ message: 'Error al solicitar cancelación' });
        } finally {
            setIsSubmittingCancel(false);
        }
    };

    if (!order) return null;

    const totalPaid = order.payments?.reduce((acc: number, p: any) => acc + (p.status === 'completed' ? Number(p.amount) : 0), 0) || 0;
    const balance = order.total - totalPaid;

    const handlePrintKitchen = async () => {
        try {
            const response = await fetch(`${API_URL}/tickets/order/${order.id}/kitchen.pdf`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Error al generar comanda');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Open in new window for printing
            const printWindow = window.open(url, '_blank');
            if (printWindow) {
                printWindow.onload = () => {
                    printWindow.print();
                };
            }
        } catch (error) {
            console.error('Error printing:', error);
            setAlertModal({ message: 'Error al imprimir la comanda' });
        }
    };


    const handleApproveCancellationClick = () => {
        setConfirmModal({
            message: '¿Está seguro de aprobar la cancelación? Esta acción no se puede deshacer.',
            onConfirm: async () => {
                if (!order) return;
                setIsSubmittingCancel(true);
                try {
                    await api.post(`/orders/${order.id}/cancel-process`, { approved: true, notes: 'Aprobado manualmente' });
                    if (onOrderUpdated) onOrderUpdated();
                    onClose();
                } catch (error) {
                    console.error('Error approving cancellation:', error);
                    setAlertModal({ message: 'Error al aprobar la solicitud' });
                } finally {
                    setIsSubmittingCancel(false);
                }
            },
        });
    };

    const handleDenyCancellation = async () => {
        if (!order) return;

        setIsSubmittingCancel(true);
        try {
            await api.post(`/orders/${order.id}/cancel-process`, { approved: false, notes: denialReason });
            setIsDenying(false);
            setDenialReason('');
            if (onOrderUpdated) onOrderUpdated();
            setAlertModal({ message: 'Solicitud rechazada correctamente' });
            onClose();
        } catch (error) {
            console.error('Error denying cancellation:', error);
            setAlertModal({ message: 'Error al rechazar la solicitud' });
        } finally {
            setIsSubmittingCancel(false);
        }
    };

    if (!order) return null;

    return (
        <>
            <Transition show={isOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={onClose}>
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
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
                                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-bg-dark border border-border-dark p-6 text-left align-middle shadow-2xl transition-all">
                                    <div className="flex justify-between items-start border-b border-border-dark pb-4 mb-4">
                                        <div>
                                            <Dialog.Title as="h3" className="text-xl font-bold text-white flex items-center gap-3">
                                                Pedido {order.order_number}
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-accent-primary/10 text-accent-primary border border-accent-primary/20 uppercase tracking-wider">
                                                    {order.status}
                                                </span>
                                            </Dialog.Title>
                                            <p className="text-text-muted text-sm mt-1">
                                                {format(new Date(order.created_at), "eeee, d 'de' MMMM 'a las' HH:mm", { locale: es })}
                                            </p>
                                        </div>
                                        <button onClick={onClose} className="text-text-muted hover:text-white p-1">
                                            <span className="material-symbols-outlined">close</span>
                                        </button>
                                    </div>

                                    {order.cancellation_status === 'pending' && (
                                        <div className="mb-4 bg-status-warning/10 border border-status-warning/30 p-3 rounded-lg">
                                            <div className="flex flex-col md:flex-row items-start md:items-center gap-3 justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="material-symbols-outlined text-status-warning">pending</span>
                                                    <div>
                                                        <p className="text-status-warning font-bold text-sm">Solicitud de Cancelación Pendiente</p>
                                                        <p className="text-text-muted text-xs italic">Motivo: "{order.cancellation_reason}"</p>
                                                    </div>
                                                </div>

                                                {(canProcessCancellation) && !isDenying && (
                                                    <div className="flex gap-2 mt-2 md:mt-0">
                                                        <button
                                                            onClick={() => {
                                                                console.log('[DEBUG] Rechazar clicked. Current isDenying:', isDenying);
                                                                setIsDenying(true);
                                                            }}
                                                            disabled={isSubmittingCancel}
                                                            className="px-3 py-1.5 bg-status-alert/20 text-status-alert text-xs font-bold rounded hover:bg-status-alert/30 transition-colors border border-status-alert/30"
                                                        >
                                                            Rechazar
                                                        </button>
                                                        <button
                                                            onClick={handleApproveCancellationClick}
                                                            disabled={isSubmittingCancel}
                                                            className="px-3 py-1.5 bg-status-success text-bg-deep text-xs font-bold rounded hover:bg-status-success/90 transition-colors shadow-lg shadow-status-success/10"
                                                        >
                                                            Aprobar
                                                        </button>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Inline denial reason form - same UX as waiter cancellation */}
                                            {isDenying && canProcessCancellation && (
                                                <div className="mt-3 bg-bg-deep p-3 rounded-lg border border-status-alert/30 animate-in slide-in-from-top-2">
                                                    <label className="text-xs text-text-muted block mb-1">Motivo del rechazo:</label>
                                                    <textarea
                                                        className="w-full bg-card-dark border border-border-dark rounded-md p-2 text-sm text-white focus:border-status-alert outline-none"
                                                        rows={2}
                                                        placeholder="Ej: El pedido ya fue preparado, no se puede cancelar..."
                                                        value={denialReason}
                                                        onChange={(e) => setDenialReason(e.target.value)}
                                                        autoFocus
                                                    />
                                                    <div className="flex justify-end gap-2 mt-2">
                                                        <button
                                                            onClick={() => { setIsDenying(false); setDenialReason(''); }}
                                                            className="px-3 py-1.5 text-xs font-bold text-text-muted hover:text-white"
                                                            disabled={isSubmittingCancel}
                                                        >
                                                            Cancelar
                                                        </button>
                                                        <button
                                                            onClick={handleDenyCancellation}
                                                            disabled={denialReason.trim().length < 5 || isSubmittingCancel}
                                                            className="px-3 py-1.5 text-xs font-bold bg-status-alert text-white rounded hover:bg-status-alert/80 disabled:opacity-50"
                                                            title={denialReason.trim().length < 5 ? 'Mínimo 5 caracteres' : ''}
                                                        >
                                                            {isSubmittingCancel ? 'Enviando...' : 'Confirmar Rechazo'}
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Cancellation DENIED banner - show to everyone, especially waiter */}
                                    {order.cancellation_status === 'denied' && (
                                        <div className="mb-4 bg-status-alert/10 border border-status-alert/30 p-3 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <span className="material-symbols-outlined text-status-alert">block</span>
                                                <div>
                                                    <p className="text-status-alert font-bold text-sm">Cancelación Rechazada</p>
                                                    <p className="text-text-muted text-xs mt-1">
                                                        <span className="text-gray-400">Solicitud:</span> "{order.cancellation_reason}"
                                                    </p>
                                                    <p className="text-status-alert/80 text-xs font-medium mt-1">
                                                        <span className="text-gray-400">Motivo del rechazo:</span> "{order.cancellation_denied_reason || 'Sin motivo especificado'}"
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div className="md:col-span-2">
                                            <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3">Productos</h4>
                                            <div className="bg-bg-deep rounded-xl border border-border-dark overflow-hidden">
                                                <table className="w-full text-sm">
                                                    <thead className="bg-card-dark text-text-muted">
                                                        <tr>
                                                            <th className="px-4 py-2 text-left font-medium">Cant</th>
                                                            <th className="px-4 py-2 text-left font-medium">Producto</th>
                                                            <th className="px-4 py-2 text-right font-medium">Total</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-border-dark">
                                                        {order.items.map((item) => (
                                                            <tr key={item.id} className="text-gray-200">
                                                                <td className="px-4 py-3 font-mono text-accent-primary">{item.quantity}</td>
                                                                <td className="px-4 py-3">
                                                                    <div className="font-medium">{item.product_name}</div>

                                                                    {/* Removed Ingredients */}
                                                                    {item.removed_ingredients && item.removed_ingredients.length > 0 && (
                                                                        <div className="flex flex-wrap gap-1 mt-1">
                                                                            {item.removed_ingredients.map((ing, i) => (
                                                                                <span key={`rem-${i}`} className="text-[9px] font-bold text-status-alert bg-status-alert/10 px-1.5 py-0.5 rounded border border-status-alert/20 uppercase">
                                                                                    SIN {ing}
                                                                                </span>
                                                                            ))}
                                                                        </div>
                                                                    )}

                                                                    {/* Modifiers */}
                                                                    {item.modifiers && item.modifiers.length > 0 && (
                                                                        <div className="mt-1 space-y-0.5">
                                                                            {item.modifiers.map((mod, i) => (
                                                                                <div key={`mod-${i}`} className="text-[10px] text-accent-secondary font-medium">
                                                                                    + {mod.modifier?.name || 'Extra'}
                                                                                    {Number(mod.unit_price) > 0 && ` ($${Number(mod.unit_price).toLocaleString()})`}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}

                                                                    {/* Notes */}
                                                                    {item.notes && (
                                                                        <div className="mt-1 flex items-start gap-1">
                                                                            <span className="material-symbols-outlined text-[10px] text-text-muted mt-0.5">sticky_note_2</span>
                                                                            <p className="text-[10px] text-text-muted italic">"{item.notes}"</p>
                                                                        </div>
                                                                    )}
                                                                </td>
                                                                <td className="px-4 py-3 text-right font-mono">${Number(item.subtotal).toLocaleString()}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>

                                            {order.customer_notes && (
                                                <div className="mt-4 p-3 bg-accent-alert/5 border border-accent-alert/10 rounded-lg">
                                                    <h5 className="text-[10px] font-bold text-accent-alert uppercase mb-1">Notas Especiales</h5>
                                                    <p className="text-xs text-gray-300 italic">"{order.customer_notes}"</p>
                                                </div>
                                            )}
                                        </div>

                                        <div className="space-y-6">
                                            <div>
                                                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3">Información</h4>
                                                <div className="space-y-3">
                                                    <div className="p-3 bg-bg-deep rounded-lg border border-border-dark">
                                                        <p className="text-[10px] text-text-muted uppercase mb-1">Tipo / Mesa</p>
                                                        <p className="text-sm font-bold text-white">
                                                            {order.table_id ? `Mesa ${order.table_id}` : (order.delivery_type === 'takeaway' ? 'Para Llevar' : 'Domicilio')}
                                                        </p>
                                                    </div>
                                                    <div className="p-3 bg-bg-deep rounded-lg border border-border-dark">
                                                        <p className="text-[10px] text-text-muted uppercase mb-1">Atendido por</p>
                                                        <p className="text-sm font-bold text-white">{order.created_by_name || 'Desconocido'}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div>
                                                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3">Resumen de Pago</h4>
                                                <div className="bg-bg-deep rounded-lg border border-border-dark p-4 space-y-2">
                                                    <div className="flex justify-between text-xs text-text-muted">
                                                        <span>Total</span>
                                                        <span>${Number(order.total).toLocaleString()}</span>
                                                    </div>
                                                    <div className="flex justify-between text-xs text-status-success">
                                                        <span>Pagado</span>
                                                        <span>${totalPaid.toLocaleString()}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-border-dark">
                                                        <span>Habe</span>
                                                        <span className={balance > 0 ? 'text-status-alert' : 'text-status-success'}>
                                                            ${balance.toLocaleString()}
                                                        </span>
                                                    </div>
                                                </div>

                                                {balance > 0 && canOpenPayment && (
                                                    <button
                                                        onClick={() => onOpenPayment(order)}
                                                        className="w-full mt-4 bg-status-success hover:bg-status-success/90 text-bg-deep font-bold py-2 rounded-lg transition-all flex items-center justify-center gap-2"
                                                    >
                                                        <span className="material-symbols-outlined">payments</span>
                                                        Registrar Pago
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-8 pt-4 border-t border-border-dark flex flex-wrap gap-3">
                                        {canCancel && order.status !== 'delivered' && order.status !== 'cancelled' && (
                                            <button
                                                onClick={() => onStatusChange(order.id, 'cancelled')}
                                                className="px-4 py-2 text-sm font-medium text-status-alert hover:bg-status-alert/10 rounded-lg transition-colors"
                                            >
                                                Cancelar Pedido
                                            </button>
                                        )}

                                        {/* Waiter Cancellation Request Button */}
                                        {canRequestCancellation && order.status !== 'delivered' && order.status !== 'cancelled' && order.cancellation_status !== 'pending' && !isCancelling && (
                                            <button
                                                onClick={() => setIsCancelling(true)}
                                                className="px-4 py-2 text-sm font-medium text-status-warning hover:bg-status-warning/10 rounded-lg transition-colors border border-status-warning/30"
                                            >
                                                Solicitar Cancelación
                                            </button>
                                        )}

                                        {/* Cancellation Logic Form */}
                                        {isCancelling && (
                                            <div className="w-full bg-bg-deep p-3 rounded-lg border border-border-dark mb-2 animate-in slide-in-from-top-2">
                                                <label className="text-xs text-text-muted block mb-1">Motivo de cancelación:</label>
                                                <textarea
                                                    className="w-full bg-card-dark border border-border-dark rounded-md p-2 text-sm text-white focus:border-accent-primary outline-none"
                                                    rows={2}
                                                    placeholder="Cliente se retiró, pedido duplicado, etc..."
                                                    value={cancellationReason}
                                                    onChange={(e) => setCancellationReason(e.target.value)}
                                                />
                                                <div className="flex justify-end gap-2 mt-2">
                                                    <button
                                                        onClick={() => setIsCancelling(false)}
                                                        className="px-3 py-1.5 text-xs font-bold text-text-muted hover:text-white"
                                                        disabled={isSubmittingCancel}
                                                    >
                                                        Cancelar
                                                    </button>
                                                    <button
                                                        onClick={handleRequestCancellation}
                                                        disabled={cancellationReason.trim().length < 5 || isSubmittingCancel}
                                                        className="px-3 py-1.5 text-xs font-bold bg-status-warning text-bg-deep rounded hover:bg-status-warning/80 disabled:opacity-50"
                                                        title={cancellationReason.trim().length < 5 ? "Mínimo 5 caracteres" : ""}
                                                    >
                                                        {isSubmittingCancel ? 'Enviando...' : 'Confirmar Solicitud'}
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                        <div className="flex-grow" />

                                        {onAddItems && order.status !== 'delivered' && order.status !== 'cancelled' && (
                                            <button
                                                onClick={() => onAddItems(order)}
                                                className="px-6 py-2 bg-accent-primary/10 hover:bg-accent-primary/20 text-accent-primary text-sm font-bold rounded-lg transition-colors flex items-center gap-2 border border-accent-primary/20"
                                            >
                                                <span className="material-symbols-outlined text-sm">add_shopping_cart</span>
                                                Agregar Productos
                                            </button>
                                        )}

                                        {/* Print Kitchen Command */}
                                        {order.status !== 'cancelled' && (
                                            <button
                                                onClick={handlePrintKitchen}
                                                className="px-4 py-2 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 text-sm font-bold rounded-lg transition-colors flex items-center gap-2 border border-blue-600/20"
                                                title="Imprimir comanda para cocina"
                                            >
                                                <span className="material-symbols-outlined text-sm">print</span>
                                                Comanda
                                            </button>
                                        )}

                                        {/* Workflow Status Buttons controlled by XState */}
                                        {wfState.can({ type: 'ACCEPT' }) && (
                                            <button
                                                onClick={() => send({ type: 'ACCEPT' })}
                                                disabled={wfState.matches('updating')}
                                                className="px-6 py-2 bg-status-warning text-bg-deep text-sm font-bold rounded-lg transition-colors flex items-center gap-2 hover:brightness-110 shadow-lg shadow-status-warning/20 disabled:opacity-50"
                                            >
                                                <span className="material-symbols-outlined text-sm font-bold">restaurant</span>
                                                Aceptar y Preparar
                                            </button>
                                        )}

                                        {wfState.can({ type: 'MARK_READY' }) && (
                                            <button
                                                onClick={() => send({ type: 'MARK_READY' })}
                                                disabled={wfState.matches('updating')}
                                                className="px-6 py-2 bg-status-success text-bg-deep text-sm font-bold rounded-lg transition-colors flex items-center gap-2 hover:brightness-110 shadow-lg shadow-status-success/20 disabled:opacity-50"
                                            >
                                                <span className="material-symbols-outlined text-sm font-bold">notifications_active</span>
                                                Ya está Listo
                                            </button>
                                        )}

                                        {wfState.can({ type: 'DELIVER' }) && (
                                            <button
                                                onClick={() => send({ type: 'DELIVER' })}
                                                disabled={wfState.matches('updating')}
                                                className="px-6 py-2 bg-accent-primary text-bg-deep text-sm font-bold rounded-lg transition-colors flex items-center gap-2 hover:brightness-110 shadow-lg shadow-accent-primary/20 disabled:opacity-50"
                                            >
                                                <span className="material-symbols-outlined text-sm font-bold">local_shipping</span>
                                                Despachar / Entregar
                                            </button>
                                        )}

                                        {order.status === 'delivered' && balance > 0 && canOpenPayment && (
                                            <button
                                                onClick={() => onOpenPayment(order)}
                                                className="px-6 py-2 bg-status-success text-bg-deep text-sm font-bold rounded-lg transition-colors flex items-center gap-2 hover:brightness-110 shadow-lg shadow-status-success/20"
                                            >
                                                <span className="material-symbols-outlined text-sm font-bold">payments</span>
                                                Cobrar Mesa
                                            </button>
                                        )}

                                        <button
                                            type="button"
                                            className="px-6 py-2 bg-border-dark hover:bg-border-dark/80 text-white text-sm font-bold rounded-lg transition-colors"
                                            onClick={onClose}
                                        >
                                            Cerrar
                                        </button>
                                    </div>
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </Dialog>
            </Transition>

            {/* Confirmación (reemplaza window.confirm) */}
            {confirmModal && (
                <ConfirmModal
                    isOpen={!!confirmModal}
                    onClose={() => setConfirmModal(null)}
                    title="Confirmar acción"
                    message={confirmModal.message}
                    confirmText="Aceptar"
                    cancelText="Cancelar"
                    onConfirm={confirmModal.onConfirm}
                />
            )}

            {/* Alertas (reemplaza window.alert) */}
            {alertModal && (
                <ConfirmModal
                    isOpen={!!alertModal}
                    onClose={() => setAlertModal(null)}
                    message={alertModal.message}
                    confirmText="Entendido"
                    variant="alert"
                />
            )}
        </>
    );
};
