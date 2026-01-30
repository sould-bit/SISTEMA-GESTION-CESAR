from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Column, Numeric
import uuid

if TYPE_CHECKING:
    from app.models.production_event import ProductionEvent
    from app.models.production_event_input_batch import ProductionEventInputBatch


class ProductionEventInput(SQLModel, table=True):
    __tablename__ = "production_event_inputs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    production_event_id: uuid.UUID = Field(foreign_key="production_events.id", index=True)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", index=True)
    
    quantity: float = Field(description="Cantidad consumida")
    cost_allocated: Decimal = Field(default=0, sa_column=Column(Numeric(18, 4)), description="Costo asignado a este input (FIFO)")

    # Relationships
    production_event: Optional["ProductionEvent"] = Relationship(back_populates="inputs")
    batch_consumptions: List["ProductionEventInputBatch"] = Relationship(
        back_populates="production_event_input",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
