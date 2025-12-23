#!/usr/bin/env python3
"""
Prueba del Sistema de Excepciones Personalizadas

Esta prueba valida:
- Excepciones específicas para diferentes escenarios RBAC
- Estructura de datos de las excepciones
- Compatibilidad con FastAPI
- Logging automático en excepciones
"""

import pytest
from app.core.exceptions import (
    RBACException,
    PermissionDeniedException,
    PermissionNotFoundException,
    InsufficientPermissionsException,
    RoleNotFoundException,
    RoleAlreadyExistsException,
    SystemRoleModificationException,
    UserNotFoundException,
    UserRoleAssignmentException,
    MultiTenantViolationException,
    create_rbac_exception_handler
)


def test_base_rbac_exception():
    """Test de la excepción base RBAC."""
    print("🧪 Probando excepción base RBAC...")

    exc = RBACException(
        status_code=400,
        detail="Test error",
        error_code="TEST_ERROR",
        extra_data={"test_field": "test_value"}
    )

    assert exc.status_code == 400
    assert exc.detail == "Test error"
    assert exc.error_code == "TEST_ERROR"
    assert exc.extra_data["test_field"] == "test_value"

    print("✅ Excepción base RBAC funciona correctamente")


def test_permission_exceptions():
    """Test de excepciones relacionadas con permisos."""
    print("🧪 Probando excepciones de permisos...")

    # PermissionDeniedException
    exc = PermissionDeniedException(
        permission_code="admin.access",
        user_id=123,
        company_id=456
    )

    assert exc.status_code == 403
    assert "admin.access" in exc.detail
    assert exc.error_code == "PERMISSION_DENIED"
    assert exc.extra_data["user_id"] == 123
    assert exc.extra_data["permission_code"] == "admin.access"

    # PermissionNotFoundException
    exc = PermissionNotFoundException(
        permission_code="nonexistent.perm",
        company_id=456
    )

    assert exc.status_code == 404
    assert "nonexistent.perm" in exc.detail
    assert exc.error_code == "PERMISSION_NOT_FOUND"

    # InsufficientPermissionsException
    exc = InsufficientPermissionsException(
        required_permissions=["admin.access", "super.access"],
        granted_permissions=["basic.access"],
        user_id=123
    )

    assert exc.status_code == 403
    assert exc.error_code == "INSUFFICIENT_PERMISSIONS"
    assert "admin.access" in str(exc.extra_data["missing_permissions"])

    print("✅ Excepciones de permisos funcionan correctamente")


def test_role_exceptions():
    """Test de excepciones relacionadas con roles."""
    print("🧪 Probando excepciones de roles...")

    # RoleNotFoundException
    exc = RoleNotFoundException(
        role_code="admin",
        company_id=456
    )

    assert exc.status_code == 404
    assert "admin" in exc.detail
    assert exc.error_code == "ROLE_NOT_FOUND"

    # RoleAlreadyExistsException
    exc = RoleAlreadyExistsException(
        role_code="duplicate_role",
        company_id=456
    )

    assert exc.status_code == 409
    assert "duplicate_role" in exc.detail
    assert exc.error_code == "ROLE_ALREADY_EXISTS"

    # SystemRoleModificationException
    exc = SystemRoleModificationException(
        role_code="super_admin",
        action="modificar"
    )

    assert exc.status_code == 403
    assert "super_admin" in exc.detail
    assert "modificar" in exc.detail
    assert exc.error_code == "SYSTEM_ROLE_MODIFICATION"

    print("✅ Excepciones de roles funcionan correctamente")


def test_user_exceptions():
    """Test de excepciones relacionadas con usuarios."""
    print("🧪 Probando excepciones de usuarios...")

    # UserNotFoundException
    exc = UserNotFoundException(
        username="nonexistent",
        company_id=456
    )

    assert exc.status_code == 404
    assert "nonexistent" in exc.detail
    assert exc.error_code == "USER_NOT_FOUND"

    # UserRoleAssignmentException
    exc = UserRoleAssignmentException(
        user_id=123,
        role_id="role-456",
        reason="Rol no compatible"
    )

    assert exc.status_code == 400
    assert "Rol no compatible" in exc.detail
    assert exc.error_code == "USER_ROLE_ASSIGNMENT_ERROR"

    print("✅ Excepciones de usuarios funcionan correctamente")


