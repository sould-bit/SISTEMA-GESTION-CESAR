"""Add production_event_input_batches table

Revision ID: 5f655380bf68
Revises: 675cac6241d8
Create Date: 2026-01-17 19:56:50.895012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5f655380bf68'
down_revision: Union[str, Sequence[str], None] = '675cac6241d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create production_event_input_batches table for precise undo tracking."""
    op.create_table(
        'production_event_input_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('production_event_input_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('production_event_inputs.id', ondelete='CASCADE'), 
                  nullable=False, index=True),
        sa.Column('source_batch_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('ingredient_batches.id'), 
                  nullable=False, index=True),
        sa.Column('quantity_consumed', sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column('cost_attributed', sa.Numeric(18, 4), nullable=False, default=0),
    )


def downgrade() -> None:
    """Drop production_event_input_batches table."""
    op.drop_table('production_event_input_batches')
