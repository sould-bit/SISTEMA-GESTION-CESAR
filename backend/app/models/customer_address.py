from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class CustomerAddress(SQLModel, table=True):
    """
    Modelo de Dirección de Cliente.
    Lugares de entrega frecuentes del cliente.
    """
    __tablename__ = "customer_addresses"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True, nullable=False)
    
    name: str = Field(max_length=50, description="Alias (ej. Casa, Oficina)")
    address: str = Field(max_length=255, description="Dirección formateada")
    details: Optional[str] = Field(default=None, max_length=100, description="Apto, Bloque, Torre")
    
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    
    is_default: bool = Field(default=False)

    # Relaciones
    customer: "Customer" = Relationship(back_populates="addresses")
