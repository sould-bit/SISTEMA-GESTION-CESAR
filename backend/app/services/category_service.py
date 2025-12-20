"""
🗂️ CATEGORY SERVICE - Lógica de Gestión de Categorías

Este servicio maneja toda la lógica de negocio relacionada con categorías:
- CRUD completo de categorías
- Validaciones multi-tenant
- Control de unicidad por empresa
- Soft delete para integridad referencial

Características:
- ✅ Multi-tenant: Todas las operaciones filtradas por company_id
- ✅ Validación: Unicidad de nombres por empresa
- ✅ Seguridad: Solo usuarios de la empresa pueden acceder
- ✅ Transaccional: Manejo seguro de BD con rollback
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead

import logging

logger = logging.getLogger(__name__)


class CategoryService:
    """
    🗂️ Servicio de Categorías

    Gestiona todas las operaciones CRUD de categorías con aislamiento multi-tenant.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializar servicio con sesión de BD

        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db

    async def get_categories(self, company_id: int, active_only: bool = True) -> List[CategoryRead]:
        """
        📋 LISTAR CATEGORÍAS DE UNA EMPRESA

        Retorna todas las categorías de la empresa especificada.

        Args:
            company_id: ID de la empresa
            active_only: Si True, solo categorías activas

        Returns:
            List[CategoryRead]: Lista de categorías
        """
        try:
            # Construir query base
            query = select(Category).where(Category.company_id == company_id)

            # Filtrar por activas si se solicita
            if active_only:
                query = query.where(Category.is_active == True)

            result = await self.db.execute(query)
            categories = result.scalars().all()

            logger.info(f"✅ Listadas {len(categories)} categorías para empresa {company_id}")
            return categories

        except Exception as e:
            logger.error(f"❌ Error listando categorías: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al listar categorías"
            )

    async def create_category(self, category_data: CategoryCreate, company_id: int) -> CategoryRead:
        """
        ➕ CREAR NUEVA CATEGORÍA

        Crea una categoría para la empresa especificada con validación de unicidad.

        Args:
            category_data: Datos de la nueva categoría
            company_id: ID de la empresa (viene del usuario autenticado)

        Returns:
            CategoryRead: Categoría creada

        Raises:
            HTTPException: Si ya existe una categoría con el mismo nombre
        """
        try:
            # 1. Verificar unicidad del nombre en la empresa
            existing_category = await self._check_category_exists(
                category_data.name,
                company_id
            )

            if existing_category:
                logger.warning(f"⚠️ Intento de crear categoría duplicada: '{category_data.name}' en empresa {company_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe una categoría con el nombre '{category_data.name}' en esta empresa"
                )

            # 2. Crear instancia del modelo
            category = Category(
                name=category_data.name,
                description=category_data.description,
                is_active=category_data.is_active,
                company_id=company_id
            )

            # 3. Guardar en BD con manejo de transacción
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)

            logger.info(f"✅ Categoría creada: '{category.name}' (ID: {category.id}) para empresa {company_id}")
            return category

        except HTTPException:
            raise
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"❌ Error de integridad creando categoría: {e}")

            # Verificar si es violación de unicidad
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe una categoría con el nombre '{category_data.name}' en esta empresa"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno del servidor al crear la categoría"
                )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error inesperado creando categoría: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado al crear la categoría: {str(e)}"
            )

    async def get_category_by_id(self, category_id: int, company_id: int) -> CategoryRead:
        """
        🔍 OBTENER CATEGORÍA POR ID

        Busca una categoría específica verificando que pertenezca a la empresa.

        Args:
            category_id: ID de la categoría
            company_id: ID de la empresa (para validación multi-tenant)

        Returns:
            CategoryRead: Datos de la categoría

        Raises:
            HTTPException: Si no se encuentra o no pertenece a la empresa
        """
        try:
            result = await self.db.execute(
                select(Category).where(
                    Category.id == category_id,
                    Category.company_id == company_id
                )
            )
            category = result.scalar_one_or_none()

            if not category:
                logger.warning(f"⚠️ Categoría no encontrada: ID {category_id} en empresa {company_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada"
                )

            return category

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error obteniendo categoría {category_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al obtener la categoría"
            )

    async def update_category(
        self,
        category_id: int,
        category_data: CategoryUpdate,
        company_id: int
    ) -> CategoryRead:
        """
        ✏️ ACTUALIZAR CATEGORÍA

        Actualiza una categoría existente con validaciones.

        Args:
            category_id: ID de la categoría
            category_data: Datos a actualizar
            company_id: ID de la empresa

        Returns:
            CategoryRead: Categoría actualizada

        Raises:
            HTTPException: Si no se encuentra o hay conflictos
        """
        try:
            # 1. Obtener categoría existente
            category = await self.get_category_by_id(category_id, company_id)

            # 2. Si se está cambiando el nombre, verificar unicidad
            if category_data.name is not None and category_data.name != category.name:
                existing_category = await self._check_category_exists(
                    category_data.name,
                    company_id
                )

                if existing_category and existing_category.id != category_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe una categoría con el nombre '{category_data.name}' en esta empresa"
                    )

            # 3. Actualizar solo campos proporcionados
            update_data = category_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(category, field, value)

            # 4. Guardar cambios
            await self.db.commit()
            await self.db.refresh(category)

            logger.info(f"✅ Categoría actualizada: '{category.name}' (ID: {category.id})")
            return category

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error actualizando categoría {category_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al actualizar la categoría"
            )

    async def delete_category(self, category_id: int, company_id: int) -> dict:
        """
        🗑️ ELIMINAR CATEGORÍA (SOFT DELETE)

        Marca la categoría como inactiva en lugar de eliminarla físicamente.

        Args:
            category_id: ID de la categoría
            company_id: ID de la empresa

        Returns:
            dict: Confirmación de eliminación

        Raises:
            HTTPException: Si no se encuentra la categoría
        """
        try:
            # 1. Obtener categoría
            category = await self.get_category_by_id(category_id, company_id)

            # 2. Soft delete
            category.is_active = False

            # 3. Guardar cambios
            await self.db.commit()

            logger.info(f"✅ Categoría eliminada (soft): '{category.name}' (ID: {category.id})")
            return {
                "message": f"Categoría '{category.name}' eliminada correctamente"
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error eliminando categoría {category_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al eliminar la categoría"
            )

    # ==================== MÉTODOS PRIVADOS ====================

    async def _check_category_exists(self, name: str, company_id: int) -> Optional[Category]:
        """
        🔍 VERIFICAR SI EXISTE UNA CATEGORÍA CON EL MISMO NOMBRE

        Args:
            name: Nombre de la categoría
            company_id: ID de la empresa

        Returns:
            Category or None: Categoría existente si la hay
        """
        result = await self.db.execute(
            select(Category).where(
                Category.name == name,
                Category.company_id == company_id
            )
        )
        return result.scalar_one_or_none()
