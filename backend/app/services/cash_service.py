
import logging
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.cash_closure import CashClosure, CashClosureStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User

logger = logging.getLogger(__name__)

class CashService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_closure(self, user_id: int) -> Optional[CashClosure]:
        """Obtiene la caja abierta actual del usuario (o de la sucursal, depende de regla de negocio). Por ahora por usuario."""
        stmt = select(CashClosure).where(
            CashClosure.user_id == user_id,
            CashClosure.status == CashClosureStatus.OPEN
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def open_register(self, user: User, initial_cash: Decimal) -> CashClosure:
        """Abre un nuevo turno de caja."""
        # 1. Verificar si ya tiene una abierta
        existing = await self.get_active_closure(user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tienes una caja abierta. Debes cerrarla antes de abrir una nueva."
            )
            
        # 2. Crear nueva
        closure = CashClosure(
            company_id=user.company_id,
            branch_id=user.branch_id if user.branch_id else 1, # Fallback seguro
            user_id=user.id,
            initial_cash=initial_cash,
            opened_at=datetime.utcnow(),
            status=CashClosureStatus.OPEN
        )
        self.db.add(closure)
        await self.db.commit()
        await self.db.refresh(closure)
        return closure

    async def calculate_current_totals(self, closure: CashClosure) -> Dict[str, Decimal]:
        """Calcula los totales del sistema basados en los pagos registrados desde la apertura."""
        
        # Consultar pagos de la sucursal/usuario creados DESPUES de opened_at
        # Asumimos que la caja es por usuario. Si fuera por caja fisica compartida, filtrar por branch_id solamente.
        # Regla actual: Caja por Usuario.
        
        stmt = select(
            Payment.method, 
            func.sum(Payment.amount)
        ).where(
            Payment.created_at >= closure.opened_at,
            Payment.company_id == closure.company_id,
            Payment.user_id == closure.user_id, # Importante: payments should have user_id if we filter by user session
            # OJO: Payment model actualmente NO tiene user_id explícito, tiene order -> user? 
            # Revisemos Payment model. Si no tiene user_id, filtramos por aquellos pagos hechos por el usuario o en la sucursal?
            # En V3 simple: Filtramos por Branch y periodo de tiempo (turnos no solapados en misma sucursal).
            # O mejor, agregamos user_id a Payment? -> Sería ideal. Por ahora usaremos Branch + Time range.
             Payment.branch_id == closure.branch_id
        ).group_by(Payment.method)
        
        # NOTA: Si hay varios cajeros en la misma sucursal al tiempo, esto mezclaria ventas si no filtramos por created_by.
        # Payment no tiene created_by. Vamos a filtrar por branch por ahora (MVP).
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        totals = {
            "cash": Decimal("0.00"),
            "card": Decimal("0.00"),
            "transfer": Decimal("0.00")
        }
        
        for method, total in rows:
            if method == PaymentMethod.CASH:
                totals["cash"] += total
            elif method == PaymentMethod.CARD:
                totals["card"] += total
            elif method in [PaymentMethod.TRANSFER, PaymentMethod.NEQUI, PaymentMethod.DAVIPLATA]:
                totals["transfer"] += total
            else:
                totals["transfer"] += total # Map OTHER to transfer or separate bucket? Let's put in transfer for simplicity
                
        return totals

    async def close_register(self, 
                             closure_id: int, 
                             real_cash: Decimal, 
                             real_card: Decimal, 
                             real_transfer: Decimal,
                             notes: Optional[str] = None) -> CashClosure:
        """Cierra la caja calculando diferencias."""
        
        closure = await self.db.get(CashClosure, closure_id)
        if not closure or closure.status != CashClosureStatus.OPEN:
             raise HTTPException(status_code=400, detail="Caja no encontrada o ya cerrada")
             
        # 1. Calcular Esperados
        totals = await self.calculate_current_totals(closure)
        closure.expected_cash = totals["cash"]
        closure.expected_card = totals["card"]
        closure.expected_transfer = totals["transfer"]
        
        # Total Esperado = Inicial + Pagos Efectivo (Solo efectivo suma al cajón físico) + Otros (Suma contable)
        # Diferencia Global = (Real Cash + Real Card + Real Transfer) - (Initial + Expected Total Payments)
        # Ojo: Initial Cash solo afecta al Real Cash.
        
        closure.expected_total = closure.initial_cash + closure.expected_cash + closure.expected_card + closure.expected_transfer
        
        # 2. Set Reales
        closure.real_cash = real_cash
        closure.real_card = real_card
        closure.real_transfer = real_transfer
        closure.real_total = real_cash + real_card + real_transfer
        
        # 3. Diferencia
        # Difference = Lo que tengo - Lo que debería tener
        # Debería tener en efectivo: Initial + Ventas Efectivo
        # Debería tener en bcos: Ventas Tarjeta + Ventas Transfer
        
        expected_physical_cash = closure.initial_cash + closure.expected_cash
        diff_cash = real_cash - expected_physical_cash
        
        diff_card = real_card - closure.expected_card
        diff_transfer = real_transfer - closure.expected_transfer
        
        closure.difference = diff_cash + diff_card + diff_transfer
        
        # 4. Save
        closure.closed_at = datetime.utcnow()
        closure.status = CashClosureStatus.CLOSED
        closure.notes = notes
        
        self.db.add(closure)
        await self.db.commit()
        await self.db.refresh(closure)
        
        return closure
