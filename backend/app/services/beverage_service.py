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
    
    async def get_merchandise_ingredients(self, company_id: int) -> list[Ingredient]:
        """Get all MERCHANDISE type ingredients for a company."""
        stmt = select(Ingredient).where(
            Ingredient.company_id == company_id,
            Ingredient.ingredient_type == IngredientType.MERCHANDISE,
            Ingredient.is_active == True
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
