#!/usr/bin/env python3
"""
Script para crear todas las tablas faltantes en la base de datos.
Usa SQLModel.metadata.create_all() para crear las tablas que no están en las migraciones.
"""

import asyncio
from sqlmodel import SQLModel
from app.database import engine
from app.models import Category, Company, Branch, Subscription, User

async def create_tables():
    """Crear todas las tablas definidas en los modelos."""

    print("🔨 Creando tablas faltantes...")

    # Crear todas las tablas definidas en los modelos
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    print("✅ Todas las tablas creadas exitosamente!")

    # Verificar tablas creadas
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = result.fetchall()

    print("\n📋 Tablas en la base de datos:")
    for table in tables:
        print(f"  - {table[0]}")

if __name__ == "__main__":
    asyncio.run(create_tables())

