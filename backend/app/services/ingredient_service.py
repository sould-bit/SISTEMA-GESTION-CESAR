"""
Servicio CRUD para Ingredientes (Insumos / Materia Prima).

A diferencia de Productos, los Ingredientes:
- Se compran y se gastan, pero NO se venden directamente en el POS.
- Ejemplos: Aceite, Harina, Tomates, Carne.
"""

from typing import List, Optional
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException

from app.models.ingredient import Ingredient
from app.models.ingredient_inventory import IngredientInventory
from app.models.ingredient_cost_history import IngredientCostHistory
from app.models.ingredient_batch import IngredientBatch


class IngredientService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        company_id: int,
        name: str,
        sku: Optional[str],
        base_unit: str,
        current_cost: Decimal = Decimal(0),
        yield_factor: float = 1.0,
        category_id: Optional[int] = None,
        ingredient_type: str = "RAW",
    ) -> Ingredient:
        """Crea un nuevo ingrediente."""
        
        # Generar SKU automático si no existe
        if not sku:
            import random
            import string
            # Generar SKU tipo ING-1234AB
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            sku = f"ING-{suffix}"
            
            # Verificar si existe (reintento simple)
            existing = await self.get_by_sku(company_id, sku)
            if existing:
                sku = f"ING-{int(datetime.utcnow().timestamp())}"

        # Verificar unicidad de SKU por empresa
        existing = await self.get_by_sku(company_id, sku)
        if existing:
            if existing.is_active:
                raise HTTPException(status_code=400, detail=f"SKU {sku} already exists for this company")
            else:
                # Si el SKU existe pero está inactivo (eliminado), lo renombramos para liberarlo
                timestamp_suffix = int(datetime.utcnow().timestamp())
                existing.sku = f"{existing.sku}-OLD-{timestamp_suffix}"
                self.session.add(existing)
                # No hacemos commit aún, se hará junto con la creación del nuevo

        ingredient = Ingredient(
            id=uuid.uuid4(),
            company_id=company_id,
            name=name,
            sku=sku,
            base_unit=base_unit,
            current_cost=current_cost,
            last_cost=Decimal(0),
            yield_factor=yield_factor,
            category_id=category_id,
            ingredient_type=ingredient_type,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        self.session.add(ingredient)
        await self.session.commit()
        await self.session.refresh(ingredient)
        return ingredient

    async def get_by_id(self, ingredient_id: uuid.UUID) -> Optional[Ingredient]:
        """Obtiene un ingrediente por ID."""
        stmt = select(Ingredient).where(Ingredient.id == ingredient_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, company_id: int, sku: str) -> Optional[Ingredient]:
        """Obtiene un ingrediente por SKU dentro de una empresa."""
        stmt = select(Ingredient).where(
            and_(Ingredient.company_id == company_id, Ingredient.sku == sku)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(
        self, company_id: int, active_only: bool = True, skip: int = 0, limit: int = 100,
        branch_id: Optional[int] = None,
        ingredient_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[dict]:
        """Lista ingredientes de una empresa, opcionalmente con stock de una sucursal y filtro por tipo."""
        if branch_id:
            # Query con JOIN para obtener stock y valor del inventario
            # Necesitamos sumar (quantity_remaining * cost_per_unit) de los lotes activos
            from sqlalchemy import func
            
            # Subquery para stock total
            # Subquery para stock total (Calculated from Batches for accuracy)
            stock_subquery = select(
                IngredientBatch.ingredient_id,
                func.sum(IngredientBatch.quantity_remaining).label("stock")
            ).where(
                IngredientBatch.branch_id == branch_id, 
                IngredientBatch.is_active == True
            ).group_by(IngredientBatch.ingredient_id).subquery()
            
            # Subquery para valor del inventario (Total Invested)
            # PRECISIÓN MEJORADA: Si no hay consumo, usa total_cost directamente
            # Si hay consumo parcial, usa fórmula proporcional
            from sqlalchemy import case
            value_expr = case(
                # Si no hay consumo (remaining == initial), usar total_cost directo
                (IngredientBatch.quantity_remaining == IngredientBatch.quantity_initial, 
                 IngredientBatch.total_cost),
                # Si hay consumo parcial, calcular proporcional
                else_=IngredientBatch.total_cost * (
                    IngredientBatch.quantity_remaining / 
                    func.nullif(IngredientBatch.quantity_initial, 0)
                )
            )
            value_subquery = select(
                IngredientBatch.ingredient_id,
                func.sum(value_expr).label("total_value")
            ).where(
                IngredientBatch.branch_id == branch_id,
                IngredientBatch.is_active == True
            ).group_by(IngredientBatch.ingredient_id).subquery()

            stmt = select(
                    Ingredient, 
                    stock_subquery.c.stock,
                    value_subquery.c.total_value
                )\
                .outerjoin(stock_subquery, Ingredient.id == stock_subquery.c.ingredient_id)\
                .outerjoin(value_subquery, Ingredient.id == value_subquery.c.ingredient_id)\
                .where(Ingredient.company_id == company_id)
        else:
            # Query global (all branches) with aggregation
            from sqlalchemy import func
            
            # Subquery for total stock across all branches
            # Subquery for total stock across all branches directly from BATCHES (Source of Truth)
            stock_subquery = select(
                IngredientBatch.ingredient_id,
                func.sum(IngredientBatch.quantity_remaining).label("stock")
            ).join(IngredientBatch.ingredient).where(
                Ingredient.company_id == company_id,
                IngredientBatch.is_active == True
            ).group_by(IngredientBatch.ingredient_id).subquery()
            
            # Subquery for total value (active batches) across all branches
            # PRECISIÓN MEJORADA: Si no hay consumo, usa total_cost directamente
            from sqlalchemy import case
            value_expr = case(
                (IngredientBatch.quantity_remaining == IngredientBatch.quantity_initial, 
                 IngredientBatch.total_cost),
                else_=IngredientBatch.total_cost * (
                    IngredientBatch.quantity_remaining / 
                    func.nullif(IngredientBatch.quantity_initial, 0)
                )
            )
            value_subquery = select(
                IngredientBatch.ingredient_id,
                func.sum(value_expr).label("total_value")
            ).join(IngredientBatch.ingredient).where(
                Ingredient.company_id == company_id,
                IngredientBatch.is_active == True
            ).group_by(IngredientBatch.ingredient_id).subquery()

            stmt = select(
                    Ingredient, 
                    stock_subquery.c.stock,
                    value_subquery.c.total_value
                )\
                .outerjoin(stock_subquery, Ingredient.id == stock_subquery.c.ingredient_id)\
                .outerjoin(value_subquery, Ingredient.id == value_subquery.c.ingredient_id)\
                .where(Ingredient.company_id == company_id)

        # Common Filters (Apply search BEFORE offset/limit)
        if search:
            stmt = stmt.where(
                or_(
                    Ingredient.name.ilike(f"%{search}%"),
                    Ingredient.sku.ilike(f"%{search}%")
                )
            )
            
        if ingredient_type:
            # Convert string to Enum if needed for proper comparison
            from app.models.ingredient import IngredientType
            try:
                type_enum = IngredientType(ingredient_type) if isinstance(ingredient_type, str) else ingredient_type
                stmt = stmt.where(Ingredient.ingredient_type == type_enum)
            except ValueError:
                # Invalid type string, filter will return nothing
                pass

        if active_only:
            stmt = stmt.where(Ingredient.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        rows = result.all()
        
        # Process rows to calculate cost and return dicts
        final_results = []
        for row in rows:
            # row structure is (Ingredient, stock, total_value) due to the select keys
            ingredient = row[0]
            stock = row[1] or 0
            total_value = row[2] or 0
            
            # --- BACKEND FINANCIAL LOGIC ---
            # Calculate Effective Cost (WAC vs Reference)
            if stock > 0 and total_value > 0:
                calculated_cost = total_value / stock
                print(f"[DEBUG-BACKEND] WAC Calc for {ingredient.name}: Stock={stock}, Val={total_value} -> EffCost={calculated_cost}")
            else:
                calculated_cost = ingredient.current_cost
                print(f"[DEBUG-BACKEND] Fallback Cost for {ingredient.name}: Stock={stock} -> EffCost={calculated_cost}")
            
            # Serialize to dict (Manual mapping for performance/custom fields)
            ing_dict = {
                "id": ingredient.id,
                "company_id": ingredient.company_id,
                "name": ingredient.name,
                "sku": ingredient.sku,
                "ingredient_type": ingredient.ingredient_type,
                "base_unit": ingredient.base_unit,
                "yield_factor": ingredient.yield_factor,
                "current_cost": ingredient.current_cost,
                "last_cost": ingredient.last_cost,
                "category_id": ingredient.category_id,
                "is_active": ingredient.is_active,
                "created_at": ingredient.created_at,
                "updated_at": ingredient.updated_at,
                "stock": stock,
                "total_inventory_value": total_value,
                "calculated_cost": calculated_cost 
            }
            final_results.append(ing_dict)
            
        return final_results

    async def _try_restore_original_sku(self, ingredient: Ingredient) -> None:
        """
        Intenta restaurar el SKU original de un ingrediente eliminado.
        Elimina sufijos como '-DEL-...' si el SKU original está disponible.
        """
        if not ingredient.sku or "-DEL-" not in ingredient.sku:
            return

        # Extraer posible SKU original (todo antes del PRIMER -DEL-)
        # Formato esperado: "ORIGINAL-SKU-DEL-TIMESTAMP"
        # Si hay anidados: "ORIGINAL-SKU-DEL-1-DEL-2" -> Queremos "ORIGINAL-SKU"
        parts = ingredient.sku.split("-DEL-")
        if len(parts) < 2:
            return
            
        # Tomar siempre la raíz (parte 0) como el objetivo ideal
        original_sku = parts[0]
        
        # Verificar si está disponible 
        
        # Verificar si está disponible
        existing = await self.get_by_sku(ingredient.company_id, original_sku)
        
        if not existing:
            # Está libre, lo tomamos
            print(f"[RECOVERY] Restoring SKU for {ingredient.name}: {ingredient.sku} -> {original_sku}")
            ingredient.sku = original_sku
        else:
            # Está ocupado. 
            # Si el que ocupa el SKU está inactivo, podríamos liberarlo ('robarle' el SKU),
            # pero por seguridad (evitar ciclos), mejor dejamos este con su sufijo o generamos uno nuevo.
            # LOGIC: Si está ocupado, NO hacemos nada. El usuario deberá arreglarlo manualmente si quiere.
            print(f"[RECOVERY] Cannot restore SKU {original_sku} for {ingredient.name}. It is taken.")

    async def update(
        self,
        ingredient_id: uuid.UUID,
        name: Optional[str] = None,
        sku: Optional[str] = None,
        base_unit: Optional[str] = None,
        current_cost: Optional[Decimal] = None,
        yield_factor: Optional[float] = None,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Ingredient]:
        """Actualiza un ingrediente existente."""
        ingredient = await self.get_by_id(ingredient_id)
        if not ingredient:
            return None

        if name is not None:
            ingredient.name = name
        if sku is not None:
            # Verificar unicidad de nuevo SKU
            existing = await self.get_by_sku(ingredient.company_id, sku)
            if existing and existing.id != ingredient_id:
                if existing.is_active:
                    raise HTTPException(status_code=400, detail=f"SKU {sku} already exists")
                else:
                    # Liberar SKU de ítem inactivo
                    timestamp_suffix = int(datetime.utcnow().timestamp())
                    existing.sku = f"{existing.sku}-OLD-{timestamp_suffix}"
                    self.session.add(existing)
            ingredient.sku = sku
        if base_unit is not None:
            ingredient.base_unit = base_unit
        if current_cost is not None:
            # Guardar costo anterior antes de actualizar
            previous_cost = ingredient.current_cost
            if current_cost != previous_cost:
                ingredient.last_cost = previous_cost
                ingredient.current_cost = current_cost
                
                # Log History
                history = IngredientCostHistory(
                    ingredient_id=ingredient.id,
                    previous_cost=previous_cost,
                    new_cost=current_cost,
                    reason="Actualización manual",
                    created_at=datetime.utcnow()
                )
                self.session.add(history)
        if yield_factor is not None:
            ingredient.yield_factor = yield_factor
        if category_id is not None:
            ingredient.category_id = category_id
        if is_active is not None:
            # Detectar restauración: De inactivo (False) a activo (True)
            if is_active is True and not ingredient.is_active:
                await self._try_restore_original_sku(ingredient)
                
            ingredient.is_active = is_active

        ingredient.updated_at = datetime.utcnow()
        self.session.add(ingredient)
        await self.session.commit()
        await self.session.refresh(ingredient)
        return ingredient

    async def delete(self, ingredient_id: uuid.UUID) -> bool:
        """Elimina lógicamente un ingrediente (soft delete) y libera su SKU."""
        ingredient = await self.get_by_id(ingredient_id)
        if not ingredient:
            return False

        # Liberar SKU añadiendo sufijo si está activo
        if ingredient.is_active:
            # Evitar anidamiento: Si ya tiene -DEL-, usamos la raiz
            base_sku = ingredient.sku.split("-DEL-")[0]
            
            timestamp_suffix = int(datetime.utcnow().timestamp())
            ingredient.sku = f"{base_sku}-DEL-{timestamp_suffix}"
            ingredient.is_active = False
            ingredient.updated_at = datetime.utcnow()
            
            self.session.add(ingredient)
            await self.session.commit()
            
        return True

    async def update_cost_from_purchase(
        self, 
        ingredient_id: uuid.UUID, 
        new_cost: Decimal, 
        use_weighted_average: bool = False,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Optional[Ingredient]:
        """
        Actualiza el costo de un ingrediente y registra el historial.
        """
        ingredient = await self.get_by_id(ingredient_id)
        if not ingredient:
            return None

        previous_cost = ingredient.current_cost
        ingredient.last_cost = previous_cost
        
        if use_weighted_average:
            # Promedio simple para MVP (idealmente necesitaría stock actual)
            ingredient.current_cost = (ingredient.current_cost + new_cost) / 2
        else:
            ingredient.current_cost = new_cost

        ingredient.updated_at = datetime.utcnow()
        self.session.add(ingredient)
        
        # Registrar Historial
        if ingredient.current_cost != previous_cost:
            history = IngredientCostHistory(
                ingredient_id=ingredient.id,
                previous_cost=previous_cost,
                new_cost=ingredient.current_cost,
                reason=reason,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            self.session.add(history)

        await self.session.commit()
        await self.session.refresh(ingredient)
        return ingredient

    async def get_cost_history(self, ingredient_id: uuid.UUID) -> List[IngredientCostHistory]:
        """Obtiene el historial de costos de un ingrediente."""
        stmt = select(IngredientCostHistory)\
            .where(IngredientCostHistory.ingredient_id == ingredient_id)\
            .order_by(IngredientCostHistory.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_batches(self, ingredient_id: uuid.UUID, active_only: bool = True) -> List[IngredientBatch]:
        """Obtener lotes de un ingrediente."""
        stmt = select(IngredientBatch).where(IngredientBatch.ingredient_id == ingredient_id)
        if active_only:
            stmt = stmt.where(IngredientBatch.is_active == True)
        
        stmt = stmt.order_by(IngredientBatch.acquired_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[IngredientBatch]:
        """Obtiene un lote por ID."""
        stmt = select(IngredientBatch).where(IngredientBatch.id == batch_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_batch(
        self,
        batch_id: uuid.UUID,
        quantity_initial: Optional[Decimal] = None,
        quantity_remaining: Optional[Decimal] = None,
        cost_per_unit: Optional[Decimal] = None,
        total_cost: Optional[Decimal] = None,
        supplier: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[IngredientBatch]:
        """Actualiza un lote existente con todos sus campos."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None

        # Actualizar cantidad inicial
        if quantity_initial is not None:
            batch.quantity_initial = quantity_initial
            
        # Actualizar cantidad restante
        if quantity_remaining is not None:
            batch.quantity_remaining = quantity_remaining
            # Si cantidad es 0, desactivar automáticamente
            if quantity_remaining <= 0:
                batch.is_active = False
                
        # Actualizar costos
        if cost_per_unit is not None:
            batch.cost_per_unit = cost_per_unit
        if total_cost is not None:
            batch.total_cost = total_cost
            
        # Recalcular costo unitario si se cambió total_cost pero no cost_per_unit
        if total_cost is not None and cost_per_unit is None and batch.quantity_initial > 0:
            batch.cost_per_unit = total_cost / batch.quantity_initial
            
        # Recalcular total_cost si se cambió cost_per_unit pero no total_cost
        if cost_per_unit is not None and total_cost is None:
            batch.total_cost = cost_per_unit * batch.quantity_initial
            
        if supplier is not None:
            batch.supplier = supplier
        if is_active is not None:
            batch.is_active = is_active

        # Integrity Check: Force deactivation if quantity is zero
        # This overrides manual is_active=True to prevent ghost batches
        current_remaining = quantity_remaining if quantity_remaining is not None else batch.quantity_remaining
        if current_remaining <= 0:
            batch.is_active = False

        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def delete_batch(self, batch_id: uuid.UUID) -> bool:
        """
        Elimina un lote (hard delete) y actualiza el inventario.
        
        IMPORTANTE: NO usa update_ingredient_stock() para evitar que el FIFO
        consuma de otros lotes. Solo decrementa directamente el inventario.
        """
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return False

        # Actualizar stock directamente (SIN FIFO)
        if batch.quantity_remaining > 0:
            from app.models.ingredient_inventory import IngredientInventory, IngredientTransaction
            
            # 1. Obtener inventario
            stmt = select(IngredientInventory).where(
                IngredientInventory.branch_id == batch.branch_id,
                IngredientInventory.ingredient_id == batch.ingredient_id
            ).with_for_update()
            result = await self.session.execute(stmt)
            inventory = result.scalar_one_or_none()
            
            if inventory:
                # 2. Decrementar stock directamente
                inventory.stock -= batch.quantity_remaining
                self.session.add(inventory)
                
                # 3. Registrar transacción
                txn = IngredientTransaction(
                    inventory_id=inventory.id,
                    transaction_type="BATCH_DELETION",
                    quantity=-batch.quantity_remaining,
                    balance_after=inventory.stock,
                    reference_id=None,
                    user_id=None,
                    reason=f"Eliminación de lote {batch.id}"
                )
                self.session.add(txn)

        await self.session.delete(batch)
        await self.session.commit()
        return True

    async def sync_inventory_from_batches(self, company_id: int):
        """
        FORCE SYNC: Updates ingredient_inventory and ingredient cost 
        based on the SUM of active batches.
        Serves as the 'Single Source of Truth' repair tool.
        """
        from sqlalchemy import select, func
        from app.models.ingredient import Ingredient
        from app.models.ingredient_batch import IngredientBatch
        from app.models.ingredient_inventory import IngredientInventory
        
        # 1. Get all ingredients for company
        stmt = select(Ingredient).where(Ingredient.company_id == company_id)
        result = await self.session.execute(stmt)
        ingredients = result.scalars().all()
        
        sync_log = []
        
        for ing in ingredients:
            # 2. Get Real Stock from Batches (Grouped by Branch)
            batch_query = select(
                IngredientBatch.branch_id,
                func.sum(IngredientBatch.quantity_remaining).label("real_stock")
            ).where(
                IngredientBatch.ingredient_id == ing.id,
                IngredientBatch.is_active == True
            ).group_by(IngredientBatch.branch_id)
            
            batches_result = await self.session.execute(batch_query)
            batches_data = batches_result.fetchall()
            
            # Map branch_id -> stock
            real_stock_map = {row.branch_id: row.real_stock for row in batches_data}
            
            # 3. Update Inventory Records
            # First, get existing inventory records
            inv_query = select(IngredientInventory).where(IngredientInventory.ingredient_id == ing.id)
            inv_result = await self.session.execute(inv_query)
            inventories = inv_result.scalars().all()
            
            existing_branches = set()
            
            for inv in inventories:
                existing_branches.add(inv.branch_id)
                real_val = real_stock_map.get(inv.branch_id, 0)
                
                if float(inv.stock) != float(real_val):
                    old_val = inv.stock
                    inv.stock = real_val
                    sync_log.append(f"Updated {ing.name} (Branch {inv.branch_id}): {old_val} -> {real_val}")
            
            # Create missing records if batches exist for a branch but no inventory record
            for branch_id, real_val in real_stock_map.items():
                if branch_id not in existing_branches:
                    new_inv = IngredientInventory(
                        ingredient_id=ing.id,
                        branch_id=branch_id,
                        stock=real_val,
                        min_stock=0,
                        max_stock=100
                    )
                    self.session.add(new_inv)
                    sync_log.append(f"Created Inv {ing.name} (Branch {branch_id}): {real_val}")
            
            # 4. Repair Cost (If 0 and batches exist)
            if ing.current_cost == 0:
                latest_batch_q = select(IngredientBatch).where(
                    IngredientBatch.ingredient_id == ing.id,
                    IngredientBatch.is_active == True,
                    IngredientBatch.cost_per_unit > 0
                ).order_by(IngredientBatch.acquired_at.desc()).limit(1)
                lb_res = await self.session.execute(latest_batch_q)
                latest_batch = lb_res.scalar_one_or_none()
                
                if latest_batch:
                   ing.current_cost = latest_batch.cost_per_unit
                   sync_log.append(f"Fixed Cost {ing.name}: $0 -> ${latest_batch.cost_per_unit}")

        await self.session.commit()
        return sync_log

