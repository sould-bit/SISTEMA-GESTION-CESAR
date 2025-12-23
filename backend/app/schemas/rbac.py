from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# PERMISSION CATEGORY SCHEMAS
# ============================================================================

class PermissionCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


class PermissionCategoryCreate(PermissionCategoryBase):
    pass


class PermissionCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class PermissionCategoryRead(PermissionCategoryBase):
    id: UUID
    company_id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# PERMISSION SCHEMAS
# ============================================================================

class PermissionBase(BaseModel):
    category_id: UUID
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    is_active: bool = True


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    category_id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    is_active: Optional[bool] = None


class PermissionRead(PermissionBase):
    id: UUID
    company_id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# ROLE SCHEMAS
# ============================================================================

class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    hierarchy_level: int = Field(50, ge=0, le=100)
    is_active: bool = True


class RoleCreate(RoleBase):
    permission_ids: Optional[List[UUID]] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hierarchy_level: Optional[int] = None
    is_active: Optional[bool] = None


class RoleRead(RoleBase):
    id: UUID
    company_id: int
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoleWithPermissions(RoleRead):
    permissions: List[PermissionRead] = []
