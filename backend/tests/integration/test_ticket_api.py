"""
Integration Tests for Ticket/Comanda PDF Generation
====================================================
Tests para la generación de tickets de caja y cocina.
"""

import pytest
from httpx import AsyncClient


class TestTicketAPI:
    """Tests para endpoints de tickets PDF."""
    
    @pytest.mark.anyio
    async def test_download_receipt_requires_auth(self, client: AsyncClient):
        """Sin autenticación debe retornar 401."""
        response = await client.get("/tickets/order/1/receipt.pdf")
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_download_kitchen_requires_auth(self, client: AsyncClient):
        """Sin autenticación debe retornar 401."""
        response = await client.get("/tickets/order/1/kitchen.pdf")
        assert response.status_code == 401
    
    @pytest.mark.anyio
    async def test_download_receipt_not_found(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Pedido inexistente debe retornar 404."""
        response = await client.get(
            "/tickets/order/99999/receipt.pdf", 
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.anyio
    async def test_download_kitchen_not_found(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Pedido inexistente debe retornar 404."""
        response = await client.get(
            "/tickets/order/99999/kitchen.pdf", 
            headers=auth_headers
        )
        assert response.status_code == 404
