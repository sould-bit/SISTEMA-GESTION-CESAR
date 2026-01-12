"""
🧾 Ticket Service - Orquestación de Tickets
============================================

Responsabilidad ÚNICA: Obtener datos y coordinar la generación de tickets.
Para modificar el DISEÑO del ticket → editar ticket_renderer.py

Autor: Sistema de Gestión César
"""

import io
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.services.ticket_renderer import TicketRenderer, TicketConfig

logger = logging.getLogger(__name__)


class TicketService:
    """
    Servicio de tickets - Solo maneja datos.
    
    Para cambiar el diseño visual:
    - Editar TicketRenderer en ticket_renderer.py
    - O pasar una TicketConfig personalizada
    
    # TODO: EVOLUCIÓN OPCIÓN B - WebSocket + Agente Local
    # =====================================================
    # async def send_to_printer(self, order_id: int, branch_id: int):
    #     from app.core.websockets import sio
    #     order_data = await self._get_order_data(order_id, company_id)
    #     await sio.emit("print_ticket", order_data, room=f"printer_{branch_id}")
    # =====================================================
    """
    
    def __init__(self, db: AsyncSession, config: TicketConfig = None):
        """
        Inicializa el servicio.
        
        Args:
            db: Sesión de base de datos
            config: Configuración de estilos (opcional, usa default si no se pasa)
        """
        self.db = db
        self.renderer = TicketRenderer(config)
    
    async def generate_ticket_pdf(self, order_id: int, company_id: int) -> io.BytesIO:
        """
        Genera un PDF de ticket de caja.
        
        Args:
            order_id: ID del pedido
            company_id: ID de la empresa (multi-tenant)
            
        Returns:
            BytesIO con el PDF
        """
        # 1. Obtener datos
        order_data = await self._get_order_data(order_id, company_id)
        if not order_data:
            raise ValueError(f"Pedido {order_id} no encontrado")
        
        # 2. Renderizar PDF
        return self.renderer.render_receipt(order_data)
    
    async def generate_kitchen_ticket_pdf(self, order_id: int, company_id: int) -> io.BytesIO:
        """
        Genera un PDF de comanda para cocina.
        
        Args:
            order_id: ID del pedido
            company_id: ID de la empresa (multi-tenant)
            
        Returns:
            BytesIO con el PDF
        """
        # 1. Obtener datos
        order_data = await self._get_order_data(order_id, company_id)
        if not order_data:
            raise ValueError(f"Pedido {order_id} no encontrado")
        
        # 2. Renderizar PDF
        return self.renderer.render_kitchen(order_data)
    
    # =========================================================================
    # MÉTODOS PRIVADOS - OBTENCIÓN DE DATOS
    # =========================================================================
    
    async def _get_order_data(self, order_id: int, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos del pedido en formato diccionario.
        
        Valida que el pedido pertenezca a la empresa (multi-tenant).
        """
        logger.info(f"🔍 Buscando Order: id={order_id}, company_id={company_id}")
        
        result = await self.db.execute(
            select(Order)
            .where(
                Order.id == order_id,
                Order.company_id == company_id
            )
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.company),
                selectinload(Order.branch)
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"❌ Pedido NO encontrado: id={order_id}, company_id={company_id}")
            return None
        
        logger.info(f"✅ Pedido encontrado: {order.order_number}")
        
        # Transformar a diccionario para el renderer
        return self._order_to_dict(order)
    
    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        """Convierte Order ORM a diccionario para el renderer."""
        return {
            "id": order.id,
            "order_number": order.order_number,
            "company_name": order.company.name if order.company else "Mi Restaurante",
            "branch_name": order.branch.name if order.branch else "",
            "delivery_type": order.delivery_type,
            "customer_notes": order.customer_notes,
            "created_at": order.created_at,
            "subtotal": float(order.subtotal) if order.subtotal else 0,
            "tax_total": float(order.tax_total) if order.tax_total else 0,
            "delivery_fee": float(order.delivery_fee) if order.delivery_fee else 0,
            "total": float(order.total) if order.total else 0,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else f"Item #{item.product_id}",
                    "quantity": float(item.quantity) if item.quantity else 1,
                    "unit_price": float(item.unit_price) if item.unit_price else 0,
                    "subtotal": float(item.subtotal) if item.subtotal else 0,
                    "notes": item.notes
                }
                for item in order.items
            ]
        }


# =============================================================================
# EVOLUCIÓN OPCIÓN B: WEBSOCKET + AGENTE
# =============================================================================
#
# Para activar impresión automática, agregar a esta clase:
#
# async def send_to_printer(self, order_id: int, company_id: int, branch_id: int):
#     """Envía ticket a impresora via WebSocket."""
#     from app.core.websockets import sio
#     
#     order_data = await self._get_order_data(order_id, company_id)
#     if not order_data:
#         raise ValueError(f"Pedido {order_id} no encontrado")
#     
#     await sio.emit("print_job", {
#         "type": "receipt",
#         "data": order_data
#     }, room=f"printer_{branch_id}_receipt")
#     
#     logger.info(f"🖨️ Ticket enviado a impresora: Branch {branch_id}")
#
#
# async def send_to_kitchen(self, order_id: int, company_id: int, branch_id: int):
#     """Envía comanda a cocina via WebSocket."""
#     from app.core.websockets import sio
#     
#     order_data = await self._get_order_data(order_id, company_id)
#     if not order_data:
#         raise ValueError(f"Pedido {order_id} no encontrado")
#     
#     await sio.emit("print_job", {
#         "type": "kitchen",
#         "data": order_data
#     }, room=f"printer_{branch_id}_kitchen")
#     
#     logger.info(f"🍳 Comanda enviada a cocina: Branch {branch_id}")
#
# =============================================================================
