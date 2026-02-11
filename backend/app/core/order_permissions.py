"""
🔐 Mapeo de Permisos para Transiciones de Pedidos

Módulo centralizado que define qué permiso se requiere para cada transición
de estado en la máquina de estados de pedidos. Permite escalabilidad y
configuración desde Staff > Roles y Permisos sin hardcodear roles.

Constantes:
    PERMISSION_ORDER_UPDATE: Actualizar pedidos (aceptar, preparar, marcar listo, entregar)
    PERMISSION_ORDER_CANCEL: Cancelar pedidos
    PERMISSION_ORDER_MANAGE: Gestionar cancelaciones críticas (preparing/ready)

Convención: Se usa orders.update para flujo normal (aceptar → cocina → listo → entregar)
y orders.cancel para cancelaciones. orders.manage_all para operaciones especiales.
"""

from typing import Optional
from app.models.order import OrderStatus

# Códigos de permisos estándar (deben existir en BD)
PERMISSION_ORDER_UPDATE = "orders.update"
PERMISSION_ORDER_CANCEL = "orders.cancel"
PERMISSION_ORDER_MANAGE = "orders.manage_all"


def get_required_permission(old_status: OrderStatus, new_status: OrderStatus) -> Optional[str]:
    """
    Obtiene el permiso requerido para una transición de estado.

    Args:
        old_status: Estado actual del pedido
        new_status: Estado destino

    Returns:
        Código del permiso requerido, o None si no hay restricción.
        En producción, todas las transiciones definidas requieren permiso.
    """
    transition = (old_status, new_status)

    # Cancelaciones: 
    if new_status == OrderStatus.CANCELLED:
        # Permitir cancelar pedidos PENDING solo con orders.update (meseros lo tienen)
        if old_status == OrderStatus.PENDING:
            return PERMISSION_ORDER_UPDATE
        # Otros estados requieren permiso explícito de cancelación
        return PERMISSION_ORDER_CANCEL

    # Flujo de preparación y entrega: orders.update
    # PENDING/CONFIRMED -> PREPARING (Aceptar y Preparar)
    # PREPARING -> READY (Ya está Listo)
    # READY -> DELIVERED (Despachar/Entregar)
    # READY -> PREPARING (Revertir)
    update_transitions = {
        (OrderStatus.PENDING, OrderStatus.CONFIRMED),
        (OrderStatus.PENDING, OrderStatus.PREPARING),
        (OrderStatus.CONFIRMED, OrderStatus.PREPARING),
        (OrderStatus.PREPARING, OrderStatus.READY),
        (OrderStatus.READY, OrderStatus.DELIVERED),
        (OrderStatus.READY, OrderStatus.PREPARING),
    }

    if transition in update_transitions:
        return PERMISSION_ORDER_UPDATE

    return PERMISSION_ORDER_UPDATE  # Fallback seguro
