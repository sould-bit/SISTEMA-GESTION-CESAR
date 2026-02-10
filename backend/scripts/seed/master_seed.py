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
    RolePermission, Category, Product, Branch, Table, Order, OrderItem, Inventory
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

    async def seed_branches(self, company: Company) -> Dict[str, "Branch"]:
        """Carga sucursales"""
        try:
            data = await self.load_json("branches.json")
        except FileNotFoundError:
            print("ℹ️  No se encontró branches.json, creando sucursal por defecto...")
            result = await self.session.execute(
                select(Branch).filter(
                    Branch.code == "MAIN",
                    Branch.company_id == company.id
                )
            )
            branch = result.scalar_one_or_none()
            if not branch:
                branch = Branch(
                    name="Sucursal Principal",
                    code="MAIN",
                    company_id=company.id,
                    is_main=True,
                    is_active=True
                )
                self.session.add(branch)
                await self.session.commit()
                print(f"✅ Sucursal por defecto creada: {branch.name}")
            return {"MAIN": branch}

        branches = {}
        for branch_data in data["branches"]:
            company_code_in_branch = branch_data.pop("company_code", self.company_code)
            if company_code_in_branch != company.slug:
                continue

            branch_data["company_id"] = company.id

            result = await self.session.execute(
                select(Branch).filter(
                    Branch.code == branch_data["code"],
                    Branch.company_id == company.id
                )
            )
            branch = result.scalar_one_or_none()

            if not branch:
                branch = Branch(**branch_data)
                self.session.add(branch)
                print(f"✅ Sucursal creada: {branch.name}")

            branches[branch.code] = branch

        await self.session.commit()
        return branches

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
                await self.session.flush()  # Flush to get ID immediately
                print(f"✅ Categoría creada: {category.name}")
            else:
                print(f"ℹ️  Categoría ya existe: {category.code}")

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
                await self.session.flush()  # Commit inmediato para evitar conflictos
                print(f"✅ Permiso creado: {permission.name}")
            else:
                print(f"ℹ️  Permiso ya existe: {permission.code}")

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
                        granted_by=None  # Evitar hardcodear ID para prevenir IntegrityError
                    )
                    self.session.add(role_permission)
                    print(f"✅ Permiso asignado: {role.name} -> {permission.name}")

        await self.session.commit()

    async def seed_users(self, company: Company, roles: Dict[str, Role], branches: Dict[str, "Branch"]):
        """Carga usuarios de prueba"""
        data = await self.load_json("users.json")
        default_branch = branches.get("MAIN")

        for user_data in data["users"]:
            user_data_copy = user_data.copy()

            # Reemplazar códigos por IDs
            role_code = user_data_copy.pop("role_code")
            company_code_in_user = user_data_copy.pop("company_code")
            branch_code = user_data_copy.pop("branch_code", "MAIN")

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
                
                # Asignar branch_id
                branch = branches.get(branch_code, default_branch)
                if branch:
                    user_data_copy["branch_id"] = branch.id

                # Hash de contraseña
                from app.utils.security import get_password_hash
                user_data_copy["hashed_password"] = get_password_hash(user_data_copy.pop("password"))

                user = User(**user_data_copy)
                self.session.add(user)
                print(f"✅ Usuario creado: {user.username} (branch: {branch_code})")
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

    async def seed_inventory(self, company: Company, branches: Dict[str, "Branch"]):
        """Carga inventario inicial para productos"""
        from app.models.inventory import Inventory
        from decimal import Decimal
        
        # Obtener todos los productos de la compañía
        result = await self.session.execute(
            select(Product).filter(Product.company_id == company.id)
        )
        products = result.scalars().all()
        
        if not products:
            print("ℹ️  No hay productos para crear inventario")
            return
        
        # Usar la primera sucursal
        branch = list(branches.values())[0] if branches else None
        if not branch:
            print("ℹ️  No hay sucursales para crear inventario")
            return
        
        for product in products:
            # Verificar si ya existe inventario
            result = await self.session.execute(
                select(Inventory).filter(
                    Inventory.product_id == product.id,
                    Inventory.branch_id == branch.id
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                inventory = Inventory(
                    product_id=product.id,
                    branch_id=branch.id,
                    stock=Decimal("100"),
                    min_stock=Decimal("10")
                )
                self.session.add(inventory)
                print(f"✅ Inventario creado: {product.name} (stock: 100)")
            else:
                print(f"ℹ️  Inventario ya existe: {product.name}")
        
        await self.session.commit()
    
    async def seed_tables(self, company: Company, branches: Dict[str, "Branch"]):
        """Carga mesas"""
        try:
            data = await self.load_json("tables.json")
        except FileNotFoundError:
            print("ℹ️  No se encontró tables.json, saltando...")
            return

        # Usar la primera sucursal
        branch = list(branches.values())[0] if branches else None
        if not branch: return

        tables = {}
        for table_data in data["tables"]:
            table_data["branch_id"] = branch.id
            
            result = await self.session.execute(
                select(Table).filter(
                    Table.table_number == table_data["table_number"],
                    Table.branch_id == branch.id
                )
            )
            table = result.scalar_one_or_none()
            if not table:
                table = Table(**table_data)
                self.session.add(table)
                print(f"✅ Mesa creada: {table.table_number}")
            tables[table.table_number] = table
        
        await self.session.commit()
        return tables

    async def seed_demo_orders(self, company: Company, branches: Dict[str, "Branch"], users: List[User], tables: Dict[int, Table], products: List[Product]):
        """Crea pedidos de prueba para E2E"""
        if not tables or not products:
            print("ℹ️  Saltando pedidos demo (sin mesas o productos)")
            return

        branch = list(branches.values())[0]
        user = users[0] if users else None
        
        # Mesa 1 con pedido pendiente
        table1 = tables.get(1)
        if table1:
            order1 = Order(
                company_id=company.id,
                branch_id=branch.id,
                order_number="ORDER-001",
                status="confirmed",
                table_id=table1.id,
                created_by_id=user.id if user else None,
                total=50000,
                subtotal=45000,
                tax_total=5000
            )
            self.session.add(order1)
            await self.session.flush()
            
            # Item para el pedido
            item1 = OrderItem(
                order_id=order1.id,
                product_id=products[0].id,
                quantity=1,
                unit_price=50000,
                subtotal=50000
            )
            self.session.add(item1)
            table1.status = "occupied"
            self.session.add(table1)
            print(f"✅ Pedido demo creado para Mesa 1: {order1.order_number}")

        await self.session.commit()

    async def run(self, dry_run: bool = False, reset: bool = False, genesis_mode: bool = False):
        """Ejecuta el seeding completo"""
        print("🌱 Iniciando Master Seed...")
        print(f"📁 Directorio de datos: {self.data_dir}")
        print(f"🏢 Compañía: {self.company_code}")
        print(f"🔍 Dry run: {dry_run}")
        print(f"🔄 Reset: {reset}")
        print(f"🧬 Genesis Mode: {genesis_mode}")
        print("-" * 50)

        if reset:
            print("🗑️  Reset activado - limpiando datos existentes...")
            await self.clean_database()

        try:
            """los datos configuracionales como categorias , permisos roles , y datos para funcion del sistema por defecto """
            
            # 1. Compañías (Template o Negocio)
            if genesis_mode:
                print("⚙️  Modo Genesis: Usando 'System Template' company...")
                company = await self.get_or_create_company({
                    "name": "System Template", 
                    "slug": "system_template",
                    "plan": "system",
                    "is_active": False
                })
            else:
                print("🏢 Creando compañías de negocio...")
                company = await self.seed_companies()

            # 2. Categorías de permisos
            print("📂 Creando categorías de permisos...")
            categories = await self.seed_categories(company)

            # 3. Permisos
            print("🔐 Creando permisos...")
            permissions = await self.seed_permissions(company, categories)

            # 4. Roles
            print("👥 Creando roles...")
            roles = await self.seed_roles(company)

            # 5. Sucursales
            print("🏪 Creando sucursales...")
            branches = await self.seed_branches(company)

            # 6. Usuarios
            print("👤 Creando usuarios...")
            await self.seed_users(company, roles, branches)

            # 6. Asignaciones rol-permiso
            print("🔗 Asignando permisos a roles...")
            await self.seed_role_permissions(roles, permissions)

            if genesis_mode:
                print("🛑 Modo Genesis finalizado. Datos de negocio NO cargados.")
                print("   (El sistema está listo para pruebas de Registro/Onboarding)")
                return

            # 7. Categorías de productos
            print("📂 Creando categorías de productos...")
            prod_categories = await self.seed_product_categories(company)

            # 8. Productos
            print("🍎 Creando productos...")
            await self.seed_products(company, prod_categories)
            
            # Obtener productos creados
            result = await self.session.execute(select(Product).filter(Product.company_id == company.id))
            products = result.scalars().all()

            # 9. Inventario inicial
            print("📦 Creando inventario inicial...")
            await self.seed_inventory(company, branches)

            # 10. Mesas
            print("🪑 Creando mesas...")
            tables = await self.seed_tables(company, branches)

            # 11. Pedidos Demo
            print("📝 Creando pedidos demo...")
            # Obtener usuarios para asignar
            result = await self.session.execute(select(User).filter(User.company_id == company.id))
            users_list = result.scalars().all()
            await self.seed_demo_orders(company, branches, users_list, tables, products)

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

    async def clean_database(self):
        """Elimina todos los datos de las tablas principales"""
        from sqlalchemy import text
        
        tables = [
            # Orden transaccional/dependiente primero
            "order_item_modifiers", "order_items", "orders", "payments",
            "cash_closures", "audit_logs", "print_jobs",
            "recipe_items", "active_recipes", "recipes",
            "ingredient_transactions", "ingredient_batches", "product_modifiers",
            "inventory_transactions", "inventory_counts", "inventory_count_items",
            "production_event_input_batches", "production_event_inputs", "production_events",
            
            # Tablas principales
            "ingredients", "products", "categories", "inventories",
            "users", "role_permissions", "roles", "permissions", "permission_categories",
            "branches", "companies", 
            "customers", "customer_addresses", "delivery_shifts"
        ]
        
        print("⚠️  Limpiando tablas...")
        for table in tables:
            try:
                # Use CASCADE to handle FKs automatically
                await self.session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                print(f"   - {table} limpiada")
            except Exception as e:
                # Si la tabla no existe o error, solo loguear warning
                print(f"   ⚠️ No se pudo limpiar {table} (quizás no existe aun): {e}")

        await self.session.commit()
        print("✨ Base de datos limpia")


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Master Seed Script")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría")
    parser.add_argument("--reset", action="store_true", help="Limpiar datos existentes")
    parser.add_argument("--genesis", action="store_true", help="Modo Genesis: Solo cargar config de sistema")
    parser.add_argument("--company", default="fastops", help="Código de compañía")

    args = parser.parse_args()

    async for session in get_session():
        seeder = MasterSeeder(session, args.company)
        await seeder.run(dry_run=args.dry_run, reset=args.reset, genesis_mode=args.genesis)
        break


if __name__ == "__main__":
    asyncio.run(main())
