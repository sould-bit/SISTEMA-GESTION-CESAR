from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID

if TYPE_CHECKING:
    from .role import Role
    from .company import Company
    from .branch import Branch


class User(SQLModel, table=True):
    """
    Modelo de Usuario Multi-Tenant con RBAC.
    
    Cambios en v3.3:
    - Agregado role_id (UUID) para sistema RBAC
    - Campo 'role' (str) deprecado, se mantiene por compatibilidad
    - Métodos de verificación de permisos
    """
    model_config = {
            "example": {
                "username": "cajero1",
                "email": "cajero@sisalchi.com",
                "full_name": "Juan Pérez",
                "role": "cajero",
                "company_id": 1,
                "branch_id": 1
            }
        }

    __tablename__ = "users"
    
    # El usuario debe ser único POR COMPAÑÍA (dos empresas pueden tener un empleado "juan")
    __table_args__ = (
        UniqueConstraint("company_id", "username", name="unique_username_per_company"),
        Index("idx_users_login", "company_id", "username", "is_active"),
        Index("idx_users_role", "company_id", "role_id", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # CLAVES FORÁNEAS
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: Optional[int] = Field(foreign_key="branches.id", index=True, nullable=True, default=None)
    
    # NUEVO: Sistema RBAC
    role_id: Optional[UUID] = Field(
        foreign_key="roles.id",
        index=True,
        nullable=True,
        default=None,
        description="Rol del usuario en el sistema RBAC"
    )
    
    # Datos del usuario
    username: str = Field(index=True, max_length=50)
    email: str = Field(max_length=100) # Ya no es único globalmente, solo por compañía
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    
    # DEPRECADO: Mantener por compatibilidad con código legacy
    # TODO: Migrar a role_id y eliminar este campo en v4.0
    role: str = Field(default="cajero", max_length=20, description="DEPRECADO: Usar role_id") 
    
    is_active: bool = Field(default=True)
    
    # CAMPOS DE AUDITORÍA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    
    # RELACIONES
    company: "Company" = Relationship()
    branch: Optional["Branch"] = Relationship()
    user_role: Optional["Role"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[User.role_id]"}
    )
    
    def can_access_branch(self, branch_id: int) -> bool:
        """
        Verifica si el usuario puede acceder a una sucursal específica.
        
        Reglas:
        - Si branch_id es None, puede acceder a todas las sucursales de su empresa
        - Si tiene branch_id asignado, solo puede acceder a esa sucursal
        """
        if self.branch_id is None:
            return True  # Acceso a todas las sucursales
        return self.branch_id == branch_id

    @property
    def role_name(self) -> str:
        """Retorna el nombre del rol (ej: 'Cajero') o el código legacy."""
        if self.user_role:
            return self.user_role.name
        return self.role

    
       