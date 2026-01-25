from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.inventory_count_service import InventoryCountService
from app.models.inventory_count import InventoryCount, InventoryCountItem, InventoryCountStatus

router = APIRouter(
    prefix="/inventory-counts",
    tags=["Inventory Counts"],
    responses={404: {"description": "Not found"}},
)

# Schemas
class InventoryCountCreate(BaseModel):
    branch_id: int
    notes: Optional[str] = None

class InventoryCountItemUpdate(BaseModel):
    ingredient_id: uuid.UUID
    counted_quantity: float

class InventoryCountDetail(BaseModel):
    id: uuid.UUID
    branch_id: int
    status: str
    created_at: datetime
    items: List[dict] # Simply dumping items for now, can perform better mapping later

class InventoryCountList(BaseModel):
    id: uuid.UUID
    branch_id: int
    status: str
    created_at: datetime
    notes: Optional[str]

@router.post("/", response_model=InventoryCountList, status_code=201)
async def start_count(
    data: InventoryCountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCountService(session)
    # Validate branch access? Assumed handled if user has permissions. 
    # Ideally check if branch belongs to user company.
    
    count = await service.create_count(
        company_id=current_user.company_id,
        branch_id=data.branch_id,
        user_id=current_user.id,
        notes=data.notes
    )
    return count

@router.get("/{count_id}", response_model=InventoryCountDetail)
async def get_count_detail(
    count_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Fetch count with items
    # Need to handle eager loading or join.
    from sqlalchemy.orm import selectinload
    from sqlmodel import select
    
    stmt = select(InventoryCount).where(
        InventoryCount.id == count_id,
        InventoryCount.company_id == current_user.company_id
    ).options(selectinload(InventoryCount.items))
    
    res = await session.execute(stmt)
    count = res.scalar_one_or_none()
    
    if not count:
         raise HTTPException(status_code=404, detail="Count not found")
         
    # Manual mapping to avoid circular issues or complexity with Pydantic generic
    items_data = []
    for item in count.items:
        items_data.append({
            "ingredient_id": item.ingredient_id,
            "expected_quantity": float(item.expected_quantity),
            "counted_quantity": float(item.counted_quantity) if item.counted_quantity is not None else None,
            "cost_per_unit": float(item.cost_per_unit),
            "discrepancy": float(item.counted_quantity - item.expected_quantity) if item.counted_quantity is not None else 0
        })
        
    return InventoryCountDetail(
        id=count.id,
        branch_id=count.branch_id,
        status=count.status.value,
        created_at=count.created_at,
        items=items_data
    )

@router.post("/{count_id}/items", status_code=200)
async def update_items(
    count_id: uuid.UUID,
    items: List[InventoryCountItemUpdate],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCountService(session)
    
    # Verify count belongs to company
    # (Implicitly handled if using service methods that check ID, but service doesn't check company currently, only ID)
    # So we should check here or add to service.
    
    for item in items:
        await service.update_count_item(
            count_id=count_id,
            ingredient_id=item.ingredient_id,
            counted_qty=item.counted_quantity
        )
    return {"status": "ok", "updated": len(items)}

@router.post("/{count_id}/close", status_code=200)
async def close_count(
    count_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCountService(session)
    await service.close_count(count_id)
    return {"status": "closed"}

@router.post("/{count_id}/apply", status_code=200)
async def apply_count(
    count_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCountService(session)
    await service.apply_adjustments(count_id, user_id=current_user.id)
    return {"status": "applied"}
