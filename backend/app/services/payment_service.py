
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.payment import PaymentCreate

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_payment(self, payment_data: PaymentCreate, user_id: int, company_id: int) -> Payment:
        """
        Registra un nuevo pago para una orden.
        Valida que la orden exista y pertenezca a la empresa.
        Actualiza el estado de la orden si se completa el pago.
        """
        try:
            # 1. Validar Orden
            stmt = select(Order).where(
                Order.id == payment_data.order_id,
                Order.company_id == company_id
            ).options(selectinload(Order.payments))
            
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Orden no encontrada o no pertenece a su empresa"
                )

            if order.status == OrderStatus.CANCELLED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pueden registrar pagos a una orden cancelada"
                )

            # 2. Validar Montos (Opcional - Evitar sobrepago masivo)
            total_paid = sum(p.amount for p in order.payments if p.status == PaymentStatus.COMPLETED)
            remaining = order.total - total_paid
            
            if payment_data.amount <= 0:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El monto del pago debe ser mayor a 0"
                )
            
            # (Opcional) Permitir propinas o deshabilitar sobrepago estricto
            # if payment_data.amount > remaining:
            #     # Podríamos aceptar y registrar como "CAMBIO" o rechazar
            #     pass

            # 3. Crear Pago
            new_payment = Payment(
                company_id=company_id,
                branch_id=order.branch_id,
                user_id=user_id,
                order_id=order.id,
                amount=payment_data.amount,
                method=payment_data.method,
                status=PaymentStatus.COMPLETED, # Asumimos OK si llega aquí por ahora
                transaction_id=payment_data.transaction_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_payment)
            
            # 4. Actualizar Estado de la Orden
            # Recalcular total pagado incluyendo el nuevo pago
            new_total_paid = total_paid + payment_data.amount
            
            if new_total_paid >= order.total:
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CONFIRMED
                    logger.info(f"✅ Orden {order.order_number} pagada totalmente. Estado -> CONFIRMED")
            
            await self.db.commit()
            await self.db.refresh(new_payment)
            
            return new_payment

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error procesando pago: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno procesando el pago"
            )

    async def get_order_payments(self, order_id: int, company_id: int) -> List[Payment]:
        """
        Obtiene el historial de pagos de una orden.
        """
        stmt = select(Payment).where(
            Payment.order_id == order_id,
            Payment.company_id == company_id
        ).order_by(Payment.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
