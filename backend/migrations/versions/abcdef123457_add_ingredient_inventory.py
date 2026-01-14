"""add_ingredient_inventory

Revision ID: abcdef123457
Revises: abcdef123456
Create Date: 2026-02-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abcdef123457'
down_revision: Union[str, Sequence[str], None] = 'abcdef123456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create IngredientInventory
    op.create_table('ingredient_inventory',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('stock', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('min_stock', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('max_stock', sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('branch_id', 'ingredient_id', name='uq_ingredient_inventory_branch')
    )
    op.create_index('idx_ingredient_inventory_branch', 'ingredient_inventory', ['branch_id'], unique=False)

    # 2. Create IngredientTransaction
    op.create_table('ingredient_transactions',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('inventory_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('transaction_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('balance_after', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('reference_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['ingredient_inventory.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('ingredient_transactions')
    op.drop_index('idx_ingredient_inventory_branch', table_name='ingredient_inventory')
    op.drop_table('ingredient_inventory')
