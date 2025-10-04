#!/usr/bin/env python3
"""
Test script for the upcoming surveys API endpoint
"""
import asyncio
import sys
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta, timezone
import uuid
import bcrypt

# Load environment variables
load_dotenv('/app/backend/.env')

sys.path.append('/app/backend')

from mongodb_database import mongo_db

# JWT Configuration (from server.py)
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT token (copied from server.py)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def test_api_endpoint():
    """Test the upcoming surveys API endpoint"""
    try:
        # Connect to database
        await mongo_db.connect()
        
        # Create test user
        test_user_id = str(uuid.uuid4())
        test_company = "Test API Company"
        
        password_hash = bcrypt.hashpw("testpass".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        test_user = {
            "id": test_user_id,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "manager",
            "department": "technical",
            "company": test_company,
            "zalo": "test123",
            "is_active": True,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "permissions": {}
        }
        
        # Create test ship
        test_ship = {
            "id": str(uuid.uuid4()),
            "name": "API Test Ship",
            "company": test_company,
            "flag": "Panama",
            "ship_type": "Container",
            "created_at": datetime.utcnow()
        }
        
        # Create test certificates with upcoming surveys
        current_date = datetime.now()
        
        cert1 = {
            "id": str(uuid.uuid4()),
            "ship_id": test_ship["id"],
            "cert_name": "Safety Construction Certificate",
            "cert_abbreviation": "SCC",
            "next_survey": (current_date + timedelta(days=45)).strftime('%Y-%m-%d'),
            "next_survey_type": "Annual",
            "status": "Valid",
            "created_at": datetime.utcnow()
        }
        
        cert2 = {
            "id": str(uuid.uuid4()),
            "ship_id": test_ship["id"],
            "cert_name": "Load Line Certificate",
            "cert_abbreviation": "LLC",
            "next_survey": (current_date - timedelta(days=10)).strftime('%Y-%m-%d'),
            "next_survey_type": "Annual",
            "status": "Expired",
            "created_at": datetime.utcnow()
        }
        
        # Insert test data
        await mongo_db.create("users", test_user)
        await mongo_db.create("ships", test_ship)
        await mongo_db.create("certificates", cert1)
        await mongo_db.create("certificates", cert2)
        
        print("✅ Test data created successfully")
        
        # Generate JWT token
        token_data = {"sub": test_user_id}
        access_token = create_access_token(token_data)
        
        print(f"🔑 Generated JWT token for user: {test_user['username']}")
        
        # Test the API endpoint
        url = "http://localhost:8001/api/certificates/upcoming-surveys"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"🌐 Testing API endpoint: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint works successfully!")
            print(f"📊 Found {data.get('total_count', 0)} upcoming surveys")
            print(f"🏢 Company: {data.get('company', 'N/A')}")
            print(f"📅 Check date: {data.get('check_date', 'N/A')}")
            
            upcoming_surveys = data.get('upcoming_surveys', [])
            if upcoming_surveys:
                print("\n🔍 Upcoming surveys:")
                for survey in upcoming_surveys:
                    status_icon = "⚠️" if survey.get('is_overdue') else "🔔" if survey.get('is_due_soon') else "📅"
                    print(f"{status_icon} {survey.get('ship_name')} - {survey.get('cert_name_display')}")
                    print(f"   Next Survey: {survey.get('next_survey_date')} ({survey.get('days_until_survey')} days)")
                    print(f"   Type: {survey.get('next_survey_type')}")
            else:
                print("ℹ️ No upcoming surveys found")
                
            print(f"\n📋 Full response:")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"❌ API endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
        
        # Clean up test data
        await mongo_db.delete("users", {"id": test_user_id})
        await mongo_db.delete("ships", {"id": test_ship["id"]})
        await mongo_db.delete("certificates", {"ship_id": test_ship["id"]})
        print("\n🧹 Test data cleaned up")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_api_endpoint())
    if success:
        print("\n✅ API endpoint test passed!")
    else:
        print("\n❌ API endpoint test failed!")