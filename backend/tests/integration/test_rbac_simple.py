#!/usr/bin/env python3
"""
Pruebas Simples del Sistema RBAC - Validación Básica

Este script valida los conceptos fundamentales del sistema RBAC
sin depender de configuraciones complejas de pytest.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

async def test_basic_imports():
    """Test que los módulos principales se pueden importar."""
    print("🧪 Probando importaciones básicas...")

    try:
        from app.models.role import Role
        from app.models.permission import Permission
        from app.models.role_permission import RolePermission
        from app.models.permission_category import PermissionCategory
        from app.services.role_service import RoleService
        from app.services.permission_service import PermissionService
        print("✅ Importaciones de modelos y servicios exitosas")
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

async def test_decorators_syntax():
    """Test que los decoradores se pueden importar y tienen sintaxis correcta."""
    print("🧪 Probando decoradores de permisos...")

    try:
        from app.core.permissions import (
            require_permission,
            require_any_permission,
            require_all_permissions
        )
        print("✅ Decoradores importados correctamente")

        # Verificar que son funciones/callables
        assert callable(require_permission)
        assert callable(require_any_permission)
        assert callable(require_all_permissions)
        print("✅ Decoradores son callables")
        return True
    except Exception as e:
        print(f"❌ Error con decoradores: {e}")
        return False

async def test_schemas_validation():
    """Test que los esquemas Pydantic funcionan."""
    print("🧪 Probando esquemas Pydantic...")

    try:
        from app.schemas.rbac import (
            RoleCreate,
            RoleRead,
            PermissionCreate,
            PermissionRead,
            PermissionCategoryCreate
        )
        print("✅ Esquemas importados correctamente")

        # Probar creación de objetos
        role_data = RoleCreate(
            name="Rol de Prueba",
            code="test_role",
            hierarchy_level=50
        )
        print(f"✅ RoleCreate funciona: {role_data.name}")

        permission_data = PermissionCreate(
            category_id="550e8400-e29b-41d4-a716-446655440000",  # UUID dummy
            name="Permiso de Prueba",
            code="test.permission",
            resource="test",
            action="permission"
        )
        print(f"✅ PermissionCreate funciona: {permission_data.code}")

        return True
    except Exception as e:
        print(f"❌ Error con esquemas: {e}")
        return False

async def test_models_instantiation():
    """Test que los modelos se pueden instanciar."""
    print("🧪 Probando instanciación de modelos...")

    try:
        from app.models.role import Role
        from app.models.permission import Permission
        from uuid import uuid4

        # Crear instancias sin BD
        role = Role(
            company_id=1,
            name="Rol de Test",
            code="test_role",
            hierarchy_level=50,
            is_system=False,
            is_active=True
        )
        print(f"✅ Role creado: {role.name}")

        permission = Permission(
            company_id=1,
            category_id=uuid4(),
            name="Permiso de Test",
            code="test.permission",
            resource="test",
            action="permission",
            is_system=False,
            is_active=True
        )
        print(f"✅ Permission creado: {permission.code}")

        # Probar métodos
        higher_role = Role(
            company_id=1,
            name="Rol Superior",
            code="higher_role",
            hierarchy_level=80,
            is_system=False,
            is_active=True
        )
        can_inherit = role.can_inherit_from(higher_role)
        assert can_inherit == True
        print("✅ Método can_inherit_from funciona")

        return True
    except Exception as e:
        print(f"❌ Error con modelos: {e}")
        return False

def test_basic_validation():
    """Tests básicos de validación sin async."""
    print("🧪 Probando validaciones básicas...")

    try:
        from app.schemas.rbac import RoleCreate

        # Test validación de campos requeridos
        try:
            invalid_role = RoleCreate(name="", code="")  # Debería fallar
            print("❌ Validación no funciona")
            return False
        except Exception:
            print("✅ Validación de campos requeridos funciona")

        # Test validación de longitud
        try:
            long_name = "a" * 200  # Muy largo
            invalid_role = RoleCreate(name=long_name, code="test")
            print("❌ Validación de longitud no funciona")
            return False
        except Exception:
            print("✅ Validación de longitud funciona")

        return True
    except Exception as e:
        print(f"❌ Error en validaciones: {e}")
        return False

async def main():
    """Función principal de pruebas."""
    print("🔬 VALIDACIÓN SIMPLE DEL SISTEMA RBAC")
    print("=" * 50)

    tests = [
        ("Importaciones", test_basic_imports),
        ("Decoradores", test_decorators_syntax),
        ("Esquemas", test_schemas_validation),
        ("Modelos", test_models_instantiation),
        ("Validaciones", test_basic_validation),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))

    # Resultados finales
    print(f"\n{'='*50}")
    print("📊 RESULTADOS:")
    print('='*50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"   {test_name:15} : {status}")
        if not passed:
            all_passed = False

    print('='*50)

    if all_passed:
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("\n✨ El sistema RBAC tiene una base sólida.")
        print("\n🚀 PRÓXIMOS PASOS RECOMENDADOS:")
        print("   • Implementar cache Redis")
        print("   • Mejorar logging estructurado")
        print("   • Crear excepciones personalizadas")
        print("   • Actualizar dependencias críticas")
    else:
        print("⚠️  Algunas validaciones fallaron.")
        print("🔧 Revisa los errores arriba.")

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
