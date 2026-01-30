"""
📍 SCHEMAS DE SUCURSALES (BRANCHES)

Esquemas Pydantic para validación de sucursales.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BranchCreate(BaseModel):
    """Schema para crear una nueva sucursal."""
    name: str = Field(..., min_length=2, max_length=200, description="Nombre de la sucursal")
    code: str = Field(..., min_length=2, max_length=20, pattern="^[A-Z0-9_-]+$",
                     description="Código corto (mayúsculas, números, guiones)")
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    is_main: bool = Field(False, description="Si es la sucursal principal")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Sucursal Centro",
                "code": "CENT",
                "address": "Calle 80 #45-23",
                "phone": "+57 300 123 4567",
                "is_main": True
            }
        }
    }


class BranchUpdate(BaseModel):
    """Schema para actualizar una sucursal."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    code: Optional[str] = Field(None, min_length=2, max_length=20, pattern="^[A-Z0-9_-]+$")
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    is_main: Optional[bool] = None
    is_active: Optional[bool] = None


class BranchResponse(BaseModel):
    """Schema de respuesta para sucursales."""
    id: int
    company_id: int
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_main: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Estadísticas (opcional, se calculan)
    user_count: Optional[int] = None
    
    model_config = {"from_attributes": True}


class BranchList(BaseModel):
    """Lista paginada de sucursales."""
    items: List[BranchResponse]
    total: int
    page: int
    size: int
