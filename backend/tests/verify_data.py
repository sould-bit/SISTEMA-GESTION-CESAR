
import asyncio
import sys
from sqlalchemy import select, or_

# Mock missing libs if needed (to be safe in host env)
from unittest.mock import MagicMock
sys.modules["redis.asyncio"] = MagicMock()
sys.modules["jwt"] = MagicMock()
sys.modules["jose"] = MagicMock()
sys.modules["passlib"] = MagicMock()
sys.modules["passlib.context"] = MagicMock()

# Adjust path to find 'app'
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import async_session_factory
from app.models.company import Company
from app.models.user import User
from app.models.branch import Branch

async def verify_data():
    async with async_session_factory() as session:
        print("--- Verifying Data ---")
        
        # 1. Search for Company 'perrossteck'
        print("\n> BUSCANDO EMPRESA 'perrossteck'...")
        stmt_company = select(Company).where(
            or_(
                Company.name.ilike("%perrossteck%"),
                Company.slug.ilike("%perrossteck%")
            )
        )
        result_company = await session.execute(stmt_company)
        company = result_company.scalars().first()
        
        if not company:
            print("❌ Empresa 'perrossteck' NO ENCONTRADA.")
            # List all companies to help
            print("  Empresas disponibles:")
            all_comps = (await session.execute(select(Company))).scalars().all()
            for c in all_comps:
                print(f"  - ID: {c.id}, Name: {c.name}, Slug: {c.slug}")
            return
        
        print(f"✅ Empresa encontrada: ID={company.id}, Name='{company.name}', Slug='{company.slug}'")
        
        # 2. Search for User 'carlos' in that company
        print(f"\n> BUSCANDO USUARIO 'carlos' en la empresa {company.id}...")
        stmt_user = select(User).where(
            User.username.ilike("%carlos%"),
            User.company_id == company.id
        )
        result_user = await session.execute(stmt_user)
        user = result_user.scalars().first()
        
        if user:
            print(f"✅ Usuario encontrado: ID={user.id}, Username='{user.username}', BranchID={user.branch_id}")
        else:
            print("❌ Usuario 'carlos' NO ENCONTRADO en esta empresa.")
        
        # 3. Check Branches for this company
        print(f"\n> BUSCANDO SUCURSALES para la empresa {company.id}...")
        stmt_branch = select(Branch).where(Branch.company_id == company.id)
        result_branch = await session.execute(stmt_branch)
        branches = result_branch.scalars().all()
        
        if not branches:
            print("❌ NO existen sucursales para esta empresa.")
        else:
            print(f"✅ Se encontraron {len(branches)} sucursales:")
            for b in branches:
                print(f"  - ID: {b.id}, Name: '{b.name}', Code: '{b.code}', Active: {b.is_active}")

if __name__ == "__main__":
    asyncio.run(verify_data())
