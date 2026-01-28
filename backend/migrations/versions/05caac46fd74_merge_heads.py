"""merge_heads

Revision ID: 05caac46fd74
Revises: 5f655380bf68, b001_partial_unique_products
Create Date: 2026-01-27 01:58:20.638460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05caac46fd74'
down_revision: Union[str, Sequence[str], None] = ('5f655380bf68', 'b001_partial_unique_products')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
