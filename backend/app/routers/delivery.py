"""
Delivery Router (API de Domiciliarios)
======================================
Endpoints para gestión de entregas y domiciliarios.

Endpoints públicos para cajeros:
- GET  /delivery/available        - Listar domiciliarios
- POST /orders/{id}/assign-delivery - Asignar domiciliario

Endpoints para domiciliarios:
- GET  /delivery/my-orders        - Mis pedidos
- POST /delivery/orders/{id}/picked-up - Marcar recogido
- POST /delivery/orders/{id}/delivered - Confirmar entrega
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.delivery_service import DeliveryService
from app.schemas.delivery import (
    AssignDriverRequest,
    CloseShiftRequest,
    DriverRead,
    DeliveryOrderRead,
    DeliveryOrderList,
    AssignmentResponse,
    DeliveryStatusUpdate,
    ShiftSummary
)

router = APIRouter(prefix="/delivery", tags=["Delivery"])


# =============================================================================
# ENDPOINTS PARA CAJEROS / ADMINISTRADORES
# =============================================================================

@router.get("/available", response_model=List[DriverRead])
async def list_available_drivers(
    branch_id: int = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los domiciliarios disponibles para asignar.
    
    Permisos: Cajero, Administrador
    """
    delivery_service = DeliveryService(db)
    
    drivers = await delivery_service.get_available_drivers(
        company_id=current_user.company_id,
        branch_id=branch_id
    )
    
    # Enriquecer con conteo de pedidos activos
    result = []
    for driver in drivers:
        active_count = await delivery_service.count_active_orders_for_driver(driver.id)
        result.append(DriverRead(
            id=driver.id,
            full_name=driver.full_name,
            username=driver.username,
            is_available=active_count == 0,
            active_orders_count=active_count
        ))
    
    return result


