from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID, uuid4


class Role(SQLModel, table=True):
    """
    Roles del Sistema - RBAC.
    
    Agrupa permisos en roles coherentes que pueden asignarse a usuarios.
    Soporta jerarquía de roles para herencia de permisos.
    
    Roles del sistema (predefinidos):
    - super_admin (nivel 100) → Acceso total
    - admin (nivel 80) → Gestión completa
    - manager (nivel 60) → Operaciones y reportes
    - cashier (nivel 40) → Ventas y caja
    - kitchen (nivel 30) → Pedidos de cocina
    - delivery (nivel 20) → Domicilios
    - viewer (nivel 10) → Solo lectura
    
    Roles personalizados:
    - Los usuarios pueden crear roles según sus necesidades
    - Ej: "Mesero Senior", "Supervisor de Turno", etc.
    
    Multi-Tenant: Cada rol pertenece a una empresa.
    """
    __tablename__ = "roles"
    
    # Restricciones de integridad
    __table_args__ = (
        # No permitir dos roles con el mismo código en la misma empresa
        UniqueConstraint("company_id", "code", name="unique_role_code_per_company"),
        # Índices para optimizar queries
        Index("idx_roles_company_active", "company_id", "is_active"),
        Index("idx_roles_hierarchy", "company_id", "hierarchy_level"),
        Index("idx_roles_system", "is_system", "is_active"),
    )
    
    # Campos principales
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Multi-Tenancy
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    # Información del rol
    name: str = Field(
        max_length=100,
        description="Nombre legible (ej: 'Administrador', 'Cajero')"
    )
    code: str = Field(
        max_length=50,
        description="Código único (ej: 'admin', 'cashier'). Usado en código."
    )
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Descripción del rol y sus responsabilidades"
    )
    
    # Jerarquía de roles
    hierarchy_level: int = Field(
        default=50,
        description="Nivel jerárquico (0-100). Mayor = más privilegios. Usado para herencia."
    )
    
    # Flags de sistema
    is_system: bool = Field(
        default=False,
        description="True = rol del sistema (no editable por usuario)"
    )
    is_active: bool = Field(default=True)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relaciones
    # users: List["User"] = Relationship(back_populates="role")
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")
    
    def __repr__(self) -> str:
        return f"<Role {self.code} (level {self.hierarchy_level})>"
    
    def can_inherit_from(self, other_role: "Role") -> bool:
        """
        Verifica si este rol puede heredar permisos de otro rol.
        Un rol puede heredar de roles con nivel jerárquico menor o igual.
        """
        return self.hierarchy_level >= other_role.hierarchy_level
