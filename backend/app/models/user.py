from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index

class User(SQLModel, table=True):
    """
    Modelo de Usuario Multi-Tenant.
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
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # CLAVES FORÁNEAS (NUEVO)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: Optional[int] = Field(foreign_key="branches.id", index=True, nullable=True, default=None)
    
    username: str = Field(index=True, max_length=50)
    email: str = Field(max_length=100) # Ya no es único globalmente, solo por compañía
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    
    role: str = Field(default="cajero", max_length=20) 
    
    is_active: bool = Field(default=True)
    
    # CAMPOS DE AUDITORÍA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    
    # RELACIONES
    company: "Company" = Relationship()
    branch: Optional["Branch"] = Relationship()

    
       