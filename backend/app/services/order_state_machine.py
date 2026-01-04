import logging
from typing import Optional, Set
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, update

from app.models.order import Order, OrderStatus
from app.models.order_audit import OrderAudit
from app.models.user import User

logger = logging.getLogger(__name__)

class OrderStateMachine:
    """
    Máquina de Estados Finita para Pedidos.
    Controla las transiciones permitidas y efectos secundarios.
    """

    # Definición Estricta del Grafo de Estados
    VALID_TRANSITIONS: dict[OrderStatus, Set[OrderStatus]] = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
        OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
        OrderStatus.READY: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.DELIVERED: set(),  # Estado terminal
        OrderStatus.CANCELLED: set(),  # Estado terminal (No reabrir)
    }

    # Definición de RBAC (Opción A: Seguridad Integrada)
    # Define qué roles pueden ejecutar qué transiciones.
    # Si la lista de roles es None o vacía, permitimos a todos (o restringimos todo, según política).
    # Aquí: None = Permitido para roles básicos (waiter/cashier/manager/admin)
    #       Lista explícita = Solo esos roles
    RBAC_RULES: dict[tuple[OrderStatus, OrderStatus], Set[str]] = {
        # Cancelar algo confirmado es delicado -> Solo Jefes
        (OrderStatus.CONFIRMED, OrderStatus.CANCELLED): {"manager", "admin"},
        (OrderStatus.PREPARING, OrderStatus.CANCELLED): {"manager", "admin"}, 
        # Entregar es tarea de meseros y repartidores (y jefes por supuesto)
        (OrderStatus.READY, OrderStatus.DELIVERED): {"waiter", "cashier", "manager", "admin"},
        # Cancelación simple (Pending -> Cancelled)
        (OrderStatus.PENDING, OrderStatus.CANCELLED): {"waiter", "cashier", "manager", "admin"},
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transition(
        self, 
        order: Order, 
        new_status: OrderStatus, 
        user: Optional[User] = None,
        meta: Optional[dict] = None
    ) -> bool:
        """
        Intenta realizar una transición de estado segura.
        
        Principios:
        1. Idempotencia: Si ya está en new_status, retorna True (sin cambios).
        2. Validación: Verifica si la transición es permitida por el grafo.
        3. Seguridad (RBAC): Verifica si el usuario tiene rol para esta acción.
        4. Bloqueo Optimista: Usa rowcount para asegurar atomicidad.
        5. Auditoría: Registra el cambio.
        
        Returns:
            bool: True si cambió, False si era idempotente.
        Raises:
            HTTPException 400: Transición inválida.
            HTTPException 403: No autorizado (RBAC).
            HTTPException 409: Conflicto de concurrencia.
        """
        old_status = order.status

        # 1. Idempotencia
        if old_status == new_status:
            logger.info(f"🔁 Transición idempotente para Orden {order.id}: {old_status} -> {new_status}")
            return False

        # 2. Validación de Grafo
        allowed = self.VALID_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            error_msg = f"Transición inválida: de '{old_status}' a '{new_status}' no es permitida."
            logger.warning(f"🚫 {error_msg} (Orden {order.id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 3. Seguridad (RBAC) - Opción A
        if user:
            # Buscar regla específica para esta transición
            required_roles = self.RBAC_RULES.get((old_status, new_status))
            
            # Si hay regla, validar. Si no hay regla específica, asumimos política por defecto (ej: permitir standard)
            # Para este caso, si no está definida, asumimos que es una operación estándar permitida para staff.
            # Pero para ser estrictos, si quisiéramos bloquear todo lo no definido:
            # if not required_roles: required_roles = {...default...}
            
            if required_roles:
                # Acceso robusto al rol:
                role_name = "guest"
                
                # Caso 1: User.role es un objeto ORM (Role model)
                if hasattr(user, "role") and user.role and not isinstance(user.role, str):
                     role_name = getattr(user.role, "code", getattr(user.role, "name", "guest")).lower()
                
                # Caso 2: User.role es un string (Mocking o estructura simple)
                elif hasattr(user, "role") and isinstance(user.role, str):
                    role_name = user.role.lower()

                if role_name not in required_roles:
                     logger.warning(f"🔒 Acceso Denegado: Usuario '{user.username}' ({role_name}) intentó {old_status}->{new_status}")
                     raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"No tiene permisos para cambiar el estado a {new_status}"
                     )

        # 4. Hooks Transaccionales (Hooks Pre-Commit)
        await self._run_transactional_hooks(order, new_status)

        try:
            # 5. Ejecución con Bloqueo Optimista
            stmt = (
                update(Order)
                .where(Order.id == order.id)
                .where(Order.status == old_status)
                .values(
                    status=new_status.value, 
                    updated_at=datetime.utcnow()
                )
            )
            
            result = await self.db.execute(stmt)
            
            if result.rowcount == 0:
                logger.warning(f"⚔️ Conflicto de Concurrencia en Orden {order.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El estado del pedido ha cambiado concurrentemente."
                )

            # 6. Auditoría
            old_val = old_status.value if hasattr(old_status, "value") else old_status
            new_val = new_status.value if hasattr(new_status, "value") else new_status
            
            audit_entry = OrderAudit(
                order_id=order.id,
                old_status=old_val,
                new_status=new_val,
                changed_by_user_id=user.id if user else None,
                meta=meta
            )
            self.db.add(audit_entry)
            
            # Commit de la transacción
            await self.db.commit()
            
            # Actualizar objeto en memoria
            order.status = new_status
            
            logger.info(f"✅ Estado Orden {order.id}: {old_status} -> {new_status}")
            
            return True

        except HTTPException:
            # Re-lanzar excepciones HTTP conocidas (400, 403, 409)
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error crítico en transición de estado: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al actualizar estado del pedido"
            )

    async def _run_transactional_hooks(self, order: Order, new_status: OrderStatus):
        """
        Ejecuta lógicas críticas que deben ocurrir DENTRO de la transacción DB.
        Ej: Descontar inventario al confirmar.
        """
        if new_status == OrderStatus.CONFIRMED:
            # Reservar stock, validar saldos, etc.
            pass
        elif new_status == OrderStatus.CANCELLED:
            # Liberar reservas si aplica
            pass

    async def _run_post_commit_hooks(self, order: Order, new_status: OrderStatus):
        """
        Ejecuta lógicas no críticas (fuego y olvido) DESPUÉS del commit.
        Ej: Enviar notificaciones, websockets, emails.
        """
        # TODO: Implementar envío de eventos (Ticket 7)
        pass
