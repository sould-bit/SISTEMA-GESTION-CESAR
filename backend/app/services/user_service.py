from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger(__name__)

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self, company_id: int) -> List[User]:
        stmt = select(User).where(User.company_id == company_id).options(
            selectinload(User.user_role),
            selectinload(User.branch)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user(self, user_id: int, company_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id, User.company_id == company_id).options(selectinload(User.user_role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, company_id: int, user_data: UserCreate) -> User:
        # Check if email/username exists in company
        # Check collision separately for better error message
        # Check email
        stmt_email = select(User).where(User.email == user_data.email, User.company_id == company_id)
        if (await self.session.execute(stmt_email)).scalar_one_or_none():
            logger.warning(f"Registration failed: Email {user_data.email} already exists in company {company_id}")
            raise ValueError(f"El email '{user_data.email}' ya está registrado en esta empresa.")

        # Check username
        stmt_username = select(User).where(User.username == user_data.username, User.company_id == company_id)
        if (await self.session.execute(stmt_username)).scalar_one_or_none():
             logger.warning(f"Registration failed: Username {user_data.username} already exists in company {company_id}")
             raise ValueError(f"El usuario '{user_data.username}' ya existe en esta empresa.")

        # Validate Role
        role = await self.session.get(Role, user_data.role_id)
        if not role or role.company_id != company_id:
            raise ValueError("Invalid Role ID")

        # Create User
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            company_id=company_id,
            branch_id=user_data.branch_id,
            role_id=user_data.role_id,
            role=role.code, # Legacy field support
            is_active=user_data.is_active
        )
        
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        
        # Populate relationship for response serialization
        new_user.user_role = role
        
        return new_user

    async def update_user(self, user_id: int, company_id: int, user_data: UserUpdate) -> User:
        user = await self.get_user(user_id, company_id)
        if not user:
            raise ValueError("User not found")

        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            user.hashed_password = get_password_hash(update_data.pop("password"))

        if "role_id" in update_data and update_data["role_id"]:
             # Validate Role
            role = await self.session.get(Role, update_data["role_id"])
            if not role or role.company_id != company_id:
                raise ValueError("Invalid Role ID")
            user.role = role.code # Legacy update

        for key, value in update_data.items():
            setattr(user, key, value)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int, company_id: int) -> bool:
        user = await self.get_user(user_id, company_id)
        if not user:
            return False
        
        user.is_active = False # Soft delete
        self.session.add(user)
        await self.session.commit()
        return True
