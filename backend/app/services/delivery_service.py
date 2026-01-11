"""
Delivery Service (Servicio de Domiciliarios)
=============================================
Lógica de negocio para gestión de entregas y domiciliarios.

Responsabilidades:
- Listar domiciliarios disponibles
- Asignar domiciliario a pedido
- Marcar pedido como recogido/entregado
- Gestión de turnos

Depende de:
- Order model (pedidos)
- User model (domiciliarios son usuarios con rol "Domiciliario")
- DeliveryShift model (turnos)
"""

import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.order import Order, OrderStatus
from app.models.user import User
from app.models.delivery_shift import DeliveryShift
from app.models.payment import Payment, PaymentMethod

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Servicio para gestión de domiciliarios y entregas.
    
    Patrón: Instance-based (recibe db en constructor)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # DOMICILIARIOS DISPONIBLES
    # =========================================================================
    
    async def get_available_drivers(
        self, 
        company_id: int, 
        branch_id: Optional[int] = None
    ) -> List[User]:
        """
        Lista los domiciliarios disponibles para asignar pedidos.
        
        Un domiciliario está disponible si:
        - Tiene rol "Domiciliario"
        - Está activo
        - Tiene un turno activo (opcional, según config)
        
        Returns:
            Lista de usuarios con rol domiciliario
        """
        # Buscar usuarios con rol Domiciliario
        query = (
            select(User)
            .options(selectinload(User.role))
            .where(
                User.company_id == company_id,
                User.is_active == True
            )
        )
        
        # Si se especifica sucursal, filtrar
        if branch_id:
            query = query.where(User.branch_id == branch_id)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Filtrar por rol "Domiciliario"
        drivers = [u for u in users if u.role and u.role.name.lower() == "domiciliario"]
        
        logger.info(f"📦 Encontrados {len(drivers)} domiciliarios para company {company_id}")
        return drivers
    
    async def count_active_orders_for_driver(self, driver_id: int) -> int:
        """Cuenta cuántos pedidos activos tiene un domiciliario."""
        result = await self.db.execute(
            select(func.count(Order.id))
            .where(
                Order.delivery_person_id == driver_id,
                Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY])
            )
        )
        return result.scalar() or 0
    
    # =========================================================================
    # ASIGNACIÓN DE DOMICILIARIO
    # =========================================================================
    
    async def assign_driver(
        self,
        order_id: int,
        driver_id: int,
        company_id: int,
        assigned_by_user_id: Optional[int] = None
    ) -> Order:
        """
        Asigna un domiciliario a un pedido.
        
        Validaciones:
        - El pedido debe existir y pertenecer a la empresa
        - El pedido debe ser de tipo 'delivery'
        - El pedido debe estar en estado READY (listo para recoger)
        - El domiciliario debe existir y estar activo
        
        Args:
            order_id: ID del pedido
            driver_id: ID del usuario domiciliario
            company_id: ID de la empresa (multi-tenant)
            assigned_by_user_id: Quién hizo la asignación (auditoría)
        
        Returns:
            Order actualizado
        """
        # 1. Buscar pedido
        order = await self.db.get(Order, order_id)
        if not order or order.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado"
            )
        
        # 2. Validar tipo delivery
        if order.delivery_type != "delivery":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden asignar domiciliarios a pedidos tipo 'delivery'"
            )
        
        # 3. Validar estado (debe estar READY)
        if order.status != OrderStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pedido debe estar en estado 'READY', actualmente está en '{order.status.value}'"
            )
        
        # 4. Validar domiciliario
        driver = await self.db.get(User, driver_id)
        if not driver or driver.company_id != company_id or not driver.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domiciliario no encontrado o inactivo"
            )
        
        # 5. Asignar
        order.delivery_person_id = driver_id
        order.assigned_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"✅ Pedido {order.order_number} asignado a {driver.full_name}")
        return order
    
    # =========================================================================
    # TRACKING DE ENTREGA
    # =========================================================================
    
    async def mark_picked_up(
        self,
        order_id: int,
        driver_id: int,
        company_id: int
    ) -> Order:
        """
        Marca un pedido como recogido por el domiciliario.
        
        Solo el domiciliario asignado puede marcar como recogido.
        """
        order = await self._get_order_for_driver(order_id, driver_id, company_id)
        
        # Validar estado
        if order.status != OrderStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El pedido debe estar en estado 'READY' para recoger"
            )
        
        # Marcar como recogido
        order.picked_up_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"📦 Pedido {order.order_number} recogido por domiciliario")
        return order
    
    async def mark_delivered(
        self,
        order_id: int,
        driver_id: int,
        company_id: int
    ) -> Order:
        """
        Marca un pedido como entregado.
        
        Cambia el estado a DELIVERED y registra el timestamp.
        Solo el domiciliario asignado puede marcar como entregado.
        """
        order = await self._get_order_for_driver(order_id, driver_id, company_id)
        
        # Validar que ya fue recogido
        if not order.picked_up_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe marcar el pedido como 'recogido' antes de entregarlo"
            )
        
        # Cambiar estado a DELIVERED
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(order)
        
        logger.info(f"✅ Pedido {order.order_number} ENTREGADO")
        return order
    
    async def get_driver_orders(
        self,
        driver_id: int,
        company_id: int,
        only_active: bool = True
    ) -> List[Order]:
        """
        Lista los pedidos asignados a un domiciliario.
        
        Args:
            driver_id: ID del domiciliario
            company_id: ID de la empresa
            only_active: Si True, solo muestra pedidos no entregados
        
        Returns:
            Lista de pedidos
        """
        query = select(Order).where(
            Order.company_id == company_id,
            Order.delivery_person_id == driver_id
        )
        
        if only_active:
            query = query.where(
                Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY])
            )
        
        query = query.order_by(Order.assigned_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================
    
    async def _get_order_for_driver(
        self,
        order_id: int,
        driver_id: int,
        company_id: int
    ) -> Order:
        """Helper para obtener un pedido validando que pertenece al domiciliario."""
        order = await self.db.get(Order, order_id)
        
        if not order or order.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado"
            )
        
        if order.delivery_person_id != driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este pedido no está asignado a usted"
            )
        
        return order
    
    # =========================================================================
    # GESTIÓN DE TURNOS
    # =========================================================================
    
    async def start_shift(
        self,
        driver_id: int,
        company_id: int,
        branch_id: int
    ) -> DeliveryShift:
        """
        Inicia un turno para el domiciliario.
        
        Un domiciliario solo puede tener un turno activo a la vez.
        
        Args:
            driver_id: ID del domiciliario
            company_id: ID de la empresa
            branch_id: ID de la sucursal
        
        Returns:
            DeliveryShift creado
        """
        # Verificar que no tenga turno activo
        existing_shift = await self.get_active_shift(driver_id, company_id)
        if existing_shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tiene un turno activo. Debe cerrar el turno actual primero."
            )
        
        # Crear nuevo turno
        shift = DeliveryShift(
            company_id=company_id,
            branch_id=branch_id,
            delivery_person_id=driver_id,
            started_at=datetime.utcnow(),
            status="active"
        )
        
        self.db.add(shift)
        await self.db.commit()
        await self.db.refresh(shift)
        
        logger.info(f"🟢 Turno iniciado para domiciliario {driver_id}")
        return shift
    
    async def get_active_shift(
        self,
        driver_id: int,
        company_id: int
    ) -> Optional[DeliveryShift]:
        """Obtiene el turno activo del domiciliario, si existe."""
        result = await self.db.execute(
            select(DeliveryShift)
            .where(
                DeliveryShift.company_id == company_id,
                DeliveryShift.delivery_person_id == driver_id,
                DeliveryShift.status == "active"
            )
        )
        return result.scalar_one_or_none()
    
    async def end_shift(
        self,
        shift_id: int,
        driver_id: int,
        company_id: int,
        cash_collected: Decimal,
        notes: Optional[str] = None
    ) -> DeliveryShift:
        """
        Cierra el turno del domiciliario con cuadre de caja.
        
        Calcula:
        - Total de pedidos entregados
        - Total de ventas
        - Efectivo esperado (pedidos pagados en efectivo)
        - Diferencia con lo reportado
        
        Args:
            shift_id: ID del turno a cerrar
            driver_id: ID del domiciliario (validación)
            company_id: ID de la empresa
            cash_collected: Efectivo que el domiciliario entrega
            notes: Notas opcionales
        
        Returns:
            DeliveryShift actualizado con resumen
        """
        # 1. Obtener turno
        shift = await self.db.get(DeliveryShift, shift_id)
        if not shift or shift.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado"
            )
        
        if shift.delivery_person_id != driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este turno no le pertenece"
            )
        
        if shift.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turno ya está cerrado"
            )
        
        # 2. Calcular estadísticas del turno
        # Pedidos entregados durante este turno
        delivered_orders = await self.db.execute(
            select(Order)
            .options(selectinload(Order.payments))
            .where(
                Order.delivery_person_id == driver_id,
                Order.delivered_at >= shift.started_at,
                Order.status == OrderStatus.DELIVERED
            )
        )
        orders = delivered_orders.scalars().all()
        
        total_delivered = len(orders)
        total_earnings = sum(o.total for o in orders)
        
        # Calcular efectivo esperado (solo pedidos pagados en efectivo)
        expected_cash = Decimal("0.00")
        for order in orders:
            for payment in order.payments:
                if payment.method == PaymentMethod.CASH:
                    expected_cash += payment.amount
        
        # 3. Actualizar turno
        shift.ended_at = datetime.utcnow()
        shift.total_delivered = total_delivered
        shift.total_earnings = total_earnings
        shift.expected_cash = expected_cash
        shift.cash_collected = cash_collected
        shift.closing_notes = notes
        shift.status = "closed"
        
        await self.db.commit()
        await self.db.refresh(shift)
        
        difference = cash_collected - expected_cash
        logger.info(
            f"🔴 Turno cerrado: {total_delivered} entregas, "
            f"Esperado: ${expected_cash}, Recibido: ${cash_collected}, "
            f"Diferencia: ${difference}"
        )
        
        return shift
    
    async def get_shift_history(
        self,
        driver_id: int,
        company_id: int,
        limit: int = 10
    ) -> List[DeliveryShift]:
        """Obtiene el historial de turnos del domiciliario."""
        result = await self.db.execute(
            select(DeliveryShift)
            .where(
                DeliveryShift.company_id == company_id,
                DeliveryShift.delivery_person_id == driver_id
            )
            .order_by(DeliveryShift.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
