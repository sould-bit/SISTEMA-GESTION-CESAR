from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """respuesta con el token JWT"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """datos contenidos del token"""
    username: Optional[str] = None

class LoginRequest(BaseModel):
    """datos para iniciar sesion"""
    username: str
    password: str


    class Config: # DOCUMENTACION DE LA CLASE
        """configuracion de la clase"""
        json_eschema_extra  = {
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
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True # permite convertir desde modelos SQLmodel