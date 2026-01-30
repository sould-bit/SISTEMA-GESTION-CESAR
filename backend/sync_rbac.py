#!/usr/bin/env python3
"""
Script para sincronizar datos globales de RBAC.
Ejecutar con: python sync_rbac.py
"""
import asyncio
import sys
import os

# Añadir el directorio actual (backend) al path para importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session
from app.services.rbac_sync_service import RBACSyncService
from app.core.logging_config import get_rbac_logger

logger = get_rbac_logger("rbac_sync")

async def run_sync():
    """
    Ejecuta la sincronización global de RBAC.
    """
    print("🔄 Iniciando Sincronización Global de RBAC...")
    
    async with async_session() as session:
        service = RBACSyncService(session)
        try:
            stats = await service.sync_global_metadata()
            print(f"✅ Sincronización Completada Exitosamente:")
            print(f"   - Categorías creadas: {stats['categories_created']}")
            print(f"   - Permisos creados: {stats['permissions_created']}")
            print(f"   - Permisos actualizados: {stats['permissions_updated']}")
        except Exception as e:
            print(f"❌ Error durante la sincronización: {e}")
            logger.error(f"RBAC Sync Error: {e}")
            raise

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(run_sync())
