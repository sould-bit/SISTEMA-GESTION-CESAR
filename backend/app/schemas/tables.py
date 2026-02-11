from typing import Optional
from pydantic import BaseModel
from app.models.table import TableStatus

class TableBase(BaseModel):
    table_number: int
    seat_count: int = 4
    status: TableStatus = TableStatus.AVAILABLE
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    is_active: bool = True

class TableCreate(TableBase):
    branch_id: int

class TableUpdate(BaseModel):
    table_number: Optional[int] = None
    seat_count: Optional[int] = None
    status: Optional[TableStatus] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    is_active: Optional[bool] = None

class TableRead(TableBase):
    id: int
    branch_id: int
