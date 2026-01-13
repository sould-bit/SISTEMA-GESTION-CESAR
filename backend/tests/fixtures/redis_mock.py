
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    """
    Mock global de Redis para evitar conexiones reales durante los tests.
    Esto previene que el sistema de cache interfiera o requiera un servidor Redis.
    """
    with pytest.MonkeyPatch.context() as m:
        # Mock de la clase RBACCache
        mock_cache = MagicMock()
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        mock_cache.set_user_permissions = AsyncMock(return_value=True)
        mock_cache.invalidate_user_permissions = AsyncMock(return_value=True)
        mock_cache.invalidate_role_permissions = AsyncMock(return_value=True)
        mock_cache.invalidate_company_permissions = AsyncMock(return_value=0)

        # Mock de get_rbac_cache para devolver nuestro mock
        m.setattr("app.core.cache.get_rbac_cache", lambda: mock_cache)

        # Mock de ProductCache
        mock_prod_cache = MagicMock()
        mock_prod_cache.get_list = AsyncMock(return_value=None)
        mock_prod_cache.set_list = AsyncMock(return_value=True)
        mock_prod_cache.get_detail = AsyncMock(return_value=None)
        mock_prod_cache.set_detail = AsyncMock(return_value=True)
        mock_prod_cache.invalidate_company = AsyncMock(return_value=0)
        mock_prod_cache.invalidate_product = AsyncMock(return_value=0)

        m.setattr("app.core.cache.get_product_cache", lambda: mock_prod_cache)

        yield mock_cache
