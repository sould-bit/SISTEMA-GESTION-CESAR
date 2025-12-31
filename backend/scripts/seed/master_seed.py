#!/usr/bin/env python3
"""
Master Seed Script - Poblado completo de datos iniciales
=======================================================

Este script carga todos los datos de seed desde archivos JSON
y los inserta en la base de datos en el orden correcto.

Uso:
    python scripts/seed/master_seed.py

Opciones:
    --dry-run    : Solo mostrar qué se haría, sin ejecutar
    --reset      : Limpiar datos existentes antes de cargar
    --company    : Especificar código de compañía (default: fastops)
"""

import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy import select

# Agregar backend al path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import get_session
from app.models import (
    Company, User, Role, Permission, PermissionCategory,
    RolePermission, Category, Product
)
from app.services.auth_service import AuthService
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.services.permission_category_service import PermissionCategoryService
from sqlalchemy.ext.asyncio import AsyncSession


class MasterSeeder:
    """Clase principal para el seeding de datos"""

    def __init__(self, session: AsyncSession, company_code: str = "fastops"):
        self.session = session
        self.company_code = company_code
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "seeds"

        # Servicios
        self.auth_service = AuthService(session)
        self.role_service = RoleService(session)
        self.permission_service = PermissionService(session)
        self.category_service = PermissionCategoryService(session)

    async def load_json(self, filename: str) -> Dict[str, Any]:
        """Carga un archivo JSON de datos de seed"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo de seed no encontrado: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def get_or_create_company(self, company_data: Dict[str, Any]) -> Company:
        """Obtiene o crea una compañía"""
        print(f"DEBUG: Processing company: {company_data.get('name', 'Unknown')}")
        
        # Map 'code' to 'slug' if present
        if "code" in company_data and "slug" not in company_data:
            company_data["slug"] = company_data.pop("code")

        # Map 'subscription_plan' to 'plan'
        if "subscription_plan" in company_data and "plan" not in company_data:
            company_data["plan"] = company_data.pop("subscription_plan")

        print(f"DEBUG: Final company_data: {company_data}")

        # Buscar compañía existente
        result = await self.session.execute(
            select(Company).filter(Company.slug == company_data["slug"])
        )
        company = result.scalar_one_or_none()

        if not company:
            company = Company(**company_data)
            self.session.add(company)
            await self.session.commit()
            await self.session.refresh(company)
            print(f"✅ Compañía creada: {company.name}")

        return company

    async def seed_companies(self) -> Company:
        """Carga compañías y retorna la compañía por defecto"""
        data = await self.load_json("companies.json")
        default_company = None

        for company_data in data["companies"]:
            company = await self.get_or_create_company(company_data)
            if company.slug == self.company_code:
                default_company = company

        if not default_company:
            # Si no existe la compañía especificada, crear una básica
            default_company = await self.get_or_create_company({
                "name": f"Empresa {self.company_code.title()}",
                "slug": self.company_code,
                "description": f"Compañía por defecto para {self.company_code}",
                "is_active": True,
                "subscription_plan": "premium"
            })

        return default_company

    async def seed_categories(self, company: Company) -> Dict[str, PermissionCategory]:
        """Carga categorías de permisos"""
        data = await self.load_json("permission_categories.json")
        categories = {}

        for category_data in data["categories"]:
            category_data["company_id"] = company.id

            # Verificar si ya existe
            result = await self.session.execute(
                select(PermissionCategory).filter(
                    PermissionCategory.code == category_data["code"],
                    PermissionCategory.company_id == company.id
                )
            )
            category = result.scalar_one_or_none()

            if not category:
                category = PermissionCategory(**category_data)
                self.session.add(category)
                print(f"✅ Categoría creada: {category.name}")

            categories[category.code] = category

        await self.session.commit()
        return categories

    async def seed_permissions(self, company: Company, categories: Dict[str, PermissionCategory]) -> Dict[str, Permission]:
        """Carga permisos"""
        data = await self.load_json("permissions.json")
        permissions = {}

        for permission_data in data["permissions"]:
            permission_data["company_id"] = company.id

            # Asignar categoría si existe
            if "category" in permission_data:
                category_code = permission_data.pop("category")
                if category_code in categories:
                    permission_data["category_id"] = categories[category_code].id

            # Verificar si ya existe
            result = await self.session.execute(
                select(Permission).filter(
                    Permission.code == permission_data["code"],
                    Permission.company_id == company.id
                )
            )
            permission = result.scalar_one_or_none()

            if not permission:
                permission = Permission(**permission_data)
                self.session.add(permission)
                print(f"✅ Permiso creado: {permission.name}")

            permissions[permission.code] = permission

        await self.session.commit()
        return permissions

    async def seed_roles(self, company: Company) -> Dict[str, Role]:
        """Carga roles"""
        data = await self.load_json("roles.json")
        roles = {}

        for role_data in data["roles"]:
            role_data["company_id"] = company.id

            # Verificar si ya existe
            result = await self.session.execute(
                select(Role).filter(
                    Role.code == role_data["code"],
                    Role.company_id == company.id
                )
            )
            role = result.scalar_one_or_none()

            if not role:
                role = Role(**role_data)
                self.session.add(role)
                print(f"✅ Rol creado: {role.name}")

            roles[role.code] = role

        await self.session.commit()
        return roles

    async def seed_role_permissions(self, roles: Dict[str, Role], permissions: Dict[str, Permission]):
        """Asigna permisos a roles"""
        data = await self.load_json("role_permissions.json")

        for assignment in data["role_permissions"]:
            role_code = assignment["role_code"]
            permission_codes = assignment["permission_codes"]

            if role_code not in roles:
                print(f"⚠️  Rol no encontrado: {role_code}")
                continue

            role = roles[role_code]

            for perm_code in permission_codes:
                if perm_code not in permissions:
                    print(f"⚠️  Permiso no encontrado: {perm_code}")
                    continue

                permission = permissions[perm_code]

                # Verificar si ya existe la asignación
                result = await self.session.execute(
                    select(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                        granted_by=1  # Usuario admin por defecto
                    )
                    self.session.add(role_permission)
                    print(f"✅ Permiso asignado: {role.name} -> {permission.name}")

        await self.session.commit()

    async def seed_users(self, company: Company, roles: Dict[str, Role]):
        """Carga usuarios de prueba"""
        data = await self.load_json("users.json")

        for user_data in data["users"]:
            user_data_copy = user_data.copy()

            # Reemplazar códigos por IDs
            role_code = user_data_copy.pop("role_code")
            company_code_in_user = user_data_copy.pop("company_code")

            if company_code_in_user != company.slug:
                continue  # Saltar usuarios de otras compañías

            if role_code not in roles:
                print(f"⚠️  Rol no encontrado para usuario {user_data['username']}: {role_code}")
                continue

            # Verificar si el usuario ya existe
            result = await self.session.execute(
                select(User).filter(
                    User.username == user_data["username"],
                    User.company_id == company.id
                )
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                # Crear usuario
                user_data_copy["company_id"] = company.id
                user_data_copy["role_id"] = roles[role_code].id

                # Hash de contraseña
                from app.utils.security import get_password_hash
                user_data_copy["hashed_password"] = get_password_hash(user_data_copy.pop("password"))

                user = User(**user_data_copy)
                self.session.add(user)
                print(f"✅ Usuario creado: {user.username}")
            else:
                print(f"ℹ️  Usuario ya existe: {user_data['username']}")

        await self.session.commit()

    async def seed_product_categories(self, company: Company) -> Dict[str, Category]:
        """Carga categorías de productos"""
        try:
            data = await self.load_json("categories.json")
        except FileNotFoundError:
            print("ℹ️  No se encontró categories.json, saltando...")
            return {}

        categories = {}
        for cat_data in data["categories"]:
            cat_data["company_id"] = company.id

            result = await self.session.execute(
                select(Category).filter(
                    Category.name == cat_data["name"],
                    Category.company_id == company.id
                )
            )
            category = result.scalar_one_or_none()

            if not category:
                category = Category(**cat_data)
                self.session.add(category)
                print(f"✅ Categoría de producto creada: {category.name}")
            else:
                print(f"ℹ️  Categoría de producto ya existe: {cat_data['name']}")
            
            categories[category.name] = category

        await self.session.commit()
        return categories

    async def seed_products(self, company: Company, categories: Dict[str, Category]):
        """Carga productos"""
        try:
            data = await self.load_json("products.json")
        except FileNotFoundError:
            print("ℹ️  No se encontró products.json, saltando...")
            return

        for prod_data in data["products"]:
            cat_name = prod_data.pop("category_name", None)
            prod_data["company_id"] = company.id
            
            if cat_name in categories:
                prod_data["category_id"] = categories[cat_name].id

            result = await self.session.execute(
                select(Product).filter(
                    Product.name == prod_data["name"],
                    Product.company_id == company.id
                )
            )
            product = result.scalar_one_or_none()

            if not product:
                product = Product(**prod_data)
                self.session.add(product)
                print(f"✅ Producto creado: {product.name}")
            else:
                print(f"ℹ️  Producto ya existe: {prod_data['name']}")

        await self.session.commit()

    async def run(self, dry_run: bool = False, reset: bool = False):
        """Ejecuta el seeding completo"""
        print("🌱 Iniciando Master Seed...")
        print(f"📁 Directorio de datos: {self.data_dir}")
        print(f"🏢 Compañía: {self.company_code}")
        print(f"🔍 Dry run: {dry_run}")
        print(f"🔄 Reset: {reset}")
        print("-" * 50)

        if reset:
            print("🗑️  Reset activado - limpiando datos existentes...")
            # Aquí iría código para limpiar datos si fuera necesario

        try:
            # 1. Compañías
            print("🏢 Creando compañías...")
            company = await self.seed_companies()

            # 2. Categorías
            print("📂 Creando categorías...")
            categories = await self.seed_categories(company)

            # 3. Permisos
            print("🔐 Creando permisos...")
            permissions = await self.seed_permissions(company, categories)

            # 4. Roles
            print("👥 Creando roles...")
            roles = await self.seed_roles(company)

            # 5. Usuarios
            print("👤 Creando usuarios...")
            await self.seed_users(company, roles)

            # 6. Asignaciones rol-permiso
            print("🔗 Asignando permisos a roles...")
            await self.seed_role_permissions(roles, permissions)

            # 7. Categorías de productos
            print("📂 Creando categorías de productos...")
            prod_categories = await self.seed_product_categories(company)

            # 8. Productos
            print("🍎 Creando productos...")
            await self.seed_products(company, prod_categories)

            if not dry_run:
                await self.session.commit()
                print("✅ Master Seed completado exitosamente!")
            else:
                print("🔍 Dry run completado - no se guardaron cambios")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error durante el seeding: {e}")
            await self.session.rollback()
            raise


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Master Seed Script")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría")
    parser.add_argument("--reset", action="store_true", help="Limpiar datos existentes")
    parser.add_argument("--company", default="fastops", help="Código de compañía")

    args = parser.parse_args()

    async for session in get_session():
        seeder = MasterSeeder(session, args.company)
        await seeder.run(dry_run=args.dry_run, reset=args.reset)
        break


if __name__ == "__main__":
    asyncio.run(main())
