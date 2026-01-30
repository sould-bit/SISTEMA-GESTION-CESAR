import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("STEP 1: Start")
try:
    import app.database
    print("STEP 2: DB Imported")
except Exception as e:
    print(f"ERROR DB: {e}")

try:
    from app.services.rbac_sync_service import RBACSyncService
    print("STEP 3: Service Imported")
except Exception as e:
    print(f"ERROR SERVICE: {e}")
    import traceback
    traceback.print_exc()

print("STEP 4: End")
