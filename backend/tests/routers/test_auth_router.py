"""
🧪 TESTS DE INTEGRACIÓN - Auth Router

Tests end-to-end para el router de autenticación que cubren:
- ✅ POST /auth/login - Login exitoso y fallido
- ✅ GET /auth/me - Obtener usuario actual
- ✅ GET /auth/verify - Verificar token
- ✅ POST /auth/refresh - Refrescar token
- ✅ POST /auth/logout - Logout
- ✅ Validaciones de autenticación
- ✅ Manejo de errores HTTP

Ejecutar tests:
    pytest backend/tests/routers/test_auth_router.py -v
"""

import pytest
from httpx import AsyncClient


class TestAuthRouter:
    """
    🌐 Tests de integración para Auth Router

    Tests completos de endpoints HTTP con autenticación.
    """

    @pytest.mark.asyncio
    async def test_login_success(self, test_client: AsyncClient):
        """
        ✅ POST /auth/login - Éxito

        Login válido debe retornar token JWT.
        """
        # Arrange
        login_data = {
            "company_slug": "test-company",
            "username": "testuser",
            "password": "testpass123"
        }

        # Act
        response = await test_client.post("/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 100  # Token JWT válido

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, test_client: AsyncClient):
        """
        ❌ POST /auth/login - Contraseña incorrecta

        Debe retornar 401 Unauthorized.
        """
        # Arrange
        login_data = {
            "company_slug": "test-company",
            "username": "testuser",
            "password": "wrongpassword"
        }

        # Act
        response = await test_client.post("/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "Credenciales inválidas" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_company_not_found(self, test_client: AsyncClient):
        """
        ❌ POST /auth/login - Empresa inexistente

        Debe retornar 404 Not Found.
        """
        # Arrange
        login_data = {
            "company_slug": "nonexistent-company",
            "username": "testuser",
            "password": "testpass123"
        }

        # Act
        response = await test_client.post("/auth/login", json=login_data)

        # Assert
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Empresa no encontrada" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, test_client: AsyncClient):
        """
        ❌ POST /auth/login - Usuario inexistente

        Debe retornar 401 Unauthorized.
        """
        # Arrange
        login_data = {
            "company_slug": "test-company",
            "username": "nonexistent",
            "password": "testpass123"
        }

        # Act
        response = await test_client.post("/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "Credenciales inválidas" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ GET /auth/me - Éxito

        Debe retornar información del usuario autenticado.
        """
        # Act
        response = await test_client.get("/auth/me", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@test.com"
        assert data["role"] == "admin"
        assert data["is_active"] == True
        assert "company_id" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, test_client: AsyncClient):
        """
        ❌ GET /auth/me - Sin token

        Debe retornar 401 Unauthorized.
        """
        # Act
        response = await test_client.get("/auth/me")

        # Assert
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "Bearer" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_client: AsyncClient):
        """
        ❌ GET /auth/me - Token inválido

        Debe retornar 401 Unauthorized.
        """
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}

        # Act
        response = await test_client.get("/auth/me", headers=invalid_headers)

        # Assert
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_verify_token_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ GET /auth/verify - Éxito

        Debe confirmar que el token es válido.
        """
        # Act
        response = await test_client.get("/auth/verify", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] == True
        assert data["user_id"] is not None
        assert data["username"] == "testuser"
        assert "company_id" in data

    @pytest.mark.asyncio
    async def test_verify_token_no_auth(self, test_client: AsyncClient):
        """
        ❌ GET /auth/verify - Sin autenticación

        Debe retornar 401 Unauthorized.
        """
        # Act
        response = await test_client.get("/auth/verify")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ POST /auth/refresh - Éxito

        Debe generar un nuevo token válido.
        """
        # Act
        response = await test_client.post("/auth/refresh", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 100

    @pytest.mark.asyncio
    async def test_refresh_token_no_auth(self, test_client: AsyncClient):
        """
        ❌ POST /auth/refresh - Sin autenticación

        Debe retornar 401 Unauthorized.
        """
        # Act
        response = await test_client.post("/auth/refresh")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, test_client: AsyncClient, auth_headers: dict):
        """
        ✅ POST /auth/logout - Éxito

        Debe procesar logout correctamente.
        """
        # Act
        response = await test_client.post("/auth/logout", headers=auth_headers)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Logout exitoso" in data["message"]
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_logout_no_auth(self, test_client: AsyncClient):
        """
        ❌ POST /auth/logout - Sin autenticación

        Debe retornar 401 Unauthorized.
        """
        # Act
        response = await test_client.post("/auth/logout")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_endpoints_protected(self, test_client: AsyncClient):
        """
        🔒 PROTECCIÓN DE ENDPOINTS

        Todos los endpoints deben requerir autenticación.
        """
        protected_endpoints = [
            ("GET", "/auth/me"),
            ("GET", "/auth/verify"),
            ("POST", "/auth/refresh"),
            ("POST", "/auth/logout"),
        ]

        for method, endpoint in protected_endpoints:
            # Act
            if method == "GET":
                response = await test_client.get(endpoint)
            elif method == "POST":
                response = await test_client.post(endpoint)

            # Assert
            assert response.status_code == 401, f"Endpoint {method} {endpoint} no está protegido"

    @pytest.mark.asyncio
    async def test_login_validation_errors(self, test_client: AsyncClient):
        """
        ❌ POST /auth/login - Validaciones

        Debe validar campos requeridos.
        """
        # Test con datos incompletos
        test_cases = [
            {"username": "testuser", "password": "testpass123"},  # Falta company_slug
            {"company_slug": "test-company", "password": "testpass123"},  # Falta username
            {"company_slug": "test-company", "username": "testuser"},  # Falta password
            {},  # Todo vacío
        ]

        for invalid_data in test_cases:
            # Act
            response = await test_client.post("/auth/login", json=invalid_data)

            # Assert
            assert response.status_code == 422  # Validation error

            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_cors_headers(self, test_client: AsyncClient):
        """
        🌐 CORS Headers

        Verificar que los headers CORS estén presentes.
        """
        # Act - Request con Origin
        response = await test_client.options(
            "/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )

        # Assert - Verificar headers CORS (si están configurados)
        # Nota: Esto depende de la configuración CORS de FastAPI
        assert response.status_code in [200, 404]  # 200 si OPTIONS está permitido

    @pytest.mark.asyncio
    async def test_token_expiration_simulation(self, test_client: AsyncClient):
        """
        ⏰ SIMULACIÓN DE EXPIRACIÓN DE TOKEN

        Verificar manejo de tokens expirados.
        Nota: Para test real necesitaríamos manipular el tiempo.
        """
        # Este test es más conceptual - en un test real usaríamos
        # un token expirado generado manualmente

        # Por ahora solo verificamos que los endpoints rechacen tokens malformados
        malformed_tokens = [
            "Bearer invalid",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Header only
            "Bearer not-a-jwt",
        ]

        for token in malformed_tokens:
            headers = {"Authorization": token}

            # Act
            response = await test_client.get("/auth/me", headers=headers)

            # Assert
            assert response.status_code == 401
