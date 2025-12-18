from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index 

class Company(SQLModel, table=True):
    """
    Modelo de Negocio (Tenant).
    Representa a cada cliente del SaaS (ej: 'El Rincón', 'Salchipapas de la 80').
    """
    __tablename__ = "companies"
 
    __table_args__ = (
    Index("idx_companies_active", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, description="Nombre comercial")
    slug: str = Field(max_length=100, unique=True, index=True, description="Identificador unico para subdominios")
    legal_name: Optional[str] = Field(default=None, max_length=200)
    tax_id: Optional[str] = Field(default=None, max_length=50, description="NIT o RUT")
    
    # Datos del dueño
    owner_name: Optional[str] = Field(default=None, max_length=200)
    owner_email: Optional[str] = Field(default=None, max_length=200)
    owner_phone: Optional[str] = Field(default=None, max_length=50)
    
    # Configuración SaaS
    plan: str = Field(default="free", max_length=20) # free, basic, premium
    is_active: bool = Field(default=True)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relaciones (se llenarán al crear los otros modelos)
    branches: List["Branch"] = Relationship(back_populates="company")
    subscription: "Subscription" = Relationship(back_populates="company")
