from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.production_service import ProductionService
from decimal import Decimal

class ProductionInputItem(BaseModel):
    ingredient_id: uuid.UUID
    quantity: Decimal

class ProductionOutputItem(BaseModel):
    ingredient_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    base_unit: Optional[str] = 'units'
    category_id: Optional[int] = None

class ProductionCreateRequest(BaseModel):
    inputs: List[ProductionInputItem]
    output: ProductionOutputItem
    output_quantity: Decimal
    notes: Optional[str] = None

class ProductionEventResponse(BaseModel):
    id: uuid.UUID
    output_ingredient_id: uuid.UUID
    input_cost_total: Decimal
    calculated_unit_cost: Decimal
    created_at: str

router = APIRouter(
    prefix="/kitchen/production",
    tags=["Kitchen Production"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ProductionEventResponse, status_code=201)
async def register_production(
    data: ProductionCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Registrar transformación de insumos (Ej. Carne -> Carne Moldeada).
    Soporta múltiples insumos y creación automática de insumo destino.
    """
    service = ProductionService(session)
    
    # Asumimos branch_id del usuario (igual que en otros endpoints)
    branch_id = getattr(current_user, 'branch_id', 1) or 1
    
    # Convertir Pydantic models a dicts (Decimal safe)
    inputs_dict = [i.model_dump() for i in data.inputs]
    output_dict = data.output.model_dump()
    
    event = await service.register_production_event(
        company_id=current_user.company_id,
        branch_id=branch_id,
        user_id=current_user.id,
        inputs=inputs_dict,
        output=output_dict,
        output_quantity=data.output_quantity,
        notes=data.notes
    )
    
    return ProductionEventResponse(
        id=event.id,
        output_ingredient_id=event.output_ingredient_id,
        input_cost_total=event.input_cost_total,
        calculated_unit_cost=event.calculated_unit_cost,
        created_at=event.created_at.isoformat()
    )

class ProductionInputDetail(BaseModel):
    ingredient_name: str
    quantity: Decimal
    unit: str
    cost_allocated: Decimal
    cost_per_unit: Decimal


class ProductionDetailResponse(BaseModel):
    id: uuid.UUID
    date: str
    inputs: List[ProductionInputDetail]
    output_quantity: Decimal
    notes: Optional[str] = None

@router.get("/batch/{batch_id}", response_model=ProductionDetailResponse)
async def get_production_by_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from app.models.production_event import ProductionEvent
    from app.models.production_event_input import ProductionEventInput
    from app.models.ingredient import Ingredient
    from sqlmodel import select

    # 1. Buscar el evento de producción asociado al lote
    stmt = select(ProductionEvent).where(ProductionEvent.output_batch_id == batch_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Production event not found for this batch")

    # 2. Buscar los insumos consumidos
    # Join ProductionEventInput -> Ingredient to get names
    stmt_inputs = (
        select(ProductionEventInput, Ingredient.name, Ingredient.base_unit)
        .join(Ingredient, ProductionEventInput.ingredient_id == Ingredient.id)
        .where(ProductionEventInput.production_event_id == event.id)
    )
    res_inputs = await session.execute(stmt_inputs)
    inputs_data = res_inputs.all() # [(InputObj, name, unit), ...]

    formatted_inputs = []
    for inp, name, unit in inputs_data:
        # Calcular costo unitario (avoid division by zero if quantity is 0, though unlikely)
        quantity = Decimal(inp.quantity)
        total_cost = inp.cost_allocated # Already Decimal from DB
        unit_cost = total_cost / quantity if quantity > 0 else Decimal(0)

        formatted_inputs.append(ProductionInputDetail(
            ingredient_name=name,
            quantity=quantity,
            unit=unit,
            cost_allocated=total_cost,
            cost_per_unit=unit_cost
        ))

    return ProductionDetailResponse(
        id=event.id,
        date=event.created_at.isoformat(),
        inputs=formatted_inputs,
        output_quantity=event.output_quantity, # Already decimal/numeric
        notes=event.notes
    )
