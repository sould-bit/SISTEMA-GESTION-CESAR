# backend/seed_data.py
"""
Script de Seed para poblar la base de datos con datos iniciales.
Versión ASYNC para la nueva arquitectura.

Ejecución: python seed_data.py
"""
import asyncio
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Company, Branch, Subscription, User
from app.config import settings
from app.utils.security import get_password_hash
from datetime import datetime, timedelta


async def seed_database():
    """Función principal de seeding."""
    print("🚀 Iniciando Seed de Base de Datos...")
    
    # Crear engine async
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # =====================================================
        # VERIFICAR SI YA HAY DATOS (Idempotencia)
        # =====================================================
        result = await session.execute(select(Company))
        existing_company = result.scalar_one_or_none()
        if existing_company:
            print("⚠️  Ya existen datos en la base de datos. Seed cancelado.")
            print("   Si deseas reiniciar, ejecuta: docker-compose down -v")
            return
        
        # =====================================================
        # EMPRESA 1: El Rincón (tu cliente principal)
        # =====================================================
        print("\n🏢 Creando Empresa 1: El Rincón...")

        # Crear la empresa manualmente (datos específicos, no aleatorios)
        empresa_rincon = Company(
            name="El Rincón de las Salchipapas",
            slug="el-rincon",
            legal_name="El Rincón S.A.S",
            tax_id="900.123.456-7",
            owner_name="César",
            owner_email="cesar@elrincon.com",
            owner_phone="+57 300 123 4567",
            plan="premium",
            is_active=True
        )
        session.add(empresa_rincon)
        await session.commit()
        await session.refresh(empresa_rincon)
        print(f"   ✅ Empresa creada: {empresa_rincon.name} (ID: {empresa_rincon.id})")

        # Suscripción para El Rincón
        sub_rincon = Subscription(
            company_id=empresa_rincon.id,
            plan="premium",
            status="active",
            amount=100000,
            currency="COP"
        )
        session.add(sub_rincon)
        await session.commit()
        await session.refresh(sub_rincon)
        print(f"   ✅ Suscripción: {sub_rincon.plan} - ${sub_rincon.amount:,.0f} COP")

        # Sucursales de El Rincón
        sucursal_principal = Branch(
            company_id=empresa_rincon.id,
            name="Sede Norte",
            code="NORTE",
            address="Calle 80 #45-23",
            phone="+57 1 234 5678",
            is_active=True,
            is_main=True
        )
        session.add(sucursal_principal)
        
        sucursal_centro = Branch(
            company_id=empresa_rincon.id,
            name="Sede Centro",
            code="CENTRO",
            address="Carrera 7 #32-10",
            phone="+57 1 876 5432",
            is_active=True,
            is_main=False
        )
        session.add(sucursal_centro)
        session.commit()
        session.refresh(sucursal_principal)
        session.refresh(sucursal_centro)
        print(f"   ✅ Sucursales: {sucursal_principal.name}, {sucursal_centro.name}")
        
        # Usuario Admin de El Rincón
        admin_rincon = User(
            company_id=empresa_rincon.id,
            branch_id=sucursal_principal.id,
            username="admin",
            email="admin@elrincon.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Administrador El Rincón",
            role="admin",
            is_active=True
        )
        session.add(admin_rincon)
        
        # Cajero de prueba
        cajero_rincon = User(
            company_id=empresa_rincon.id,
            branch_id=sucursal_principal.id,
            username="cajero1",
            email="cajero@elrincon.com",
            hashed_password=pwd_context.hash("cajero123"),
            full_name="Juan Pérez",
            role="cajero",
            is_active=True
        )
        session.add(cajero_rincon)
        session.commit()
        print(f"   ✅ Usuarios: admin@elrincon.com, cajero@elrincon.com")
        
        # =====================================================
        # EMPRESA 2: Datos aleatorios con Factory Boy (demo)
        # =====================================================
        print("\n🏢 Creando Empresa 2 (datos aleatorios con Factory)...")
        
        # Aquí usamos la Factory para generar datos aleatorios
        empresa_demo = CompanyFactory.build(plan="basic")
        session.add(empresa_demo)
        session.commit()
        session.refresh(empresa_demo)
        print(f"   ✅ Empresa creada: {empresa_demo.name}")
        
        # Sucursal aleatoria
        sucursal_demo = BranchFactory.build(
            company=None,
            company_id=empresa_demo.id,
            is_main=True
        )
        session.add(sucursal_demo)
        session.commit()
        session.refresh(sucursal_demo)
        print(f"   ✅ Sucursal: {sucursal_demo.name}")
        
        # Usuario admin aleatorio
        admin_demo = UserFactory.build(
            company=None,
            company_id=empresa_demo.id,
            branch=None,
            branch_id=sucursal_demo.id,
            role="admin"
        )
        session.add(admin_demo)
        session.commit()
        print(f"   ✅ Usuario: {admin_demo.email}")
        
    print("\n" + "="*50)
    print("🎉 ¡Seed completado exitosamente!")
    print("="*50)
    print("\n📋 Credenciales de acceso:")
    print("   Admin El Rincón: admin@elrincon.com / admin123")
    print("   Cajero El Rincón: cajero@elrincon.com / cajero123")


if __name__ == "__main__":
    seed_database()