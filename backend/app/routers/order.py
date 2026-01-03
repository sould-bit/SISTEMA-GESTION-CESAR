from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_session
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderRead, OrderUpdateStatus
from app.models.user import User
from app.auth_deps import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
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
    
    return await service.create_order(order_data, current_user.company_id)

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
