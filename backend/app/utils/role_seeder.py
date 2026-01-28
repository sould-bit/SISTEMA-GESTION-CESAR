from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.role import Role
from app.models.company import Company
import logging

logger = logging.getLogger(__name__)

async def seed_default_roles(db: AsyncSession, company_id: int):
    """Seed default roles for a specific company."""
    
    default_roles = [
        {
            "name": "Gerente",
            "code": "manager",
            "description": "Gestión operativa del negocio",
            "hierarchy": 90
        },
        {
            "name": "Cajero",
            "code": "cashier",
            "description": "Manejo de caja y cobros",
            "hierarchy": 50
        },
        {
            "name": "Cocinero",
            "code": "cook",
            "description": "Pantalla de cocina e inventario",
            "hierarchy": 40
        },
        {
            "name": "Mesero",
            "code": "server",
            "description": "Toma de pedidos y atención",
            "hierarchy": 30
        },
        {
            "name": "Repartidor",
            "code": "delivery",
            "description": "Entrega de pedidos",
            "hierarchy": 20
        }
    ]

    for role_data in default_roles:
        # Check if exists
        result = await db.execute(
            select(Role).where(
                Role.company_id == company_id,
                Role.code == role_data["code"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            role = Role(
                company_id=company_id,
                name=role_data["name"],
                code=role_data["code"],
                description=role_data["description"],
                hierarchy_level=role_data["hierarchy"],
                is_system=True,
                is_active=True
            )
            db.add(role)
            logger.info(f"Creating role {role_data['name']} for company {company_id}")
    
    await db.commit()
