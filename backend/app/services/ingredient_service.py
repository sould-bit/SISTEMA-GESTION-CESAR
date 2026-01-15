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
        sku: str,
        base_unit: str,
        current_cost: Decimal = Decimal(0),
        yield_factor: float = 1.0,
        category_id: Optional[int] = None,
    ) -> Ingredient:
        """Crea un nuevo ingrediente."""
        # Verificar unicidad de SKU por empresa
        existing = await self.get_by_sku(company_id, sku)
        if existing:
            raise HTTPException(status_code=400, detail=f"SKU {sku} already exists for this company")

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
            # Query con JOIN para obtener stock
            stmt = select(Ingredient, IngredientInventory.stock)\
                .outerjoin(IngredientInventory, 
                    and_(
                        Ingredient.id == IngredientInventory.ingredient_id,
                        IngredientInventory.branch_id == branch_id
                    )
                )\
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
            # Procesar tuplas (Ingredient, stock)
            rows = result.all()
            for ingredient, stock in rows:
                data = ingredient.model_dump()
                data["stock"] = stock if stock is not None else Decimal(0)
                ingredients_data.append(data)
        else:
            # Resultado estándar
            rows = result.scalars().all()
            for ingredient in rows:
                data = ingredient.model_dump()
                # Stock opcional/0 si no se pide branch
                data["stock"] = Decimal(0) 
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
                raise HTTPException(status_code=400, detail=f"SKU {sku} already exists")
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
        """Elimina lógicamente un ingrediente (soft delete)."""
        ingredient = await self.get_by_id(ingredient_id)
        if not ingredient:
            return False

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

