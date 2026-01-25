from sqlmodel import SQLModel, Field
import uuid

class UnitConversion(SQLModel, table=True):
    __tablename__ = "unit_conversions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    from_unit: str = Field(index=True)
    to_unit: str = Field(index=True)
    factor: float = Field(description="Factor multiplicador: from * factor = to. Ej: from 'kg' to 'g', factor = 1000")
