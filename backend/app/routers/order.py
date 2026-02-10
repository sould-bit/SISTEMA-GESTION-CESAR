from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_session
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderRead, OrderUpdateStatus, OrderItemCreate, OrderItemUpdate, OrderCancelRequest, OrderCancelProcess
from app.models.user import User
from app.auth_deps import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[OrderRead])
async def get_orders(
    branch_id: int | None = None,
    # Accept status as comma separated string or list
    status: str | None = None,
    delivery_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Listar pedidos de la compañía actual.
    Filtros opcionales: branch_id, status (comma separated).
    """
    service = OrderService(db)
    
    status_list = None
    if status:
        # Convert comma separated string to list of enums
        from app.models.order import OrderStatus
        try:
            status_list = [OrderStatus(s.strip()) for s in status.split(',')]
        except ValueError:
            pass

    return await service.get_orders(
        company_id=current_user.company_id,
        branch_id=branch_id,
        statuses=status_list,
        delivery_type=delivery_type,
        limit=limit,
        offset=offset
    )

@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Crear un nuevo pedido.
    Requiere autenticación activa.
    El pedido se asocia a la compañía del usuario.
    """
    service = OrderService(db)
    # Validar que el usuario tenga acceso a la sucursal indicada? 
    # Por ahora confiamos en que el frontend envía la sucursal correcta 
    # y el backend valida company_id del usuario vs productos/branch si implementamos esa validación.
    # En OrderService validamos que los productos sean de company_id.
    
    return await service.create_order(order_data, current_user.company_id, current_user.id)

@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los detalles de un pedido.
    """
    service = OrderService(session)
    return await service.get_order(order_id, current_user.company_id)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    status_update: OrderUpdateStatus,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza el estado de un pedido siguiendo la máquina de estados.
    """
    service = OrderService(session)
    return await service.update_status(
        order_id=order_id,
        new_status=status_update.status,
        company_id=current_user.company_id,
        user=current_user
    )

@router.get("/active/table/{table_id}", response_model=OrderRead)
async def get_active_order_by_table(
    table_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el pedido activo de una mesa específica.
    """
    service = OrderService(db)
    order = await service.get_active_order_by_table(table_id, current_user.company_id)
    if not order:
        raise HTTPException(status_code=404, detail="No hay pedido activo para esta mesa")
    return order

@router.post("/{order_id}/items", response_model=OrderRead)
async def add_items_to_order(
    order_id: int,
    items: List[OrderItemCreate],
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Agrega items a un pedido existente.
    """
    service = OrderService(db)
    return await service.add_items_to_order(
        order_id=order_id,
        items_data=items,
        company_id=current_user.company_id,
        user_id=current_user.id
    )

@router.patch("/{order_id}/items/{item_id}", response_model=OrderRead)
async def update_order_item(
    order_id: int,
    item_id: int,
    item_update: OrderItemUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza un item del pedido (cantidad, notas, modificadores).
    """
    service = OrderService(db)
    # Convert pydantic to dict, exclude None to avoid overwriting with None
    update_data = item_update.model_dump(exclude_unset=True)
    
    return await service.update_order_item(
        order_id=order_id,
        item_id=item_id,
        update_data=update_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )

@router.delete("/{order_id}/items/{item_id}", response_model=OrderRead)
async def remove_order_item(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un item del pedido y restaura el stock.
    """
    service = OrderService(db)
    return await service.remove_order_item(
        order_id=order_id,
        item_id=item_id,
        company_id=current_user.company_id,
        user_id=current_user.id
    )

@router.post("/{order_id}/cancel-request", response_model=OrderRead)
async def request_order_cancellation(
    order_id: int,
    cancel_data: OrderCancelRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Solicita la cancelación de un pedido.
    """
    service = OrderService(db)
    return await service.request_cancellation(
        order_id=order_id,
        reason=cancel_data.reason,
        company_id=current_user.company_id,
        user=current_user
    )

@router.post("/{order_id}/cancel-process", response_model=OrderRead)
async def process_order_cancellation(
    order_id: int,
    process_data: OrderCancelProcess,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Aprueba o deniega una solicitud de cancelación.
    """
    service = OrderService(db)
    return await service.process_cancellation_approval(
        order_id=order_id,
        approved=process_data.approved,
        notes=process_data.notes,
        company_id=current_user.company_id,
        user=current_user
    )
