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
    TokenVerification
)
from app.utils.security import decode_access_token
from app.config import settings
from app.services import AuthService

from logging import getLogger

logger = getLogger(__name__)

# ============================================
# CONFIGURACIÓN DEL ROUTER
# ============================================
router = APIRouter(prefix="/auth", tags=["authentication"])

# ============================================
# OAUTH2 SCHEME
# ============================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ============================================
# CONSTANTES DE EXCEPCIONES (Clean Code)
# ============================================
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o token expirado",
    headers={"WWW-Authenticate": "Bearer"},
)

INACTIVE_USER_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Usuario inactivo"
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

# ============================================
# DEPENDENCIA: GET CURRENT USER
# ============================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    🛡️ GUARDIÁN DEL SISTEMA
    
    Esta función es una DEPENDENCIA que:
    1. Recibe el token JWT
    2. Lo decodifica y valida
    3. Busca el usuario en la BD
    4. Verifica que esté activo
    5. Devuelve el usuario o lanza error 401
    
    Uso en endpoints:
    @router.get("/protegido")
    async def mi_endpoint(user: User = Depends(get_current_user)):
        # Solo se ejecuta si el token es válido
        return {"mensaje": f"Hola {user.username}"}
    
    Args:
        token: Token JWT extraído del header Authorization
        session: Sesión de base de datos
    
    Returns:
        User: Usuario autenticado
    
    Raises:
        HTTPException 401: Si el token es inválido o usuario no existe
    """
    try:
        # 1. Decodificar el token JWT
        payload = decode_access_token(token)
        if payload is None:
            raise CREDENTIALS_EXCEPTION
            
        # 2. Extraer user_id del payload (payload es un dict)
        user_id = payload.get("user_id")
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
            
    except Exception as e:
        logger.error(f"❌ Error decodificando token: {e}")
        raise CREDENTIALS_EXCEPTION

    # 3. Buscar usuario en la base de datos
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 4. Validar que existe
    if user is None:
        logger.warning(f"❌ Usuario ID {user_id} no encontrado en BD")
        raise CREDENTIALS_EXCEPTION

    # 5. Validar que está activo
    if not user.is_active:
        logger.warning(f"❌ Usuario {user.username} inactivo intentando acceder")
        raise INACTIVE_USER_EXCEPTION

    return user

# ============================================
# ENDPOINT: LOGIN
# ============================================
@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    🔑 INICIAR SESIÓN (Generar Token JWT)

    Utiliza el AuthService para manejar toda la lógica de autenticación.
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