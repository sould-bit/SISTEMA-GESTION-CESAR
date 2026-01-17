from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
import uuid

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.recipe_analytics_service import RecipeAnalyticsService
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from sqlmodel import select
from sqlalchemy.orm import selectinload

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
    responses={404: {"description": "Not found"}},
)

class CalibrationItem(BaseModel):
    ingredient_id: uuid.UUID
    new_quantity: float

class CalibrationRequest(BaseModel):
    items: List[CalibrationItem]

@router.get("/recipe-efficiency/{recipe_id}")
async def get_recipe_efficiency(
    recipe_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = RecipeAnalyticsService(session)
    # Use user's branch for analysis? Or Company aggregate?
    # Usually analysis is per branch or global. 
    # Let's default to user's branch if available, else first branch.
    branch_id = current_user.branch_id or 1
    
    recommendation = await service.get_recipe_recommendation(recipe_id, branch_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    return recommendation

@router.post("/calibrate-recipe/{recipe_id}")
async def calibrate_recipe(
    recipe_id: uuid.UUID,
    data: CalibrationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Aplica los cambios sugeridos a la receta.
    Actualiza gross_quantity de los items.
    """
    # Verify recipe belongs to company
    stmt = select(Recipe).where(Recipe.id == recipe_id, Recipe.company_id == current_user.company_id)
    res = await session.execute(stmt)
    recipe = res.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    # Update Items
    updated_count = 0
    from decimal import Decimal
    
    for cal_item in data.items:
        # Find item in recipe
        stmt_item = select(RecipeItem).where(
            RecipeItem.recipe_id == recipe_id,
            RecipeItem.ingredient_id == cal_item.ingredient_id
        )
        res_item = await session.execute(stmt_item)
        item = res_item.scalar_one_or_none()
        
        if item:
            item.gross_quantity = Decimal(cal_item.new_quantity)
            session.add(item)
            updated_count += 1
            
    await session.commit()
    
    # 2. Recalculate Cost
    from app.services.recipe_service import RecipeService
    recipe_service = RecipeService(session)
    recalc_res = await recipe_service.recalculate_cost(recipe_id, current_user.company_id)
    
    # 3. Financial Analysis & Price Suggestion
    # Reload recipe with product to get Price
    stmt_rp = select(Recipe).where(Recipe.id == recipe_id).options(selectinload(Recipe.product))
    res_rp = await session.execute(stmt_rp)
    recipe_fresh = res_rp.scalar_one()
    
    product = recipe_fresh.product
    analysis = {
        "status": "calibrated", 
        "items_updated": updated_count,
        "old_cost": float(recalc_res.old_total_cost or 0),
        "new_cost": float(recalc_res.new_total_cost or 0),
        "cost_increase": float((recalc_res.new_total_cost or 0) - (recalc_res.old_total_cost or 0))
    }
    
    if product and product.price > 0:
        old_cost = recalc_res.old_total_cost or Decimal(0)
        new_cost = recalc_res.new_total_cost or Decimal(0)
        price = product.price
        
        # Current Margin (Pre-calibration)
        # Avoid zero division
        old_margin_pct = 0.0
        if price > 0:
            old_margin_pct = float((price - old_cost) / price)
            
        # Suggested Price to maintain exact margin %
        # P_new = C_new / (1 - Margin%)
        suggested_price = float(price)
        if old_margin_pct < 1.0: # Valid margin
             cost_factor = 1.0 - old_margin_pct
             if cost_factor > 0:
                 suggested_price = float(new_cost) / cost_factor
        
        analysis.update({
            "current_price": float(price),
            "old_margin_pct": old_margin_pct,
            "new_margin_pct_if_static": float((price - new_cost) / price) if price > 0 else 0,
            "suggested_price": round(suggested_price, 2)
        })
        
    return analysis
