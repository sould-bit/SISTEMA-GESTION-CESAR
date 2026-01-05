
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment_service import PaymentService
from app.auth_deps import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

def get_payment_service(session: AsyncSession = Depends(get_session)) -> PaymentService:
    return PaymentService(session)

@router.post("/", response_model=PaymentRead)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """
    Registra un nuevo pago para una orden.
    Puede ser parcial o total.
    """
    return await service.process_payment(
        payment_data=payment_data,
        user_id=current_user.id,
        company_id=current_user.company_id
    )

@router.get("/order/{order_id}", response_model=List[PaymentRead])
async def get_order_payments(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service)
):
    """
    Obtiene todos los pagos realizados a una orden específica.
    """
    return await service.get_order_payments(
        order_id=order_id,
        company_id=current_user.company_id
    )
