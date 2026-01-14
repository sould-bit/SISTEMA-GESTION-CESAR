"""add_menu_engineering_v4_1

Revision ID: abcdef123456
Revises: 8d7accc79277
Create Date: 2026-02-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abcdef123456'
down_revision: Union[str, Sequence[str], None] = '8d7accc79277'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Drop old tables if they exist (defensive)
    # Since we are re-engineering, we drop existing recipe tables.
    # We must drop foreign keys first if any.

    # Try/Except block for safety in case tables don't exist in dev env
    try:
        op.drop_table('recipe_items')
    except Exception:
        pass

    try:
        op.drop_table('recipes')
    except Exception:
        pass

    # 2. Create Ingredients
    op.create_table('ingredients',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('sku', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('base_unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('current_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('last_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('yield_factor', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingredients_name'), 'ingredients', ['name'], unique=False)
    op.create_index(op.f('ix_ingredients_sku'), 'ingredients', ['sku'], unique=False)
    op.create_index(op.f('ix_ingredients_company_id'), 'ingredients', ['company_id'], unique=False)
    op.create_index(op.f('ix_ingredients_category_id'), 'ingredients', ['category_id'], unique=False)

    # 3. Create UnitConversions
    op.create_table('unit_conversions',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('from_unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('to_unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('factor', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unit_conversions_from_unit'), 'unit_conversions', ['from_unit'], unique=False)
    op.create_index(op.f('ix_unit_conversions_to_unit'), 'unit_conversions', ['to_unit'], unique=False)

    # 4. Create Recipes (New Schema)
    op.create_table('recipes',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('batch_yield', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('preparation_time', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipes_company_id'), 'recipes', ['company_id'], unique=False)
    op.create_index(op.f('ix_recipes_product_id'), 'recipes', ['product_id'], unique=False)

    # 5. Create RecipeItems (New Schema)
    op.create_table('recipe_items',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('recipe_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('ingredient_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('gross_quantity', sa.Float(), nullable=False),
        sa.Column('net_quantity', sa.Float(), nullable=False),
        sa.Column('measure_unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('calculated_cost', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipe_items_recipe_id'), 'recipe_items', ['recipe_id'], unique=False)
    op.create_index(op.f('ix_recipe_items_ingredient_id'), 'recipe_items', ['ingredient_id'], unique=False)

    # 6. Add active_recipe_id to Products
    op.add_column('products', sa.Column('active_recipe_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key(None, 'products', 'recipes', ['active_recipe_id'], ['id'])

def downgrade() -> None:
    # Drop in reverse order
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.drop_column('products', 'active_recipe_id')

    op.drop_table('recipe_items')
    op.drop_table('recipes')
    op.drop_table('unit_conversions')
    op.drop_table('ingredients')
