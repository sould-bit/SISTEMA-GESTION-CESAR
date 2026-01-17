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
from sqlalchemy import select, and_
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
        self, company_id: int, active_only: bool = True, skip: int = 0, limit: int = 100, branch_id: Optional[int] = None
    ) -> List[dict]:
        """Lista ingredientes de una empresa, opcionalmente con stock de una sucursal."""
        if branch_id:
            # Query con JOIN para obtener stock y valor del inventario
            # Necesitamos sumar (quantity_remaining * cost_per_unit) de los lotes activos
            from sqlalchemy import func
            
            # Subquery para stock total
            stock_subquery = select(
                IngredientInventory.ingredient_id,
                IngredientInventory.stock
            ).where(IngredientInventory.branch_id == branch_id).subquery()
            
            # Subquery para valor del inventario (Total Invested)
            value_subquery = select(
                IngredientBatch.ingredient_id,
                func.sum(IngredientBatch.quantity_remaining * IngredientBatch.cost_per_unit).label("total_value")
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
            # Query simple sin stock (solo Ingredient)
            stmt = select(Ingredient).where(Ingredient.company_id == company_id)
            
        if active_only:
            stmt = stmt.where(Ingredient.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        
        ingredients_data = []
        if branch_id:
            # Procesar tuplas (Ingredient, stock, total_value)
            rows = result.all()
            for ingredient, stock, total_value in rows:
                data = ingredient.model_dump()
                data["stock"] = stock if stock is not None else Decimal(0)
                data["total_inventory_value"] = total_value if total_value is not None else Decimal(0)
                ingredients_data.append(data)
        else:
            # Resultado estándar
            rows = result.scalars().all()
            for ingredient in rows:
                data = ingredient.model_dump()
                # Stock opcional/0 si no se pide branch
                data["stock"] = Decimal(0) 
                data["total_inventory_value"] = Decimal(0)
                ingredients_data.append(data)
                
        return ingredients_data

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
            timestamp_suffix = int(datetime.utcnow().timestamp())
            ingredient.sku = f"{ingredient.sku}-DEL-{timestamp_suffix}"
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

        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def delete_batch(self, batch_id: uuid.UUID) -> bool:
        """Elimina un lote (hard delete) y actualiza el inventario."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return False

        # Actualizar stock (Restar lo que queda en el lote)
        if batch.quantity_remaining > 0:
            from app.services.inventory_service import InventoryService
            inv_service = InventoryService(self.session)
            await inv_service.update_ingredient_stock(
                branch_id=batch.branch_id,
                ingredient_id=batch.ingredient_id,
                quantity_delta=-batch.quantity_remaining,
                transaction_type="BATCH_DELETION", # Use custom type for Delta update
                reason=f"Eliminación de lote {batch.id}"
            )

        await self.session.delete(batch)
        await self.session.commit()
        return True

