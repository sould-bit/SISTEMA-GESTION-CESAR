from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.modifier import ProductModifier, ModifierRecipeItem
from app.models.product import Product

class ModifierService:
    
    async def get_modifiers(self, session: AsyncSession, company_id: int) -> List[ProductModifier]:
        """Obtiene todos los modificadores de una empresa."""
        statement = (
            select(ProductModifier)
            .where(ProductModifier.company_id == company_id)
            .where(ProductModifier.is_active == True)
            .options(selectinload(ProductModifier.recipe_items).selectinload(ModifierRecipeItem.ingredient))
        )
        result = await session.execute(statement)
        modifiers = result.scalars().all()
        # Explicitly touch relationships to ensure they are loaded while session is active
        for output_modifier in modifiers:
            for item in output_modifier.recipe_items:
                _ = item.ingredient
        return modifiers

    async def get_modifier_by_id(self, session: AsyncSession, modifier_id: int) -> Optional[ProductModifier]:
        """Obtiene un modificador por ID, incluyendo sus items de receta."""
        statement = (
            select(ProductModifier)
            .where(ProductModifier.id == modifier_id)
            .options(selectinload(ProductModifier.recipe_items).selectinload(ModifierRecipeItem.ingredient))
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_modifier(self, session: AsyncSession, modifier_data: ProductModifier) -> ProductModifier:
        """Crea un nuevo modificador."""
        session.add(modifier_data)
        await session.commit()
        await session.refresh(modifier_data)
        return modifier_data

    async def update_modifier(self, session: AsyncSession, modifier_id: int, update_data: dict) -> Optional[ProductModifier]:
        """Actualiza un modificador existente."""
        modifier = await self.get_modifier_by_id(session, modifier_id)
        if not modifier:
            return None
            
        for key, value in update_data.items():
            setattr(modifier, key, value)
            
        session.add(modifier)
        await session.commit()
        await session.refresh(modifier)
        return modifier

    async def update_recipe_items(self, session: AsyncSession, modifier_id: int, items_data: List[dict]) -> ProductModifier:
        """
        Actualiza (reescribe) los items de la receta de un modificador.
        """
        modifier = await self.get_modifier_by_id(session, modifier_id)
        if not modifier:
            raise ValueError("Modificador no encontrado")

        # Eliminar items anteriores
        for item in modifier.recipe_items:
            await session.delete(item)
            
        # Crear nuevos items
        for item_data in items_data:
            new_item = ModifierRecipeItem(
                modifier_id=modifier_id,
                ingredient_product_id=item_data['ingredient_product_id'],
                quantity=item_data['quantity'],
                unit=item_data['unit']
            )
            session.add(new_item)
            
        await session.commit()
        # await session.refresh(modifier) # Refresh might not reload relationship immediately without expire
        return await self.get_modifier_by_id(session, modifier_id)

modifier_service = ModifierService()
