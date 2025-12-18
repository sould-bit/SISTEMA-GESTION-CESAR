from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index
class Subscription(SQLModel, table=True):
    """
    Modelo de Suscripción.
    Controla el plan y la facturación del negocio.
    """
    __tablename__ = "subscriptions"
    __table_args__ = (
    Index("idx_subscriptions_status", "status", "current_period_end"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    
    plan: str = Field(default="free", max_length=20) # free, basic, premium
    status: str = Field(default="active", max_length=20) # active, cancelled, past_due, trialing
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    current_period_start: Optional[datetime] = Field(default=None)
    current_period_end: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    
    amount: float = Field(default=0.0)
    currency: str = Field(default="COP", max_length=3)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relación (necesitaremos actualizar Company para que tenga el back_populates)
    company: "Company" = Relationship(back_populates="subscription")