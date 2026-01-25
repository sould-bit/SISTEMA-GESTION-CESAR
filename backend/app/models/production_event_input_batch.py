"""
ProductionEventInputBatch Model

Stores granular batch consumption details for production events.
This enables precise stock restoration when undoing productions by tracking
exactly which batch(es) each input quantity came from.

Separation of Concerns:
- This model ONLY handles data storage for batch consumption tracking.
- Business logic for consumption/restoration lives in InventoryService.
- Production workflow logic lives in ProductionService.
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Column, Numeric
import uuid

if TYPE_CHECKING:
    from app.models.production_event_input import ProductionEventInput
    from app.models.ingredient_batch import IngredientBatch


class ProductionEventInputBatch(SQLModel, table=True):
    """
    Junction table tracking which batches were consumed for each production input.
    
    Example: If a production consumed 600g of Tomato:
    - ProductionEventInput: (ingredient_id=Tomato, quantity=600, cost=X)
    - ProductionEventInputBatch #1: (source_batch_id=A, quantity_consumed=500)
    - ProductionEventInputBatch #2: (source_batch_id=B, quantity_consumed=100)
    """
    __tablename__ = "production_event_input_batches"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Parent reference
    production_event_input_id: uuid.UUID = Field(
        foreign_key="production_event_inputs.id",
        index=True,
        description="The production input this consumption belongs to"
    )
    
    # Source batch reference
    source_batch_id: uuid.UUID = Field(
        foreign_key="ingredient_batches.id",
        index=True,
        description="The batch from which stock was consumed"
    )
    
    # Consumption details
    quantity_consumed: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(18, 4)),
        description="Quantity consumed from this specific batch"
    )
    
    # Cost attribution (derived from batch's cost_per_unit * quantity_consumed)
    cost_attributed: Decimal = Field(
        default=Decimal(0),
        sa_column=Column(Numeric(18, 4)),
        description="Cost attributed from this batch consumption"
    )

    # Relationships
    production_event_input: Optional["ProductionEventInput"] = Relationship(
        back_populates="batch_consumptions"
    )
