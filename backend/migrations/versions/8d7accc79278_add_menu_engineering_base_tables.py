"""add_menu_engineering_base_tables

Revision ID: 8d7accc79278
Revises: 8d7accc79277
Create Date: 2026-01-14 12:00:00.000000

This migration creates the base tables for Menu Engineering:
- unit_conversions: Standard unit conversion factors
- ingredients: Raw materials/supplies
- recipe_items: Recipe-Ingredient pivot table (if not exists)
- Adds company_id to recipes if missing
- Adds active_recipe_id column to products if missing
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '8d7accc79278'
down_revision: Union[str, Sequence[str], None] = '8d7accc79277'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(bind, table_name: str) -> bool:
    insp = inspect(bind)
    return table_name in insp.get_table_names()

def column_exists(bind, table_name: str, column_name: str) -> bool:
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade() -> None:
    bind = op.get_bind()
    
    # 1. Unit Conversions Table
    if not table_exists(bind, 'unit_conversions'):
        op.create_table('unit_conversions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('from_unit', sa.String(length=20), nullable=False),
            sa.Column('to_unit', sa.String(length=20), nullable=False),
            sa.Column('factor', sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_unit_conversions_from_to', 'unit_conversions', ['from_unit', 'to_unit'], unique=False)

    # 2. Ingredients Table
    if not table_exists(bind, 'ingredients'):
        op.create_table('ingredients',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('sku', sa.String(length=50), nullable=False),
            sa.Column('base_unit', sa.String(length=20), nullable=False),
            sa.Column('current_cost', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
            sa.Column('last_cost', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
            sa.Column('yield_factor', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_ingredients_name', 'ingredients', ['name'], unique=False)
        op.create_index('idx_ingredients_sku', 'ingredients', ['sku'], unique=False)
        op.create_index('idx_ingredients_company', 'ingredients', ['company_id'], unique=False)

    # 3. Recipes Table - check if company_id column exists
    if table_exists(bind, 'recipes'):
        if not column_exists(bind, 'recipes', 'company_id'):
            op.add_column('recipes', sa.Column('company_id', sa.Integer(), nullable=True))
            # Set default for existing records, then make not null
            op.execute("UPDATE recipes SET company_id = (SELECT company_id FROM products WHERE products.id = recipes.product_id) WHERE company_id IS NULL")
            op.alter_column('recipes', 'company_id', nullable=False)
            op.create_foreign_key('fk_recipes_company', 'recipes', 'companies', ['company_id'], ['id'])
    else:
        # Create recipes if it doesn't exist
        op.create_table('recipes',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('batch_yield', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('total_cost', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
            sa.Column('preparation_time', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_recipes_company', 'recipes', ['company_id'], unique=False)
        op.create_index('idx_recipes_product', 'recipes', ['product_id'], unique=False)

    # 4. Recipe Items (Pivot Table)
    if not table_exists(bind, 'recipe_items'):
        op.create_table('recipe_items',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('gross_quantity', sa.Float(), nullable=False),
            sa.Column('net_quantity', sa.Float(), nullable=False),
            sa.Column('measure_unit', sa.String(length=20), nullable=False),
            sa.Column('calculated_cost', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_recipe_items_recipe', 'recipe_items', ['recipe_id'], unique=False)
        op.create_index('idx_recipe_items_ingredient', 'recipe_items', ['ingredient_id'], unique=False)

    # 5. Add active_recipe_id to products if not exists
    if table_exists(bind, 'products') and not column_exists(bind, 'products', 'active_recipe_id'):
        # Note: existing recipes table uses INTEGER for id, not UUID
        op.add_column('products', sa.Column('active_recipe_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_products_active_recipe', 'products', 'recipes', ['active_recipe_id'], ['id'])

def downgrade() -> None:
    bind = op.get_bind()
    
    # Only drop what we may have created
    if column_exists(bind, 'products', 'active_recipe_id'):
        op.drop_constraint('fk_products_active_recipe', 'products', type_='foreignkey')
        op.drop_column('products', 'active_recipe_id')
    
    if table_exists(bind, 'recipe_items'):
        op.drop_table('recipe_items')
    
    if table_exists(bind, 'ingredients'):
        op.drop_table('ingredients')
    
    if table_exists(bind, 'unit_conversions'):
        op.drop_table('unit_conversions')
