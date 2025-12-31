from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID, uuid4


class RolePermission(SQLModel, table=True):
    """
    Tabla de Relación: Roles ↔ Permisos (Many-to-Many).
    
    Conecta roles con permisos específicos.
    Incluye auditoría de quién otorgó el permiso y cuándo.
    Soporta permisos temporales con fecha de expiración.
    
    Ejemplos:
    - Role "cashier" tiene Permission "products.read"
    - Role "admin" tiene Permission "users.manage"
    - Role "kitchen" tiene Permission "orders.update" (solo cocina)
    """
    __tablename__ = "role_permissions"
    
    # Restricciones de integridad
    __table_args__ = (
        # No permitir asignar el mismo permiso dos veces al mismo rol
        UniqueConstraint("role_id", "permission_id", name="unique_role_permission"),
        # Índices para optimizar queries
        Index("idx_role_perm_role", "role_id"),
        Index("idx_role_perm_permission", "permission_id"),
        Index("idx_role_perm_expires", "expires_at"),
    )
    
    # Campos principales
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Relaciones
    role_id: UUID = Field(
        foreign_key="roles.id",
        index=True,
        nullable=False
    )
    permission_id: UUID = Field(
        foreign_key="permissions.id",
        index=True,
        nullable=False
    )
    
    # Auditoría de otorgamiento
    granted_by: Optional[int] = Field(
        foreign_key="users.id",
        nullable=True,
        description="Usuario que otorgó este permiso al rol"
    )
    granted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha y hora en que se otorgó el permiso"
    )
    
    # Permisos temporales (opcional)
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Fecha de expiración del permiso (None = permanente)"
    )
    
    # Relaciones
    role: "Role" = Relationship(back_populates="role_permissions")
    permission: "Permission" = Relationship()
    # granted_by_user: Optional["User"] = Relationship()
    
    def __repr__(self) -> str:
        return f"<RolePermission role={self.role_id} perm={self.permission_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Verifica si el permiso ha expirado."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Verifica si el permiso está activo (no expirado)."""
        return not self.is_expired
