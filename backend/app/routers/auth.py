"""
🔐 ROUTER DE AUTENTICACIÓN - EL REACTOR ARC DEL SISTEMA

Este módulo es el corazón de la seguridad. Maneja:
- Login de usuarios
- Generación de tokens JWT
- Validación de tokens
- Protección de endpoints
Conceptos clave:
- OAuth2: Estándar de autenticación
- JWT: Tokens seguros que expiran
- Multi-tenant: Aislamiento por empresa
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import User
from app.schemas.auth import(
    LoginRequest,
    Token,
    TokenData,
    UserResponse,
    TokenVerification,
    LoginResponse
)
from app.schemas.registration import (
    RegistrationRequest,
    RegistrationResponse,
    CompanyAvailabilityCheck,
    CompanyAvailabilityResponse
)
from app.utils.security import decode_access_token
from app.config import settings
from app.services import AuthService
from app.services.registration_service import RegistrationService

from logging import getLogger

logger = getLogger(__name__)

# ============================================
# CONFIGURACIÓN DEL ROUTER
# ============================================
router = APIRouter(prefix="/auth", tags=["authentication"])

# Importar dependencias desde el nuevo módulo para evitar ciclos
from app.auth_deps import (
    get_current_user,
    oauth2_scheme,
    CREDENTIALS_EXCEPTION,
    INACTIVE_USER_EXCEPTION
)

# ============================================
# DEPENDENCIAS DE SERVICIOS
# ============================================
def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """
    🛠️ DEPENDENCIA: INYECTAR AUTH SERVICE

    Proporciona una instancia del AuthService con la sesión de BD.
    """
    return AuthService(session)

def get_registration_service(session: AsyncSession = Depends(get_session)) -> RegistrationService:
    """
    🛠️ DEPENDENCIA: INYECTAR REGISTRATION SERVICE
    """
    return RegistrationService(session)

# ============================================
# ENDPOINT: REGISTRO PÚBLICO
# ============================================
@router.post("/register", response_model=RegistrationResponse)
async def register_company(
    data: RegistrationRequest,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """
    🏢 REGISTRAR NUEVO NEGOCIO (Público - Sin autenticación)

    Crea automáticamente:
    - Company con el plan seleccionado (free/basic/premium)
    - Subscription (activa o trial de 14 días)
    - Branch "Principal"
    - Rol admin para la empresa
    - Usuario admin (el owner)

    Retorna token JWT para auto-login.

    Ejemplo:
    ```json
    POST /auth/register
    {
        "company_name": "Mi Restaurante",
        "company_slug": "mi-restaurante",
        "owner_name": "Juan Pérez",
        "owner_email": "juan@email.com",
        "password": "miPassword123",
        "plan": "free"
    }
    ```
    """
    return await registration_service.register_company(data)

@router.post("/check-slug", response_model=CompanyAvailabilityResponse)
async def check_slug_availability(
    data: CompanyAvailabilityCheck,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """
    🔍 VERIFICAR DISPONIBILIDAD DE SLUG (Público)

    Verifica si un identificador de empresa está disponible.
    Si no lo está, sugiere una alternativa.
    """
    return await registration_service.check_slug_availability(data.slug)

# ============================================
# ENDPOINT: LOGIN
# ============================================
@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    🔑 INICIAR SESIÓN (Smart Auth)

    Utiliza AuthService para autenticar por email.
    Puede retornar un token (si login OK) o una lista de opciones (si usuario está en múltiples empresas).
    """
    return await auth_service.authenticate_user(login_data)
# ============================================
# ENDPOINT: GET CURRENT USER INFO
# ============================================
@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    👤 OBTENER DATOS DEL USUARIO ACTUAL

    Este es un endpoint PROTEGIDO que requiere autenticación.
    Solo se ejecuta si el token es válido.

    Ejemplo de uso:
    ```bash
    curl -X GET "http://localhost:8000/auth/me" \
      -H "Authorization: Bearer TU_TOKEN_AQUI"
    ```

    Respuesta:
    {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Administrador",
        "role": "admin",
        "is_active": true,
        "company_id": 1,
        "branch_id": 1
    }

    Args:
        current_user: Usuario inyectado por get_current_user
        auth_service: Servicio de autenticación

    Returns:
        UserResponse: Datos del usuario (sin contraseña)
    """
    return await auth_service.get_current_user_info(current_user)

# ============================================
# ENDPOINT: VERIFY TOKEN
# ============================================
@router.get("/verify", response_model=TokenVerification)
async def verify_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    ✅ VERIFICAR SI EL TOKEN ES VÁLIDO

    Endpoint simple para que el frontend verifique si el usuario
    aún está autenticado (útil al refrescar la página).

    Ejemplo de uso:
    ```bash
    curl -X GET "http://localhost:8000/auth/verify" \
      -H "Authorization: Bearer TU_TOKEN_AQUI"
    ```

    Respuesta exitosa:
    {
        "valid": true,
        "user_id": 1,
        "username": "admin",
        "company_id": 1
    }

    Error (token inválido):
    {
        "detail": "Token inválido o expirado"
    }

    Args:
        current_user: Usuario inyectado por get_current_user
        auth_service: Servicio de autenticación

    Returns:
        TokenVerification: Confirmación de validez
    """
    return await auth_service.verify_user_token(current_user)

    # ============================================
# ENDPOINT: REFRESH TOKEN (BONUS)
# ============================================
@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    🔄 REFRESCAR TOKEN

    Genera un nuevo token para el usuario actual.
    Útil cuando el token está por expirar.

    Ejemplo de uso:
    ```bash
    curl -X POST "http://localhost:8000/auth/refresh" \
      -H "Authorization: Bearer TU_TOKEN_ACTUAL"
    ```

    Args:
        current_user: Usuario inyectado por get_current_user
        auth_service: Servicio de autenticación

    Returns:
        Token: Nuevo token JWT
    """
    return await auth_service.refresh_user_token(current_user)

# ============================================
# ENDPOINT: LOGOUT (BONUS - Opcional)
# ============================================
@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    🚪 LOGOUT

    En JWT stateless, el logout es principalmente del lado del frontend
    (eliminar el token del localStorage).

    Este endpoint es más para logging/auditoría.

    Para implementar logout real, necesitarías:
    - Una blacklist de tokens en Redis
    - O tokens con ID único que puedas invalidar

    Args:
        current_user: Usuario inyectado por get_current_user
        auth_service: Servicio de autenticación

    Returns:
        dict: Confirmación de logout
    """
    return await auth_service.logout_user(current_user)