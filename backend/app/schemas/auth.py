from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)  # permite convertir desde modelos SQLModel

    id: int
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    company_id: int
    branch_id: int | None
    

class TokenVerification(BaseModel):
    """schema para verificar el token"""
    valid: bool
    user_id: int
    username: str
    company_id: int