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
from app.services.ingredient_service import IngredientService
from app.services.cost_engine_service import CostEngineService
from app.services.inventory_service import InventoryService
from app.models.ingredient_inventory import IngredientInventory
from app.schemas.ingredients import (
    IngredientCreate,
    IngredientUpdate,
    IngredientResponse,
    IngredientListResponse,
    IngredientListResponse,
    IngredientCostUpdate,
    IngredientStockUpdate,
    IngredientCostHistoryResponse,
    IngredientBatchResponse,
    IngredientBatchUpdate,
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
        branch_id=current_user.branch_id
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
        user_id=current_user.id,
        reason=data.reason,
    )
    
    # Recalcular recetas afectadas
    cost_engine = CostEngineService(session)
    await cost_engine.recalculate_all_recipes_for_ingredient(ingredient_id)
    
    return ingredient

@router.get("/{ingredient_id}/history", response_model=List[IngredientCostHistoryResponse])
async def get_cost_history(
    ingredient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el historial de costos de un ingrediente."""
    service = IngredientService(session)
    
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    history = await service.get_cost_history(ingredient_id)
    return history


@router.get("/{ingredient_id}/batches", response_model=List[IngredientBatchResponse])
async def get_ingredient_batches(
    ingredient_id: uuid.UUID,
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Obtiene los lotes (batches) de un ingrediente."""
    service = IngredientService(session)
    
    existing = await service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    batches = await service.get_batches(ingredient_id, active_only=active_only)
    return batches


@router.get("/{ingredient_id}/impact", response_model=dict)
async def get_ingredient_impact(
    ingredient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Analiza el impacto de un ingrediente en el menú.
    
    Retorna el número de recetas que lo usan, costo total y uso promedio.
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


    return impact


@router.post("/{ingredient_id}/stock", response_model=dict)
async def update_ingredient_stock(
    ingredient_id: uuid.UUID,
    data: IngredientStockUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza el stock físico de un ingrediente.
    
    Usado para:
    - Registrar inventario inicial
    - Entrada de compras (si se maneja cantidad)
    - Ajustes por merma/pérdida
    """
    # Verificar propiedad del ingrediente
    ing_service = IngredientService(session)
    existing = await ing_service.get_by_id(ingredient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if existing.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Preparar cantidad (si es OUT, debe ser negativa)
    quantity = data.quantity
    if data.transaction_type == "OUT":
        quantity = quantity * -1
        
    # Usar InventoryService para actualizar el stock
    inv_service = InventoryService(session)
    
    # Obtener el branch_id del usuario actual (asumiendo que el usuario pertenece a un branch activo)
    # Por ahora usaremos el primer branch de la compañía como fallback o requerir branch en el header
    # Simplificación: Usar branch_id = 1 o buscar el branch asociado al usuario.
    # TODO: Implementar lógica robusta de selección de sucursal. Asumiremos branch_id del usuario si existe.
    branch_id = current_user.branch_id if hasattr(current_user, 'branch_id') and current_user.branch_id else 1
    
    inventory, _, _, _ = await inv_service.update_ingredient_stock(
        branch_id=branch_id,
        ingredient_id=ingredient_id,
        quantity_delta=quantity,
        transaction_type=data.transaction_type,
        user_id=current_user.id,
        reference_id=data.reference_id,
        reason=data.reason,
        cost_per_unit=data.cost_per_unit,
        supplier=data.supplier
    )
    
    return {
        "ingredient_id": ingredient_id,
        "new_stock": inventory.stock,
        "branch_id": branch_id
    }


@router.patch("/batches/{batch_id}", response_model=IngredientBatchResponse)
async def update_batch(
    batch_id: uuid.UUID,
    data: IngredientBatchUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Actualiza un lote específico.
    
    Permite modificar cantidad restante, proveedor o desactivar el lote.
    """
    service = IngredientService(session)
    
    # Obtener el batch y verificar propiedad
    batch = await service.get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    ingredient = await service.get_by_id(batch.ingredient_id)
    if not ingredient or ingredient.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Actualizar el batch
    updated_batch = await service.update_batch(
        batch_id=batch_id,
        quantity_initial=data.quantity_initial,
        quantity_remaining=data.quantity_remaining,
        cost_per_unit=data.cost_per_unit,
        total_cost=data.total_cost,
        supplier=data.supplier,
        is_active=data.is_active
    )
    
    return updated_batch


@router.delete("/batches/{batch_id}", status_code=204)
async def delete_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Elimina un lote específico.
    
    Este es un hard delete. Se recomienda usar PATCH para desactivar.
    """
    service = IngredientService(session)
    
    # Obtener el batch y verificar propiedad
    batch = await service.get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    ingredient = await service.get_by_id(batch.ingredient_id)
    if not ingredient or ingredient.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Intentar revertir producción si aplica
    # Si el lote fue producido internamente, revert_production_by_output_batch 
    # maneja todo: restaurar inputs, restar output, eliminar batch y evento
    from app.services.production_service import ProductionService
    prod_service = ProductionService(session)
    was_production = await prod_service.revert_production_by_output_batch(batch_id)
    
    if not was_production:
        # Solo eliminar si NO era de producción (compra/ajuste)
        await service.delete_batch(batch_id)
    
    return None