@router.post("/orders/{order_id}/assign", response_model=AssignmentResponse)
async def assign_driver_to_order(
    order_id: int,
    request: AssignDriverRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Asigna un domiciliario a un pedido.
    
    Reglas:
    - El pedido debe ser tipo 'delivery'
    - El pedido debe estar en estado 'READY'
    - El domiciliario debe existir y estar activo
    
    Permisos: Cajero, Administrador
    """
    delivery_service = DeliveryService(db)
    
    order = await delivery_service.assign_driver(
        order_id=order_id,
        driver_id=request.driver_id,
        company_id=current_user.company_id,
        assigned_by_user_id=current_user.id
    )
    
    # Obtener nombre del driver para respuesta
    driver = await db.get(User, request.driver_id)
    
    return AssignmentResponse(
        message="Domiciliario asignado exitosamente",
        order_id=order.id,
        driver_id=request.driver_id,
        driver_name=driver.full_name if driver else "Desconocido",
        assigned_at=order.assigned_at or datetime.utcnow()
    )


# =============================================================================
# ENDPOINTS PARA DOMICILIARIOS
# =============================================================================

@router.get("/my-orders", response_model=DeliveryOrderList)
async def get_my_orders(
    only_active: bool = True,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los pedidos asignados al domiciliario actual.
    
    Args:
        only_active: Si True (default), solo muestra pedidos pendientes de entrega
    
    Permisos: Domiciliario
    """
    delivery_service = DeliveryService(db)
    
    orders = await delivery_service.get_driver_orders(
        driver_id=current_user.id,
        company_id=current_user.company_id,
        only_active=only_active
    )
    
    # Convertir a schema de respuesta
    orders_read = []
    for order in orders:
        orders_read.append(DeliveryOrderRead(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer.full_name if order.customer else None,
            customer_phone=order.customer.phone if order.customer else None,
            delivery_address=order.delivery_address or "",
            delivery_notes=order.delivery_notes,
            status=order.status.value,
            total=order.total,
            delivery_fee=order.delivery_fee,
            created_at=order.created_at,
            assigned_at=order.assigned_at,
            picked_up_at=order.picked_up_at
        ))
    
    return DeliveryOrderList(
        orders=orders_read,
        total_count=len(orders_read)
    )


@router.post("/orders/{order_id}/picked-up", response_model=DeliveryStatusUpdate)
async def mark_order_picked_up(
    order_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca un pedido como recogido.
    
    El domiciliario indica que ya recogió el pedido del local
    y va en camino al cliente.
    
    Permisos: Solo el domiciliario asignado
    """
    delivery_service = DeliveryService(db)
    
    order = await delivery_service.mark_picked_up(
        order_id=order_id,
        driver_id=current_user.id,
        company_id=current_user.company_id
    )
    
    return DeliveryStatusUpdate(
        message="Pedido marcado como recogido",
        order_id=order.id,
        order_number=order.order_number,
        new_status="picked_up",
        timestamp=order.picked_up_at or datetime.utcnow()
    )


@router.post("/orders/{order_id}/delivered", response_model=DeliveryStatusUpdate)
async def mark_order_delivered(
    order_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Marca un pedido como entregado.
    
    El domiciliario confirma que entregó el pedido al cliente.
    Esto cambia el estado del pedido a 'DELIVERED'.
    
    Permisos: Solo el domiciliario asignado
    """
    delivery_service = DeliveryService(db)
    
    order = await delivery_service.mark_delivered(
        order_id=order_id,
        driver_id=current_user.id,
        company_id=current_user.company_id
    )
    
    return DeliveryStatusUpdate(
        message="Pedido entregado exitosamente",
        order_id=order.id,
        order_number=order.order_number,
        new_status=order.status.value,
        timestamp=order.delivered_at or datetime.utcnow()
    )


# =============================================================================
# ENDPOINTS DE TURNOS
# =============================================================================

@router.post("/shift/start", response_model=ShiftSummary)
async def start_shift(
    branch_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia un turno de trabajo para el domiciliario.
    
    Un domiciliario solo puede tener un turno activo.
    
    Permisos: Domiciliario
    """
    delivery_service = DeliveryService(db)
    
    shift = await delivery_service.start_shift(
        driver_id=current_user.id,
        company_id=current_user.company_id,
        branch_id=branch_id
    )
    
    return ShiftSummary(
        id=shift.id,
        driver_name=current_user.full_name,
        total_orders=0,
        total_delivered=0,
        total_earnings=shift.total_earnings,
        expected_cash=shift.expected_cash,
        cash_collected=shift.cash_collected,
        difference=shift.difference,
        status=shift.status,
        started_at=shift.started_at,
        ended_at=shift.ended_at
    )


@router.get("/shift/current", response_model=ShiftSummary)
async def get_current_shift(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el turno activo del domiciliario.
    
    Permisos: Domiciliario
    """
    delivery_service = DeliveryService(db)
    
    shift = await delivery_service.get_active_shift(
        driver_id=current_user.id,
        company_id=current_user.company_id
    )
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tiene un turno activo"
        )
    
    return ShiftSummary(
        id=shift.id,
        driver_name=current_user.full_name,
        total_orders=shift.total_orders,
        total_delivered=shift.total_delivered,
        total_earnings=shift.total_earnings,
        expected_cash=shift.expected_cash,
        cash_collected=shift.cash_collected,
        difference=shift.difference,
        status=shift.status,
        started_at=shift.started_at,
        ended_at=shift.ended_at
    )


@router.post("/shift/close", response_model=ShiftSummary)
async def close_shift(
    request: CloseShiftRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cierra el turno activo con cuadre de caja.
    
    El domiciliario reporta el efectivo recaudado.
    El sistema calcula el esperado y muestra la diferencia.
    
    Permisos: Domiciliario
    """
    delivery_service = DeliveryService(db)
    
    # Primero obtener turno activo
    active_shift = await delivery_service.get_active_shift(
        driver_id=current_user.id,
        company_id=current_user.company_id
    )
    
    if not active_shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tiene un turno activo para cerrar"
        )
    
    shift = await delivery_service.end_shift(
        shift_id=active_shift.id,
        driver_id=current_user.id,
        company_id=current_user.company_id,
        cash_collected=request.cash_collected,
        notes=request.notes
    )
    
    return ShiftSummary(
        id=shift.id,
        driver_name=current_user.full_name,
        total_orders=shift.total_orders,
        total_delivered=shift.total_delivered,
        total_earnings=shift.total_earnings,
        expected_cash=shift.expected_cash,
        cash_collected=shift.cash_collected,
        difference=shift.difference,
        status=shift.status,
        started_at=shift.started_at,
        ended_at=shift.ended_at
    )


@router.get("/shift/history", response_model=List[ShiftSummary])
async def get_shift_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Historial de turnos del domiciliario.
    
    Permisos: Domiciliario
    """
    delivery_service = DeliveryService(db)
    
    shifts = await delivery_service.get_shift_history(
        driver_id=current_user.id,
        company_id=current_user.company_id,
        limit=limit
    )
    
    return [
        ShiftSummary(
            id=s.id,
            driver_name=current_user.full_name,
            total_orders=s.total_orders,
            total_delivered=s.total_delivered,
            total_earnings=s.total_earnings,
            expected_cash=s.expected_cash,
            cash_collected=s.cash_collected,
            difference=s.difference,
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at
        )
        for s in shifts
    ]
