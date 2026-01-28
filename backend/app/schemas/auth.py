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
    """
    Datos para iniciar sesión.
    
    Estrategia v3.5 (Smart Auth):
    - Se requiere email y password.
    - company_slug es opcional (se usa para desempate si el email existe en varias empresas).
    """
    model_config = {
        "example": {
            "email": "admin@imperio.com",
            "password": "securePass123",
            "company_slug": "opcional-para-desempate"
        }
    }

    email: str
    password: str
    company_slug: str | None = None
    # username obsoleto para login, pero mantenemos compatibilidad si se envía
    username: str | None = None


class CompanyOption(BaseModel):
    """Opción de empresa para usuarios multi-tenant"""
    name: str
    slug: str
    role: str

class LoginResponse(BaseModel):
    """
    Respuesta polimórfica de login:
    - Si login exitoso: devuelve 'token'
    - Si requiere selección: devuelve 'options'
    """
    token: Token | None = None
    options: List[CompanyOption] | None = None
    requires_selection: bool = False
        

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