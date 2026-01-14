"""
Motor de Costos para el Sistema de Ingeniería de Menú.

UPDATED: Aligned with actual database schema where:
- RecipeItems use ingredient_product_id referencing products table
- Products can act as "ingredients" for recipes
- IDs are INTEGER not UUID

Este servicio se encarga de:
1. Recalcular costos de recetas cuando cambia el precio de un producto/ingrediente.
2. Propagar cambios de costos a productos relacionados.
3. Servir como punto central para cálculos de rentabilidad.
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.product import Product


class CostEngineService:
    """
    Servicio central para el cálculo y propagación de costos.
    
    Implementa el patrón Observer: cuando un producto ingrediente cambia de precio,
    se recalculan todas las recetas que lo usan.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def recalculate_all_recipes_for_product(self, product_id: int) -> List[int]:
        """
        Recalcula el costo de todas las recetas que usan un producto como ingrediente.
        
        Llamado típicamente cuando:
        - Se actualiza el precio de un producto que se usa como ingrediente.
        
        Returns:
            Lista de IDs de recetas actualizadas.
        """
        # Obtener el producto actualizado
        stmt_prod = select(Product).where(Product.id == product_id)
        result_prod = await self.session.execute(stmt_prod)
        product = result_prod.scalar_one_or_none()
        
        if not product:
            return []
        
        # Encontrar todos los RecipeItems que usan este producto
        stmt_items = select(RecipeItem).where(RecipeItem.ingredient_product_id == product_id)
        result_items = await self.session.execute(stmt_items)
        items = result_items.scalars().all()
        
        updated_recipe_ids = set()
        
        for item in items:
            # Recalcular costo del item usando precio del producto
            # unit_cost = cantidad * precio_unitario del producto
            if item.quantity and product.price:
                new_item_cost = Decimal(str(item.quantity)) * Decimal(str(product.price))
                item.unit_cost = new_item_cost
                self.session.add(item)
                updated_recipe_ids.add(item.recipe_id)
        
        # Recalcular total_cost de cada receta afectada
        for recipe_id in updated_recipe_ids:
            await self._recalculate_recipe_total(recipe_id)
        
        await self.session.commit()
        return list(updated_recipe_ids)

    async def _recalculate_recipe_total(self, recipe_id: int) -> Decimal:
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
        
        total = sum((item.unit_cost or Decimal(0) for item in items), Decimal(0))
        recipe.total_cost = total
        self.session.add(recipe)
        
        return total

    async def calculate_recipe_margin(self, recipe_id: int, selling_price: Decimal) -> dict:
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
        
        food_cost = recipe.total_cost or Decimal(0)
        gross_profit = selling_price - food_cost
        food_cost_percentage = (food_cost / selling_price) * 100
        margin_percentage = (gross_profit / selling_price) * 100
        
        return {
            "food_cost_percentage": round(food_cost_percentage, 2),
            "margin_percentage": round(margin_percentage, 2),
            "gross_profit": round(gross_profit, 2),
        }

    async def get_product_impact_analysis(self, product_id: int) -> dict:
        """
        Analiza el impacto de un producto-ingrediente en el menú.
        
        Returns:
            dict con recipes_count, total_recipes_cost, avg_usage_per_recipe
        """
        stmt_items = (
            select(RecipeItem)
            .where(RecipeItem.ingredient_product_id == product_id)
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
        total_cost = sum((item.unit_cost or Decimal(0) for item in items), Decimal(0))
        avg_usage = sum(float(item.quantity or 0) for item in items) / len(items)
        
        return {
            "recipes_count": recipes_count,
            "total_recipes_cost": round(total_cost, 2),
            "avg_usage_per_recipe": round(avg_usage, 2),
        }

    # Legacy support for ingredient-based calls (optional fallback)
    async def recalculate_all_recipes_for_ingredient(self, ingredient_id) -> List[int]:
        """
        Legacy method - redirects to product-based recalculation.
        The system uses products as ingredients, not a separate ingredients table.
        """
        # This is a stub - in the current schema, ingredients ARE products
        # If ingredient_id is passed, we'll skip recalculation since
        # the separate ingredients table is not used for recipe_items
        return []
