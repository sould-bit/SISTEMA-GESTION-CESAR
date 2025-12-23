from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID, uuid4


class Permission(SQLModel, table=True):
    """
    Permisos Granulares del Sistema.
    
    Define acciones específicas que pueden realizarse sobre recursos.
    Estructura: {resource}.{action}
    
    Ejemplos:
    - products.create → Crear productos
    - orders.read → Ver pedidos
    - inventory.adjust → Ajustar inventario
    - cash.close → Cerrar caja
    - reports.financial → Ver reportes financieros
    
    Multi-Tenant: Cada permiso pertenece a una empresa.
    """
    __tablename__ = "permissions"
    
    # Restricciones de integridad
    __table_args__ = (
        # No permitir dos permisos con el mismo código en la misma empresa
        UniqueConstraint("company_id", "code", name="unique_permission_code_per_company"),
        # Índices para optimizar queries
        Index("idx_perm_company_category", "company_id", "category_id"),
        Index("idx_perm_resource_action", "company_id", "resource", "action"),
        Index("idx_perm_active", "company_id", "is_active"),
    )
    
    # Campos principales
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Multi-Tenancy
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    # Relación con categoría
    category_id: UUID = Field(
        foreign_key="permission_categories.id",
        index=True,
        nullable=False
    )
    
    # Información del permiso
    code: str = Field(
        max_length=100,
        description="Código único (ej: 'products.create'). Formato: {resource}.{action}"
    )
    name: str = Field(
        max_length=100,
        description="Nombre legible (ej: 'Crear Productos')"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Descripción detallada del permiso"
    )
    
    # Componentes del permiso
    resource: str = Field(
        max_length=50,
        description="Recurso sobre el que actúa (ej: 'products', 'orders')"
    )
    action: str = Field(
        max_length=50,
        description="Acción a realizar (ej: 'create', 'read', 'update', 'delete')"
    )
    
    # Flags de sistema
    is_system: bool = Field(
        default=False,
        description="True = permiso del sistema (no editable por usuario)"
    )
    is_active: bool = Field(default=True)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relaciones
    category: "PermissionCategory" = Relationship()
    # role_permissions: List["RolePermission"] = Relationship(back_populates="permission")
    
    def __repr__(self) -> str:
        return f"<Permission {self.code}>"
    
    @property
    def full_code(self) -> str:
        """Retorna el código completo del permiso."""
        return f"{self.resource}.{self.action}"
