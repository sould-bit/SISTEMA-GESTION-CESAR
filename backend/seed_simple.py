# backend/seed_simple.py
"""
Script SIMPLE de Seed para poblar la base de datos con datos básicos de prueba.
Versión ASYNC para testing rápido.

Ejecución: python seed_simple.py
"""
import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Company, Branch, User
from app.config import settings
from app.utils.security import get_password_hash
from datetime import datetime


async def seed_simple():
    """Crear datos básicos para testing del login."""

    print("🚀 Iniciando Seed Simple...")

    # Crear engine async
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Verificar si ya hay datos
            result = await session.execute(select(Company))
            existing = result.scalar_one_or_none()
            if existing:
                print("⚠️  Ya hay datos en la BD. Cancelando...")
                return

            # Crear empresa
            company = Company(
                name="El Rincón",
                slug="elrincon",
                legal_name="El Rincón S.A.S",
                tax_id="123456789",
                owner_name="César",
                owner_email="cesar@test.com",
                owner_phone="3001234567",
                plan="premium",
                is_active=True,
                timezone="America/Bogota",
                currency="COP"
            )
            session.add(company)
            await session.commit()
            await session.refresh(company)
            print(f"✅ Empresa creada: {company.name}")

            # Crear sucursal
            branch = Branch(
                company_id=company.id,
                name="Sucursal Principal",
                code="MAIN",
                address="Calle 123",
                phone="1234567",
                is_active=True,
                is_main=True
            )
            session.add(branch)
            await session.commit()
            await session.refresh(branch)
            print(f"✅ Sucursal creada: {branch.name}")

            # Crear usuario admin
            user = User(
                company_id=company.id,
                branch_id=branch.id,
                username="admin",
                email="admin@test.com",
                full_name="Administrador",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✅ Usuario creado: {user.username}")

            print("🎉 Seed completado exitosamente!")
            print("   Usuario: admin")
            print("   Password: admin123")
            print("   Empresa: elrincon")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_simple())

