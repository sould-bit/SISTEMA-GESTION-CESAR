import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from sqlmodel import col

from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.services.order_counter_service import OrderCounterService
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderRead, OrderItemRead, PaymentRead
from app.services.print_service import PrintService
from app.services.inventory_service import InventoryService
from app.services.recipe_service import RecipeService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.counter_service = OrderCounterService(db)
        self.print_service = PrintService(db)

    async def create_order(self, order_data: OrderCreate, company_id: int, user_id: int) -> OrderRead:
        """
        Crea un nuevo pedido con validación de stock y precios actuales.
        Genera número de orden secuencial seguro.
        """
        try:
            # 1. Obtener IDs de productos solicitados
            product_dict = {item.product_id: item for item in order_data.items}
            product_ids = list(product_dict.keys())
            
            product_ids = list(product_dict.keys())
            
            logger.error(f"DEBUG: create_order params - company_id type: {type(company_id)}, user_id type: {type(user_id)}")
            logger.error(f"DEBUG: company_id value: {company_id}, user_id value: {user_id}")
            
            # 2. Consultar productos en DB (para obtener precio real y validar stock/existencia)
            stmt = select(Product).where(
                col(Product.id).in_(product_ids),
                Product.company_id == company_id,
                Product.is_active == True
            )
            result = await self.db.execute(stmt)
            products = result.scalars().all()
            
            # Validar que todos los productos existan y sean de la empresa
            if len(products) != len(product_ids):
                found_ids = {p.id for p in products}
                missing = set(product_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Productos no válidos o inactivos: {missing}"
                )
            
            # Map products by ID for easy access
            db_products = {p.id: p for p in products}
            
            # 3. Calcular totales y construir items
            order_items: List[OrderItem] = []
            subtotal = Decimal("0.00")
            tax_total = Decimal("0.00")
            
            for pid, user_item in product_dict.items():
                product = db_products[pid]
                
                # TODO: Validar stock disponible aquí si Product tiene manejo de inventario estricto
                
                # Usamos el precio del producto en DB como base de seguridad
                unit_price = product.price
                quantity = user_item.quantity
                
                # Calcular montos
                line_subtotal = unit_price * quantity
                # Asumimos tax incluido o cero por ahora, o usamos product.tax_rate si existiera
                # En modelo anterior Product tiene tax_rate, usémoslo si existe
                product_tax_rate = getattr(product, 'tax_rate', Decimal("0.00")) or Decimal("0.00")
                line_tax = line_subtotal * product_tax_rate
                
                # Crear Item
                item = OrderItem(
                    product_id=pid,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=line_subtotal,
                    tax_amount=line_tax,
                    notes=user_item.notes
                )
                order_items.append(item)
                
                subtotal += line_subtotal
                tax_total += line_tax
            
            total = subtotal + tax_total

            # 4. Obtener Número de Orden Secuencial
            print(f"DEBUG: Getting Order Number for Branch {order_data.branch_id}")
            # order_number = await self.counter_service.get_next_number(
            #     company_id=company_id, 
            #     branch_id=order_data.branch_id,
            #     counter_type="general" 
            # )
            order_number = "TEST-123"
            print(f"DEBUG: Order Number {order_number} obtained")

            # 5. Inventory & Stock Management integration
            inventory_service = InventoryService(self.db)
            recipe_service = RecipeService(self.db)
            
            # Re-iterate items to process stock deduction
            # NOTE: We do this before creating the Order in DB to ensure stock exists (if we enforce it)
            # or we could do it after. Doing it here allows failing early.
            
            for pid, user_item in product_dict.items():
                product = db_products[pid]
                quantity = user_item.quantity
                
                # Check for Recipe
                recipe = await recipe_service.get_recipe_by_product(pid, company_id)
                
                if recipe:
                    # Deduct Ingredients
                    for recipe_item in recipe.items:
                        qty_needed = recipe_item.quantity * quantity
                        await inventory_service.update_stock(
                            branch_id=order_data.branch_id,
                            product_id=recipe_item.ingredient_product_id,
                            quantity_delta=-qty_needed,
                            transaction_type="SALE",
                            user_id=user_id,
                            reference_id=f"ORDER-{order_number}",
                            reason=f"Sale of {product.name} (Recipe)"
                        )
                else:
                    # Deduct Product Directly (Simple Product like Soda)
                    await inventory_service.update_stock(
                        branch_id=order_data.branch_id,
                        product_id=pid,
                        quantity_delta=-quantity,

                        transaction_type="SALE",
                        user_id=user_id,
                        reference_id=f"ORDER-{order_number}",
                        reason=f"Sale of {product.name}"
                    )

            # 6. Crear la Orden (Cabecera)
            new_order = Order(
                company_id=company_id,
                branch_id=order_data.branch_id,
                order_number=order_number,
                status=OrderStatus.PENDING,
                subtotal=subtotal,
                tax_total=tax_total,
                total=total,
                customer_notes=order_data.customer_notes
            )
            
            # Asociar items
            new_order.items = order_items
            
            # 8. Procesar Pagos Iniciales (si existen)
            if order_data.payments:
                for pay_data in order_data.payments:
                    payment = Payment(
                        amount=pay_data.amount,
                        method=pay_data.method,
                        status=PaymentStatus.COMPLETED, # Asumimos completado si viene en creación directa (POS)
                        transaction_id=pay_data.transaction_id,
                        company_id=company_id,
                        branch_id=order_data.branch_id,
                        user_id=user_id
                    )
                    new_order.payments.append(payment)
                
                # Actualizar estado si está pagado totalmente? 
                # Por ahora dejamos lógica simple: Si hay pagos >= total, podría pasar a CONFIRMED
                paid_amount = sum(p.amount for p in order_data.payments)
                if paid_amount >= total:
                    new_order.status = OrderStatus.CONFIRMED

            self.db.add(new_order)
            await self.db.commit()
            
            # 9. Refrescar y devolver con relaciones cargadas
            # Usando refresh normal a veces no carga relaciones, mejor query explicito
            # o confiar en lazy=selectin si está configurado (pero lo quitamos en otros modelos).
            # En Order model: items tiene lazy defaults (no selectin explícito en cambios recientes? Check model).
            # Order model: items relationship no tiene lazy="selectin" definido explícitamente en el snippet anterior.
            # Haremos una query de recarga segura.
            
            stmt_refresh = select(Order).where(Order.id == new_order.id)
            # Para asegurar carga de items y payments en la respuesta
            from sqlalchemy.orm import selectinload
            stmt_refresh = stmt_refresh.options(
                selectinload(Order.items).selectinload(OrderItem.product), 
                selectinload(Order.payments)
            )
            
            result = await self.db.execute(stmt_refresh)
            refreshed_order = result.scalar_one()
            
            logger.info(f"✅ Pedido creado: {order_number} (ID: {refreshed_order.id})")
            
            # 10. Trigger Print Job (Async)
            try:
                await self.print_service.create_print_job(refreshed_order.id, company_id)
            except Exception as e:
                # No fallamos el pedido si falla la impresión, solo logueamos
                logger.error(f"⚠️ Error al enviar a impresión: {e}")

            # 11. Trigger WebSocket Events (Async)
            # Convert to dict for JSON serialization
            try:
                # Basic sync to dict for WS (or use schema dump)
                # refreshed_order is ORM model, need schema or dict
                # We used _build_order_response to return, let's use that data
                response_schema = self._build_order_response(refreshed_order)
                order_dict = response_schema.model_dump(mode='json')

                await NotificationService.notify_order_created(order_dict, company_id)
                await NotificationService.notify_kitchen(order_dict, order_data.branch_id)
            except Exception as e:
                logger.error(f"⚠️ Error al enviar notificación WS: {e}")

            return self._build_order_response(refreshed_order)

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            import traceback
            logger.error(f"❌ Error al crear pedido: {e}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al procesar el pedido"
            )

    async def get_order(self, order_id: int, company_id: int) -> OrderRead:
        from sqlalchemy.orm import selectinload
        stmt = select(Order).where(
            Order.id == order_id, 
            Order.company_id == company_id
        ).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            
        return self._build_order_response(order)

    async def update_status(self, order_id: int, new_status: OrderStatus, company_id: int, user: Optional['User'] = None) -> OrderRead:
        """
        Actualiza el estado de un pedido utilizando la Máquina de Estados.
        """
        # 1. Recuperar orden (reutilizamos get_order pero necesitamos el objeto ORM, no el Schema)
        # Asi que hacemos query manual similar a get_order pero sin serializar aun
        from sqlalchemy.orm import selectinload
        from app.services.order_state_machine import OrderStateMachine
        
        stmt = select(Order).where(
            Order.id == order_id, 
            Order.company_id == company_id
        ).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

        # 2. Ejecutar Transición
        machine = OrderStateMachine(self.db)
        await machine.transition(order, new_status, user)
        
        # 3. Retornar actualizado
        return self._build_order_response(order)

    def _build_order_response(self, order: Order) -> OrderRead:
        """
        Transforma el modelo de BD a un esquema de respuesta OrderRead.
        Maneja manualmente la extracción de nombres de productos para evitar errores de validación.
        """
        items_read = []
        for item in order.items:
            items_read.append(OrderItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Desconocido",
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                notes=item.notes
            ))

        payments_read = [
            PaymentRead.model_validate(p) for p in order.payments
        ]

        return OrderRead(
            id=order.id,
            order_number=order.order_number,
            branch_id=order.branch_id,
            company_id=order.company_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_total=order.tax_total,
            total=order.total,
            customer_notes=order.customer_notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items_read,
            payments=payments_read
        )
