import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import async_session_factory
from app.models.user import User
from app.models.rbac import Role, Permission, RolePermission

async def check_user_permissions(email: str):
    async with async_session_factory() as session:
        # Get user with role
        stmt = select(User).where(User.email == email).options(
            selectinload(User.user_role).selectinload(Role.permissions)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print(f"User {email} not found")
            return

        print(f"User: {user.full_name} ({user.username})")
        
        role_name = "None"
        role_code = "None"
        permissions = []

        if user.user_role:
            role_name = user.user_role.name
            role_code = user.user_role.code
            permissions = user.user_role.permissions
        
        print(f"Role: {role_name} (Code: {role_code})")
        print("-" * 30)
        print("Effective Permissions:")
        
        if role_code == 'admin':
             print("- ALL (Admin has full access)")
        elif not permissions:
            print("- No permissions assigned")
        else:
            for perm in permissions:
                print(f"- {perm.name} ({perm.code})")

if __name__ == "__main__":
    asyncio.run(check_user_permissions("kate@gmail.com"))
