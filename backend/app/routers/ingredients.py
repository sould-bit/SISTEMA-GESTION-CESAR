"""
Router para Ingredientes (Insumos / Materia Prima).

Endpoints CRUD para gestionar ingredientes que se usan en recetas.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.ingredient_service import IngredientService
from app.services.cost_engine_service import CostEngineService
from app.schemas.ingredients import (
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
    IngredientListResponse,
    IngredientCostUpdate,
)

router = APIRouter(
    prefix="/ingredients",
    tags=["Ingredients"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[IngredientListResponse])
async def list_ingredients(
    active_only: bool = Query(True, description="Solo ingredientes activos"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Lista ingredientes de la empresa del usuario."""
    service = IngredientService(session)
    ingredients = await service.list_by_company(
        company_id=current_user.company_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return ingredients


@router.get("/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene un ingrediente por ID."""
    service = IngredientService(session)
    ingredient = await service.get_by_id(ingredient_id)
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    if ingredient.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ingredient


@router.post("/", response_model=IngredientResponse, status_code=201)
async def create_ingredient(
    data: IngredientCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Crea un nuevo ingrediente."""
    service = IngredientService(session)
    ingredient = await service.create(
        company_id=current_user.company_id,
        name=data.name,
        sku=data.sku,
        base_unit=data.base_unit,
        current_cost=data.current_cost,
        yield_factor=data.yield_factor,
        category_id=data.category_id,
    )
    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: uuid.UUID,
    data: IngredientUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Actualiza un ingrediente existente."""
    service = IngredientService(session)
    
    # Verificar propiedad
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    ingredient = await service.update(
        ingredient_id=ingredient_id,
        name=data.name,
        sku=data.sku,
        base_unit=data.base_unit,
        current_cost=data.current_cost,
        yield_factor=data.yield_factor,
        category_id=data.category_id,
        is_active=data.is_active,
    )
    return ingredient


@router.delete("/{ingredient_id}", status_code=204)
async def delete_ingredient(
    ingredient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Elimina lógicamente un ingrediente (soft delete)."""
    service = IngredientService(session)
    
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await service.delete(ingredient_id)
    return None


@router.post("/{ingredient_id}/update-cost", response_model=IngredientResponse)
async def update_ingredient_cost(
    ingredient_id: uuid.UUID,
    data: IngredientCostUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza el costo de un ingrediente y recalcula las recetas afectadas.
    
    Típicamente usado después de registrar una compra.
    """
    service = IngredientService(session)
    
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    ingredient = await service.update_cost_from_purchase(
        ingredient_id=ingredient_id,
        new_cost=data.new_cost,
        use_weighted_average=data.use_weighted_average,
    )
    
    # Recalcular recetas afectadas
    cost_engine = CostEngineService(session)
    await cost_engine.recalculate_all_recipes_for_ingredient(ingredient_id)
    
    return ingredient


@router.get("/{ingredient_id}/impact", response_model=dict)
async def get_ingredient_impact(
    ingredient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza el impacto de un ingrediente en el menú.
    
    Retorna el número de recetas que lo usan y el costo total.
    """
    service = IngredientService(session)
    
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    cost_engine = CostEngineService(session)
    impact = await cost_engine.get_ingredient_impact_analysis(ingredient_id)
    
    return impact
