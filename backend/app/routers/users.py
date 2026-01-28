from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.dependencies import get_current_user
from app.services.user_service import UserService
from app.utils.role_seeder import seed_default_roles
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.core.permissions import require_permission

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)

@router.get("/", response_model=List[UserRead])
@require_permission("users.read")
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """List all users in the company."""
    return await user_service.list_users(current_user.company_id)

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@require_permission("users.create")
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Create a new employee user."""
    try:
        return await user_service.create_user(current_user.company_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{user_id}", response_model=UserRead)
@require_permission("users.update")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user details."""
    try:
        return await user_service.update_user(user_id, current_user.company_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{user_id}")
@require_permission("users.delete")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Soft delete a user."""
    success = await user_service.delete_user(user_id, current_user.company_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deactivated successfully"}

@router.post("/fix-roles")
async def fix_missing_roles(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Helper endpoint to seed missing roles for the current company."""
    if current_user.role != "admin" and getattr(current_user.user_role, 'code', '') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can run this")
    
    await seed_default_roles(session, current_user.company_id)
    return {"message": "Roles seeded successfully"}
