from redis.asyncio import Redis, from_url
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def get_redis_client() -> Redis:
    """
    Retorna una instancia de cliente Redis asíncrono.
    """
    try:
        # from_url maneja el pool de conexiones internamente
        return from_url(
            settings.CELERY_BROKER_URL, # Reutilizamos la URL de Redis configurada (o REDIS_URL si existiera explícita)
            encoding="utf-8", 
            decode_responses=True
        )
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        raise e
