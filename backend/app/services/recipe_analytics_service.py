from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col
from app.models.ingredient_inventory import IngredientInventory, IngredientTransaction
from app.models.inventory_count import InventoryCount, InventoryCountItem
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem

class RecipeAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ingredient_usage_stats(
        self, 
        ingredient_id: uuid.UUID, 
        branch_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> dict:
        """
        Calcula el uso teórico vs real de un ingrediente.
        """
        # 1. Uso Teórico (Ventas)
        # Sumar transacciones de tipo SALE
        # Need to join IngredientInventory to filter by ingredient_id
        stmt_theoretical = select(func.sum(IngredientTransaction.quantity))\
            .join(IngredientInventory)\
            .where(
                IngredientInventory.ingredient_id == ingredient_id,
                IngredientInventory.branch_id == branch_id,
                IngredientTransaction.transaction_type == "SALE",
                IngredientTransaction.created_at >= start_date,
                IngredientTransaction.created_at <= end_date
            )
        res_theo = await self.db.execute(stmt_theoretical)
        theoretical_usage = abs(res_theo.scalar() or 0) # Sale is negative, take abs
        
        # 2. Desviaciones (Auditorías)
        stmt_adj = select(func.sum(IngredientTransaction.quantity))\
            .join(IngredientInventory)\
            .where(
                IngredientInventory.ingredient_id == ingredient_id,
                IngredientInventory.branch_id == branch_id,
                IngredientTransaction.transaction_type == "ADJUST",
                IngredientTransaction.created_at >= start_date,
                IngredientTransaction.created_at <= end_date
            )
        res_adj = await self.db.execute(stmt_adj)
        adjustments = res_adj.scalar() or 0
        
        real_usage = Decimal(theoretical_usage) - Decimal(adjustments)
        
        # Prepare Insight Message
        message = ""
        if real_usage > 0:
            diff_pct = (real_usage - theoretical_usage) / real_usage
            if abs(diff_pct) > 0.1: # Significant deviation
                # Convert to readable units (simplified for now, using base unit)
                # Ideally use UnitConversionService to display in "g" or "kg" appropriately
                excess_or_save = "más" if real_usage > theoretical_usage else "menos"
                message = f"Tu receta dice {theoretical_usage:.2f}, pero tu cocina usa {real_usage:.2f} reales."
        
        return {
            "ingredient_id": ingredient_id,
            "theoretical_usage": float(theoretical_usage),
            "real_usage": float(real_usage),
            "discrepancy": float(adjustments), # Negative = Loss
            "efficiency": float(theoretical_usage / real_usage) if real_usage > 0 else 1.0,
            "message": message
        }

    async def get_recipe_recommendation(self, recipe_id: uuid.UUID, branch_id: int):
        """
        Analiza una receta y sugiere calibración basada en el ingrediente principal.
        """
        # 1. Get Recipe
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        # Load items
        from sqlalchemy.orm import selectinload
        stmt = stmt.options(selectinload(Recipe.items).selectinload(RecipeItem.ingredient))
        res = await self.db.execute(stmt)
        recipe = res.scalar_one_or_none()
        
        if not recipe:
            return None
            
        recommendations = []
        
        # Periodo de análisis: Últimos 30 días default
        end_date = datetime.utcnow()
        from datetime import timedelta
        start_date = end_date - timedelta(days=30)
        
        for item in recipe.items:
            # Analizar cada ingrediente
            stats = await self.get_ingredient_usage_stats(
                item.ingredient_id, 
                branch_id, 
                start_date, 
                end_date
            )
            print(f"DEBUG STATS for {item.ingredient_id}: {stats}")
            
            # Simple Heuristic: If discrepancy > 10%
            if stats["efficiency"] < 0.9: # Consume mas de lo esperado
                # Suggest increasing quantity
                # New quantity = Current * (Real / Theoretical) = Current / Efficiency
                # Example: Receta 150g. Eff 0.83 (150/180).
                # New = 150 / 0.83 = 180g.
                current_qty = float(item.gross_quantity)
                suggested_qty = current_qty / stats["efficiency"]
                
                cost_impact = (suggested_qty - current_qty) * float(item.ingredient.current_cost or 0)
                
                recommendations.append({
                    "ingredient_name": item.ingredient.name,
                    "current_quantity": current_qty,
                    "suggested_quantity": round(suggested_qty, 3),
                    "efficiency": round(stats["efficiency"], 2),
                    "cost_impact_per_unit": round(cost_impact, 2),
                    "message": f"Tu cocina usa {round(suggested_qty, 1)}g reales vs {round(current_qty, 1)}g teóricos."
                })
                
        return {
            "recipe_id": recipe.id,
            "recipe_name": recipe.name,
            "period": "Last 30 days",
            "recommendations": recommendations
        }
