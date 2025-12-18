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

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import User, Company
from app.schemas.auth import(
    LoginRequest,
    Token,
    TokenData,
    UserResponse,
    TokenVerification
) 
from app.utils.security import verify_password, create_access_token, decode_access_token
from app.config import settings

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
    session: AsyncSession = Depends(get_session)
):
    """
    🔑 INICIAR SESIÓN (Generar Token JWT)
    """
    # 1. Buscar empresa
    result = await session.execute(select(Company).where(Company.slug == login_data.company_slug))
    company = result.scalar_one_or_none()
    if not company or not company.is_active:
        raise HTTPException(status_code=404, detail="Empresa no encontrada o inactiva")

    # 2. Buscar usuario EN esa empresa
    statement = select(User).where(
        User.username == login_data.username,
        User.company_id == company.id  # <--- FILTRO CLAVE
    )
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    # 2. Validar existencia y contraseña
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"🔒 Intento de login fallido para: {login_data.username}")
        raise CREDENTIALS_EXCEPTION
    
    # 3. Validar estado activo
    if not user.is_active:
        raise INACTIVE_USER_EXCEPTION

    # 4. Generar Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Datos extra para el frontend
    token_payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "company_id": user.company_id,
        "role": user.role,
        "plan": user.company.plan if user.company else "free"
    }

    access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires
    )

    logger.info(f"✅ Login exitoso: {user.username} (Empresa: {user.company_id})")

    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }
# ============================================
# ENDPOINT: GET CURRENT USER INFO
# ============================================


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user :User = Depends(get_current_user)):
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
    
    Returns:
        UserResponse: Datos del usuario (sin contraseña)
    """

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        company_id=current_user.company_id,
        branch_id=current_user.branch_id
    )

# ============================================
# ENDPOINT: VERIFY TOKEN
# ============================================

@router.get("/verify", response_model=TokenVerification)
async def verify_token(current_user: User =Depends(get_current_user)):
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
    
    Returns:
        dict: Confirmación de validez
    """
#
    return TokenVerification(
        valid=True,
        user_id=current_user.id,
        username=current_user.username,
        company_id=current_user.company_id
    )

    # ============================================
# ENDPOINT: REFRESH TOKEN (BONUS)
# ============================================

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
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
    
    Returns:
        Token: Nuevo token JWT
    """
    # Preparar datos para el nuevo token
    token_data = {
        "user_id": current_user.id,
        "company_id": current_user.company_id,
        "branch_id": current_user.branch_id,
        "role": current_user.role,
        "username": current_user.username,
        "plan": current_user.company.plan if current_user.company else "free"
    }

    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    logger.info(f"✅ Token refrescado para: {current_user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ============================================
# ENDPOINT: LOGOUT (BONUS - Opcional)
# ============================================

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
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
    
    Returns:
        dict: Confirmación de logout
    """
    
    print(f"👋 Logout: {current_user.username}")
    
    return {
        "message": "Logout exitoso",
        "detail": "Elimina el token del cliente"
    }