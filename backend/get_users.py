import asyncio
import httpx

async def get_info():
    async with httpx.AsyncClient() as client:
        # 1. Get Companies
        try:
            r = await client.get('http://localhost:8000/debug/companies')
            print("Companies:", r.text)
            data = r.json()
            if data['companies']:
                slug = data['companies'][0]['slug']
                
                # 2. Get Users
                r2 = await client.get(f'http://localhost:8000/debug/users/{slug}')
                users = r2.json()['users']
                for u in users:
                    print(f"User: {u['username']} - {u['email']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_info())
