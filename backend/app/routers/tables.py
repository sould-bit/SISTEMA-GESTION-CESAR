from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, Session
from app.database import get_session
from app.models.table import Table, TableStatus
from app.dependencies import get_current_user, verify_current_user_company
from app.models.user import User
from app.schemas.tables import TableCreate

import logging
logger = logging.getLogger(__name__)
logger.info("Modulo de tablas cargado correctamente")

router = APIRouter(
    prefix="/tables",
    tags=["tables"]
)

@router.post("/", response_model=Table)
async def create_table(
    table_in: TableCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Crea una mesa individual.
    """
    target_branch_id = table_in.branch_id
    
    # Basic authorization check
    if current_user.role_id != 1 and target_branch_id != current_user.branch_id:
         raise HTTPException(status_code=403, detail="Not authorized for this branch")

    # Check duplicate
    stmt = select(Table).where(
        Table.branch_id == target_branch_id,
        Table.table_number == table_in.table_number
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Table number already exists in this branch")

    new_table = Table.model_validate(table_in)
    session.add(new_table)
    await session.commit()
    await session.refresh(new_table)
    return new_table

@router.post("/setup", response_model=List[Table])
async def setup_tables(
    count: int,
    branch_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Genera un número específico de mesas para la sucursal actual.
    Si branch_id no se especifica, usa la sucursal del usuario (si tiene).
    """
    target_branch_id = branch_id or current_user.branch_id
    if not target_branch_id:
        raise HTTPException(status_code=400, detail="Branch ID required")

    # Verificar si ya existen mesas (opcional: o simplemente añadir)
    # Por ahora, simplemente añadimos las mesas continuando la numeración o desde 1
    
    # Verificar si ya existen mesas
    result = await session.execute(select(Table).where(Table.branch_id == target_branch_id))
    existing_tables = result.scalars().all()
    start_number = len(existing_tables) + 1
    
    new_tables = []
    for i in range(count):
        table = Table(
            branch_id=target_branch_id,
            table_number=start_number + i,
            status=TableStatus.AVAILABLE
        )
        session.add(table)
        new_tables.append(table)
    
    await session.commit()
    for t in new_tables:
        await session.refresh(t)
        
    return new_tables

@router.get("/", response_model=List[Table])
async def list_tables(
    branch_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    target_branch_id = branch_id or current_user.branch_id
    if not target_branch_id:
         # Si es superadmin o tiene acceso a multiples, podria listar todas? Mejor restringir.
         # Por simplicidad, retornamos vacio si no hay branch context o error
         if current_user.role_id == 1: # Superadmin
             stmt = select(Table)
             result = await session.execute(stmt)
             return result.scalars().all()
         raise HTTPException(status_code=400, detail="Branch context required")

    stmt = select(Table).where(Table.branch_id == target_branch_id).order_by(Table.table_number)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.patch("/{table_id}/status", response_model=Table)
async def update_table_status(
    table_id: int,
    status: TableStatus,
    session: Session = Depends(get_session)
):
    table = await session.get(Table, table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table.status = status
    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table
