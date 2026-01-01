"""
🍔 RECIPE SERVICE - Lógica de Negocio para Recetas

Este servicio maneja toda la lógica de recetas:
- CRUD completo de recetas
- Cálculo automático de costos
- Gestión de ingredientes
- Validaciones multi-tenant
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException, status

from app.models import Recipe, RecipeItem, Product
from app.schemas.recipes import (
    RecipeCreate,
    RecipeUpdate,
    RecipeItemCreate,
    RecipeResponse,
    RecipeListResponse,
    RecipeItemResponse,
    RecipeCostRecalculateResponse
)

import logging

logger = logging.getLogger(__name__)


class RecipeService:
    """
    🍔 Servicio de Recetas
    
    Maneja toda la lógica de negocio relacionada con recetas
    y cálculo de costos de productos.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CREATE ====================

    async def create_recipe(
        self,
        recipe_data: RecipeCreate,
        company_id: int
    ) -> Recipe:
        """
        Crear una nueva receta con sus ingredientes.
        
        Args:
            recipe_data: Datos de la receta incluyendo items
            company_id: ID de la empresa
            
        Returns:
            Recipe creada con costo calculado
        """
        # 1. Verificar que el producto existe y pertenece a la empresa
        product = await self._get_product(recipe_data.product_id, company_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {recipe_data.product_id} no encontrado"
            )

        # 2. Verificar que el producto no tiene receta
        existing = await self._get_recipe_by_product(recipe_data.product_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto ya tiene una receta asignada (ID: {existing.id})"
            )

        # 3. Validar que todos los ingredientes existen
        await self._validate_ingredients(recipe_data.items, company_id)

        # 4. Crear la receta
        recipe = Recipe(
            company_id=company_id,
            product_id=recipe_data.product_id,
            name=recipe_data.name,
            description=recipe_data.description,
            total_cost=Decimal("0.00"),
            is_active=True
        )
        self.db.add(recipe)
        await self.db.flush()  # Obtener ID

        # 5. Crear items y calcular costo
        total_cost = await self._create_recipe_items(recipe.id, recipe_data.items, company_id)
        recipe.total_cost = total_cost

        await self.db.commit()
        await self.db.refresh(recipe)

        logger.info(f"✅ Receta creada: {recipe.name} (ID: {recipe.id}) - Costo: ${total_cost}")
        logger.info(f"✅ Receta creada: {recipe.name} (ID: {recipe.id}) - Costo: ${total_cost}")
        
        # Re-fetch completo para response
        return await self.get_recipe(recipe.id, company_id)

    # ==================== READ ====================

    async def get_recipe(self, recipe_id: int, company_id: int) -> Optional[Recipe]:
        """Obtener receta por ID con sus items."""
        result = await self.db.execute(
            select(Recipe)
            .where(Recipe.id == recipe_id, Recipe.company_id == company_id)
            .options(
                selectinload(Recipe.items).selectinload(RecipeItem.ingredient),
                selectinload(Recipe.product)
            )
        )
        return result.scalar_one_or_none()

    async def get_recipe_by_product(
        self,
        product_id: int,
        company_id: int
    ) -> Optional[Recipe]:
        """Obtener receta de un producto específico."""
        result = await self.db.execute(
            select(Recipe)
            .where(
                Recipe.product_id == product_id,
                Recipe.company_id == company_id,
                Recipe.is_active == True
            )
            .options(selectinload(Recipe.items).selectinload(RecipeItem.ingredient))
        )
        return result.scalar_one_or_none()

    async def list_recipes(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False
    ) -> List[Recipe]:
        """Listar recetas de una empresa."""
        query = select(Recipe).where(Recipe.company_id == company_id)
        
        if not include_inactive:
            query = query.where(Recipe.is_active == True)
        
        query = query.options(
            selectinload(Recipe.product),
            selectinload(Recipe.items)
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== UPDATE ====================

    async def update_recipe(
        self,
        recipe_id: int,
        company_id: int,
        update_data: RecipeUpdate
    ) -> Recipe:
        """Actualizar datos básicos de una receta."""
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receta no encontrada"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(recipe, key, value)

        recipe.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(recipe)

        logger.info(f"✅ Receta actualizada: {recipe.name} (ID: {recipe.id})")
        logger.info(f"✅ Receta actualizada: {recipe.name} (ID: {recipe.id})")
        
        # Re-fetch completo para response
        return await self.get_recipe(recipe.id, company_id)

    async def update_recipe_items(
        self,
        recipe_id: int,
        company_id: int,
        items: List[RecipeItemCreate]
    ) -> Recipe:
        """
        Reemplazar todos los items de una receta.
        
        Esto elimina los items existentes y crea nuevos.
        """
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receta no encontrada"
            )

        # Validar ingredientes
        await self._validate_ingredients(items, company_id)

        # Eliminar items existentes
        for item in recipe.items:
            await self.db.delete(item)

        # Crear nuevos items
        total_cost = await self._create_recipe_items(recipe.id, items, company_id)
        recipe.total_cost = total_cost
        recipe.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(recipe)

        logger.info(f"✅ Items actualizados para receta {recipe.id} - Nuevo costo: ${total_cost}")
        logger.info(f"✅ Items actualizados para receta {recipe.id} - Nuevo costo: ${total_cost}")
        
        # Re-fetch completo para response
        return await self.get_recipe(recipe.id, company_id)

    # ==================== DELETE ====================

    async def delete_recipe(self, recipe_id: int, company_id: int) -> bool:
        """Soft delete de una receta."""
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receta no encontrada"
            )

        recipe.is_active = False
        recipe.updated_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"🗑️ Receta eliminada (soft): {recipe.name} (ID: {recipe.id})")
        return True

    # ==================== COST CALCULATION ====================

    async def recalculate_cost(self, recipe_id: int, company_id: int) -> RecipeCostRecalculateResponse:
        """
        Recalcular el costo total de una receta basado en precios actuales.
        
        Útil cuando los precios de ingredientes han cambiado.
        """
        recipe = await self.get_recipe(recipe_id, company_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receta no encontrada"
            )

        old_cost = recipe.total_cost
        new_cost = Decimal("0.00")
        items_updated = 0

        for item in recipe.items:
            # Obtener precio actual del ingrediente
            ingredient = await self._get_product(item.ingredient_product_id, company_id)
            if ingredient and ingredient.is_active:
                old_unit_cost = item.unit_cost
                item.unit_cost = ingredient.price
                new_cost += item.quantity * ingredient.price
                
                if old_unit_cost != ingredient.price:
                    items_updated += 1

        recipe.total_cost = new_cost
        recipe.updated_at = datetime.utcnow()

        await self.db.commit()

        difference = new_cost - old_cost
        logger.info(f"💰 Costo recalculado: {recipe.name} - Antes: ${old_cost}, Ahora: ${new_cost}")

        return RecipeCostRecalculateResponse(
            recipe_id=recipe_id,
            old_total_cost=old_cost,
            new_total_cost=new_cost,
            difference=difference,
            items_updated=items_updated
        )

    # ==================== PRIVATE METHODS ====================

    async def _get_product(self, product_id: int, company_id: int) -> Optional[Product]:
        """Obtener producto verificando empresa."""
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def _get_recipe_by_product(self, product_id: int) -> Optional[Recipe]:
        """Verificar si un producto ya tiene receta."""
        result = await self.db.execute(
            select(Recipe).where(Recipe.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def _validate_ingredients(
        self,
        items: List[RecipeItemCreate],
        company_id: int
    ) -> None:
        """Validar que todos los ingredientes existen y pertenecen a la empresa."""
        for item in items:
            ingredient = await self._get_product(item.ingredient_product_id, company_id)
            if not ingredient:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ingrediente {item.ingredient_product_id} no encontrado"
                )
            if not ingredient.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ingrediente '{ingredient.name}' está inactivo"
                )

    async def _create_recipe_items(
        self,
        recipe_id: int,
        items: List[RecipeItemCreate],
        company_id: int
    ) -> Decimal:
        """Crear items de receta y retornar costo total."""
        total_cost = Decimal("0.00")

        for item_data in items:
            # Obtener precio del ingrediente
            ingredient = await self._get_product(item_data.ingredient_product_id, company_id)
            unit_cost = ingredient.price if ingredient else Decimal("0.00")

            # Crear item
            recipe_item = RecipeItem(
                recipe_id=recipe_id,
                ingredient_product_id=item_data.ingredient_product_id,
                quantity=item_data.quantity,
                unit=item_data.unit,
                unit_cost=unit_cost
            )
            self.db.add(recipe_item)

            # Acumular costo
            total_cost += item_data.quantity * unit_cost

        return total_cost

    # ==================== RESPONSE BUILDERS ====================

    def build_recipe_response(self, recipe: Recipe) -> RecipeResponse:
        """Construir response completo de receta."""
        items_response = []
        for item in recipe.items:
            items_response.append(RecipeItemResponse(
                id=item.id,
                recipe_id=item.recipe_id,
                ingredient_product_id=item.ingredient_product_id,
                quantity=item.quantity,
                unit=item.unit,
                unit_cost=item.unit_cost,
                subtotal=item.quantity * item.unit_cost,
                ingredient_name=item.ingredient.name if item.ingredient else None,
                created_at=item.created_at
            ))

        return RecipeResponse(
            id=recipe.id,
            company_id=recipe.company_id,
            product_id=recipe.product_id,
            product_name=recipe.product.name if recipe.product else None,
            name=recipe.name,
            description=recipe.description,
            total_cost=recipe.total_cost,
            is_active=recipe.is_active,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            items=items_response,
            items_count=len(items_response)
        )

    def build_recipe_list_response(self, recipe: Recipe) -> RecipeListResponse:
        """Construir response para listado de recetas."""
        return RecipeListResponse(
            id=recipe.id,
            company_id=recipe.company_id,
            product_id=recipe.product_id,
            product_name=recipe.product.name if recipe.product else None,
            name=recipe.name,
            total_cost=recipe.total_cost,
            is_active=recipe.is_active,
            items_count=len(recipe.items) if recipe.items else 0,
            created_at=recipe.created_at
        )
