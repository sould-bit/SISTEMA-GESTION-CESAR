"""
Beverage Service - Atomic creation of MERCHANDISE items with Product + Ingredient + Recipe 1:1

This service implements the "1:1 Bridge" pattern where:
- In the warehouse: It's an Ingredient (MERCHANDISE type) with cost, supplier, stock
- On the table: It's a Product (sale) with price, photo, category
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.ingredient import Ingredient, IngredientType
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.services.ingredient_service import IngredientService
from app.services.inventory_service import InventoryService


class BeverageService:
    """
    Handles atomic creation of beverages/merchandise items.
    
    A beverage (Coca-Cola, Beer, etc.) has a "double life":
    - Ingredient (MERCHANDISE): For inventory, cost tracking, batches
    - Product: For sales, POS display, pricing
    - Recipe 1:1: Links them invisibly to reuse order stock deduction logic
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ingredient_service = IngredientService(db)
        self.inventory_service = InventoryService(db)
    
    async def create_beverage(
        self,
        name: str,
        cost: Decimal,
        sale_price: Decimal,
        initial_stock: Decimal,
        unit: str,
        branch_id: int,
        company_id: int,
        user_id: int,
        sku: Optional[str] = None,
        supplier: Optional[str] = None,
        image_url: Optional[str] = None,
        category_id: Optional[int] = None,
        category_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Atomically creates the complete beverage structure.
        Supports inline category creation/lookup via `category_name`.
        """
        # 0. Handle Category (Find or Create)
        final_category_id = category_id
        
        if category_name and not final_category_id:
            # Try to find existing category by name
            from app.models.category import Category
            stmt = select(Category).where(
                Category.name == category_name,
                Category.company_id == company_id
            )
            result = await self.db.execute(stmt)
            existing_cat = result.scalar_one_or_none()
            
            if existing_cat:
                final_category_id = existing_cat.id
            else:
                # Create new category
                new_cat = Category(
                    name=category_name,
                    company_id=company_id,
                    is_active=True
                )
                self.db.add(new_cat)
                await self.db.flush()
                final_category_id = new_cat.id

        # 1. Create Ingredient (the "warehouse" entity)
        final_sku = sku if sku else f"BEV-{name[:4].upper()}-{uuid.uuid4().hex[:6].upper()}"
        
        ingredient = Ingredient(
            name=name,
            sku=final_sku,
            base_unit=unit,
            current_cost=cost,
            last_cost=cost,
            yield_factor=1.0,  # No waste for packaged items
            category_id=final_category_id,
            company_id=company_id,
            ingredient_type=IngredientType.MERCHANDISE,
            is_active=True
        )
        self.db.add(ingredient)
        await self.db.flush()  # Get ingredient ID
        
        # 2. Create initial batch if stock > 0
        if initial_stock > 0:
            await self.inventory_service.update_ingredient_stock(
                branch_id=branch_id,
                ingredient_id=ingredient.id,
                quantity_delta=initial_stock,
                transaction_type="IN",
                cost_per_unit=cost,
                supplier=supplier or "Compra Inicial",
                user_id=user_id,
                reason=f"Stock inicial de {name}"
            )
        
        # 3. Create Product (the "sales" entity)
        product = Product(
            name=name,
            price=sale_price,
            stock=0,  # Stock is tracked via ingredient, not product
            category_id=final_category_id,
            company_id=company_id,
            image_url=image_url,
            description=description or f"Bebida: {name}",
            is_active=True,
            tax_rate=Decimal("0")
        )
        self.db.add(product)
        await self.db.flush()  # Get product ID
        
        # 4. Create Recipe 1:1 (the invisible bridge)
        recipe = Recipe(
            product_id=product.id,
            name=f"Receta Auto: {name}",
            description="Receta 1:1 generada automáticamente para mercadería",
            company_id=company_id,
            is_active=True
        )
        self.db.add(recipe)
        await self.db.flush()  # Get recipe ID
        
        # 5. Create single RecipeItem (qty=1)
        recipe_item = RecipeItem(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            company_id=company_id,
            gross_quantity=Decimal("1"),
            net_quantity=Decimal("1"),  # 1:1 ratio, yield is 1.0
            measure_unit=unit,
            calculated_cost=cost
        )
        self.db.add(recipe_item)
        
        # Commit transaction
        await self.db.commit()
        await self.db.refresh(product)
        await self.db.refresh(ingredient)
        await self.db.refresh(recipe)
        
        return {
            "product": product,
            "ingredient": ingredient,
            "recipe": recipe,
            "message": f"Bebida '{name}' creada exitosamente con estructura 1:1"
        }
    
    async def update_beverage(
        self,
        product_id: int,
        name: Optional[str] = None,
        cost: Optional[Decimal] = None,
        sale_price: Optional[Decimal] = None,
        image_url: Optional[str] = None,
        category_id: Optional[int] = None,
        sku: Optional[str] = None,
        additional_stock: Optional[Decimal] = None,
        branch_id: Optional[int] = None,
        user_id: Optional[int] = None,
        supplier: Optional[str] = None
    ) -> dict:
        """
        Updates a beverage and cascades changes to linked Ingredient.
        
        - Product: name, price, image_url, category_id
        - Ingredient: name, current_cost, sku
        - Optionally add more stock via new batch
        """
        # 1. Find the Product
        product = await self.db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # 2. Find the linked Recipe and Ingredient
        stmt = select(Recipe).where(
            Recipe.product_id == product_id,
            Recipe.is_active == True
        )
        result = await self.db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        ingredient = None
        if recipe:
            # Get the first (and only) recipe item to find the ingredient
            stmt = select(RecipeItem).where(RecipeItem.recipe_id == recipe.id)
            result = await self.db.execute(stmt)
            recipe_item = result.scalar_one_or_none()
            if recipe_item:
                ingredient = await self.db.get(Ingredient, recipe_item.ingredient_id)
        
        # FALLBACK: If no recipe found, try to find MERCHANDISE ingredient with same name
        if not ingredient:
            stmt = select(Ingredient).where(
                Ingredient.name == product.name,
                Ingredient.company_id == product.company_id,
                Ingredient.ingredient_type == IngredientType.MERCHANDISE,
                Ingredient.is_active == True
            )
            result = await self.db.execute(stmt)
            ingredient = result.scalar_one_or_none()
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"update_beverage: product={product.name}, recipe_found={recipe is not None}, ingredient_found={ingredient is not None}")
        
        # 3. Update Product fields
        if name is not None:
            product.name = name
        if sale_price is not None:
            product.price = sale_price
        if image_url is not None:
            product.image_url = image_url
        if category_id is not None:
            product.category_id = category_id
        
        # 4. Update Ingredient fields (if linked)
        if ingredient:
            if name is not None:
                ingredient.name = name
            if cost is not None:
                # Update current cost reference ONLY
                # (Do NOT update batches here; batches are historical records)
                # PROTECT against zeroing out cost accidentally
                if cost > 0:
                    ingredient.last_cost = ingredient.current_cost
                    ingredient.current_cost = cost
                else:
                    # Log warning or just ignore
                    logger.warning(f"Ignored attempt to set cost to {cost} for ingredient {ingredient.name}")
                
            if sku is not None:
                ingredient.sku = sku
        
        # 5. Add additional stock as new batch (if provided)
        if additional_stock and additional_stock > 0 and ingredient and branch_id:
            unit_cost = cost if cost else ingredient.current_cost
            await self.inventory_service.update_ingredient_stock(
                branch_id=branch_id,
                ingredient_id=ingredient.id,
                quantity_delta=additional_stock,
                transaction_type="IN",
                cost_per_unit=unit_cost,
                supplier=supplier or "Compra Adicional",
                user_id=user_id,
                reason=f"Stock adicional para {product.name}"
            )
        
        await self.db.commit()
        await self.db.refresh(product)
        if ingredient:
            await self.db.refresh(ingredient)
        
        return {
            "product": product,
            "ingredient": ingredient,
            "message": f"Bebida '{product.name}' actualizada correctamente"
        }
    
    async def delete_beverage(self, product_id: int) -> dict:
        """
        Soft-deletes a beverage and cascades to linked Ingredient and Batches.
        
        - Product: is_active = False
        - Ingredient: is_active = False  
        - Batches: is_active = False
        """
        # 1. Find the Product
        product = await self.db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # 2. Find the linked Recipe and Ingredient
        stmt = select(Recipe).where(
            Recipe.product_id == product_id,
            Recipe.is_active == True
        )
        result = await self.db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        ingredient = None
        if recipe:
            # Get the recipe item to find the ingredient
            stmt = select(RecipeItem).where(RecipeItem.recipe_id == recipe.id)
            result = await self.db.execute(stmt)
            recipe_item = result.scalar_one_or_none()
            if recipe_item:
                ingredient = await self.db.get(Ingredient, recipe_item.ingredient_id)
        
        # 3. Soft-delete Product
        product.is_active = False
        
        # 4. Soft-delete Ingredient (if linked)
        if ingredient:
            ingredient.is_active = False
            
            # 5. Deactivate all related batches
            from app.models.ingredient_batch import IngredientBatch
            stmt = select(IngredientBatch).where(
                IngredientBatch.ingredient_id == ingredient.id,
                IngredientBatch.is_active == True
            )
            result = await self.db.execute(stmt)
            batches = result.scalars().all()
            for batch in batches:
                batch.is_active = False
        
        # 6. Deactivate Recipe
        if recipe:
            recipe.is_active = False
        
        await self.db.commit()
        
        return {
            "message": f"Bebida '{product.name}' eliminada correctamente",
            "product_id": product_id,
            "ingredient_deactivated": ingredient is not None
        }
    
    async def get_merchandise_ingredients(self, company_id: int) -> list[Ingredient]:
        """Get all MERCHANDISE type ingredients for a company."""
        stmt = select(Ingredient).where(
            Ingredient.company_id == company_id,
            Ingredient.ingredient_type == IngredientType.MERCHANDISE,
            Ingredient.is_active == True
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

