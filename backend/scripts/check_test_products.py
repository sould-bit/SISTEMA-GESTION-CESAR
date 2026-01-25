"""
Script para revisar productos e ingredientes que empiezan con 'test'
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.product import Product, Ingredient

async def check_products():
    async with AsyncSessionLocal() as session:
        # Query products starting with 'test'
        stmt = select(Product).where(Product.name.ilike('test%'))
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        print('=' * 60)
        print('PRODUCTOS QUE EMPIEZAN CON "test"')
        print('=' * 60)
        
        for p in products:
            print(f'ID: {p.id}')
            print(f'  Name: {p.name}')
            print(f'  is_active: {p.is_active}')
            print(f'  is_deleted: {p.is_deleted}')
            print(f'  price: {p.price}')
            print(f'  company_id: {p.company_id}')
            print('-' * 40)
        
        if not products:
            print('No se encontraron productos')
        
        print()
        print('=' * 60)
        print('INGREDIENTES QUE EMPIEZAN CON "test"')
        print('=' * 60)
        
        # Query ingredients starting with 'test'
        stmt2 = select(Ingredient).where(Ingredient.name.ilike('test%'))
        result2 = await session.execute(stmt2)
        ingredients = result2.scalars().all()
        
        for i in ingredients:
            print(f'ID: {i.id}')
            print(f'  Name: {i.name}')
            print(f'  is_active: {i.is_active}')
            print(f'  is_deleted: {i.is_deleted}')
            print(f'  current_cost: {i.current_cost}')
            print(f'  company_id: {i.company_id}')
            print('-' * 40)
        
        if not ingredients:
            print('No se encontraron ingredientes')

if __name__ == "__main__":
    asyncio.run(check_products())
