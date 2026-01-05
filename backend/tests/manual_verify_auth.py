
import asyncio
import sys
import os
from datetime import timedelta

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.utils.security import create_access_token, create_refresh_token, decode_access_token
from app.models.user import User
from app.models.company import Company
from app.models.role import Role

async def verify_auth_flow():
    print("🚀 Starting Auth Flow Verification")
    
    # 1. Test Key Generation
    print("\n1. Testing Token Generation Utilities")
    data = {"user_id": 1, "company_id": 1}
    
    access_token = create_access_token(data)
    print(f"✅ Access Token Generated: {access_token[:20]}...")
    
    refresh_token = create_refresh_token(data)
    print(f"✅ Refresh Token Generated: {refresh_token[:20]}...")
    
    # 2. Test Decoding
    print("\n2. Testing Token Decoding")
    decoded = decode_access_token(access_token)
    if decoded and decoded["user_id"] == 1:
        print("✅ Access Token Decoded Successfully")
    else:
        print("❌ Access Token Decoding Failed")
        
    decoded_refresh = decode_access_token(refresh_token)
    if decoded_refresh and decoded_refresh["type"] == "refresh":
         print("✅ Refresh Token Decoded and Verified as 'refresh' type")
    else:
         print(f"❌ Refresh Token Verification Failed: {decoded_refresh}")

    print("\n🎉 Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_auth_flow())
