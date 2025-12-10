#permite ver als bariavles de entorno automaticamente
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Clase que contiene la configuracion de la aplicacion"""
    
    # Database
    DATABASE_URL: str  # URL de la base de datos
    
    # Security
    SECRET_KEY: str  # Clave para la encriptacion
    ALGORITHM: str = "HS256"  # Algoritmo de encriptacion
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Tiempo de expiracion del token en minutos

    class Config:
        env_file = ".env"

#instancia global de la configuracion
settings = Settings()