from typing import List, Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.services.unit_conversion_service import UnitConversionService
from app.schemas.recipes import (
    RecipeUpdate,
    RecipeItemCreate,
    RecipeResponse,
    RecipeListResponse,
    RecipeItemResponse,
    RecipeCostRecalculateResponse
)

class RecipeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversion_service = UnitConversionService(session)

    async def list_recipes(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False
    ) -> List[Recipe]:
        stmt = select(Recipe).where(Recipe.company_id == company_id)
        if not include_inactive:
            stmt = stmt.where(Recipe.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit).order_by(Recipe.created_at.desc())
        stmt = stmt.options(selectinload(Recipe.product)) 
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recipe(self, recipe_id: uuid.UUID, company_id: int) -> Optional[Recipe]:
        stmt = select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.company_id == company_id
        ).options(
            selectinload(Recipe.items).selectinload(RecipeItem.ingredient),
            selectinload(Recipe.product)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_recipe_by_product(self, product_id: int, company_id: int) -> Optional[Recipe]:
        stmt = select(Recipe).where(
            Recipe.product_id == product_id,
            Recipe.company_id == company_id
        ).options(
            selectinload(Recipe.items).selectinload(RecipeItem.ingredient),
            selectinload(Recipe.product)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_recipe(self, product_id: int, company_id: int, name: str, items_data: List[dict]) -> Recipe:
        """
        Crea una receta nueva y calcula su costo inicial.
        """
        # Validar si ya existe receta para este producto?
        # TODO: Add check if product already has recipe? Router docs say "Un producto solo puede tener una receta"
        
        recipe = Recipe(
            id=uuid.uuid4(),
            product_id=product_id,
            company_id=company_id,
            name=name,
            version=1
        )
        self.session.add(recipe)
        await self.session.flush() # Para tener ID disponible si fuera necesario, aunque es UUID
        
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
                net_quantity=item_data.get("net_quantity"), # Optional?
                measure_unit=measure_unit,
                calculated_cost=item_cost
            )
            # Calculate cost method in model uses yield_factor, but here we did manual calc. 
            # Let's trust manual calc for now or use model method? 
            # Model method: self.net_quantity = ...
            # Code above set net_quantity from input.
            
            self.session.add(item)
            total_cost += item_cost

        recipe.total_cost = total_cost
        self.session.add(recipe)
        await self.session.commit()
        await self.session.refresh(recipe)
        # Load relationships for response
        stmt = select(Recipe).where(Recipe.id == recipe.id).options(
            selectinload(Recipe.items).selectinload(RecipeItem.ingredient),
            selectinload(Recipe.product)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_recipe(self, recipe_id: uuid.UUID, company_id: int, update_data: RecipeUpdate) -> Recipe:
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        if update_data.name is not None:
            recipe.name = update_data.name
        # Description not in model, ignore
        if update_data.is_active is not None:
            recipe.is_active = update_data.is_active
            
        self.session.add(recipe)
        await self.session.commit()
        await self.session.refresh(recipe)
        return recipe

    async def update_recipe_items(self, recipe_id: uuid.UUID, company_id: int, items_data: List[RecipeItemCreate]) -> Recipe:
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
             raise HTTPException(status_code=404, detail="Recipe not found")

        # Delete existing items
        stmt = delete(RecipeItem).where(RecipeItem.recipe_id == recipe_id)
        await self.session.execute(stmt)
        
        total_cost = Decimal(0)
        
        for item_data in items_data:
            ingredient_id = item_data.ingredient_id
            stmt = select(Ingredient).where(Ingredient.id == ingredient_id, Ingredient.company_id == company_id)
            result = await self.session.execute(stmt)
            ingredient = result.scalar_one_or_none()
            
            if not ingredient:
                raise HTTPException(status_code=400, detail=f"Ingredient {ingredient_id} not found")

            gross_qty = item_data.gross_quantity
            measure_unit = item_data.measure_unit

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
                net_quantity=None, # Will be calculated or null
                measure_unit=measure_unit,
                calculated_cost=item_cost
            )
            self.session.add(item)
            total_cost += item_cost
             
        recipe.total_cost = total_cost
        self.session.add(recipe)
        await self.session.commit()
        await self.session.refresh(recipe)
        
        # Reload for response
        return await self.get_recipe(recipe_id, company_id)

    async def delete_recipe(self, recipe_id: uuid.UUID, company_id: int):
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
             raise HTTPException(status_code=404, detail="Recipe not found")
        
        recipe.is_active = False
        self.session.add(recipe)
        await self.session.commit()

    async def recalculate_cost(self, recipe_id: uuid.UUID, company_id: int) -> RecipeCostRecalculateResponse:
         recipe = await self.get_recipe(recipe_id, company_id)
         if not recipe:
             raise HTTPException(status_code=404, detail="Recipe not found")
             
         old_cost = recipe.total_cost
         
         # Logic from previous recalculate_recipe_cost
         stmt_items = select(RecipeItem).where(RecipeItem.recipe_id == recipe_id)
         result_items = await self.session.execute(stmt_items)
         items = result_items.scalars().all()
         
         new_total_cost = Decimal(0)
         items_updated = 0
         
         for item in items:
            stmt_ing = select(Ingredient).where(Ingredient.id == item.ingredient_id)
            result_ing = await self.session.execute(stmt_ing)
            ingredient = result_ing.scalar_one_or_none()

            if ingredient:
                 try:
                    qty_in_base = await self.conversion_service.convert(item.gross_quantity, item.measure_unit, ingredient.base_unit)
                    new_item_cost = Decimal(qty_in_base) * ingredient.current_cost
                    if item.calculated_cost != new_item_cost:
                        item.calculated_cost = new_item_cost
                        self.session.add(item)
                        items_updated += 1
                    new_total_cost += new_item_cost
                 except ValueError:
                     pass 

         recipe.total_cost = new_total_cost
         self.session.add(recipe)
         await self.session.commit()
         
         return RecipeCostRecalculateResponse(
             recipe_id=recipe_id,
             old_total_cost=old_cost,
             new_total_cost=new_total_cost,
             difference=new_total_cost - old_cost,
             items_updated=items_updated
         )

    def build_recipe_response(self, recipe: Recipe) -> RecipeResponse:
        items_response = []
        for item in recipe.items:
             items_response.append(RecipeItemResponse(
                 id=item.id,
                 recipe_id=item.recipe_id,
                 ingredient_id=item.ingredient_id,
                 gross_quantity=item.gross_quantity,
                 net_quantity=item.net_quantity,
                 measure_unit=item.measure_unit,
                 calculated_cost=item.calculated_cost,
                 ingredient_name=item.ingredient.name if item.ingredient else None,
                 ingredient_unit=item.ingredient.base_unit if item.ingredient else None,
                 created_at=item.created_at
             ))
        
        return RecipeResponse(
            id=recipe.id,
            company_id=recipe.company_id,
            product_id=recipe.product_id,
            product_name=recipe.product.name if recipe.product else None,
            name=recipe.name,
            description=None, # Not in model
            total_cost=recipe.total_cost,
            is_active=recipe.is_active,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            items=items_response,
            items_count=len(recipe.items)
        )

    def build_recipe_list_response(self, recipe: Recipe) -> RecipeListResponse:
        return RecipeListResponse(
            id=recipe.id,
            company_id=recipe.company_id,
            product_id=recipe.product_id,
            product_name=recipe.product.name if recipe.product else None,
            name=recipe.name,
            total_cost=recipe.total_cost,
            is_active=recipe.is_active,
            items_count=len(recipe.items) if recipe.items else 0, # Assuming items might not be loaded, check logic
            created_at=recipe.created_at
        )
