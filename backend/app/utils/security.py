from datetime import datetime , timedelta
from passlib.context import CryptContext
from typing import Optional
from jose import JWTError, jwt
from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str)-> bool:
    """verifica si la contraseña es correcta"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str)-> str:
    """genera un hash de la contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT.
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": "admin"})
        expires_delta: Tiempo de expiración
    
    Returns:
        Token JWT como string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
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
    
    # Convertir payload a TokenData
    return TokenData(
        user_id=payload.get("user_id"),
        company_id=payload.get("company_id"),
        branch_id=payload.get("branch_id"),
        role=payload.get("role"),
        plan=payload.get("plan"),
        username=payload.get("username")
    )