#permite ver als bariavles de entorno automaticamente
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Clase que contiene la configuracion de la aplicacion"""
    
    model_config =SettingsConfigDict(
        env_file = ".env",
        extra = "ignore",
        env_file_encoding = 'utf-8'
    )


    # Database
    DATABASE_URL: str  # URL de la base de datos
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"  # URL de Redis (default para desarrollo local)
    
    # Security
    SECRET_KEY: str  # Clave para la encriptacion
    ALGORITHM: str = "HS256"  # Algoritmo de encriptacion
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Tiempo de expiracion del token en minutos

    # Celery settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    
#instancia global de la configuracion
settings = Settings()