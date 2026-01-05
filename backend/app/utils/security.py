from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional, List
from jose import JWTError, jwt
from uuid import UUID
from app.config import settings
from app.schemas.auth import TokenData




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = settings.ALGORITHM


def verify_password(plain_password: str, hashed_password: str)-> bool:
    """verifica si la contraseña es correcta"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str)-> str:
    """
    Genera un hash de la contraseña.

    ADVERTENCIA: Esta es una operación síncrona y que consume CPU.
    En un endpoint asíncrono, DEBE ser llamada usando `run_in_executor`
    para evitar bloquear el servidor.
    Ejemplo:
    hashed_password = await run_in_executor(None, get_password_hash, "nueva_contraseña")
    """
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    permissions: Optional[List[str]] = None,
    role_id: Optional[UUID] = None,
    role_code: Optional[str] = None
) -> str:
    """
    Crea un token JWT con soporte para permisos RBAC.
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": "admin"})
        expires_delta: Tiempo de expiración
        permissions: Lista de códigos de permisos del usuario (v3.3)
        role_id: UUID del rol del usuario (v3.3)
        role_code: Código del rol del usuario (v3.3)
    
    Returns:
        Token JWT como string
    """
    to_encode = data.copy()
    
    # Agregar permisos si se proporcionan (v3.3)
    if permissions:
        to_encode["permissions"] = permissions
    
    # Agregar role_id y role_code si se proporcionan (v3.3)
    if role_id:
        to_encode["role_id"] = str(role_id)  # Convertir UUID a string
    
    if role_code:
        to_encode["role_code"] = role_code
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un refresh token JWT.
    
    Args:
        data: Datos a incluir en el token (solo user_id y company_id)
        expires_delta: Tiempo de expiración (default: 7 días)
        
    Returns:
        Refresh token JWT como string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT como string
    
    Returns:
        Diccionario con los datos del token, o None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def get_user_from_token(token: str) -> Optional[TokenData]:
    """
    Obtiene los datos del usuario desde un token JWT.
    
    Actualizado en v3.3 para incluir permisos del sistema RBAC.
    
    Args:
        token: Token JWT (puede venir con o sin "Bearer ")
    
    Returns:
        TokenData con los datos del usuario, o None si es inválido
    """
    # Remover "Bearer " si está presente
    if token.startswith("Bearer "):
        token = token[7:]
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
     # Validar que tenga los campos requeridos
    required_fields = ["user_id", "company_id", "role", "plan"]
    if not all(field in payload for field in required_fields):
        return None 

    # Convertir payload a TokenData
    return TokenData(
        user_id=payload.get("user_id"),
        company_id=payload.get("company_id"),
        branch_id=payload.get("branch_id"),
        role=payload.get("role"),  # Legacy
        plan=payload.get("plan"),
        username=payload.get("username"),
        # NUEVO: Sistema RBAC (v3.3)
        role_id=payload.get("role_id"),
        role_code=payload.get("role_code"),
        permissions=payload.get("permissions", [])
    )