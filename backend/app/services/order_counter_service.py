"""
🔢 ORDER COUNTER SERVICE - Gestión de Números Consecutivos

Este servicio se encarga de generar números de pedido correlativos (001, 002, ...)
asegurando que no haya saltos ni duplicados incluso bajo alta concurrencia.

Utiliza 'SELECT FOR UPDATE' de SQL para bloquear la fila del contador
durante la transacción de creación del pedido.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import text

from app.models.order_counter import OrderCounter
import logging

logger = logging.getLogger(__name__)

class OrderCounterService:
    """
    🔢 Servicio de Contadores
    
    Proporciona lógica para incrementar valores secuenciales de forma segura.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_next_number(
        self, 
        company_id: int, 
        branch_id: int, 
        counter_type: str = "general"
    ) -> str:
        """
        Genera el siguiente número consecutivo para un pedido.
        
        Implementa bloqueo pesimista (Row-level locking) para evitar 
        que dos órdenes reciban el mismo número simultáneamente.
        """
        try:
            # 1. Buscar el contador con bloqueo (FOR UPDATE)
            # Nota: 'with_for_update' asegura que ninguna otra transacción
            # pueda leer/modificar esta fila hasta que hagamos commit/rollback.
            query = (
                select(OrderCounter)
                .where(
                    OrderCounter.company_id == company_id,
                    OrderCounter.branch_id == branch_id,
                    OrderCounter.counter_type == counter_type
                )
                .with_for_update()
            )
            
            result = await self.db.execute(query)
            counter = result.scalar_one_or_none()

            # 2. Si no existe, crearlo dinámicamente
            if not counter:
                logger.info(f"🆕 Creando nuevo contador '{counter_type}' para sucursal {branch_id}")
                counter = OrderCounter(
                    company_id=company_id,
                    branch_id=branch_id,
                    counter_type=counter_type,
                    last_value=0,
                    prefix=f"PED-" # Prefijo por defecto
                )
                self.db.add(counter)
                # Necesitamos flush para que el objeto sea rastreado antes de seguir
                await self.db.flush()

            # 3. Incrementar el valor
            counter.last_value += 1
            next_val = counter.last_value
            
            # 4. Formatear el número final (ej: PED-00001)
            prefix = counter.prefix or ""
            formatted_number = f"{prefix}{str(next_val).zfill(5)}"
            
            logger.debug(f"🔢 Generado número de pedido: {formatted_number}")
            
            return formatted_number

        except Exception as e:
            logger.error(f"❌ Error generando número consecutivo: {e}")
            raise
