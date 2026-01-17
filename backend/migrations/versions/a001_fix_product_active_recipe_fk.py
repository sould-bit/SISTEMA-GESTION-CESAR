"""Fix recipes.id to UUID and update FKs

Revision ID: a001_fix_product_active_recipe_fk
Revises: migrate_recipe_items_ingredients
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'a001_fix_recipe_uuid'
down_revision = 'migrate_recipe_items_ingredients'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 0. Clean data to avoid conversion errors
    op.execute("DELETE FROM recipe_items")
    op.execute("DELETE FROM recipes")
    op.execute("UPDATE products SET active_recipe_id = NULL")

    # 1. Drop FKs referencing recipes.id
    # products -> recipes
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_active_recipe_id_fkey")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS fk_products_active_recipe")
    
    # recipe_items -> recipes
    op.execute("ALTER TABLE recipe_items DROP CONSTRAINT IF EXISTS recipe_items_recipe_id_fkey")
    op.execute("ALTER TABLE recipe_items DROP CONSTRAINT IF EXISTS fk_recipe_items_recipe")

    # 2. Modify recipes.id to UUID
    # Need to drop PK constraint first?
    op.execute("ALTER TABLE recipes DROP CONSTRAINT IF EXISTS recipes_pkey CASCADE")
    op.execute("ALTER TABLE recipes DROP COLUMN id")
    op.add_column('recipes', sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.create_primary_key('recipes_pkey', 'recipes', ['id'])

    # 3. Modify referencing columns to UUID
    
    # recipe_items.recipe_id
    op.execute("ALTER TABLE recipe_items ALTER COLUMN recipe_id TYPE UUID USING NULL")
    
    # products.active_recipe_id
    op.execute("ALTER TABLE products ALTER COLUMN active_recipe_id TYPE UUID USING NULL")

    # 4. Recreate FKs
    
    op.create_foreign_key(
        'fk_recipe_items_recipe',
        'recipe_items', 'recipes',
        ['recipe_id'], ['id'],
        ondelete='CASCADE' 
    )

    op.create_foreign_key(
        'fk_products_active_recipe',
        'products', 'recipes',
        ['active_recipe_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade() -> None:
    # This downgrade is destructive/lossy as it goes back to int
    op.execute("DELETE FROM recipe_items")
    op.execute("DELETE FROM recipes")
    op.execute("UPDATE products SET active_recipe_id = NULL")
    
    op.drop_constraint('fk_products_active_recipe', 'products', type_='foreignkey')
    op.drop_constraint('fk_recipe_items_recipe', 'recipe_items', type_='foreignkey')
    
    # Restore recipes.id to INT
    op.execute("ALTER TABLE recipes DROP CONSTRAINT recipes_pkey CASCADE")
    op.execute("ALTER TABLE recipes DROP COLUMN id")
    op.add_column('recipes', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.create_primary_key('recipes_pkey', 'recipes', ['id'])
    
    # Restore FK columns to INT
    op.execute("ALTER TABLE recipe_items ALTER COLUMN recipe_id TYPE INTEGER USING NULL")
    op.execute("ALTER TABLE products ALTER COLUMN active_recipe_id TYPE INTEGER USING NULL")
    
    # Restore FKs
    op.create_foreign_key(
        'recipe_items_recipe_id_fkey',
        'recipe_items', 'recipes',
        ['recipe_id'], ['id']
    )
    op.create_foreign_key(
        'products_active_recipe_id_fkey',
        'products', 'recipes',
        ['active_recipe_id'], ['id']
    )
