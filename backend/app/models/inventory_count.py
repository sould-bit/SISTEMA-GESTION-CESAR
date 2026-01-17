from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class InventoryCountStatus(str, Enum):
    OPEN = "OPEN"           # Created, counting in progress
    CLOSED = "CLOSED"       # Counting finished, waiting for review
    APPLIED = "APPLIED"     # Stock adjustments applied to inventory

class InventoryCountBase(SQLModel):
    branch_id: int = Field(foreign_key="branches.id", index=True)
    status: InventoryCountStatus = Field(default=InventoryCountStatus.OPEN)
    notes: Optional[str] = None
    
class InventoryCount(InventoryCountBase, table=True):
    __tablename__ = "inventory_counts"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    user_id: int = Field(foreign_key="users.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    
    # Relationships
    items: List["InventoryCountItem"] = Relationship(back_populates="count")

class InventoryCountItemBase(SQLModel):
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id")
    expected_quantity: Decimal = Field(default=Decimal(0), max_digits=20, decimal_places=4) # System stock at creation
    counted_quantity: Optional[Decimal] = Field(default=None, max_digits=20, decimal_places=4) # Physical count
    
class InventoryCountItem(InventoryCountItemBase, table=True):
    __tablename__ = "inventory_count_items"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    count_id: uuid.UUID = Field(foreign_key="inventory_counts.id", index=True)
    
    # Calculated fields (snapshot)
    cost_per_unit: Decimal = Field(default=Decimal(0), max_digits=20, decimal_places=4) # Snapshot of cost
    
    count: InventoryCount = Relationship(back_populates="items")
