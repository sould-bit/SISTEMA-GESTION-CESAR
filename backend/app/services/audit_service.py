"""
Audit Service
=============
Servicio para registrar y consultar logs de auditoría.

Uso:
    audit_service = AuditService(db)
    await audit_service.log(
        action=AuditAction.LOGIN_SUCCESS,
        user=current_user,
        description="Usuario inició sesión"
    )
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditService:
    """
    Servicio de auditoría centralizado.
    
    Registra todas las acciones críticas del sistema
    con contexto de usuario, IP y timestamps.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # REGISTRO DE AUDITORÍA
    # =========================================================================
    
    async def log(
        self,
        action: AuditAction,
        company_id: int,
        user: Optional[User] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        request: Optional[Request] = None,
        branch_id: Optional[int] = None
    ) -> AuditLog:
        """
        Registra una acción en el log de auditoría.
        
        Args:
            action: Tipo de acción (AuditAction enum)
            company_id: ID de la empresa (multi-tenant)
            user: Usuario que realizó la acción
            entity_type: Tipo de entidad afectada ("product", "order", etc.)
            entity_id: ID de la entidad afectada
            old_value: Estado anterior (para cambios)
            new_value: Estado nuevo (para cambios)
            description: Descripción legible de la acción
            request: Request de FastAPI para extraer IP/User-Agent
            branch_id: Sucursal donde ocurrió (si aplica)
        
        Returns:
            AuditLog creado
        """
        # Extraer info del request si está disponible
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Crear entrada de auditoría
        audit_entry = AuditLog(
            company_id=company_id,
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action.value if hasattr(action, "value") else str(action),
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            branch_id=branch_id or (user.branch_id if user else None)
        )
        
        self.db.add(audit_entry)
        await self.db.commit()
        await self.db.refresh(audit_entry)
        
        logger.debug(f"📝 Audit: {action} by {user.username if user else 'system'}")
        return audit_entry
    
    async def log_simple(
        self,
        action: AuditAction,
        company_id: int,
        description: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> AuditLog:
        """Versión simplificada para logs sin mucho contexto."""
        audit_entry = AuditLog(
            company_id=company_id,
            user_id=user_id,
            username=username,
            action=action.value if hasattr(action, "value") else str(action),
            description=description
        )
        self.db.add(audit_entry)
        await self.db.commit()
        return audit_entry
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    async def get_logs(
        self,
        company_id: int,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[AuditLog], int]:
        """
        Consulta logs con filtros y paginación.
        
        Returns:
            Tuple de (lista de logs, total de registros)
        """
        # Base query
        query = select(AuditLog).where(AuditLog.company_id == company_id)
        count_query = select(func.count(AuditLog.id)).where(AuditLog.company_id == company_id)
        
        # Aplicar filtros
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
            count_query = count_query.where(AuditLog.entity_type == entity_type)
        
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
            count_query = count_query.where(AuditLog.entity_id == entity_id)
        
        if branch_id:
            query = query.where(AuditLog.branch_id == branch_id)
            count_query = count_query.where(AuditLog.branch_id == branch_id)
        
        if date_from:
            query = query.where(AuditLog.created_at >= date_from)
            count_query = count_query.where(AuditLog.created_at >= date_from)
        
        if date_to:
            query = query.where(AuditLog.created_at <= date_to)
            count_query = count_query.where(AuditLog.created_at <= date_to)
        
        # Ordenar y paginar
        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Ejecutar
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        return logs, total
    
    async def get_log_by_id(self, log_id: int, company_id: int) -> Optional[AuditLog]:
        """Obtiene un log por ID."""
        result = await self.db.execute(
            select(AuditLog).where(
                AuditLog.id == log_id,
                AuditLog.company_id == company_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        company_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """Obtiene el historial de una entidad específica."""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.company_id == company_id,
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_summary(self, company_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total logs
        total_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.company_id == company_id)
        )
        total_logs = total_result.scalar() or 0
        
        # Logs hoy
        today_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.company_id == company_id,
                AuditLog.created_at >= today
            )
        )
        logs_today = today_result.scalar() or 0
        
        # Top acciones
        top_actions_result = await self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id).label("count"))
            .where(AuditLog.company_id == company_id)
            .group_by(AuditLog.action)
            .order_by(desc("count"))
            .limit(5)
        )
        top_actions = [{"action": r[0], "count": r[1]} for r in top_actions_result.all()]
        
        # Top usuarios
        top_users_result = await self.db.execute(
            select(AuditLog.username, func.count(AuditLog.id).label("count"))
            .where(
                AuditLog.company_id == company_id,
                AuditLog.username.isnot(None)
            )
            .group_by(AuditLog.username)
            .order_by(desc("count"))
            .limit(5)
        )
        top_users = [{"username": r[0], "count": r[1]} for r in top_users_result.all()]
        
        return {
            "total_logs": total_logs,
            "logs_today": logs_today,
            "top_actions": top_actions,
            "top_users": top_users
        }
