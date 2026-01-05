from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime

class PrintJobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PrintJob(SQLModel, table=True):
    """
    Modelo para la cola de impresión.
    Registra los trabajos de impresión enviados a Celery.
    """
    __tablename__ = "print_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    
    order_id: int = Field(index=True, nullable=False)
    
    status: PrintJobStatus = Field(default=PrintJobStatus.PENDING, index=True)
    attempts: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Relaciones (opcionales, para evitar ciclos complejos por ahora)
    # order: Optional["Order"] = Relationship(...) 
