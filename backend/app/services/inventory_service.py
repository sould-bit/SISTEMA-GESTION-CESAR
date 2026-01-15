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
    ) -> IngredientInventory:
        """
        Update Ingredient Stock (Realidad Física).
        Maneja creación de Lotes (Batches) para entradas y consumo FIFO para salidas.
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
        if new_balance < 0 and transaction_type in ["SALE", "OUT"]:
             # Permitir stock negativo temporalmente si es necesario, O lanzar error.
             # Por ahora mantenemos la restriccion pero podriamos relajarla si el usuario lo pide.
             # En FIFO, consumir mÃ¡s de lo que hay en lotes es posible (lotes quedan en 0, stock negativo total)
             # Pero idealmente no.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insumo insuficiente {ingredient_id}. Disponible: {inventory.stock}"
            )

        # ---------------------------------------------------------
        # MANEJO DE LOTES (FIFO)
        # ---------------------------------------------------------
        
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
            
            # Buscar lotes activos ordenados por antigÃ¼edad (oldest first)
            stmt_batches = select(IngredientBatch).where(
                IngredientBatch.branch_id == branch_id,
                IngredientBatch.ingredient_id == ingredient_id,
                IngredientBatch.is_active == True
            ).order_by(IngredientBatch.acquired_at.asc())
            
            result_batches = await self.db.execute(stmt_batches)
            active_batches = result_batches.scalars().all()
            
            remaining_to_consume = qty_to_consume
            
            for batch in active_batches:
                if remaining_to_consume <= 0:
                    break
                
                available = batch.quantity_remaining
                
                if available >= remaining_to_consume:
                    # Este lote cubre todo lo que falta
                    batch.quantity_remaining -= remaining_to_consume
                    remaining_to_consume = 0
                else:
                    # Consumimos todo este lote y seguimos
                    remaining_to_consume -= available
                    batch.quantity_remaining = Decimal(0)
                    batch.is_active = False # Lote agotado
                
                self.db.add(batch)
                
            # Nota: Si remaining_to_consume > 0, significa que se consumiÃ³ "aire" (stock sin lote)
            # Esto es consistente con permitir que el stock total baje de lo que suman los lotes
            # si hubo ajustes manuales previos sin lotes.

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
            reason=reason or supplier # Guardar supplier en reason si aplica
        )
        self.db.add(txn)
        await self.db.commit()
        return inventory

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
