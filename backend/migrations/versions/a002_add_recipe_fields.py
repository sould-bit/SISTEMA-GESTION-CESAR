"""Add missing recipe fields (version, batch_yield, prep_time)

Revision ID: a002_add_recipe_fields
Revises: a001_fix_recipe_uuid
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a002_add_recipe_fields'
down_revision = 'a001_fix_recipe_uuid'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add version
    op.add_column('recipes', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    # Add batch_yield
    op.add_column('recipes', sa.Column('batch_yield', sa.Float(), server_default='1.0', nullable=False))
    # Add preparation_time
    op.add_column('recipes', sa.Column('preparation_time', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    op.drop_column('recipes', 'preparation_time')
    op.drop_column('recipes', 'batch_yield')
    op.drop_column('recipes', 'version')
