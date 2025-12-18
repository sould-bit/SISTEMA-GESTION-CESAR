from pydantic import BaseModel


class Token(BaseModel):
    """respuesta con el token JWT"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """datos contenidos del token"""
    username: str | None
    user_id: int
    company_id: int
    branch_id: int | None
    role: str
    plan: str

class LoginRequest(BaseModel):
    """datos para iniciar sesion"""
    username: str
    password: str
    company_slug: str


    class Config: # DOCUMENTACION DE LA CLASE
        """configuracion de la clase"""
        json_schema_extra  = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }

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