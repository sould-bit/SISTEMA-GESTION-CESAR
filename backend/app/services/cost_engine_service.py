"""
Motor de Costos para el Sistema de Ingeniería de Menú.

Este servicio se encarga de:
1. Recalcular costos de recetas cuando cambia el precio de un ingrediente.
2. Propagar cambios de costos a productos relacionados.
3. Servir como punto central para cálculos de rentabilidad.
"""

from typing import List
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.ingredient import Ingredient
from app.services.unit_conversion_service import UnitConversionService


class CostEngineService:
    """
    Servicio central para el cálculo y propagación de costos.
    
    Implementa el patrón Observer: cuando un ingrediente cambia de precio,
    se recalculan todas las recetas que lo usan.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversion_service = UnitConversionService(session)

    async def recalculate_all_recipes_for_ingredient(self, ingredient_id: uuid.UUID) -> List[uuid.UUID]:
        """
        Recalcula el costo de todas las recetas que usan un ingrediente específico.
        
        Llamado típicamente cuando:
        - Se registra una nueva compra (PurchaseOrder) con precio diferente.
        - Se actualiza manualmente el current_cost de un ingrediente.
        
        Returns:
            Lista de IDs de recetas actualizadas.
        """
        # Obtener el ingrediente actualizado
        stmt_ing = select(Ingredient).where(Ingredient.id == ingredient_id)
        result_ing = await self.session.execute(stmt_ing)
        ingredient = result_ing.scalar_one_or_none()
        
        if not ingredient:
            return []
        
        # Encontrar todos los RecipeItems que usan este ingrediente
        stmt_items = select(RecipeItem).where(RecipeItem.ingredient_id == ingredient_id)
        result_items = await self.session.execute(stmt_items)
        items = result_items.scalars().all()
        
        updated_recipe_ids = set()
        
        for item in items:
            # Recalcular costo del item
            try:
                qty_in_base = await self.conversion_service.convert(
                    item.gross_quantity, 
                    item.measure_unit, 
                    ingredient.base_unit
                )
                new_item_cost = Decimal(qty_in_base) * ingredient.current_cost
                item.calculated_cost = new_item_cost
                self.session.add(item)
                updated_recipe_ids.add(item.recipe_id)
            except ValueError:
                # Log: unidad no convertible
                pass
        
        # Recalcular total_cost de cada receta afectada
        for recipe_id in updated_recipe_ids:
            await self._recalculate_recipe_total(recipe_id)
        
        await self.session.commit()
        return list(updated_recipe_ids)

    async def _recalculate_recipe_total(self, recipe_id: uuid.UUID) -> Decimal:
        """
        Recalcula el total_cost de una receta sumando sus items.
        """
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        result = await self.session.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            return Decimal(0)
        
        stmt_items = select(RecipeItem).where(RecipeItem.recipe_id == recipe_id)
        result_items = await self.session.execute(stmt_items)
        items = result_items.scalars().all()
        
        total = sum((item.calculated_cost for item in items), Decimal(0))
        recipe.total_cost = total
        self.session.add(recipe)
        
        return total

    async def calculate_recipe_margin(self, recipe_id: uuid.UUID, selling_price: Decimal) -> dict:
        """
        Calcula el margen de ganancia de una receta.
        
        Returns:
            dict con food_cost_percentage, margin_percentage, gross_profit
        """
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        result = await self.session.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if not recipe or selling_price <= 0:
            return {
                "food_cost_percentage": Decimal(0),
                "margin_percentage": Decimal(0),
                "gross_profit": Decimal(0),
            }
        
        food_cost = recipe.total_cost
        gross_profit = selling_price - food_cost
        food_cost_percentage = (food_cost / selling_price) * 100
        margin_percentage = (gross_profit / selling_price) * 100
        
        return {
            "food_cost_percentage": round(food_cost_percentage, 2),
            "margin_percentage": round(margin_percentage, 2),
            "gross_profit": round(gross_profit, 2),
        }

    async def get_ingredient_impact_analysis(self, ingredient_id: uuid.UUID) -> dict:
        """
        Analiza el impacto de un ingrediente en el menú.
        
        Returns:
            dict con recipes_count, total_recipes_cost, avg_usage_per_recipe
        """
        stmt_items = (
            select(RecipeItem)
            .where(RecipeItem.ingredient_id == ingredient_id)
            .options(selectinload(RecipeItem.recipe))
        )
        result = await self.session.execute(stmt_items)
        items = result.scalars().all()
        
        if not items:
            return {
                "recipes_count": 0,
                "total_recipes_cost": Decimal(0),
                "avg_usage_per_recipe": 0,
            }
        
        recipes_count = len(set(item.recipe_id for item in items))
        total_cost = sum((item.calculated_cost for item in items), Decimal(0))
        avg_usage = sum(item.gross_quantity for item in items) / len(items)
        
        return {
            "recipes_count": recipes_count,
            "total_recipes_cost": round(total_cost, 2),
            "avg_usage_per_recipe": round(avg_usage, 2),
        }
