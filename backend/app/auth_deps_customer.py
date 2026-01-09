"""
Customer Authentication Dependencies
=====================================
Dependencias para validar tokens JWT de clientes (PWA).
Separado de auth_deps.py (staff) para segregación B2B2C.
"""
from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from jose import jwt, JWTError

from app.config import settings
from app.database import get_session
from app.models.customer import Customer

security = HTTPBearer(auto_error=False)


@dataclass
class CustomerContext:
    """Contexto del cliente autenticado."""
    customer_id: int
    company_id: int
    customer: Optional[Customer] = None


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> CustomerContext:
    """
    Valida el token JWT de un cliente.
    Espera formato: sub = "customer:{customer_id}:{company_id}"
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        sub = payload.get("sub", "")
        token_type = payload.get("type")
        
        # Validar formato customer:id:company
        if token_type != "customer" or not sub.startswith("customer:"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no válido para clientes"
            )
        
        parts = sub.split(":")
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de token inválido"
            )
        
        customer_id = int(parts[1])
        company_id = int(parts[2])
        
        # Cargar customer de la BD
        result = await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.company_id == company_id
            )
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cliente no encontrado"
            )
        
        return CustomerContext(
            customer_id=customer_id,
            company_id=company_id,
            customer=customer
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


async def get_optional_customer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> Optional[CustomerContext]:
    """
    Valida token si existe, sino retorna None.
    Útil para endpoints públicos que personalizan si hay sesión.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_customer(credentials, db)
    except HTTPException:
        return None
