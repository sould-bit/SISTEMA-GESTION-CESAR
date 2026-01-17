"""Migrate recipe_items to use ingredients instead of products

Revision ID: migrate_recipe_items_to_ingredients
Revises: abcdef123457
Create Date: 2026-01-14

Changes:
- Remove ingredient_product_id (INT → products)
- Add ingredient_id (UUID → ingredients)
- Update column schema for yield/cost calculation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'migrate_recipe_items_ingredients'
down_revision = 'abcdef123457'  # After ingredient_inventory
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop existing foreign key and data (all test data)
    op.execute("DELETE FROM recipe_items")
    
    # Step 2: Drop old column and constraints
    op.drop_constraint('recipe_items_ingredient_product_id_fkey', 'recipe_items', type_='foreignkey')
    op.drop_constraint('uq_recipe_item_ingredient', 'recipe_items', type_='unique')
    op.drop_index('idx_recipe_items_recipe', table_name='recipe_items')
    op.drop_column('recipe_items', 'ingredient_product_id')
    
    # Step 3: Change id to UUID
    op.execute("ALTER TABLE recipe_items DROP CONSTRAINT recipe_items_pkey")
    op.drop_column('recipe_items', 'id')
    op.add_column('recipe_items', sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.create_primary_key('recipe_items_pkey', 'recipe_items', ['id'])
    
    # Step 4: Add new ingredient_id column (UUID)
    op.add_column('recipe_items', sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key(
        'fk_recipe_items_ingredient',
        'recipe_items', 'ingredients',
        ['ingredient_id'], ['id']
    )
    op.create_index('idx_recipe_items_ingredient', 'recipe_items', ['ingredient_id'])
    
    # Step 5: Add company_id if not exists
    op.add_column('recipe_items', sa.Column('company_id', sa.Integer(), nullable=True))
    op.execute("UPDATE recipe_items SET company_id = (SELECT company_id FROM recipes WHERE recipes.id = recipe_items.recipe_id)")
    op.alter_column('recipe_items', 'company_id', nullable=False)
    op.create_foreign_key(
        'fk_recipe_items_company',
        'recipe_items', 'companies',
        ['company_id'], ['id']
    )
    
    # Step 6: Rename/modify quantity columns for V4.1 design
    op.alter_column('recipe_items', 'quantity', new_column_name='gross_quantity', 
                    type_=sa.Numeric(10, 4), nullable=False)
    op.add_column('recipe_items', sa.Column('net_quantity', sa.Numeric(10, 4), nullable=True))
    
    # Step 7: Rename unit columns
    op.alter_column('recipe_items', 'unit', new_column_name='measure_unit',
                    type_=sa.String(50), nullable=False)
    op.alter_column('recipe_items', 'unit_cost', new_column_name='calculated_cost',
                    type_=sa.Numeric(12, 2), nullable=True)
    
    # Step 8: Recreate unique constraint
    op.create_unique_constraint(
        'uq_recipe_item_ingredient',
        'recipe_items',
        ['recipe_id', 'ingredient_id']
    )
    
    # Step 9: Recreate recipe index
    op.create_index('idx_recipe_items_recipe', 'recipe_items', ['recipe_id'])


def downgrade() -> None:
    # Revert to old schema - just drop and recreate table
    op.execute("DELETE FROM recipe_items")
    
    # Remove new columns
    op.drop_constraint('uq_recipe_item_ingredient', 'recipe_items', type_='unique')
    op.drop_constraint('fk_recipe_items_ingredient', 'recipe_items', type_='foreignkey')
    op.drop_constraint('fk_recipe_items_company', 'recipe_items', type_='foreignkey')
    op.drop_index('idx_recipe_items_ingredient', table_name='recipe_items')
    op.drop_column('recipe_items', 'ingredient_id')
    op.drop_column('recipe_items', 'company_id')
    op.drop_column('recipe_items', 'net_quantity')
    
    # Rename columns back
    op.alter_column('recipe_items', 'gross_quantity', new_column_name='quantity',
                    type_=sa.Numeric(10, 3))
    op.alter_column('recipe_items', 'measure_unit', new_column_name='unit',
                    type_=sa.String(50))
    op.alter_column('recipe_items', 'calculated_cost', new_column_name='unit_cost',
                    type_=sa.Numeric(12, 2))
    
    # Restore old id as integer
    op.execute("ALTER TABLE recipe_items DROP CONSTRAINT recipe_items_pkey")
    op.drop_column('recipe_items', 'id')
    op.add_column('recipe_items', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.create_primary_key('recipe_items_pkey', 'recipe_items', ['id'])
    
    # Restore ingredient_product_id
    op.add_column('recipe_items', sa.Column('ingredient_product_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'recipe_items_ingredient_product_id_fkey',
        'recipe_items', 'products',
        ['ingredient_product_id'], ['id']
    )
