import requests
import json

base_url = 'http://localhost:8000'
endpoints = [
    '/ingredients/audits/history',
    '/api/ingredients/audits/history'
]

for ep in endpoints:
    url = f"{base_url}{ep}"
    print(f"Testing {url}...")
    try:
        r = requests.get(f"{url}?limit=100")
        if r.status_code == 200:
            data = r.json()
            print(f"  Success! Total entries: {len(data)}")
            reversions = [x for x in data if x.get('transaction_type') == 'REVERT_ADJ']
            print(f"  REVERT_ADJ entries: {len(reversions)}")
            if reversions:
                print("  Sample transaction_type:", reversions[0]['transaction_type'])
            
            types = {}
            for x in data:
                t = x.get('transaction_type')
                types[t] = types.get(t, 0) + 1
            print(f"  Distribution: {types}")
        else:
            print(f"  Failed: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"  Exception: {e}")
