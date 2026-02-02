from decimal import Decimal
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import uuid

from app.models.inventory import Inventory, InventoryTransaction
from app.models.ingredient_inventory import IngredientInventory, IngredientTransaction
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.ingredient import Ingredient
from app.models.ingredient_batch import IngredientBatch
from app.services.unit_conversion_service import UnitConversionService

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversion_service = UnitConversionService(db)

    # =========================================================================
    # PRODUCT INVENTORY (Level A)
    # =========================================================================

    async def get_stock(self, branch_id: int, product_id: int, for_update: bool = False) -> Optional[Inventory]:
        """Obtener registro de inventario para un producto en una sucursal"""
        statement = select(Inventory).where(
            Inventory.branch_id == branch_id,
            Inventory.product_id == product_id
        )
        if for_update:
            statement = statement.with_for_update()
            
        result = await self.db.execute(statement)
        return result.scalars().one_or_none()

    async def initialize_stock(self, branch_id: int, product_id: int) -> Inventory:
        """Crear registro de inventario inicial (en 0)"""
        inventory = Inventory(
            branch_id=branch_id,
            product_id=product_id,
            stock=Decimal("0.000")
        )
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory

    async def update_stock(
        self, 
        branch_id: int, 
        product_id: int, 
        quantity_delta: Decimal, 
        transaction_type: str,
        user_id: int,
        reference_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Inventory:
        """
        Actualizar stock de manera transaccional.
        - quantity_delta: Positivo para entrada, Negativo para salida/venta
        """
        # 1. Obtener o crear inventario
        inventory = await self.get_stock(branch_id, product_id, for_update=True)
        if not inventory:
            inventory = await self.initialize_stock(branch_id, product_id)

        # 2. Calcular nuevo balance
        new_balance = inventory.stock + quantity_delta
        
        # 3. Validación: No permitir stock negativo (opcional, por ahora soft-check)
        if new_balance < 0 and transaction_type in ["SALE", "OUT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {inventory.stock}, Solicitado: {abs(quantity_delta)}"
            ) 

        # 4. Actualizar Inventario
        inventory.stock = new_balance
        self.db.add(inventory)

        # 5. Registrar Transacción (Kardex)
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=transaction_type,
            quantity=quantity_delta,
            balance_after=new_balance,
            reference_id=reference_id,
            reason=reason,
            user_id=user_id
        )
        self.db.add(transaction)
        
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory

    async def get_low_stock_alerts(self, branch_id: int) -> List[Inventory]:
        """Listar productos con stock debajo del mínimo"""
        statement = select(Inventory).where(
            Inventory.branch_id == branch_id,
            Inventory.stock <= Inventory.min_stock
        )
        result = await self.db.execute(statement)
        return result.scalars().all()

    # =========================================================================
    # INGREDIENT INVENTORY (Level C)
    # =========================================================================

    async def get_ingredient_stock(self, branch_id: int, ingredient_id: uuid.UUID, for_update: bool = False) -> Optional[IngredientInventory]:
        statement = select(IngredientInventory).where(
            IngredientInventory.branch_id == branch_id,
            IngredientInventory.ingredient_id == ingredient_id
        )
        if for_update:
            statement = statement.with_for_update()

        result = await self.db.execute(statement)
        return result.scalars().one_or_none()

    async def initialize_ingredient_stock(self, branch_id: int, ingredient_id: uuid.UUID) -> IngredientInventory:
        inventory = IngredientInventory(
            branch_id=branch_id,
            ingredient_id=ingredient_id,
            stock=Decimal("0.000")
        )
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory

    async def update_ingredient_stock(
        self,
        branch_id: int,
        ingredient_id: uuid.UUID,
        quantity_delta: Decimal,
        transaction_type: str,
        user_id: Optional[int] = None,
        reference_id: Optional[str] = None,
        reason: Optional[str] = None,
        cost_per_unit: Optional[Decimal] = None,
        supplier: Optional[str] = None
    ) -> (IngredientInventory, Decimal, Optional[IngredientBatch]):
        """
        Update Ingredient Stock (Realidad Física).
        Maneja creación de Lotes (Batches) para entradas y consumo FIFO para salidas.
        Retorna: (Inventory, TotalCostOfTransaction)
        """
        inventory = await self.get_ingredient_stock(branch_id, ingredient_id, for_update=True)
        if not inventory:
            inventory = await self.initialize_ingredient_stock(branch_id, ingredient_id)

        # Determinar el delta real y nuevo balance
        if transaction_type == "ADJUST":
            # Si es ajuste absoluto, calculamos la diferencia
            new_balance = quantity_delta
            actual_delta = new_balance - inventory.stock
        else:
            # Si es delta (IN/OUT/SALE)
            new_balance = inventory.stock + quantity_delta
            actual_delta = quantity_delta

        # Validación básica de negativo
        if new_balance < 0 and transaction_type in ["SALE", "OUT", "PRODUCTION_OUT"]:
             # Permitir stock negativo temporalmente si es necesario
            stmt_name = select(Ingredient.name).where(Ingredient.id == ingredient_id)
            res_name = await self.db.execute(stmt_name)
            ing_name = res_name.scalar_one_or_none() or str(ingredient_id)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insumo insuficiente {ing_name}. Disponible: {inventory.stock}"
            )

        # ---------------------------------------------------------
        # MANEJO DE LOTES (FIFO)
        # ---------------------------------------------------------
        
        transaction_cost = Decimal(0)
        
        # CASO 1: ENTRADA DE STOCK (Crear Lote)
        # Solo si es un aumento positivo Y se provee costo (O es una Compra/Ajuste explÃ­cito)
        if actual_delta > 0 and cost_per_unit is not None:
            new_batch = IngredientBatch(
                ingredient_id=ingredient_id,
                branch_id=branch_id,
                quantity_initial=actual_delta,
                quantity_remaining=actual_delta,
                cost_per_unit=cost_per_unit,
                total_cost=actual_delta * cost_per_unit,
                supplier=supplier,
                is_active=True
            )
            self.db.add(new_batch)
            transaction_cost = new_batch.total_cost # Costo de lo que entró
            
            # Actualizar costo del ingrediente (Ãšltimo costo registrado)
            # Opcional: PodrÃ­amos calcular promedio ponderado aquÃ­
            stmt_ing = select(Ingredient).where(Ingredient.id == ingredient_id)
            res_ing = await self.db.execute(stmt_ing)
            ingredient_obj = res_ing.scalar_one_or_none()
            if ingredient_obj:
                ingredient_obj.last_cost = ingredient_obj.current_cost # Move current to last
                ingredient_obj.current_cost = cost_per_unit
                self.db.add(ingredient_obj)


        # CASO 2: SALIDA DE STOCK (Consumo FIFO)
        elif actual_delta < 0:
            qty_to_consume = abs(actual_delta)
            transaction_cost, batch_consumptions = await self._consume_stock_fifo(branch_id, ingredient_id, qty_to_consume)
            # batch_consumptions can be used by caller (e.g., ProductionService) to store tracking data

        # ---------------------------------------------------------
        
        inventory.stock = new_balance
        self.db.add(inventory)

        txn = IngredientTransaction(
            inventory_id=inventory.id,
            transaction_type=transaction_type,
            quantity=actual_delta,
            balance_after=new_balance,
            reference_id=reference_id,
            user_id=user_id,
            reason=reason or supplier
        )
        self.db.add(txn)
        await self.db.commit()
        
        # Return batch_consumptions only if FIFO consumption occurred
        consumed_batches = batch_consumptions if 'batch_consumptions' in locals() else []
        return inventory, transaction_cost, new_batch if 'new_batch' in locals() else None, consumed_batches

    async def restore_stock_to_batches(
        self,
        branch_id: int,
        ingredient_id: uuid.UUID,
        quantity: Decimal,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        unit_cost: Optional[Decimal] = None
    ) -> IngredientInventory:
        """
        Restaura stock a un lote existente (Logic Smart Merge).
        Prioridad:
        1. Lote Activo con MISMO costo.
        2. Lote Activo más reciente (cualquier costo).
        3. Lote Inactivo más reciente (reactivarlo).
        4. Crear nuevo (Fallback).
        """
        # 1. Update Inventory (Single Source of Truth)
        inventory = await self.get_ingredient_stock(branch_id, ingredient_id, for_update=True)
        if not inventory:
             inventory = await self.initialize_ingredient_stock(branch_id, ingredient_id)
        
        inventory.stock += quantity
        self.db.add(inventory)

        # 2. Find Target Batch
        target_batch = None
        
        # Base Query for this ingredient/branch
        stmt_base = select(IngredientBatch).where(
            IngredientBatch.branch_id == branch_id,
            IngredientBatch.ingredient_id == ingredient_id
        )

        # Priority 1: Active + Exact Cost Match
        if unit_cost is not None:
            stmt_p1 = stmt_base.where(
                IngredientBatch.is_active == True,
                IngredientBatch.cost_per_unit == unit_cost
            ).order_by(IngredientBatch.acquired_at.desc())
            res_p1 = await self.db.execute(stmt_p1)
            target_batch = res_p1.scalars().first()

        # Priority 2: Active (Any Cost) - Latest
        if not target_batch:
            stmt_p2 = stmt_base.where(
                IngredientBatch.is_active == True
            ).order_by(IngredientBatch.acquired_at.desc())
            res_p2 = await self.db.execute(stmt_p2)
            target_batch = res_p2.scalars().first()

        # Priority 3: Inactive (Latest) - Reactivate
        if not target_batch:
            stmt_p3 = stmt_base.order_by(IngredientBatch.acquired_at.desc())
            res_p3 = await self.db.execute(stmt_p3)
            target_batch = res_p3.scalars().first()

        # Execute Update or Create New
        if target_batch:
            target_batch.quantity_remaining += quantity
            target_batch.is_active = True # Ensure valid
            self.db.add(target_batch)
            actual_cost_per_unit = target_batch.cost_per_unit
        else:
            # Fallback: Create new (Should rarely happen if historical data exists)
            actual_cost_per_unit = unit_cost or Decimal(0)
            new_batch = IngredientBatch(
                ingredient_id=ingredient_id,
                branch_id=branch_id,
                quantity_initial=quantity,
                quantity_remaining=quantity,
                cost_per_unit=actual_cost_per_unit,
                total_cost=quantity * actual_cost_per_unit,
                supplier="Restauración (Sin Lote Previo)",
                is_active=True
            )
            self.db.add(new_batch)

        # 3. Transaction Log
        txn = IngredientTransaction(
            inventory_id=inventory.id,
            transaction_type="PRODUCTION_ROLLBACK",
            quantity=quantity,
            balance_after=inventory.stock,
            reference_id=None,
            user_id=user_id,
            reason=reason or f"Restaurado a Lote {'Existente' if target_batch else 'Nuevo'}"
        )
        self.db.add(txn)
        
        await self.db.commit()
        return inventory

    async def _consume_stock_fifo(
        self, 
        branch_id: int, 
        ingredient_id: uuid.UUID, 
        quantity: Decimal
    ) -> tuple[Decimal, list[dict]]:
        """
        Consume stock de lotes FIFO.
        
        Returns:
            Tuple of (total_cost, batch_consumptions)
            - total_cost: Costo total de lo consumido.
            - batch_consumptions: Lista de dicts con {batch_id, quantity_consumed, cost_attributed}.
        """
        total_cost = Decimal(0)
        remaining_to_consume = quantity
        batch_consumptions = []

        # Buscar lotes activos ordenados por antigüedad (FIFO)
        stmt_batches = select(IngredientBatch).where(
            IngredientBatch.branch_id == branch_id,
            IngredientBatch.ingredient_id == ingredient_id,
            IngredientBatch.is_active == True
        ).order_by(IngredientBatch.acquired_at.asc())

        result_batches = await self.db.execute(stmt_batches)
        active_batches = result_batches.scalars().all()

        for batch in active_batches:
            if remaining_to_consume <= 0:
                break
            
            available = batch.quantity_remaining
            
            if available >= remaining_to_consume:
                # Este lote cubre todo lo que falta
                consumed_qty = remaining_to_consume
                cost_chunk = consumed_qty * batch.cost_per_unit
                total_cost += cost_chunk
                
                batch.quantity_remaining -= consumed_qty
                
                # FIX: Si el lote quedó en 0 exacto, desactivarlo
                if batch.quantity_remaining <= 0:
                    batch.is_active = False
                    
                remaining_to_consume = Decimal(0)
            else:
                # Consumimos todo este lote y seguimos
                consumed_qty = available
                cost_chunk = consumed_qty * batch.cost_per_unit
                total_cost += cost_chunk
                
                remaining_to_consume -= consumed_qty
                batch.quantity_remaining = Decimal(0)
                batch.is_active = False  # Lote agotado
            
            # Record batch consumption for later reversal
            batch_consumptions.append({
                "batch_id": batch.id,
                "quantity_consumed": consumed_qty,
                "cost_attributed": cost_chunk
            })
            
            self.db.add(batch)
            
        return total_cost, batch_consumptions

    async def restore_stock_to_batch(
        self,
        batch_id: uuid.UUID,
        quantity: Decimal,
        branch_id: int,
        ingredient_id: uuid.UUID,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Restore stock to a SPECIFIC batch (precise reversal).
        
        This is used during production undo to return stock to the exact
        batch it was consumed from.
        """
        # 1. Update Inventory (Single Source of Truth)
        inventory = await self.get_ingredient_stock(branch_id, ingredient_id, for_update=True)
        if not inventory:
            inventory = await self.initialize_ingredient_stock(branch_id, ingredient_id)
        
        inventory.stock += quantity
        self.db.add(inventory)

        # 2. Update the specific batch
        stmt = select(IngredientBatch).where(IngredientBatch.id == batch_id)
        result = await self.db.execute(stmt)
        batch = result.scalar_one_or_none()
        
        if batch:
            batch.quantity_remaining += quantity
            # Only reactivate if we're actually restoring stock
            if quantity > 0:
                batch.is_active = True
            self.db.add(batch)
        else:
            # Batch was deleted? Log warning but don't crash
            import logging
            logging.warning(f"Batch {batch_id} not found for stock restoration. Creating fallback.")
            # Fallback: Use smart restoration (legacy behavior)
            await self.restore_stock_to_batches(
                branch_id, ingredient_id, quantity, user_id, reason
            )
            return

        # 3. Create Transaction
        txn = IngredientTransaction(
            inventory_id=inventory.id,
            transaction_type="PRODUCTION_ROLLBACK",
            quantity=quantity,
            balance_after=inventory.stock,
            user_id=user_id,
            reason=reason or f"Restaurado a Lote {batch_id}"
        )
        self.db.add(txn)



    # =========================================================================
    # LIVE RECIPE EXPLOSION (Level B -> C)
    # =========================================================================

    async def process_recipe_deduction(self, branch_id: int, product_id: int, quantity_sold: int, user_id: int, reference_id: str):
        """
        Explosión de Materiales:
        Deduce stock basado en la Receta Activa. Si no hay receta, deduce del producto (fallback).
        """
        # 1. Check Active Recipe
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            return # Should not happen

        if product.active_recipe_id:
            # 2. Load Recipe Items
            stmt_recipe = select(Recipe).where(Recipe.id == product.active_recipe_id)
            result_recipe = await self.db.execute(stmt_recipe)
            recipe = result_recipe.scalar_one_or_none()

            if recipe:
                # Load Items
                # Implicitly loaded or fetch explicitly
                stmt_items = select(RecipeItem).where(RecipeItem.recipe_id == recipe.id)
                res_items = await self.db.execute(stmt_items)
                items = res_items.scalars().all()

                for item in items:
                    # 3. Calculate Deduction: Gross Qty * Units Sold
                    total_gross_qty = item.gross_quantity * quantity_sold

                    # 4. Get Ingredient Base Unit for conversion
                    stmt_ing = select(Ingredient).where(Ingredient.id == item.ingredient_id)
                    res_ing = await self.db.execute(stmt_ing)
                    ingredient = res_ing.scalar_one_or_none()

                    if ingredient:
                        # Convert to base unit
                        qty_to_deduct = await self.conversion_service.convert(
                            total_gross_qty, item.measure_unit, ingredient.base_unit
                        )

                        # 5. Deduct from Ingredient Inventory
                        await self.update_ingredient_stock(
                            branch_id=branch_id,
                            ingredient_id=ingredient.id,
                            quantity_delta=Decimal(qty_to_deduct) * -1,
                            transaction_type="SALE",
                            user_id=user_id,
                            reference_id=reference_id
                        )
                return

        # Fallback: Deduct Product Stock directly if no recipe
        await self.update_stock(
            branch_id=branch_id,
            product_id=product_id,
            quantity_delta=Decimal(quantity_sold) * -1,
            transaction_type="SALE",
            user_id=user_id,
            reference_id=reference_id
        )
