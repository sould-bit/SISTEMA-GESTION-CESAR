from typing import List, Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.ingredient import Ingredient
from app.services.unit_conversion_service import UnitConversionService

class RecipeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversion_service = UnitConversionService(session)

    async def create_recipe(self, product_id: int, company_id: int, name: str, items_data: List[dict]) -> Recipe:
        """
        Crea una receta nueva y calcula su costo inicial.
        """
        recipe = Recipe(
            id=uuid.uuid4(),
            product_id=product_id,
            company_id=company_id,
            name=name,
            version=1
        )
        self.session.add(recipe)
        await self.session.flush() # Para tener ID si fuera serial, pero es UUID
        
        total_cost = Decimal(0)
        
        for item_data in items_data:
            ingredient_id = item_data["ingredient_id"]
            # Buscar ingrediente para obtener costo
            stmt = select(Ingredient).where(Ingredient.id == ingredient_id, Ingredient.company_id == company_id)
            result = await self.session.execute(stmt)
            ingredient = result.scalar_one_or_none()

            if not ingredient:
                raise HTTPException(status_code=400, detail=f"Ingredient {ingredient_id} not found")

            # Calcular costo del item
            # Necesitamos convertir unidades: (recipe_unit -> base_unit) * unit_cost
            gross_qty = item_data["gross_quantity"]
            measure_unit = item_data["measure_unit"]

            # Convertir gross_qty (measure_unit) -> quantity (base_unit)
            try:
                qty_in_base = await self.conversion_service.convert(gross_qty, measure_unit, ingredient.base_unit)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            item_cost = Decimal(qty_in_base) * ingredient.current_cost

            item = RecipeItem(
                id=uuid.uuid4(),
                recipe_id=recipe.id,
                ingredient_id=ingredient_id,
                company_id=company_id,
                gross_quantity=gross_qty,
                net_quantity=item_data["net_quantity"],
                measure_unit=measure_unit,
                calculated_cost=item_cost
            )
            self.session.add(item)
            total_cost += item_cost

        recipe.total_cost = total_cost
        self.session.add(recipe)
        await self.session.commit()
        await self.session.refresh(recipe)
        return recipe

    async def recalculate_recipe_cost(self, recipe_id: int) -> Decimal:
        """
        Recalcula el costo total de una receta basado en los costos actuales de sus ingredientes.
        """
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        result = await self.session.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            return Decimal(0)

        # Obtener items
        stmt_items = select(RecipeItem).where(RecipeItem.recipe_id == recipe_id)
        result_items = await self.session.execute(stmt_items)
        items = result_items.scalars().all()

        total_cost = Decimal(0)
        
        for item in items:
            # Obtener ingrediente actual
            stmt_ing = select(Ingredient).where(Ingredient.id == item.ingredient_id)
            result_ing = await self.session.execute(stmt_ing)
            ingredient = result_ing.scalar_one_or_none()

            if ingredient:
                 try:
                    qty_in_base = await self.conversion_service.convert(item.gross_quantity, item.measure_unit, ingredient.base_unit)
                    # Actualizar snapshot cost
                    new_item_cost = Decimal(qty_in_base) * ingredient.current_cost
                    item.calculated_cost = new_item_cost
                    self.session.add(item)
                    total_cost += new_item_cost
                 except ValueError:
                     pass # Log error

        recipe.total_cost = total_cost
        self.session.add(recipe)
        await self.session.commit()
        return total_cost
