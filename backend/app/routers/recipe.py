"""
🍔 ROUTER DE RECETAS - API REST

Endpoints para gestión de recetas de productos.
Incluye CRUD completo y recálculo de costos.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.models import User
from app.services.recipe_service import RecipeService
from app.schemas.recipes import (
    RecipeCreate,
    RecipeUpdate,
    RecipeItemAddOrUpdate,
    RecipeResponse,
    RecipeListResponse,
    RecipeCostRecalculateResponse
)
from core.multi_tenant import verify_current_user_company

import logging

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN DEL ROUTER
# ============================================
router = APIRouter(prefix="/recipes", tags=["recipes"])


# ============================================
# DEPENDENCIA: RECIPE SERVICE
# ============================================
def get_recipe_service(session: AsyncSession = Depends(get_session)) -> RecipeService:
    """Inyectar RecipeService con sesión de BD."""
    return RecipeService(session)


# ============================================
# ENDPOINTS CRUD
# ============================================

@router.get("", response_model=List[RecipeListResponse])
async def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    📋 Listar todas las recetas de la empresa.
    
    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Máximo de registros a retornar
    - **include_inactive**: Incluir recetas inactivas
    """
    recipes = await recipe_service.list_recipes(
        company_id=company_id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )
    return [recipe_service.build_recipe_list_response(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    🔍 Obtener detalle de una receta con todos sus ingredientes.
    
    Retorna la receta con:
    - Lista completa de ingredientes
    - Costo total calculado
    - Subtotal por ingrediente
    """
    recipe = await recipe_service.get_recipe(recipe_id, company_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receta no encontrada"
        )
    return recipe_service.build_recipe_response(recipe)


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: User = Depends(get_current_user)
):
    """
    ➕ Crear una nueva receta para un producto.
    
    - El producto debe existir y pertenecer a la empresa
    - Un producto solo puede tener una receta
    - Los ingredientes deben ser productos válidos de la empresa
    - El costo total se calcula automáticamente
    """
    recipe = await recipe_service.create_recipe(recipe_data, company_id)
    logger.info(f"Usuario {current_user.username} creó receta: {recipe.name}")
    return recipe_service.build_recipe_response(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    update_data: RecipeUpdate,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    ✏️ Actualizar datos básicos de una receta.
    
    Solo actualiza nombre, descripción y estado.
    Para modificar ingredientes usar PUT /recipes/{id}/items
    """
    recipe = await recipe_service.update_recipe(recipe_id, company_id, update_data)
    return recipe_service.build_recipe_response(recipe)


@router.put("/{recipe_id}/items", response_model=RecipeResponse)
async def update_recipe_items(
    recipe_id: int,
    items_data: RecipeItemAddOrUpdate,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    🔄 Reemplazar los ingredientes de una receta.
    
    Elimina todos los ingredientes actuales y los reemplaza
    con la nueva lista. El costo se recalcula automáticamente.
    """
    recipe = await recipe_service.update_recipe_items(
        recipe_id, company_id, items_data.items
    )
    return recipe_service.build_recipe_response(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    🗑️ Eliminar una receta (soft delete).
    
    La receta se marca como inactiva, no se elimina físicamente.
    """
    await recipe_service.delete_recipe(recipe_id, company_id)
    return None


# ============================================
# ENDPOINTS ESPECIALES
# ============================================

@router.post("/{recipe_id}/recalculate", response_model=RecipeCostRecalculateResponse)
async def recalculate_recipe_cost(
    recipe_id: int,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    💰 Recalcular el costo de una receta.
    
    Útil cuando los precios de los ingredientes han cambiado.
    Actualiza el costo unitario de cada ingrediente y el total.
    
    Retorna:
    - Costo anterior
    - Nuevo costo
    - Diferencia
    - Número de items actualizados
    """
    return await recipe_service.recalculate_cost(recipe_id, company_id)


@router.get("/by-product/{product_id}", response_model=RecipeResponse)
async def get_recipe_by_product(
    product_id: int,
    company_id: int = Depends(verify_current_user_company),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    🔍 Obtener la receta de un producto específico.
    
    Alternativa a usar el ID de receta directamente.
    """
    recipe = await recipe_service.get_recipe_by_product(product_id, company_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El producto {product_id} no tiene receta"
        )
    return recipe_service.build_recipe_response(recipe)
