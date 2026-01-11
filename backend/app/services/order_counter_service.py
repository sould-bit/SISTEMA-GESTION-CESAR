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
        order_type: str = "dine_in"
    ) -> str:
        """
        Genera el siguiente número consecutivo para un pedido.
        
        Implementa bloqueo pesimista (Row-level locking) para evitar 
        que dos órdenes reciban el mismo número simultáneamente.
        
        Args:
            company_id: ID de la empresa
            branch_id: ID de la sucursal
            order_type: Tipo de pedido - "dine_in", "takeaway", "delivery"
        
        Returns:
            Número formateado con prefijo según tipo:
            - M-00001 (Mesa/dine_in)
            - L-00001 (Llevar/takeaway)
            - D-00001 (Domicilio/delivery)
        """
        # Mapeo de tipo de pedido a prefijo y counter_type
        prefix_map = {
            "dine_in": "M-",    # Mesa
            "takeaway": "L-",   # Llevar
            "delivery": "D-",   # Domicilio
        }
        
        prefix = prefix_map.get(order_type, "P-")  # P- como fallback
        counter_type = f"order_{order_type}"
        
        try:
            # 1. Buscar el contador con bloqueo (FOR UPDATE)
            query = (
                select(OrderCounter)
                .where(
                    OrderCounter.company_id == company_id,
                    OrderCounter.branch_id == branch_id,
                    OrderCounter.counter_type == counter_type
                )
            )

            # Bloqueo pesimista solo si no es SQLite
            if self.db.bind.dialect.name != "sqlite":
                 query = query.with_for_update()
            
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
                    prefix=prefix
                )
                self.db.add(counter)
                await self.db.flush()

            # 3. Incrementar el valor
            counter.last_value += 1
            next_val = counter.last_value
            
            # 4. Formatear el número final (ej: M-00001)
            formatted_number = f"{prefix}{str(next_val).zfill(5)}"
            
            logger.debug(f"🔢 Generado número de pedido: {formatted_number}")
            
            return formatted_number

        except Exception as e:
            logger.error(f"❌ Error generando número consecutivo: {e}")
            raise
