#!/usr/bin/env python3
"""
🧪 SCRIPT PARA PROBAR ENDPOINTS DE PRODUCTOS

Este script prueba todos los endpoints de productos con autenticación.
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_session
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from sqlalchemy import select
import json


async def setup_test_data():
    """Crear datos de prueba si no existen"""
    async for session in get_session():
        try:
            # Verificar usuario de prueba
            result = await session.execute(select(User).where(User.email == 'test@example.com'))
            user = result.scalar_one_or_none()

            if not user:
                # Verificar si empresa ya existe
                result = await session.execute(select(Company).where(Company.slug == 'empresa-test'))
                company = result.scalar_one_or_none()

                if not company:
                    # Crear empresa
                    company = Company(
                        name='Empresa Test',
                        slug='empresa-test',
                        owner_name='Test Owner',
                        owner_email='test@example.com'
                    )
                    session.add(company)
                    await session.commit()
                    await session.refresh(company)
                else:
                    print(f"✅ Empresa ya existe: {company.name}")

                # Crear usuario con rol válido (UUID del rol admin)
                # UUID del rol Administrador de la BD
                admin_role_id = "14d7db22-a183-476f-a269-6efe99245150"

                user = User(
                    username='testuser',
                    email='test@example.com',
                    hashed_password='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeXtVF7JzK0rZzQy',  # 'password'
                    full_name='Test User',
                    company_id=company.id,
                    role_id=admin_role_id,  # Rol admin
                    is_active=True
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Crear categoría de prueba
                category = Category(
                    name='Categoría Test',
                    description='Categoría para pruebas',
                    company_id=company.id,
                    is_active=True
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)

