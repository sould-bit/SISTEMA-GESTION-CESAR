from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import User
from app.utils.security import decode_access_token
from logging import getLogger

logger = getLogger(__name__)

# ============================================
# OAUTH2 SCHEME
# ============================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ============================================
# CONSTANTES DE EXCEPCIONES
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
