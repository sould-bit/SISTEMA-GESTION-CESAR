import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models import UnitConversion

UNIT_CONVERSIONS = [
    # Masa
    {"from_unit": "kg", "to_unit": "g", "factor": 1000.0},
    {"from_unit": "g", "to_unit": "kg", "factor": 0.001},
    {"from_unit": "lb", "to_unit": "g", "factor": 453.592},
    {"from_unit": "g", "to_unit": "lb", "factor": 0.00220462},
    {"from_unit": "lb", "to_unit": "kg", "factor": 0.453592},
    {"from_unit": "kg", "to_unit": "lb", "factor": 2.20462},
    {"from_unit": "oz", "to_unit": "g", "factor": 28.3495},
    {"from_unit": "g", "to_unit": "oz", "factor": 0.035274},

    # Volumen
    {"from_unit": "lt", "to_unit": "ml", "factor": 1000.0},
    {"from_unit": "ml", "to_unit": "lt", "factor": 0.001},
    {"from_unit": "gal", "to_unit": "lt", "factor": 3.78541},
    {"from_unit": "lt", "to_unit": "gal", "factor": 0.264172},

    # Unidades
    {"from_unit": "und", "to_unit": "und", "factor": 1.0},
]

async def seed_units():
    async with async_session() as session:
        print("Seeding unit conversions...")
        for conv in UNIT_CONVERSIONS:
            # Check if exists
            stmt = select(UnitConversion).where(
                UnitConversion.from_unit == conv["from_unit"],
                UnitConversion.to_unit == conv["to_unit"]
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                new_conv = UnitConversion(
                    id=uuid.uuid4(),
                    from_unit=conv["from_unit"],
                    to_unit=conv["to_unit"],
                    factor=conv["factor"]
                )
                session.add(new_conv)
                print(f"Added: {conv['from_unit']} -> {conv['to_unit']}")
            else:
                print(f"Skipped (exists): {conv['from_unit']} -> {conv['to_unit']}")

        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(seed_units())
