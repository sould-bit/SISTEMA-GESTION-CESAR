"""
📝 REGISTRATION SCHEMAS
Schemas para el registro público de nuevos negocios.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegistrationRequest(BaseModel):
    """
    Request para registrar un nuevo negocio.
    
    Al registrarse se crea automáticamente:
    - Company (con el plan seleccionado)
    - Subscription (free o trial)
    - Branch "Principal"
    - User Admin (el owner)
    """
    # Datos del negocio
    company_name: str = Field(..., min_length=2, max_length=200, description="Nombre comercial")
    company_slug: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$", 
                              description="Identificador único (solo minúsculas, números y guiones)")
    
    # Datos del dueño (será el admin)
    owner_name: str = Field(..., min_length=2, max_length=200)
    owner_email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    owner_phone: Optional[str] = Field(default=None, max_length=50)
    
    # Plan seleccionado
    plan: str = Field(default="free", pattern="^(free|basic|premium)$")


class RegistrationResponse(BaseModel):
    """Respuesta después del registro exitoso."""
    message: str
    company_slug: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    # Info del usuario creado
    user_id: int
    username: str
    email: str
    plan: str


class CompanyAvailabilityCheck(BaseModel):
    """Request para verificar disponibilidad de slug."""
    slug: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$")


class CompanyAvailabilityResponse(BaseModel):
    """Respuesta de verificación de slug."""
    slug: str
    available: bool
    suggestion: Optional[str] = None  # Si no está disponible, sugerir alternativa
