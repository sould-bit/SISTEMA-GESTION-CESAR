"""
Audit Schemas
=============
Pydantic schemas for Audit API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class AuditLogRead(BaseModel):
    """Audit log entry for API responses."""
    id: int
    company_id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    branch_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Paginated list of audit logs."""
    items: List[AuditLogRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogDetail(AuditLogRead):
    """Extended audit log with user agent."""
    user_agent: Optional[str] = None


# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class AuditLogFilter(BaseModel):
    """Filters for querying audit logs."""
    action: Optional[str] = None
    user_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    branch_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# =============================================================================
# SUMMARY SCHEMAS
# =============================================================================

class AuditSummary(BaseModel):
    """Summary statistics for audit logs."""
    total_logs: int
    logs_today: int
    top_actions: List[Dict[str, Any]]  # [{"action": "login_success", "count": 150}]
    top_users: List[Dict[str, Any]]    # [{"username": "admin", "count": 50}]
