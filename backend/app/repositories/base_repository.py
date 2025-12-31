"""
🏗️ BASE REPOSITORY - Repositorio Base Multi-Tenant

Esta clase base proporciona operaciones CRUD comunes con filtros automáticos
de multi-tenant para garantizar el aislamiento de datos entre empresas.

✅ get_by_id(id, company_id) - Con filtro multi-tenant
✅ get_by_id_or_404(id, company_id) - Con manejo de errores
✅ list(company_id, skip, limit) - Listado paginado
✅ create(data) - Crear nuevo producto
✅ update(id, company_id, data) - Actualizar existente
✅ delete(id, company_id, soft_delete=True) - Soft delete
✅ exists(id, company_id) - Verificar existencia
✅ count(company_id) - Contar registros

Características:
- ✅ Filtros multi-tenant automáticos
- ✅ Operaciones CRUD genéricas
- ✅ Manejo seguro de transacciones
- ✅ Logging integrado
"""

from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, SQLModel
from fastapi import HTTPException, status

import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """
    🏗️ Repositorio Base Genérico

    Proporciona operaciones CRUD comunes con aislamiento multi-tenant.
    Todas las consultas se filtran automáticamente por company_id.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Inicializar repositorio con modelo y sesión de BD

        Args:
            model: Clase del modelo SQLModel
            db: Sesión asíncrona de SQLAlchemy
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: int, company_id: int) -> Optional[ModelType]:
        """
        🔍 OBTENER POR ID CON FILTRO MULTI-TENANT

        Busca un registro por ID asegurándose de que pertenezca a la empresa.

        Args:
            id: ID del registro
            company_id: ID de la empresa para filtrado multi-tenant

        Returns:
            ModelType or None: Registro encontrado o None
        """
        try:
            result = await self.db.execute(
                select(self.model).where(
                    self.model.id == id,
                    self.model.company_id == company_id
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"❌ Error obteniendo {self.model.__name__} por ID {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno obteniendo {self.model.__name__.lower()}"
            )

    async def get_by_id_or_404(self, id: int, company_id: int) -> ModelType:
        """
        🔍 OBTENER POR ID O LANZAR 404

        Similar a get_by_id pero lanza HTTPException si no encuentra el registro.

        Args:
            id: ID del registro
            company_id: ID de la empresa

        Returns:
            ModelType: Registro encontrado

        Raises:
            HTTPException 404: Si no se encuentra el registro
        """
        record = await self.get_by_id(id, company_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} no encontrado"
            )
        return record

    async def list(
        self,
        company_id: int,
        branch_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        📋 LISTAR REGISTROS CON FILTROS MULTI-TENANT

        Lista registros de una empresa con paginación opcional.

        Args:
            company_id: ID de la empresa
            branch_id: ID de sucursal (opcional, si el modelo lo soporta)
            skip: Número de registros a saltar (paginación)
            limit: Máximo número de registros a retornar

        Returns:
            List[ModelType]: Lista de registros
        """
        try:
            # Query base con filtro multi-tenant
            query = select(self.model).where(self.model.company_id == company_id)

            # Filtro opcional por sucursal si el modelo lo soporta
            if branch_id and hasattr(self.model, 'branch_id'):
                query = query.where(self.model.branch_id == branch_id)

            # Paginación
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            records = result.scalars().all()

            logger.info(f"✅ Listados {len(records)} registros de {self.model.__name__} para empresa {company_id}")
            return records

        except Exception as e:
            logger.error(f"❌ Error listando {self.model.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno listando {self.model.__name__.lower()}s"
            )

    async def create(self, data: dict) -> ModelType:
        """
        ➕ CREAR NUEVO REGISTRO

        Crea un nuevo registro en la base de datos.

        Args:
            data: Diccionario con los datos del registro

        Returns:
            ModelType: Registro creado

        Raises:
            HTTPException: Si hay errores de validación o BD
        """
        try:
            # Crear instancia del modelo
            record = self.model(**data)

            # Guardar en BD
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)

            logger.info(f"✅ {self.model.__name__} creado: ID {record.id}")
            return record

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error creando {self.model.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno creando {self.model.__name__.lower()}"
            )

    async def update(self, id: int, company_id: int, update_data: dict) -> ModelType:
        """
        ✏️ ACTUALIZAR REGISTRO

        Actualiza un registro existente con validaciones multi-tenant.

        Args:
            id: ID del registro
            company_id: ID de la empresa
            update_data: Diccionario con campos a actualizar

        Returns:
            ModelType: Registro actualizado

        Raises:
            HTTPException: Si no se encuentra o hay errores
        """
        try:
            # Obtener registro existente
            record = await self.get_by_id_or_404(id, company_id)

            # Actualizar campos
            for field, value in update_data.items():
                setattr(record, field, value)

            # Guardar cambios
            await self.db.commit()
            await self.db.refresh(record)

            logger.info(f"✅ {self.model.__name__} actualizado: ID {record.id}")
            return record

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error actualizando {self.model.__name__} {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno actualizando {self.model.__name__.lower()}"
            )

    async def delete(self, id: int, company_id: int, soft_delete: bool = True) -> bool:
        """
        🗑️ ELIMINAR REGISTRO

        Elimina un registro (soft delete por defecto).

        Args:
            id: ID del registro
            company_id: ID de la empresa
            soft_delete: Si True, marca como inactivo; si False, elimina físicamente

        Returns:
            bool: True si se eliminó correctamente

        Raises:
            HTTPException: Si no se encuentra el registro
        """
        try:
            # Obtener registro
            record = await self.get_by_id_or_404(id, company_id)

            if soft_delete and hasattr(record, 'is_active'):
                # Soft delete
                record.is_active = False
                await self.db.commit()
                logger.info(f"✅ {self.model.__name__} eliminado (soft): ID {record.id}")
            else:
                # Hard delete
                await self.db.delete(record)
                await self.db.commit()
                logger.info(f"✅ {self.model.__name__} eliminado (hard): ID {record.id}")

            return True

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error eliminando {self.model.__name__} {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno eliminando {self.model.__name__.lower()}"
            )

    async def exists(self, id: int, company_id: int) -> bool:
        """
        🔍 VERIFICAR SI EXISTE UN REGISTRO

        Args:
            id: ID del registro
            company_id: ID de la empresa

        Returns:
            bool: True si existe
        """
        record = await self.get_by_id(id, company_id)
        return record is not None

    async def count(self, company_id: int, branch_id: Optional[int] = None) -> int:
        """
        🔢 CONTAR REGISTROS

        Cuenta el número de registros para una empresa.

        Args:
            company_id: ID de la empresa
            branch_id: ID de sucursal (opcional)

        Returns:
            int: Número de registros
        """
        try:
            from sqlalchemy import func

            query = select(func.count(self.model.id)).where(
                self.model.company_id == company_id
            )

            if branch_id and hasattr(self.model, 'branch_id'):
                query = query.where(self.model.branch_id == branch_id)

            result = await self.db.execute(query)
            count = result.scalar()

            return count or 0

        except Exception as e:
            logger.error(f"❌ Error contando {self.model.__name__}: {e}")
            return 0
