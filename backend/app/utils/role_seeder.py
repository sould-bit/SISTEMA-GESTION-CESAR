from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.role import Role
from app.models.company import Company
import logging

from app.core.rbac_defaults import DEFAULT_ROLES, DEFAULT_ROLE_PERMISSIONS_MAP

logger = logging.getLogger(__name__)

async def seed_default_roles(db: AsyncSession, company_id: int):
    """Seed default roles for a specific company."""
    
    default_roles = DEFAULT_ROLES

    # Define default permissions for each role
    role_permissions_map = DEFAULT_ROLE_PERMISSIONS_MAP

    from app.models.permission import Permission
    from app.models.role_permission import RolePermission
    from sqlmodel import and_

    # Pre-fetch all permissions for this company to avoid N+1
    stmt_perms = select(Permission).where(Permission.company_id == company_id)
    all_perms = (await db.execute(stmt_perms)).scalars().all()
    # Map code -> permission object
    perm_lookup = {p.code: p for p in all_perms}

    for role_data in default_roles:
        # 1. Create Role if not exists
        result = await db.execute(
            select(Role).where(
                Role.company_id == company_id,
                Role.code == role_data["code"]
            )
        )
        role = result.scalar_one_or_none()
        
        if not role:
            role = Role(
                company_id=company_id,
                name=role_data["name"],
                code=role_data["code"],
                description=role_data.get("description", ""),
                hierarchy_level=role_data.get("level", 10),
                is_system=True,
                is_active=True
            )
            db.add(role)
            await db.flush() # Get ID
            logger.info(f"Created role {role.name} (ID: {role.id})")
        
        # 2. Assign Permissions
        target_patterns = role_permissions_map.get(role_data["code"], [])
        if not target_patterns:
            continue

        # Filter permissions matching patterns
        perms_to_assign = []
        for pattern in target_patterns:
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                matches = [p for code, p in perm_lookup.items() if code.startswith(prefix)]
                perms_to_assign.extend(matches)
            else:
                if pattern in perm_lookup:
                    perms_to_assign.append(perm_lookup[pattern])
        
        # Remove duplicates
        unique_perms = {}
        for p in perms_to_assign:
            unique_perms[p.id] = p
        perms_to_assign = list(unique_perms.values())
        
        if not perms_to_assign:
            continue

        # Bulk assign (check existing to avoid dupes)
        # Fetch existing permission IDs for this role
        stmt_existing = select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
        existing_perm_ids = (await db.execute(stmt_existing)).scalars().all()
        existing_set = set(existing_perm_ids)

        new_count = 0
        for perm in perms_to_assign:
            if perm.id not in existing_set:
                rp = RolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                    granted_by=None # System
                )
                db.add(rp)
                new_count += 1
        
        if new_count > 0:
            logger.info(f"Assigned {new_count} permissions to role {role.name}")

    await db.commit()
