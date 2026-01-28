"""merge_heads

Revision ID: 68ac4f51243a
Revises: 05caac46fd74
Create Date: 2026-01-27 01:58:29.570767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68ac4f51243a'
down_revision: Union[str, Sequence[str], None] = '05caac46fd74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
