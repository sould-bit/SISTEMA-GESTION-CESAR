"""
Integration Tests for Audit Module
===================================
Tests básicos para la API de auditoría.
"""

import pytest
from httpx import AsyncClient


class TestAuditAPI:
    """Tests para endpoints de auditoría."""
    
    @pytest.mark.anyio
    async def test_get_audit_logs_requires_auth(self, client: AsyncClient):
        """Sin autenticación debe retornar 401."""
        response = await client.get("/audit/logs")
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_get_audit_logs_success(self, client: AsyncClient, auth_headers: dict):
        """Con autenticación debe retornar lista de logs."""
        response = await client.get("/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.anyio
    async def test_get_audit_summary(self, client: AsyncClient, auth_headers: dict):
        """Debe retornar resumen de auditoría."""
        response = await client.get("/audit/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_logs" in data
        assert "logs_today" in data
        assert "top_actions" in data
        assert "top_users" in data
    
    @pytest.mark.anyio
    async def test_get_entity_history(self, client: AsyncClient, auth_headers: dict):
        """Debe retornar historial de una entidad (puede estar vacío)."""
        response = await client.get(
            "/audit/entity/product/1",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
