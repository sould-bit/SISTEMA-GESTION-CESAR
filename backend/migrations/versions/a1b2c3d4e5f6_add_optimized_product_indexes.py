"""Add optimized product indexes for hybrid architecture

Revision ID: a1b2c3d4e5f6
Revises: 94884e4c980c
Create Date: 2025-12-27 14:00:00.000000

This migration adds/updates indexes for:
- idx_products_company_active: compound index (company_id, is_active)
- idx_products_category: compound index (company_id, category_id)

These optimize the hybrid schema queries in ProductRepository.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '94884e4c980c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Add optimized compound indexes for hybrid architecture queries.
    
    1. Drop old single-column index
    2. Create new compound index (company_id, is_active)
    3. Create new compound index (company_id, category_id)
    """
    # Drop old single-column index (if exists)
    op.execute("DROP INDEX IF EXISTS idx_products_company_active")
    
    # Create compound index for filtering by company + active status
    # Used by: get_products_basic(), get_products_with_category_name()
    op.create_index(
        'idx_products_company_active_v2',
        'products',
        ['company_id', 'is_active'],
        unique=False
    )
    
    # Create compound index for filtering by company + category
    # Used by: get_active_by_category(), filtering in listings
    op.create_index(
        'idx_products_company_category',
        'products',
        ['company_id', 'category_id'],
        unique=False
    )
    
    print("✅ Created optimized indexes for hybrid product architecture")


def downgrade() -> None:
    """Downgrade: Remove new indexes, restore original."""
    # Drop new indexes
    op.drop_index('idx_products_company_category', table_name='products')
    op.drop_index('idx_products_company_active_v2', table_name='products')
    
    # Restore original single-column index
    op.create_index(
        'idx_products_company_active',
        'products',
        ['company_id'],
        unique=False
    )
    
    print("⏪ Reverted to original indexes")
