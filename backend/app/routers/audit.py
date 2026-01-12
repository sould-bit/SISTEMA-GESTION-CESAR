"""
Audit Router
============
Endpoints para consultar logs de auditoría.

Permisos: Solo Administradores
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditLogRead,
    AuditLogList,
    AuditLogDetail,
    AuditSummary
)

router = APIRouter(prefix="/audit", tags=["Audit"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/logs", response_model=AuditLogList)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    entity_id: Optional[int] = Query(None, description="Filtrar por ID de entidad"),
    branch_id: Optional[int] = Query(None, description="Filtrar por sucursal"),
    date_from: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Fecha fin (ISO format)"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(50, ge=1, le=100, description="Tamaño de página"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los logs de auditoría con filtros opcionales.
    
    Permisos: Administrador
    """
    # TODO: Verificar permisos de admin
    
    audit_service = AuditService(db)
    logs, total = await audit_service.get_logs(
        company_id=current_user.company_id,
        action=action,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return AuditLogList(
        items=[AuditLogRead.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/logs/{log_id}", response_model=AuditLogDetail)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el detalle de un log específico.
    
    Permisos: Administrador
    """
    audit_service = AuditService(db)
    log = await audit_service.get_log_by_id(log_id, current_user.company_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log de auditoría no encontrado"
        )
    
    return AuditLogDetail.model_validate(log)


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogRead])
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de auditoría de una entidad específica.
    
    Ejemplo: /audit/entity/product/123
    
    Permisos: Administrador
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        company_id=current_user.company_id,
        limit=limit
    )
    
    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/summary", response_model=AuditSummary)
async def get_audit_summary(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticas resumidas de auditoría.
    
    Incluye:
    - Total de logs
    - Logs de hoy
    - Top 5 acciones más frecuentes
    - Top 5 usuarios más activos
    
    Permisos: Administrador
    """
    audit_service = AuditService(db)
    summary = await audit_service.get_summary(current_user.company_id)
    
    return AuditSummary(**summary)
