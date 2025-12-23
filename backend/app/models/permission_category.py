from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID, uuid4


class PermissionCategory(SQLModel, table=True):
    """
    Categorías de Permisos - Sistema Dinámico.
    
    Permite a los usuarios crear sus propias categorías de permisos
    según las necesidades de su negocio.
    
    Ejemplos:
    - Sistema: "Productos", "Pedidos", "Inventario"
    - Personalizadas: "Meseros", "Delivery", "Cocina", "Finanzas"
    
    Multi-Tenant: Cada categoría pertenece a una empresa.
    """
    __tablename__ = "permission_categories"
    
    # Restricciones de integridad
    __table_args__ = (
        # No permitir dos categorías con el mismo código en la misma empresa
        UniqueConstraint("company_id", "code", name="unique_category_code_per_company"),
        # Índices para optimizar queries
        Index("idx_perm_cat_company_active", "company_id", "is_active"),
        Index("idx_perm_cat_system", "is_system", "is_active"),
    )
    
    # Campos principales
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Multi-Tenancy
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    # Información de la categoría
    name: str = Field(max_length=100, description="Nombre legible (ej: 'Meseros')")
    code: str = Field(
        max_length=50, 
        description="Código único (ej: 'waiters'). Usado en código."
    )
    description: Optional[str] = Field(
        default=None, 
        max_length=255,
        description="Descripción de la categoría"
    )
    
    # Personalización UI (opcional)
    icon: Optional[str] = Field(
        default=None, 
        max_length=50,
        description="Icono Material Design (ej: 'restaurant_menu')"
    )
    color: Optional[str] = Field(
        default=None, 
        max_length=7,
        description="Color hexadecimal para UI (ej: '#FF5722')"
    )
    
    # Flags de sistema
    is_system: bool = Field(
        default=False,
        description="True = categoría del sistema (no editable por usuario)"
    )
    is_active: bool = Field(default=True)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relaciones
    # permissions: List["Permission"] = Relationship(back_populates="category")
    
    def __repr__(self) -> str:
        return f"<PermissionCategory {self.code} ({self.name})>"
