"""
Add partial unique index for products (active only)

Allows creating products with the same name if previous one is inactive.
This enables better product lifecycle management without name conflicts.

Revision ID: b001_partial_unique_products
Revises: a002_add_recipe_fields
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b001_partial_unique_products'
down_revision = 'a002_add_recipe_fields'
branch_labels = None
depends_on = None


def upgrade():
    """
    Replace absolute unique constraint with partial unique index.
    
    NEW BEHAVIOR:
    - Only ACTIVE products must have unique names per company
    - Inactive products can share names with active ones
    - Allows re-creating products with previously used names
    """
    
    # Step 1: Drop the existing absolute unique constraint
    # Constraint name: uq_products_company_name
    op.drop_constraint('uq_products_company_name', 'products', type_='unique')
    
    # Step 2: Create partial unique index (only for active products)
    # This uses PostgreSQL's WHERE clause in index definition
    op.execute("""
        CREATE UNIQUE INDEX uq_products_company_name_active 
        ON products(company_id, name) 
        WHERE is_active = true
    """)
    
    # Add comment explaining the change
    op.execute("""
        COMMENT ON INDEX uq_products_company_name_active IS 
        'Partial unique index: only active products must have unique names per company. 
         Inactive products can share names, allowing name reuse after deactivation.'
    """)


def downgrade():
    """
    Revert to absolute unique constraint.
    
    WARNING: This will fail if there are duplicate names 
    (one active, one inactive) in the same company.
    """
    
    # Step 1: Drop the partial unique index
    op.execute("DROP INDEX IF EXISTS uq_products_company_name_active")
    
    # Step 2: Recreate the absolute unique constraint
    # This may fail if duplicate names exist
    op.create_unique_constraint(
        'uq_products_company_name', 
        'products', 
        ['company_id', 'name']
    )
