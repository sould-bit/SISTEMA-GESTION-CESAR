import logging
from typing import Optional, Set
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, update

from app.models.order import Order, OrderStatus
from app.models.order_audit import OrderAudit
from app.models.user import User
from app.services.notification_service import NotificationService
from app.core.order_permissions import get_required_permission
from app.core.logging_config import log_security_event

# Evitar importaciones circulares: Importar servicios dentro de los métodos o con type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.inventory_service import InventoryService
    from app.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)


class OrderStateMachine:
    """
    Máquina de Estados Finita para Pedidos.
    Controla las transiciones permitidas y efectos secundarios.
    """

    # Definición Estricta del Grafo de Estados
    VALID_TRANSITIONS: dict[OrderStatus, Set[OrderStatus]] = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.PREPARING},
        OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
        OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
        OrderStatus.READY: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.DELIVERED: set(),  # Estado terminal
        OrderStatus.CANCELLED: set(),  # Estado terminal (No reabrir)
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

        # 3. Seguridad: Permisos (Permission-based RBAC)
        # Configurable desde Staff > Roles y Permisos, no roles hardcodeados.
        if user:
            required_perm = get_required_permission(old_status, new_status)
            if required_perm:
                from app.services.permission_service import PermissionService
                perm_service = PermissionService(self.db)
                has_perm = await perm_service.check_permission(
                    user_id=user.id,
                    permission_code=required_perm,
                    company_id=user.company_id
                )
                if not has_perm:
                    log_security_event(
                        event="ORDER_STATUS_DENIED",
                        user_id=user.id,
                        company_id=user.company_id,
                        details={
                            "order_id": order.id,
                            "old_status": str(old_status),
                            "new_status": str(new_status),
                            "required_permission": required_perm,
                        },
                        level="WARNING"
                    )
                    logger.warning(f"🔒 Acceso Denegado: Usuario '{user.username}' sin permiso '{required_perm}' para {old_status}->{new_status}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"No tiene permiso para cambiar el estado a {new_status} (requiere '{required_perm}')"
                    )

        # 4. Hooks Transaccionales (Hooks Pre-Commit)
        await self._run_transactional_hooks(order, new_status, user)

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

    async def _run_transactional_hooks(self, order: Order, new_status: OrderStatus, user: Optional[User] = None):
        """
        Ejecuta lógicas críticas que deben ocurrir DENTRO de la transacción DB.
        Ej: Descontar inventario al confirmar.
        """
        if new_status == OrderStatus.CONFIRMED:
            # Reservar stock, validar saldos, etc.
            pass
        elif new_status == OrderStatus.CANCELLED:
            # Restaurar stock si fue descontado previamente (Confirmed/Preparing/Ready)
            # Solo si el estado anterior era uno que descontó stock.
            # Según la lógica actual, CONFIRMED ya descuenta stock al crearse.
            # Por seguridad, restauramos si viene de cualquier estado activo.
            
            from app.services.inventory_service import InventoryService
            from app.services.recipe_service import RecipeService
            from app.models.modifier import ProductModifier
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from decimal import Decimal
            from collections import Counter

            # Asegurar que tenemos los items y sus productos cargados
            # El objeto 'order' ya debería tener items cargados por selectinload en transition()
            
            inv_service = InventoryService(self.db)
            recipe_service = RecipeService(self.db)
            
            for item in order.items:
                product = item.product
                if not product:
                    continue
                
                # 1. Restaurar stock de la receta o producto base
                recipe = await recipe_service.get_recipe_by_product(product.id, order.company_id)
                
                if recipe:
                    # Restaurar cada ingrediente de la receta
                    removed_ids = [str(x) for x in (item.removed_ingredients or [])]
                    for recipe_item in recipe.items:
                        # Ignorar si el ingrediente fue removido por el usuario
                        rec_ing_id = str(recipe_item.ingredient_id) if recipe_item.ingredient_id else str(recipe_item.ingredient_product_id)
                        if rec_ing_id in removed_ids:
                            continue
                            
                        qty_to_return = recipe_item.gross_quantity * Decimal(item.quantity)
                        
                        if recipe_item.ingredient_id:
                            await inv_service.restore_stock_to_batches(
                                branch_id=order.branch_id,
                                ingredient_id=recipe_item.ingredient_id,
                                quantity=qty_to_return,
                                user_id=user.id if user else None,
                                reason=f"Retorno por Cancelación (Orden {order.order_number})"
                            )
                        elif recipe_item.ingredient_product_id:
                            # Si la receta usa otro producto como ingrediente
                             await inv_service.update_stock(
                                branch_id=order.branch_id,
                                product_id=recipe_item.ingredient_product_id,
                                quantity_delta=qty_to_return,
                                transaction_type="IN",
                                user_id=user.id if user else None,
                                reference_id=f"ORDER-{order.order_number}",
                                reason=f"Retorno por Cancelación (Orden {order.order_number})"
                            )
                else:
                    # Si no tiene receta, devolver el producto directamente
                    await inv_service.update_stock(
                        branch_id=order.branch_id,
                        product_id=product.id,
                        quantity_delta=Decimal(item.quantity),
                        transaction_type="IN",
                        user_id=user.id if user else None,
                        reference_id=f"ORDER-{order.order_number}",
                        reason=f"Retorno por Cancelación (Orden {order.order_number})"
                    )

                # 2. Restaurar stock de los modificadores
                if item.modifiers:
                    for item_mod in item.modifiers:
                        mod_obj = item_mod.modifier # Cargado por selectinload
                        if not mod_obj: continue
                        
                        # Cada modificador puede tener sus propios recipe_items
                        total_mod_qty = Decimal(item_mod.quantity)
                        
                        for mod_recipe_item in mod_obj.recipe_items:
                            qty_needed_mod = mod_recipe_item.quantity * total_mod_qty
                            
                            if mod_recipe_item.ingredient_id:
                                await inv_service.restore_stock_to_batches(
                                    branch_id=order.branch_id,
                                    ingredient_id=mod_recipe_item.ingredient_id,
                                    quantity=qty_needed_mod,
                                    user_id=user.id if user else None,
                                    reason=f"Retorno Modificador {mod_obj.name} (Orden {order.order_number})"
                                )
                            elif mod_recipe_item.ingredient_product_id:
                                await inv_service.update_stock(
                                    branch_id=order.branch_id,
                                    product_id=mod_recipe_item.ingredient_product_id,
                                    quantity_delta=qty_needed_mod,
                                    transaction_type="IN",
                                    user_id=user.id if user else None,
                                    reference_id=f"ORDER-{order.order_number}",
                                    reason=f"Retorno Modificador {mod_obj.name} (Orden {order.order_number})"
                                )

    async def _run_post_commit_hooks(self, order: Order, new_status: OrderStatus):
        """
        Ejecuta lógicas no críticas (fuego y olvido) DESPUÉS del commit.
        Ej: Enviar notificaciones, websockets, emails.
        """
        try:
            # Notify Status Change
            await NotificationService.notify_order_status(
                order_id=order.id,
                status=new_status.value,
                company_id=order.company_id,
                branch_id=order.branch_id
            )
            # Also notify kitchen or other roles if specific transitions occur
            if new_status == OrderStatus.PREPARING:
                # Maybe notify kitchen that order is now preparing?
                pass
        except Exception as e:
            logger.error(f"⚠️ Error al enviar notificación WS (Status): {e}")
