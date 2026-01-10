from datetime import datetime
from sqlmodel import SQLModel


# base campos compartidos
class CategoryBase(SQLModel):
    """base campos compartidos"""
    name: str
    description: str | None
    is_active: bool = True  # ✅ Valor por defecto

#  create : lo que recibimos del cliente 

class CategoryCreate(CategoryBase):
    """lo que recibimos del cliente"""
    pass


#update : campos opcionales para editar 
class CategoryUpdate(SQLModel):
    """campos opcionales para editar"""
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


#read: lo que devolvemos a la api (incluye ID)

class CategoryRead(CategoryBase):
    """lo que devolvemos a la api (incluye ID)"""
    id: int
    company_id: int
    created_at: datetime