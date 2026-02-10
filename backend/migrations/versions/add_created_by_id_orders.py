"""add created_by_id to orders

Revision ID: add_created_by_id_orders
Revises: 3505193c6e28, 05caac46fd74
Create Date: 2026-02-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_created_by_id_orders'
down_revision: Union[str, Sequence[str], None] = ('3505193c6e28', '05caac46fd74')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_by_id column to orders table."""
    op.add_column('orders', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_orders_created_by_id',
        'orders',
        'users',
        ['created_by_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Remove created_by_id column from orders table."""
    op.drop_constraint('fk_orders_created_by_id', 'orders', type_='foreignkey')
    op.drop_column('orders', 'created_by_id')
