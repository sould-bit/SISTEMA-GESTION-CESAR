from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class Token(BaseModel):
    """respuesta con el token JWT"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Datos contenidos del token JWT.
    
    Actualizado en v3.3 para incluir permisos del sistema RBAC.
    """
    username: str | None
    user_id: int
    company_id: int
    branch_id: int | None
    role: str  # DEPRECADO: Usar role_code
    plan: str
    
    # NUEVO: Sistema RBAC (v3.3)
    role_id: UUID | None = None
    role_code: str | None = None
    permissions: List[str] = []  # Lista de códigos de permisos

class LoginRequest(BaseModel):
    """datos para iniciar sesion"""

    model_config  = {
            "example": {
                "username": "admin",
                "password": "admin123", 
                "company_slug": "salchipapa-burguer"
            }
        }

    username: str
    password: str
    company_slug: str


   
        

class UserResponse(BaseModel):
    """Datos del usuario para respuestas (sin contraseña)"""

    id: int
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    company_id: int
    branch_id: int | None

    class Config:
        from_attributes = True # permite convertir desde modelos SQLmodel
    

class TokenVerification(BaseModel):
    """schema para verificar el token"""
    valid: bool
    user_id: int
    username: str
    company_id: int