from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.services.modifier_service import modifier_service
from app.models.modifier import ProductModifier
from app.schemas.modifier import (
    ProductModifierRead, 
    ProductModifierCreate, 
    ProductModifierUpdate,
    ModifierRecipeItemCreate
)

from app.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/modifiers", tags=["Modifiers"])

@router.get("/", response_model=List[ProductModifierRead])
async def get_modifiers(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    return await modifier_service.get_modifiers(session, user.company_id)

@router.post("/", response_model=ProductModifierRead, status_code=status.HTTP_201_CREATED)
async def create_modifier(
    modifier_in: ProductModifierCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    modifier = ProductModifier.model_validate(modifier_in, update={"company_id": user.company_id})
    return await modifier_service.create_modifier(session, modifier)

@router.put("/{modifier_id}", response_model=ProductModifierRead)
async def update_modifier(
    modifier_id: int,
    modifier_in: ProductModifierUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    # TODO: Validate ownership (modifier belongs to user.company_id)
    updated = await modifier_service.update_modifier(session, modifier_id, modifier_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return updated

@router.put("/{modifier_id}/recipe", response_model=ProductModifierRead)
async def update_modifier_recipe(
    modifier_id: int,
    items: List[ModifierRecipeItemCreate],
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """
    Actualiza COMPLETAMENTE la receta del modificador (borra ítems anteriores y agrega nuevos).
    """
    # Convert Pydantic models to dicts
    items_data = [item.model_dump() for item in items]
    try:
        return await modifier_service.update_recipe_items(session, modifier_id, items_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
