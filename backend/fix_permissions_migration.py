
import asyncio
import logging
import sys
from sqlalchemy import select, and_
from app.database import async_session as async_session_factory
from app.models import Permission, RolePermission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_permissions")

async def fix_permissions():
    async with async_session_factory() as session:
        logger.info("Starting permission fix migration...")
        
        # 1. Get all permissions that start with 'admin.'
        stmt = select(Permission).where(Permission.code.like("admin.%"))
        result = await session.execute(stmt)
        prefixed_permissions = result.scalars().all()
        
        logger.info(f"Found {len(prefixed_permissions)} permissions with 'admin.' prefix.")
        
        migrated_count = 0
        
        for old_perm in prefixed_permissions:
            new_code = old_perm.code.replace("admin.", "", 1)
            company_id = old_perm.company_id
            
            # Check if destination permission already exists
            stmt_exist = select(Permission).where(
                and_(
                    Permission.code == new_code,
                    Permission.company_id == company_id
                )
            )
            result_exist = await session.execute(stmt_exist)
            existing_target_perm = result_exist.scalar_one_or_none()
            
            if existing_target_perm:
                logger.info(f"Target permission {new_code} already exists for company {company_id}. Merging...")
                
                # Move all RolePermissions from old to new
                stmt_rp = select(RolePermission).where(RolePermission.permission_id == old_perm.id)
                rps = (await session.execute(stmt_rp)).scalars().all()
                
                for rp in rps:
                    # Check if the role already has the target permission
                    stmt_check = select(RolePermission).where(
                        and_(
                            RolePermission.role_id == rp.role_id,
                            RolePermission.permission_id == existing_target_perm.id
                        )
                    )
                    if not (await session.execute(stmt_check)).scalar_one_or_none():
                        rp.permission_id = existing_target_perm.id
                        session.add(rp)
                    else:
                        # Duplicate assignment, delete the old one
                        await session.delete(rp)
                
                # Delete the old permission
                await session.delete(old_perm)
                
            else:
                logger.info(f"Renaming {old_perm.code} -> {new_code} (Company {company_id})")
                old_perm.code = new_code
                session.add(old_perm)
            
            migrated_count += 1
            
        await session.commit()
        logger.info(f"Migration completed. Processed {migrated_count} permissions.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_permissions())
