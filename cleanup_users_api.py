#!/usr/bin/env python3
"""
Script to clean up test users via API calls while keeping only admin and admin1
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / 'frontend' / '.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def login_as_admin():
    """Login as admin to get authentication token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def get_all_users(token):
    """Get all users from the system"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get users: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return []

def delete_user(user_id, token):
    """Delete a specific user"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(f"{API_BASE}/users/{user_id}", headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🔍 Starting user cleanup process...")
    
    # Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Failed to authenticate. Cannot proceed with cleanup.")
        return
    
    print("✅ Successfully authenticated as admin")
    
    # Get all users
    users = get_all_users(token)
    if not users:
        print("❌ No users found or failed to retrieve users")
        return
    
    print(f"📊 Found {len(users)} total users")
    
    # Show current users
    print("\n📋 Current users:")
    for user in users:
        print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
    
    # Users to keep (admin accounts)
    users_to_keep = ['admin', 'admin1']
    
    # Find users to delete
    users_to_delete = []
    for user in users:
        if user.get('username') not in users_to_keep:
            users_to_delete.append(user)
    
    if not users_to_delete:
        print("\n✅ No test users to delete. Only admin accounts found.")
        return
    
    print(f"\n🗑️  Users to be deleted ({len(users_to_delete)}):")
    for user in users_to_delete:
        print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
    
    print(f"\n⚠️  About to delete {len(users_to_delete)} test users...")
    print("   Keeping: admin, admin1")
    
    # Delete test users
    deleted_count = 0
    for user in users_to_delete:
        success = delete_user(user["id"], token)
        if success:
            deleted_count += 1
            print(f"   ✅ Deleted: {user.get('username')}")
        else:
            print(f"   ❌ Failed to delete: {user.get('username')}")
    
    # Verify cleanup
    remaining_users = get_all_users(token)
    print(f"\n📊 Cleanup complete!")
    print(f"   Deleted: {deleted_count} users")
    print(f"   Remaining: {len(remaining_users)} users")
    
    print("\n📋 Remaining users:")
    for user in remaining_users:
        print(f"  - {user.get('username')} ({user.get('full_name')}) - {user.get('role')}")
        
    print("\n🎉 User cleanup completed successfully!")

if __name__ == "__main__":
    main()