/**
 * Hook centralizado para permisos de pedidos.
 *
 * Reemplaza checks por rol (isAdmin, isCashier, etc.) con checks por permiso.
 * Configurable desde Staff > Roles y Permisos.
 *
 * Permisos usados:
 *   - orders.update: Aceptar pedidos, enviar a cocina, marcar listo
 *   - orders.cancel: Cancelar pedidos
 *   - orders.manage_all: Gestionar cancelaciones críticas
 */

import { useAppSelector } from '../stores/store';

/** Códigos de permiso estándar (alineados con backend) */
export const PERMISSION_ORDER_UPDATE = 'orders.update';
export const PERMISSION_ORDER_CANCEL = 'orders.cancel';
export const PERMISSION_ORDER_MANAGE = 'orders.manage_all';
export const PERMISSION_CASH_CLOSE = 'cash.close';

export function useOrderPermissions() {
  const user = useAppSelector((state) => state.auth.user);
  const permissions = user?.permissions ?? [];

  const has = (code: string) => permissions.includes(code);

  const canProcessCancellation = has(PERMISSION_ORDER_MANAGE) || has(PERMISSION_ORDER_CANCEL);

  return {
    /** Puede aceptar pedidos y enviarlos a cocina (PENDING → PREPARING) */
    canAcceptOrder: has(PERMISSION_ORDER_UPDATE),
    /** Puede marcar pedido como listo (PREPARING → READY) */
    canMarkReady: has(PERMISSION_ORDER_UPDATE),
    /** Puede despachar/entregar (READY → DELIVERED) */
    canDeliver: has(PERMISSION_ORDER_UPDATE),
    /** Puede cancelar pedidos directamente */
    canCancel: has(PERMISSION_ORDER_CANCEL),
    /** Puede aprobar/rechazar solicitudes de cancelación */
    canProcessCancellation,
    /** Puede solicitar cancelación (no aprobar) - p.ej. mesero */
    canRequestCancellation: has(PERMISSION_ORDER_UPDATE) && !canProcessCancellation,
    /** Puede registrar pagos / cobrar mesa */
    canOpenPayment: has(PERMISSION_CASH_CLOSE),
    /** Verificación genérica de permiso */
    has,
  };
}
