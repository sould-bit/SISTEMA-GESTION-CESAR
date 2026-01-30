from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.unit_conversion import UnitConversion

class UnitConversionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._cache = {}

    async def get_conversion_factor(self, from_unit: str, to_unit: str) -> Optional[float]:
        """
        Obtiene el factor de conversión entre dos unidades.
        Intenta busqueda directa.
        """
        key = f"{from_unit}-{to_unit}"
        if key in self._cache:
            return self._cache[key]

        # 1. Busqueda Directa
        stmt = select(UnitConversion).where(
            UnitConversion.from_unit == from_unit,
            UnitConversion.to_unit == to_unit
        )
        result = await self.session.execute(stmt)
        conversion = result.scalar_one_or_none()

        if conversion:
            self._cache[key] = conversion.factor
            return conversion.factor

        # 2. Busqueda Inversa (si existe 1 -> 2, entonces 2 -> 1 es 1/factor)
        stmt_rev = select(UnitConversion).where(
            UnitConversion.from_unit == to_unit,
            UnitConversion.to_unit == from_unit
        )
        result_rev = await self.session.execute(stmt_rev)
        conversion_rev = result_rev.scalar_one_or_none()

        if conversion_rev:
             # from_unit = to_unit * factor_rev -> to_unit = from_unit / factor_rev
             factor = 1.0 / conversion_rev.factor
             self._cache[key] = factor
             return factor

        return None

    async def convert(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """
        Convierte una cantidad de una unidad a otra.
        Lanza ValueError si no hay conversión posible.
        """
        if from_unit == to_unit:
            return quantity

        # Standard Metric Conversions
        # Mass
        if from_unit == 'kg' and to_unit == 'g':
            return quantity * 1000.0
        if from_unit == 'g' and to_unit == 'kg':
            return quantity / 1000.0
        if from_unit == 'lb' and to_unit == 'g':
            return quantity * 453.592
        if from_unit == 'oz' and to_unit == 'g':
            return quantity * 28.3495
            
        # Volume
        if from_unit == 'l' and to_unit == 'ml':
            return quantity * 1000.0
        if from_unit == 'ml' and to_unit == 'l':
            return quantity / 1000.0
        if from_unit == 'lt' and to_unit == 'ml': # Handle 'lt' alias
            return quantity * 1000.0
        if from_unit == 'ml' and to_unit == 'lt':
            return quantity / 1000.0

        factor = await self.get_conversion_factor(from_unit, to_unit)

        if factor is None:
            # TODO: Intentar conversion via unidad base intermedia (ej: oz -> g -> kg)
            raise ValueError(f"No conversion defined from {from_unit} to {to_unit}")

        return quantity * factor