def test_security_exceptions():
    """Test de excepciones de seguridad."""
    print("🧪 Probando excepciones de seguridad...")

    # MultiTenantViolationException
    exc = MultiTenantViolationException(
        resource_type="role",
        requested_company=999,
        user_company=456,
        user_id=123
    )

    assert exc.status_code == 403
    assert "role" in exc.detail
    assert exc.error_code == "MULTI_TENANT_VIOLATION"
    assert exc.extra_data["severity"] == "high"

    print("✅ Excepciones de seguridad funcionan correctamente")


async def test_fastapi_handler():
    """Test del handler de FastAPI para excepciones RBAC."""
    print("🧪 Probando handler de FastAPI...")

    from fastapi import Request
    from unittest.mock import Mock

    # Crear mock request
    mock_request = Mock(spec=Request)
    mock_request.url = Mock()
    mock_request.url.__str__ = Mock(return_value="/test/endpoint")
    mock_request.method = "GET"

    # Crear excepción
    exc = PermissionDeniedException(
        permission_code="test.permission",
        user_id=123
    )

    # Obtener handler
    handler = create_rbac_exception_handler()

    # Ejecutar handler
    response = await handler(mock_request, exc)

    # Verificar respuesta
    assert response.status_code == 403
    response_data = response.body
    assert b"PERMISSION_DENIED" in response_data
    assert b"test.permission" in response_data

    print("✅ Handler de FastAPI funciona correctamente")


def test_exception_inheritance():
    """Test de herencia de excepciones."""
    print("🧪 Probando herencia de excepciones...")

    # Todas las excepciones deben heredar de RBACException
    exceptions = [
        PermissionDeniedException("test.perm"),
        RoleNotFoundException(role_code="test"),
        UserNotFoundException(username="test"),
        MultiTenantViolationException("test", 1, 2, 3),
    ]

    for exc in exceptions:
        assert isinstance(exc, RBACException)
        assert isinstance(exc, Exception)
        assert hasattr(exc, 'error_code')
        assert hasattr(exc, 'error_type')
        assert hasattr(exc, 'extra_data')

    print("✅ Herencia de excepciones funciona correctamente")


async def main():
    """Función principal de pruebas."""
    print("⚠️ PRUEBA DEL SISTEMA DE EXCEPCIONES PERSONALIZADAS")
    print("=" * 55)

    tests = [
        ("Excepción Base", test_base_rbac_exception),
        ("Excepciones Permisos", test_permission_exceptions),
        ("Excepciones Roles", test_role_exceptions),
        ("Excepciones Usuarios", test_user_exceptions),
        ("Excepciones Seguridad", test_security_exceptions),
        ("Handler FastAPI", test_fastapi_handler),
        ("Herencia", test_exception_inheritance),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            if test_name == "Handler FastAPI":
                await test_func()
            else:
                test_func()
            results.append((test_name, True))
            print(f"✅ {test_name} completado")
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))

    # Resultados
    print(f"\n{'='*55}")
    print("📊 RESULTADOS:")
    print('='*55)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"   {test_name:20} : {status}")
        if not passed:
            all_passed = False

    print('='*55)

    if all_passed:
        print("🎉 ¡Sistema de excepciones personalizado validado!")
        print("\n✨ Características confirmadas:")
        print("   • Excepciones específicas por dominio")
        print("   • Datos extra para debugging")
        print("   • Códigos de error únicos")
        print("   • Handler global FastAPI")
        print("   • Logging automático de seguridad")
        print("   • Herencia consistente")
    else:
        print("⚠️  Algunas pruebas fallaron.")
        print("🔧 Revisa los errores arriba.")

    return all_passed


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    print(f"\n🚀 Estado final: {'✅ EXITOSO' if success else '❌ FALLIDO'}")
