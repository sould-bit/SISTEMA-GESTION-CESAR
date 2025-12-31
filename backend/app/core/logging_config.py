"""
Sistema de Logging Avanzado para el Sistema RBAC

Este módulo proporciona:
- Logging estructurado con JSON formatter
- Separación de logs por componente (RBAC, permisos, API)
- Rotación automática de archivos
- Configuración para desarrollo y producción
"""

import logging
import logging.config
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import sys
from pythonjsonlogger import jsonlogger


class RBACJsonFormatter(jsonlogger.JsonFormatter):
    """Formateador JSON personalizado para logs RBAC."""

    def add_fields(self, log_record: logging.LogRecord, record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Agregar campos personalizados al log."""
        super().add_fields(log_record, record, message_dict)

        # Agregar timestamp en formato ISO
        log_record.timestamp = datetime.now(timezone.utc).isoformat()

        # Agregar nivel de log como string
        log_record.level = record.levelname

        # Agregar nombre del módulo
        log_record.module = record.name

        # Agregar información contextual si está disponible
        if hasattr(record, 'user_id'):
            log_record.user_id = record.user_id
        if hasattr(record, 'company_id'):
            log_record.company_id = record.company_id
        if hasattr(record, 'permission_code'):
            log_record.permission_code = record.permission_code
        if hasattr(record, 'role_id'):
            log_record.role_id = record.role_id
        if hasattr(record, 'action'):
            log_record.action = record.action


class RBACLogger:
    """Sistema de logging centralizado para RBAC."""

    def __init__(self, log_level: str = "INFO", enable_json: bool = True):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_json = enable_json
        self._setup_logging()

    def _setup_logging(self):
        """Configurar el sistema de logging completo."""

        # Crear directorio de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configuración base
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {},
            "handlers": {},
            "loggers": {}
        }

        # Formateadores
        if self.enable_json:
            config["formatters"]["json"] = {
                "class": "app.core.logging_config.RBACJsonFormatter",
                "format": "%(timestamp)s %(level)s %(module)s %(message)s"
            }
        else:
            config["formatters"]["detailed"] = {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }

        # Handlers
        formatter_name = "json" if self.enable_json else "detailed"

        # Handler para consola
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": self.log_level,
            "formatter": formatter_name,
            "stream": "ext://sys.stdout"
        }

        # Handler para archivo general
        config["handlers"]["file_general"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": self.log_level,
            "formatter": formatter_name,
            "filename": log_dir / "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }

        # Handler específico para RBAC
        config["handlers"]["file_rbac"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": logging.INFO,
            "formatter": formatter_name,
            "filename": log_dir / "rbac.log",
            "maxBytes": 10485760,
            "backupCount": 10
        }

        # Handler para seguridad (warnings y errores)
        config["handlers"]["file_security"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": logging.WARNING,
            "formatter": formatter_name,
            "filename": log_dir / "security.log",
            "maxBytes": 10485760,
            "backupCount": 10
        }

        # Loggers específicos
        config["loggers"] = {
            # Logger principal de la app
            "app": {
                "level": self.log_level,
                "handlers": ["console", "file_general"],
                "propagate": False
            },
            # Logger específico para RBAC
            "app.rbac": {
                "level": logging.INFO,
                "handlers": ["console", "file_rbac", "file_security"],
                "propagate": False
            },
            # Logger para permisos
            "app.permissions": {
                "level": logging.INFO,
                "handlers": ["console", "file_rbac", "file_security"],
                "propagate": False
            },
            # Logger para API
            "app.api": {
                "level": logging.INFO,
                "handlers": ["console", "file_general"],
                "propagate": False
            }
        }

        # Aplicar configuración
        logging.config.dictConfig(config)

        # Logger raíz para capturar todo lo demás
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Obtener un logger configurado."""
        return logging.getLogger(name)

    def log_rbac_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        role_id: Optional[str] = None,
        permission_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ):
        """Log específico para acciones RBAC."""
        logger = self.get_logger("app.rbac")
        log_method = getattr(logger, level.lower(), logger.info)

        message = f"RBAC Action: {action}"
        extra = {
            "action": action,
            "user_id": user_id,
            "company_id": company_id,
            "role_id": role_id,
            "permission_code": permission_code
        }

        if details:
            extra.update(details)

        log_method(message, extra=extra)

    def log_permission_check(
        self,
        user_id: int,
        permission_code: str,
        company_id: int,
        granted: bool,
        source: str = "database"
    ):
        """Log específico para verificaciones de permisos."""
        logger = self.get_logger("app.permissions")

        level = "INFO" if granted else "WARNING"
        log_method = getattr(logger, level.lower(), logger.info)

        message = f"Permission {'granted' if granted else 'denied'}: {permission_code}"
        extra = {
            "user_id": user_id,
            "permission_code": permission_code,
            "company_id": company_id,
            "granted": granted,
            "source": source
        }

        log_method(message, extra=extra)

    def log_security_event(
        self,
        event: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        level: str = "WARNING"
    ):
        """Log para eventos de seguridad."""
        logger = self.get_logger("app.rbac")
        log_method = getattr(logger, level.lower(), logger.warning)

        message = f"Security Event: {event}"
        extra = {
            "event": event,
            "user_id": user_id,
            "company_id": company_id
        }

        if details:
            extra.update(details)

        log_method(message, extra=extra)


# Instancia global del logger
_rbac_logger_instance: Optional[RBACLogger] = None


def get_rbac_logger(name: str = "app") -> logging.Logger:
    """Factory para obtener loggers RBAC."""
    global _rbac_logger_instance

    if _rbac_logger_instance is None:
        # Configurar según entorno
        import os
        log_level = os.getenv("LOG_LEVEL", "INFO")
        enable_json = os.getenv("LOG_JSON", "true").lower() == "true"

        _rbac_logger_instance = RBACLogger(log_level=log_level, enable_json=enable_json)

    return _rbac_logger_instance.get_logger(name)


def log_rbac_action(
    action: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    role_id: Optional[str] = None,
    permission_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO"
):
    """Función de conveniencia para log de acciones RBAC."""
    global _rbac_logger_instance

    if _rbac_logger_instance is None:
        get_rbac_logger()  # Inicializar si no existe

    _rbac_logger_instance.log_rbac_action(
        action=action,
        user_id=user_id,
        company_id=company_id,
        role_id=role_id,
        permission_code=permission_code,
        details=details,
        level=level
    )


def log_permission_check(
    user_id: int,
    permission_code: str,
    company_id: int,
    granted: bool,
    source: str = "database"
):
    """Función de conveniencia para log de verificaciones de permisos."""
    global _rbac_logger_instance

    if _rbac_logger_instance is None:
        get_rbac_logger()  # Inicializar si no existe

    _rbac_logger_instance.log_permission_check(
        user_id=user_id,
        permission_code=permission_code,
        company_id=company_id,
        granted=granted,
        source=source
    )


def log_security_event(
    event: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    level: str = "WARNING"
):
    """Función de conveniencia para log de eventos de seguridad."""
    global _rbac_logger_instance

    if _rbac_logger_instance is None:
        get_rbac_logger()  # Inicializar si no existe

    _rbac_logger_instance.log_security_event(
        event=event,
        user_id=user_id,
        company_id=company_id,
        details=details,
        level=level
    )
