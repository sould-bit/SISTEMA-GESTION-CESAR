import asyncio
from sqlalchemy import text
from app.database import async_session
import uuid

async def assign_branch_permissions():
    async with async_session() as session:
        # Get admin role for company 1
        result = await session.execute(
            text("SELECT id FROM roles WHERE code = 'admin' AND company_id = 1")
        )
        role = result.fetchone()
        if not role:
            print('Admin role not found')
            return
        
        role_id = role[0]
        print(f'Admin role ID: {role_id}')
        
        # Get branch permissions
        result = await session.execute(
            text("SELECT id, code FROM permissions WHERE code LIKE 'branches.%'")
        )
        perms = result.fetchall()
        print(f'Found {len(perms)} branch permissions')
        
        for perm_id, perm_code in perms:
            await session.execute(
                text("""
                    INSERT INTO role_permissions (id, role_id, permission_id) 
                    VALUES (:id, :role_id, :perm_id) 
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                """),
                {'id': str(uuid.uuid4()), 'role_id': str(role_id), 'perm_id': str(perm_id)}
            )
            print(f'  {perm_code} OK')
        
        await session.commit()
        print('Done!')

if __name__ == "__main__":
    asyncio.run(assign_branch_permissions())
