from app.core.logging_config import get_rbac_logger, log_rbac_action, log_security_event
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from sqlmodel import col

from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.services.order_counter_service import OrderCounterService
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderRead, OrderItemRead, OrderItemModifierRead, PaymentRead
from app.services.print_service import PrintService
from app.services.inventory_service import InventoryService
from app.services.recipe_service import RecipeService
from app.services.notification_service import NotificationService
from app.models.modifier import ProductModifier, OrderItemModifier
from app.models.ingredient import Ingredient
from app.models.user import User
import uuid
from collections import Counter

logger = get_rbac_logger("app.orders")

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
        from app.models.table import Table, TableStatus
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

            # 2.1 Obtener y validar Modificadores (si existen en el payload)
            all_modifier_ids = []
            for item in order_data.items:
                if item.modifiers:
                    all_modifier_ids.extend(item.modifiers)
            
            db_modifiers = {}
            if all_modifier_ids:
                stmt_mod = select(ProductModifier).where(
                    col(ProductModifier.id).in_(all_modifier_ids),
                    ProductModifier.company_id == company_id
                ).options(selectinload(ProductModifier.recipe_items))
                result_mod = await self.db.execute(stmt_mod)
                db_modifiers = {m.id: m for m in result_mod.scalars().all()}
                
                # Validar existencia simplificada (opcional: lanzar error si falta alguno)
                missing_mods = set(all_modifier_ids) - set(db_modifiers.keys())
                if missing_mods:
                    logger.warning(f"⚠️ Modificadores solicitados no encontrados: {missing_mods}")


            # 3. Calcular totales y construir items
            order_items: List[OrderItem] = []
            subtotal = Decimal("0.00")
            tax_total = Decimal("0.00")
            
            for pid, user_item in product_dict.items():
                product = db_products[pid]
                
                # TODO: Validar stock disponible aquí si Product tiene manejo de inventario estricto
                
                # Precio Base
                unit_price = product.price
                quantity = user_item.quantity
                
                # Calcular Monto Base
                line_base_total = unit_price * quantity
                
                # Procesar Modificadores
                item_modifiers_orm: List[OrderItemModifier] = []
                modifiers_subtotal = Decimal("0.00")
                
                if user_item.modifiers:
                    # Usamos Counter para manejar cantidades (ej: 2x Extra Queso)
                    mod_counts = Counter(user_item.modifiers)
                    for mod_id, mod_qty in mod_counts.items():
                        if mod_id not in db_modifiers:
                            continue
                            
                        mod_obj = db_modifiers[mod_id]
                        # Precio unitario del modificador * cantidad de veces que se pidió * cantidad de items (OJO: quantity del item afecta?)
                        # Usualmente: 1 Hamburguesa con Queso ($1) -> Extra $1.
                        # 2 Hamburguesas con Queso ($1) -> Extra $2.
                        # El input `modifiers` viene por item. "Este item tiene estos modifiers".
                        # Si cantidad=2, ¿aplicamos modifiers a CADA una? SÍ, generalmente.
                        # Si `modifiers` lista trae [ID_QUESO], y quantity item = 2.
                        # Significa que son 2 hamburguesas, ambas con queso? O es un item global?
                        # En POS, usualmente seleccionas item -> quantity -> modifiers.
                        # Si subo quantity a 2, el modifier se duplica.
                        # ASUMIMOS: La lista `modifiers` aplica a UNA unidad del producto?
                        # O a la línea completa?
                        # Estándar: Aplica a la unidad. Si pido 2 Burgers, y agrego Queso, son 2 Quesos.
                        # Entonces: total_mod_cost = mod_price * mod_qty * quantity
                        
                        cost_per_unit = mod_obj.extra_price * mod_qty
                        total_mod_cost = cost_per_unit * quantity
                        modifiers_subtotal += total_mod_cost
                        
                        # Crear ORM
                        # Ojo: OrderItemModifier se asocia al Item.
                        # Si el item tiene quantity=2, el OrderItemModifier quantity=?
                        # Option A: quantity = mod_qty (por unidad)
                        # Option B: quantity = mod_qty * item_quantity (total)
                        # DB Definition dice: "quantity: int = Field(default=1)". 
                        # Vamos a usar TOTAL para reflejar el consumo real en inventario posteriormente si iteramos esto.
                        # Pero conceptualmente es mejor por unidad. 
                        # Usemos TOTAL para que `unit_price * quantity` de el total correcto en reportes.
                        
                        item_modifiers_orm.append(OrderItemModifier(
                            modifier_id=mod_id,
                            unit_price=mod_obj.extra_price,
                            quantity=mod_qty * int(quantity), # Total absoluto de extras en esta línea
                            cost_snapshot=Decimal("0.00") # TODO: Calcular costo ingredientes real
                        ))

                # Totales de Línea
                line_subtotal = line_base_total + modifiers_subtotal
                
                # Tax (aplica a todo el subtotal)
                product_tax_rate = getattr(product, 'tax_rate', Decimal("0.00")) or Decimal("0.00")
                line_tax = line_subtotal * product_tax_rate
                
                # Crear Item
                item = OrderItem(
                    product_id=pid,
                    quantity=quantity,
                    unit_price=unit_price, # Precio base unitario del producto
                    subtotal=line_subtotal, # Incluye modifiers
                    tax_amount=line_tax,
                    notes=user_item.notes,
                    modifiers=item_modifiers_orm,
                    removed_ingredients=user_item.removed_ingredients or []
                )
                order_items.append(item)
                
                subtotal += line_subtotal
                tax_total += line_tax
            
            total = subtotal + tax_total

            # 4. Obtener Número de Orden Secuencial con prefijo según tipo
            # M-00001 (Mesa), L-00001 (Llevar), D-00001 (Domicilio)
            order_number = await self.counter_service.get_next_number(
                company_id=company_id, 
                branch_id=order_data.branch_id,
                order_type=order_data.delivery_type
            )
            logger.info(f"🔢 Número de pedido generado: {order_number}")

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
                    item_removed_ingredients = user_item.removed_ingredients or []

                    # Deduct Ingredients (FIFO)
                    for recipe_item in recipe.items:
                        # Check if ingredient is removed
                        # Logic: removed_ingredients contains IDs (ints as string or raw int)
                        # recipe_item.ingredient_id is UUID? product_id is int? 
                        # We need to robustly check. 
                        # Frontend sends Product IDs for Products acting as ingredients?
                        # Or UUIDs? 
                        # Assuming frontend sends compatible IDs.
                        # Convert to string for comparison safety
                        
                        is_removed = False
                        rec_ing_id = str(recipe_item.ingredient_id) if recipe_item.ingredient_id else str(recipe_item.ingredient_product_id)
                        
                        if rec_ing_id in [str(x) for x in item_removed_ingredients]:
                            is_removed = True
                            
                        if is_removed:
                            # Skip stock deduction
                            continue

                        # Use gross_quantity and ingredient_id (UUID)
                        # We use InventoryService.update_ingredient_stock which handles FIFO
                        # Quantity to consume = recipe_item.gross_quantity * quantity
                        
                        qty_needed = recipe_item.gross_quantity * Decimal(quantity)
                        
                        await inventory_service.update_ingredient_stock(
                            branch_id=order_data.branch_id,
                            ingredient_id=recipe_item.ingredient_id,
                            quantity_delta=-qty_needed,
                            transaction_type="SALE",
                            user_id=user_id,
                            reference_id=f"ORDER-{order_number}",
                            reason=f"Sale of {product.name} (Recipe)"
                        )
                else:
                    # Deduct Product Directly (Legacy / Simple Product)
                    await inventory_service.update_stock(
                        branch_id=order_data.branch_id,
                        product_id=pid,
                        quantity_delta=-quantity,

                        transaction_type="SALE",
                        user_id=user_id,
                        reference_id=f"ORDER-{order_number}",
                        reason=f"Sale of {product.name}"
                    )
                
                # 5.1 Deduct Stock for Modifiers
                if user_item.modifiers:
                    mod_counts = Counter(user_item.modifiers)
                    for mod_id, mod_qty in mod_counts.items():
                        if mod_id in db_modifiers:
                            mod_obj = db_modifiers[mod_id]
                            # Total times modifier applied = items quantity * modifier qty per item
                            total_mod_applies = quantity * mod_qty
                            
                            for mod_recipe_item in mod_obj.recipe_items:
                                qty_needed_mod = mod_recipe_item.quantity * total_mod_applies
                                
                                # Check if it uses Ingredient (UUID) or Product (ID)
                                if mod_recipe_item.ingredient_id:
                                    await inventory_service.update_ingredient_stock(
                                        branch_id=order_data.branch_id,
                                        ingredient_id=mod_recipe_item.ingredient_id,
                                        quantity_delta=-qty_needed_mod,
                                        transaction_type="SALE",
                                        user_id=user_id,
                                        reference_id=f"ORDER-{order_number}",
                                        reason=f"Extra {mod_obj.name} (Modifier Ing)"
                                    )
                                elif mod_recipe_item.ingredient_product_id:
                                    # Legacy Product-based modifier
                                    await inventory_service.update_stock(
                                        branch_id=order_data.branch_id,
                                        product_id=mod_recipe_item.ingredient_product_id,
                                        quantity_delta=-qty_needed_mod,
                                        transaction_type="SALE",
                                        user_id=user_id,
                                        reference_id=f"ORDER-{order_number}",
                                        reason=f"Extra {mod_obj.name} (Modifier Prod)"
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
                customer_notes=order_data.customer_notes,
                
                # CRM (V5.0)
                customer_id=order_data.customer_id,
                delivery_type=order_data.delivery_type,
                delivery_address=order_data.delivery_address, 
                delivery_notes=order_data.delivery_notes,
                
                delivery_customer_name=order_data.delivery_customer_name,
                delivery_customer_phone=order_data.delivery_customer_phone,

                # Mesas
                table_id=order_data.table_id,

                # Auditoría
                created_by_id=user_id
            )

            
            # Asociar items
            new_order.items = order_items
            
            # 8. Procesar Pagos Iniciales (si existen)
            if order_data.payments:
                for pay_data in order_data.payments:
                    payment = Payment(
                        company_id=company_id,
                        branch_id=order_data.branch_id,
                        user_id=user_id,
                        amount=pay_data.amount,
                        method=pay_data.method,
                        status=PaymentStatus.COMPLETED,
                        transaction_id=pay_data.transaction_id
                    )
                    new_order.payments.append(payment)
                
                # Actualizar estado si está pagado totalmente? 
                # Por ahora dejamos lógica simple: Si hay pagos >= total, podría pasar a CONFIRMED
                paid_amount = sum(p.amount for p in order_data.payments)
                if paid_amount >= total:
                    new_order.status = OrderStatus.CONFIRMED

            self.db.add(new_order)
            
            # 8.1 Actualizar estado de la mesa a OCUPADA
            if order_data.table_id:
                table_stmt = select(Table).where(Table.id == order_data.table_id)
                table_result = await self.db.execute(table_stmt)
                table = table_result.scalar_one_or_none()
                if table:
                    table.status = TableStatus.OCCUPIED
                    self.db.add(table)

            await self.db.commit()
            
            # 9. Refrescar y devolver con relaciones cargadas
            # Usando refresh normal a veces no carga relaciones, mejor query explicito
            # o confiar en lazy=selectin si está configurado (pero lo quitamos en otros modelos).
            # En Order model: items tiene lazy defaults (no selectin explícito en cambios recientes? Check model).
            # Order model: items relationship no tiene lazy="selectin" definido explícitamente en el snippet anterior.
            # Haremos una query de recarga segura.
            
            stmt_refresh = select(Order).where(Order.id == new_order.id)
            # Para asegurar carga de items y payments en la respuesta
            stmt_refresh = stmt_refresh.options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
                selectinload(Order.payments),
                selectinload(Order.created_by)
            )

            
            result = await self.db.execute(stmt_refresh)
            refreshed_order = result.scalar_one()
            
            logger.info(f"✅ Pedido creado: {order_number} (ID: {refreshed_order.id})")
            
            # LOG: Trazabilidad de Negocio
            log_rbac_action(
                action="ORDER_CREATED",
                user_id=user_id,
                details={
                    "order_number": order_number,
                    "order_id": refreshed_order.id,
                    "total": str(total),
                    "branch_id": order_data.branch_id,
                    "items_count": len(refreshed_order.items)
                }
            )
            
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
                response_schema = await self._build_order_response(refreshed_order)
                order_dict = response_schema.model_dump(mode='json')

                await NotificationService.notify_order_created(order_dict, company_id)
                await NotificationService.notify_kitchen(order_dict, order_data.branch_id)
            except Exception as e:
                logger.error(f"⚠️ Error al enviar notificación WS: {e}")

            return await self._build_order_response(refreshed_order)

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            import traceback
            error_msg = f"❌ Error al crear pedido: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # LOG: Seguridad/Error de Negocio
            log_security_event(
                event="ORDER_CREATION_FAILED",
                user_id=user_id,
                details={"error": str(e), "branch_id": order_data.branch_id}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al procesar el pedido"
            )

    async def get_orders(
        self, 
        company_id: int, 
        branch_id: Optional[int] = None, 
        statuses: Optional[List[OrderStatus]] = None,
        delivery_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OrderRead]:
        """
        Listar pedidos con filtros.
        """
        stmt = select(Order).where(Order.company_id == company_id)
        
        if branch_id:
            stmt = stmt.where(Order.branch_id == branch_id)
            
        if statuses:
            stmt = stmt.where(Order.status.in_(statuses))
            
        if delivery_type:
            stmt = stmt.where(Order.delivery_type == delivery_type)
            
        # Ordenar por más reciente
        stmt = stmt.order_by(Order.created_at.desc())
        
        # Paginación
        stmt = stmt.limit(limit).offset(offset)
        
        # Cargar relaciones
        stmt = stmt.options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
            selectinload(Order.payments),
            selectinload(Order.created_by)
        )

        
        result = await self.db.execute(stmt)
        orders = result.scalars().all()
        
        # Pre-load ingredient names to avoid N+1 queries in loop
        ing_map = await self._resolve_ingredient_names_map(orders)
        
        return [await self._build_order_response(o, ingredient_map=ing_map) for o in orders]

    async def get_order(self, order_id: int, company_id: int) -> OrderRead:
        from sqlalchemy.orm import selectinload
        stmt = select(Order).where(
            Order.id == order_id, 
            Order.company_id == company_id
        ).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
            selectinload(Order.payments),
            selectinload(Order.created_by)
        )

        
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            
        return await self._build_order_response(order)

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
            selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
            selectinload(Order.payments),
            selectinload(Order.created_by)
        )

        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

        # 2. Ejecutar Transición
        old_status = order.status
        machine = OrderStateMachine(self.db)
        await machine.transition(order, new_status, user)
        
        # 2.1 Si el pedido se completa o cancela, liberar la mesa
        if new_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED] and order.table_id:
            from app.models.table import Table, TableStatus
            table_stmt = select(Table).where(Table.id == order.table_id)
            table_result = await self.db.execute(table_stmt)
            table = table_result.scalar_one_or_none()
            if table:
                # Verificar si no hay otras órdenes pendientes en esta mesa (opcional, usualmente 1 a 1)
                table.status = TableStatus.AVAILABLE
                self.db.add(table)
                await self.db.commit()

        # LOG: Trazabilidad de Estado
        log_rbac_action(
            action="ORDER_STATUS_CHANGED",
            user_id=user.id if user else None,
            details={
                "order_id": order_id,
                "order_number": order.order_number,
                "old_status": old_status,
                "new_status": new_status,
                "branch_id": order.branch_id
            }
        )
        
        # Emit WebSocket notification for real-time sync
        await NotificationService.notify_order_status(
            order_id=order_id,
            status=new_status.value,
            company_id=company_id,
            branch_id=order.branch_id,
            order_number=order.order_number
        )
        
        # 3. Retornar actualizado
        return await self._build_order_response(order)

    async def get_active_order_by_table(self, table_id: int, company_id: int) -> Optional[OrderRead]:
        """
        Busca el pedido activo actual para una mesa específica.
        Un pedido se considera activo si no está en estado DELIVERED o CANCELLED.
        """
        stmt = select(Order).where(
            Order.table_id == table_id,
            Order.company_id == company_id,
            col(Order.status).notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
        ).order_by(Order.created_at.desc())
        
        stmt = stmt.options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
            selectinload(Order.payments),
            selectinload(Order.created_by)
        )
        
        result = await self.db.execute(stmt)
        order = result.scalars().first()
        
        return await self._build_order_response(order) if order else None

    async def add_items_to_order(self, order_id: int, items_data: List[any], company_id: int, user_id: int) -> OrderRead:
        """
        Agrega nuevos productos a un pedido existente.
        """
        # 1. Obtener la orden existente
        stmt = select(Order).where(
            Order.id == order_id,
            Order.company_id == company_id
        ).options(
            selectinload(Order.items),
            selectinload(Order.payments)
        )
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No se pueden agregar items a un pedido finalizado")

        # 2. Reutilizar lógica de creación de items (simplificada o refactorizada)
        # Para evitar duplicidad extrema, creamos un OrderCreate ficticio para los nuevos items
        from app.schemas.order import OrderCreate
        temp_order_data = OrderCreate(
            items=items_data,
            branch_id=order.branch_id,
            delivery_type=order.delivery_type
        )
        
        # 3. Procesar stock y crear nuevos OrderItems
        # (Esta parte es compleja de refactorizar sin cambiar mucho create_order, 
        # así que haremos una versión ligera o llamaremos a una función compartida si existiera)
        # Por ahora, implementamos la lógica de stock mínima necesaria similar a create_order
        
        # Preparamos el entorno similar a create_order
        inventory_service = InventoryService(self.db)
        recipe_service = RecipeService(self.db)
        
        product_dict = {item.product_id: item for item in temp_order_data.items}
        product_ids = list(product_dict.keys())
        
        stmt_prod = select(Product).where(
            col(Product.id).in_(product_ids),
            Product.company_id == company_id,
            Product.is_active == True
        )
        prod_result = await self.db.execute(stmt_prod)
        db_products = {p.id: p for p in prod_result.scalars().all()}

        # Modificadores
        all_modifier_ids = []
        for item in temp_order_data.items:
            if item.modifiers:
                all_modifier_ids.extend(item.modifiers)
        
        db_modifiers = {}
        if all_modifier_ids:
            stmt_mod = select(ProductModifier).where(
                col(ProductModifier.id).in_(all_modifier_ids),
                ProductModifier.company_id == company_id
            ).options(selectinload(ProductModifier.recipe_items))
            mod_result = await self.db.execute(stmt_mod)
            db_modifiers = {m.id: m for m in mod_result.scalars().all()}

        new_items: List[OrderItem] = []
        added_subtotal = Decimal("0.00")
        added_tax = Decimal("0.00")

        for user_item in temp_order_data.items:
            product = db_products.get(user_item.product_id)
            if not product: continue
            
            unit_price = product.price
            quantity = user_item.quantity
            line_base_total = unit_price * quantity
            
            item_modifiers_orm = []
            modifiers_subtotal = Decimal("0.00")
            
            if user_item.modifiers:
                mod_counts = Counter(user_item.modifiers)
                for mod_id, mod_qty in mod_counts.items():
                    if mod_id not in db_modifiers: continue
                    mod_obj = db_modifiers[mod_id]
                    cost_per_unit = mod_obj.extra_price * mod_qty
                    modifiers_subtotal += cost_per_unit * quantity
                    item_modifiers_orm.append(OrderItemModifier(
                        modifier_id=mod_id,
                        unit_price=mod_obj.extra_price,
                        quantity=mod_qty * int(quantity)
                    ))

            line_subtotal = line_base_total + modifiers_subtotal
            product_tax_rate = getattr(product, 'tax_rate', Decimal("0.00")) or Decimal("0.00")
            line_tax = line_subtotal * product_tax_rate
            
            item = OrderItem(
                order_id=order.id, # IMPORTANTE: Asociar a la orden existente
                product_id=user_item.product_id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=line_subtotal,
                tax_amount=line_tax,
                notes=user_item.notes or "",
                modifiers=item_modifiers_orm,
                removed_ingredients=user_item.removed_ingredients or []
            )
            new_items.append(item)
            added_subtotal += line_subtotal
            added_tax += line_tax
            
            # Stock deduction logic (mirrors create_order)
            # Deduct stock for product recipe or product itself
            recipe = await recipe_service.get_recipe_by_product(user_item.product_id, company_id)
            
            if recipe:
                item_removed_ingredients = user_item.removed_ingredients or []
                for recipe_item in recipe.items:
                    is_removed = False
                    rec_ing_id = str(recipe_item.ingredient_id) if recipe_item.ingredient_id else str(recipe_item.ingredient_product_id)
                    if rec_ing_id in [str(x) for x in item_removed_ingredients]:
                        is_removed = True
                    if is_removed:
                        continue
                    
                    qty_needed = recipe_item.gross_quantity * Decimal(quantity)
                    await inventory_service.update_ingredient_stock(
                        branch_id=order.branch_id,
                        ingredient_id=recipe_item.ingredient_id,
                        quantity_delta=-qty_needed,
                        transaction_type="SALE",
                        user_id=user_id,
                        reference_id=f"ORDER-{order.order_number}",
                        reason=f"Sale of {product.name} (Recipe - Appended)"
                    )
            else:
                await inventory_service.update_stock(
                    branch_id=order.branch_id,
                    product_id=user_item.product_id,
                    quantity_delta=-quantity,
                    transaction_type="SALE",
                    user_id=user_id,
                    reference_id=f"ORDER-{order.order_number}",
                    reason=f"Sale of {product.name} (Appended)"
                )
            
            # Deduct stock for modifiers
            if user_item.modifiers:
                mod_counts = Counter(user_item.modifiers)
                for mod_id, mod_qty in mod_counts.items():
                    if mod_id in db_modifiers:
                        mod_obj = db_modifiers[mod_id]
                        total_mod_applies = quantity * mod_qty
                        for mod_recipe_item in mod_obj.recipe_items:
                            qty_needed_mod = mod_recipe_item.quantity * total_mod_applies
                            if mod_recipe_item.ingredient_id:
                                await inventory_service.update_ingredient_stock(
                                    branch_id=order.branch_id,
                                    ingredient_id=mod_recipe_item.ingredient_id,
                                    quantity_delta=-qty_needed_mod,
                                    transaction_type="SALE",
                                    user_id=user_id,
                                    reference_id=f"ORDER-{order.order_number}",
                                    reason=f"Extra {mod_obj.name} (Modifier Appended)"
                                )
                            elif mod_recipe_item.ingredient_product_id:
                                await inventory_service.update_stock(
                                    branch_id=order.branch_id,
                                    product_id=mod_recipe_item.ingredient_product_id,
                                    quantity_delta=-qty_needed_mod,
                                    transaction_type="SALE",
                                    user_id=user_id,
                                    reference_id=f"ORDER-{order.order_number}",
                                    reason=f"Extra {mod_obj.name} (Modifier Prod Appended)"
                                )
            
        # 4. Actualizar totales de la orden
        order.subtotal += added_subtotal
        order.tax_total += added_tax
        order.total += (added_subtotal + added_tax)
        
        for item in new_items:
            self.db.add(item)
            
        self.db.add(order)
        await self.db.commit()

        
        # 5. Notificar y refrescar
        # Re-usar lógica de impresión/notificación si es necesario
        
        log_rbac_action(
            action="ORDER_ITEMS_ADDED",
            user_id=user_id,
            details={
                "order_id": order_id,
                "order_number": order.order_number,
                "added_total": str(added_subtotal + added_tax)
            }
        )
        
        return await self.get_order(order_id, company_id)

    async def _resolve_ingredient_names_map(self, orders: List[Order]) -> Dict[str, str]:
        """
        Helper para resolver nombres de ingredientes eliminados (UUIDs) para un lote de órdenes.
        Evita problemas N+1 al hacer una sola consulta para todas las órdenes.
        """
        all_removed_ids = set()
        for order in orders:
            for item in order.items:
                if item.removed_ingredients:
                    all_removed_ids.update(item.removed_ingredients)

        if not all_removed_ids:
            return {}

        valid_uuids = []
        for uid_str in all_removed_ids:
            try:
                valid_uuids.append(uuid.UUID(str(uid_str)))
            except ValueError:
                pass
        
        if not valid_uuids:
            return {}

        stmt = select(Ingredient.id, Ingredient.name).where(col(Ingredient.id).in_(valid_uuids))
        result = await self.db.execute(stmt)
        rows = result.all()
        
        return {str(row.id): row.name for row in rows}

    async def _build_order_response(self, order: Order, ingredient_map: Optional[Dict[str, str]] = None) -> OrderRead:
        """
        Transforma el modelo de BD a un esquema de respuesta OrderRead.
        Resuelve los UUIDs de ingredientes eliminados a sus nombres reales de manera eficiente.
        """
        # Si no se provee mapa (ej. llamada individual), lo resolvemos para esta única orden
        if ingredient_map is None:
            ingredient_map = await self._resolve_ingredient_names_map([order])

        items_read = []
        for item in order.items:
            # Resolve removed ingredient names
            resolved_removed = []
            if item.removed_ingredients:
                for uid_str in item.removed_ingredients:
                    name = ingredient_map.get(str(uid_str))
                    if not name:
                         name = f"Ingrediente Desconocido ({str(uid_str)[:8]}...)"
                    resolved_removed.append(name)

            items_read.append(OrderItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Desconocido",
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                notes=item.notes or "",
                removed_ingredients=resolved_removed,
                modifiers=[OrderItemModifierRead.model_validate(m) for m in item.modifiers] if item.modifiers else []
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
            
            # CRM
            customer_id=order.customer_id,
            delivery_type=order.delivery_type,
            delivery_address=order.delivery_address,
            delivery_notes=order.delivery_notes,
            delivery_fee=order.delivery_fee,
            
            delivery_customer_name=order.delivery_customer_name,
            delivery_customer_phone=order.delivery_customer_phone,
            
            table_id=order.table_id,
            created_by_name=order.created_by.full_name or order.created_by.username if order.created_by else None,

            # Cancellation fields
            cancellation_status=order.cancellation_status,
            cancellation_reason=order.cancellation_reason,
            cancellation_requested_at=order.cancellation_requested_at,
            cancellation_denied_reason=order.cancellation_denied_reason,

            items=items_read,

            payments=payments_read
        )

    async def _handle_item_stock(
        self,
        item_data: dict, # Contain keys: product_id, quantity, modifiers, removed_ingredients
        company_id: int,
        branch_id: int,
        user_id: int,
        reference_id: str,
        reverse: bool = False
    ):
        """
        Manages stock deduction or restoration for an item (including modifiers).
        If reverse=True, it adds stock back (VOID/CANCEL).
        If reverse=False, it removes stock (SALE).
        """
        from collections import Counter
        from app.services.inventory_service import InventoryService
        from app.services.recipe_service import RecipeService
        from app.models.product import Product
        from app.models.modifier import ProductModifier

        inv_service = InventoryService(self.db)
        recipe_service = RecipeService(self.db)

        # 1. Product Info
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity')
        modifiers = item_data.get('modifiers') or []
        removed_ingredients = item_data.get('removed_ingredients') or []

        stmt = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            return 

        # Determine multiplier: If reverse, we invert the qty delta (so -qty becomes +qty)
        # Normal sale: delta = -qty
        # Void/Reverse: delta = +qty
        base_delta_qty = quantity if reverse else -quantity

        # 2. Product Stock (Recipe or Direct)
        recipe = await recipe_service.get_recipe_by_product(product_id, company_id)
        
        if recipe:
            for recipe_item in recipe.items:
                is_removed = False
                rec_ing_id = str(recipe_item.ingredient_id) if recipe_item.ingredient_id else str(recipe_item.ingredient_product_id)
                if rec_ing_id in [str(x) for x in removed_ingredients]:
                    is_removed = True
                
                if is_removed:
                    continue
                
                qty_needed = recipe_item.gross_quantity * quantity
                delta = qty_needed if reverse else -qty_needed
                
                if recipe_item.ingredient_id:
                    await inv_service.update_ingredient_stock(
                        branch_id=branch_id,
                        ingredient_id=recipe_item.ingredient_id,
                        quantity_delta=delta,
                        transaction_type="ADJUSTMENT" if reverse else "SALE",
                        user_id=user_id,
                        reference_id=reference_id,
                        reason=f"{'Void' if reverse else 'Sale'} of {product.name} (Recipe)"
                    )
        else:
            await inv_service.update_stock(
                branch_id=branch_id,
                product_id=product_id,
                quantity_delta=base_delta_qty,
                transaction_type="ADJUSTMENT" if reverse else "SALE",
                user_id=user_id,
                reference_id=reference_id,
                reason=f"{'Void' if reverse else 'Sale'} of {product.name}"
            )

        # 3. Modifiers Stock
        if modifiers:
            mod_counts = Counter(modifiers)
            mod_ids = list(mod_counts.keys())
            
            stmt_mod = select(ProductModifier).where(
                col(ProductModifier.id).in_(mod_ids),
                ProductModifier.company_id == company_id
            ).options(selectinload(ProductModifier.recipe_items))
            mod_result = await self.db.execute(stmt_mod)
            db_modifiers = {m.id: m for m in mod_result.scalars().all()}

            for mod_id, mod_qty in mod_counts.items():
                if mod_id not in db_modifiers: continue
                mod_obj = db_modifiers[mod_id]
                
                total_mod_applies = quantity * mod_qty 
                
                for mod_recipe_item in mod_obj.recipe_items:
                    qty_needed_mod = mod_recipe_item.quantity * total_mod_applies
                    delta_mod = qty_needed_mod if reverse else -qty_needed_mod

                    if mod_recipe_item.ingredient_id:
                        await inv_service.update_ingredient_stock(
                            branch_id=branch_id,
                            ingredient_id=mod_recipe_item.ingredient_id,
                            quantity_delta=delta_mod,
                            transaction_type="ADJUSTMENT" if reverse else "SALE",
                            user_id=user_id,
                            reference_id=reference_id,
                            reason=f"{'Void' if reverse else 'Sale'} of {mod_obj.name} (Modifier)"
                        )
                    elif mod_recipe_item.ingredient_product_id:
                        await inv_service.update_stock(
                            branch_id=branch_id,
                            product_id=mod_recipe_item.ingredient_product_id,
                            quantity_delta=delta_mod,
                            transaction_type="ADJUSTMENT" if reverse else "SALE",
                            user_id=user_id,
                            reference_id=reference_id,
                            reason=f"{'Void' if reverse else 'Sale'} of {mod_obj.name} (Modifier Product)"
                        )

    async def remove_order_item(self, order_id: int, item_id: int, company_id: int, user_id: int) -> OrderRead:
        """
        Elimina un item del pedido y repone el stock.
        """
        order = await self.get_order_orm(order_id, company_id)
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
        
        allowed_statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]
        if order.status not in allowed_statuses:
             raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No se puede modificar un pedido finalizado o cancelado")

        item_to_remove = next((i for i in order.items if i.id == item_id), None)
        if not item_to_remove:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item no encontrado en el pedido")
            
        item_data = {
            'product_id': item_to_remove.product_id,
            'quantity': item_to_remove.quantity,
            'modifiers': [m.modifier_id for m in item_to_remove.modifiers], 
            'removed_ingredients': item_to_remove.removed_ingredients
        }
        
        await self._handle_item_stock(
            item_data=item_data,
            company_id=company_id,
            branch_id=order.branch_id,
            user_id=user_id,
            reference_id=f"VOID-ITEM-{order.order_number}",
            reverse=True 
        )
        
        order.subtotal -= item_to_remove.subtotal
        order.tax_total -= item_to_remove.tax_amount
        order.total -= (item_to_remove.subtotal + item_to_remove.tax_amount)
        
        await self.db.delete(item_to_remove)
        
        self.db.add(order)
        await self.db.commit()
        # Reload order with relationships to avoid MissingGreenlet
        order = await self.get_order_orm(order.id, company_id)
        
        return await self._build_order_response(order)

    async def update_order_item(self, order_id: int, item_id: int, update_data: dict, company_id: int, user_id: int) -> OrderRead:
        """
        Actualiza cantidad/notas/modificadores de un item.
        """
        from app.models.modifier import ProductModifier
        from collections import Counter
        
        order = await self.get_order_orm(order_id, company_id)
        if not order:
             raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
             
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
             raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No se puede modificar pedido finalizado")

        item = next((i for i in order.items if i.id == item_id), None)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
            
        old_item_data = {
            'product_id': item.product_id,
            'quantity': item.quantity,
            'modifiers': [m.modifier_id for m in item.modifiers],
            'removed_ingredients': item.removed_ingredients
        }
        await self._handle_item_stock(
            item_data=old_item_data,
            company_id=company_id,
            branch_id=order.branch_id,
            user_id=user_id,
            reference_id=f"UPD-OLD-{order.order_number}",
            reverse=True
        )
        
        new_quantity = update_data.get('quantity') if update_data.get('quantity') is not None else item.quantity
        new_notes = update_data.get('notes') if update_data.get('notes') is not None else item.notes
        new_removed = update_data.get('removed_ingredients') if update_data.get('removed_ingredients') is not None else item.removed_ingredients
        
        new_modifier_ids = update_data.get('modifiers')
        if new_modifier_ids is None:
            new_modifier_ids = [m.modifier_id for m in item.modifiers]
            
        stmt_prod = select(Product).where(Product.id == item.product_id)
        res_prod = await self.db.execute(stmt_prod)
        product = res_prod.scalar_one()
        
        unit_price = product.price
        base_total = unit_price * new_quantity
        
        modifiers_subtotal = Decimal("0.00")
        new_modifiers_orm = []
        
        if new_modifier_ids:
            mod_counts = Counter(new_modifier_ids)
            stmt_mod = select(ProductModifier).where(
                col(ProductModifier.id).in_(list(mod_counts.keys())),
                ProductModifier.company_id == company_id
            ).options(selectinload(ProductModifier.recipe_items))
            res_mod = await self.db.execute(stmt_mod)
            db_modifiers = {m.id: m for m in res_mod.scalars().all()}
            
            for mod_id, count in mod_counts.items():
                if mod_id in db_modifiers:
                    mod_obj = db_modifiers[mod_id]
                    modifiers_subtotal += (mod_obj.extra_price * count) * new_quantity
                    new_modifiers_orm.append(OrderItemModifier(
                        modifier_id=mod_id,
                        unit_price=mod_obj.extra_price,
                        quantity=count * int(new_quantity)
                    ))
        
        new_subtotal = base_total + modifiers_subtotal
        tax_rate = getattr(product, 'tax_rate', Decimal("0.00")) or Decimal("0.00")
        new_tax = new_subtotal * tax_rate
        
        order.subtotal -= item.subtotal
        order.tax_total -= item.tax_amount
        order.total -= (item.subtotal + item.tax_amount)
        
        for m in list(item.modifiers):
            await self.db.delete(m)
        
        item.quantity = new_quantity
        item.notes = new_notes
        item.removed_ingredients = new_removed
        item.unit_price = unit_price
        item.subtotal = new_subtotal
        item.tax_amount = new_tax
        item.modifiers = new_modifiers_orm
        
        new_item_data = {
            'product_id': item.product_id,
            'quantity': new_quantity,
            'modifiers': new_modifier_ids,
            'removed_ingredients': new_removed
        }
        await self._handle_item_stock(
            item_data=new_item_data,
            company_id=company_id,
            branch_id=order.branch_id,
            user_id=user_id,
            reference_id=f"UPD-NEW-{order.order_number}",
            reverse=False 
        )
        
        order.subtotal += new_subtotal
        order.tax_total += new_tax
        order.total += (new_subtotal + new_tax)
        
        self.db.add(item)
        self.db.add(order)
        await self.db.commit()
        # Reload order with relationships to avoid MissingGreenlet
        order = await self.get_order_orm(order.id, company_id)
        
        return await self._build_order_response(order)

    async def get_order_orm(self, order_id: int, company_id: int) -> Optional[Order]:
        """Helper to get full ORM object. All relationships must be eagerly loaded to avoid MissingGreenlet in async."""
        stmt = select(Order).where(Order.id == order_id, Order.company_id == company_id).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
            selectinload(Order.payments),
            selectinload(Order.created_by),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def request_cancellation(self, order_id: int, reason: str, company_id: int, user: User) -> OrderRead:
        """
        Solicita la cancelación de un pedido.
        Si está PENDING, se cancela directamente.
        Si está PREPARING, entra en flujo de aprobación.
        """
        order = await self.get_order_orm(order_id, company_id)
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            
        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="El pedido ya está cancelado")

        # 1. Determinar rol con seguridad (Reloading user to get RBAC role)
        # Esto previene errores si user.role es string legado y no RBAC
        stmt_user = select(User).where(User.id == user.id).options(selectinload(User.user_role))
        res_user = await self.db.execute(stmt_user)
        full_user = res_user.scalar_one()

        role_code = full_user.role.lower()
        if full_user.user_role:
             role_code = full_user.user_role.code.lower()
        
        # 1. Determinar si se puede cancelar directamente
        # Se permite cancelar directo si:
        # - El pedido está PENDING (el cocinero aún no lo ve/prepara)
        # - O el usuario es Admin/Owner/Manager
        is_powerful = role_code in ["admin", "owner", "manager"]
        is_direct_cancel_allowed = (order.status == OrderStatus.PENDING) or is_powerful
        
        print(f"DEBUG: Request Cancellation order_status={order.status} is_powerful={is_powerful} -> Direct={is_direct_cancel_allowed}")

        if is_direct_cancel_allowed:
            # Cancelación directa
            print(f"DEBUG [request_cancellation]: Direct cancel allowed - calling update_status")
            return await self.update_status(order_id, OrderStatus.CANCELLED, company_id, user)

        # 2. Para otros casos (ej: Pedido en PREPARING/READY cancelado por mesero), entrar en modo solicitud
        if order.status in [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]:
            print(f"DEBUG [request_cancellation]: Setting cancellation_status to 'pending' for order {order_id}")
            order.cancellation_status = "pending"
            order.cancellation_reason = reason
            order.cancellation_requested_at = datetime.utcnow()
            order.cancellation_requested_by_id = user.id
            
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            
            print(f"DEBUG [request_cancellation]: After commit - cancellation_status={order.cancellation_status}")
            
            # Notificar a interesados
            await NotificationService.notify_cancellation_request(
                order_id=order.id,
                order_number=order.order_number,
                reason=reason,
                company_id=company_id,
                branch_id=order.branch_id
            )
            
            # Recargar y devolver
            order = await self.get_order_orm(order.id, company_id)
            print(f"DEBUG [request_cancellation]: After reload - cancellation_status={order.cancellation_status}")
            return await self._build_order_response(order)
            
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"No se puede solicitar cancelación en estado {order.status}"
        )

    async def process_cancellation_approval(self, order_id: int, approved: bool, notes: Optional[str], company_id: int, user: User) -> OrderRead:
        """
        Procesa (Aprueba o Deniega) una solicitud de cancelación pendiente.
        """
        order = await self.get_order_orm(order_id, company_id)
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
        
        # DEBUG: Log current order state
        print(f"DEBUG [process_cancellation_approval]: order_id={order_id}")
        print(f"DEBUG [process_cancellation_approval]: order.status={order.status}")
        print(f"DEBUG [process_cancellation_approval]: order.cancellation_status={order.cancellation_status}")
        print(f"DEBUG [process_cancellation_approval]: order.cancellation_reason={order.cancellation_reason}")
        print(f"DEBUG [process_cancellation_approval]: approved={approved}")
            
        if order.cancellation_status != "pending":
            print(f"DEBUG [process_cancellation_approval]: REJECTED - cancellation_status is '{order.cancellation_status}', expected 'pending'")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"No hay una solicitud de cancelación pendiente para este pedido (status actual: {order.cancellation_status})")

        # 1. Determinar rol con seguridad
        stmt_user = select(User).where(User.id == user.id).options(selectinload(User.user_role))
        res_user = await self.db.execute(stmt_user)
        full_user = res_user.scalar_one()

        role_code = full_user.role.lower()
        if full_user.user_role:
             role_code = full_user.user_role.code.lower()
             
        # Validar permisos: Cajero, Admin o Cocina
        allowed_roles = ["cashier", "manager", "admin", "owner", "kitchen", "cook", "chef", "super_admin"]
        if role_code not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="No tiene permisos para procesar cancelaciones")

        # Store order info before commit to avoid lazy loading issues
        order_order_number = order.order_number
        order_branch_id = order.branch_id
        
        order.cancellation_processed_at = datetime.utcnow()
        
        if approved:
            # Si se aprueba, la cancelación es efectiva
            order.cancellation_status = "approved"
            self.db.add(order)
            await self.db.commit()
            
            # Actualizar estado a CANCELLED
            await self.update_status(order_id, OrderStatus.CANCELLED, company_id, user)
            
            # Notificar aprobación al mesero
            await NotificationService.notify_cancellation_approved(
                order_id=order_id,
                order_number=order_order_number,
                company_id=company_id,
                branch_id=order_branch_id
            )
        else:
            # Si se deniega, el pedido continúa
            order.cancellation_status = "denied"
            order.cancellation_denied_reason = notes or "Sin motivo especificado"
            self.db.add(order)
            await self.db.commit()
            
            # Notificar denegación al mesero con el motivo
            await NotificationService.notify_cancellation_denied(
                order_id=order_id,
                order_number=order_order_number,
                denial_reason=notes or "Sin motivo especificado",
                company_id=company_id,
                branch_id=order_branch_id
            )

        fresh_order = await self.get_order_orm(order_id, company_id)
        return await self._build_order_response(fresh_order)
