"""
Example: How to integrate Offline Authentication in server.py

This file demonstrates how to modify your existing server.py
to support both online and offline authentication modes
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from offline_auth_service import OfflineAuthService, OnlineAuthService

app = FastAPI()

# ============================================
# STEP 1: Detect Mode at Startup
# ============================================

# Check environment variable to determine mode
IS_OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"
OFFLINE_DB_NAME = os.getenv("OFFLINE_DB_NAME", "company_offline")

# Initialize appropriate database connection
if IS_OFFLINE_MODE:
    print("🔴 ========================================")
    print("🔴 RUNNING IN OFFLINE MODE")
    print("🔴 ========================================")
    print(f"🔴 Database: {OFFLINE_DB_NAME} (Local)")
    print("🔴 Authentication: Local user database")
    print("🔴 Changes will sync when online")
    print("🔴 ========================================")
else:
    print("🟢 ========================================")
    print("🟢 RUNNING IN ONLINE MODE")
    print("🟢 ========================================")
    print("🟢 Database: MongoDB Atlas (Cloud)")
    print("🟢 Authentication: Master database")
    print("🟢 ========================================")

# ============================================
# STEP 2: Initialize Auth Service
# ============================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Import appropriate database
if IS_OFFLINE_MODE:
    from motor.motor_asyncio import AsyncIOMotorClient
    # Connect to local MongoDB
    local_client = AsyncIOMotorClient(os.getenv("LOCAL_MONGO_URL", "mongodb://localhost:27017"))
    local_db = local_client[OFFLINE_DB_NAME]
    auth_service = OfflineAuthService(local_db)
else:
    # Use existing cloud MongoDB connection
    from mongodb_database import mongo_db
    # Online auth service would use your existing implementation
    # auth_service = OnlineAuthService(mongo_db.database)
    pass

# ============================================
# STEP 3: Unified Login Endpoint
# ============================================

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that works in both online and offline mode
    
    - Online: Authenticates against master database in cloud
    - Offline: Authenticates against local database
    """
    
    if IS_OFFLINE_MODE:
        # 🔴 OFFLINE MODE
        try:
            result = await auth_service.authenticate(
                username=form_data.username,
                password=form_data.password
            )
            
            return {
                **result,
                "message": "Logged in successfully (Offline Mode)",
                "warning": "You are working offline. Changes will sync when online."
            }
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Offline authentication error: {str(e)}"
            )
    
    else:
        # 🟢 ONLINE MODE
        # Your existing online authentication logic here
        # Example:
        """
        user = await authenticate_user_online(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_online_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "mode": "online",
            "user": {...}
        }
        """
        pass

# ============================================
# STEP 4: Get Current User (Unified)
# ============================================

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user from token
    Works in both online and offline mode
    """
    
    if IS_OFFLINE_MODE:
        # 🔴 Validate token against local database
        user = await auth_service.get_current_user(token)
        return user
    else:
        # 🟢 Validate token against cloud database
        # Your existing get_current_user logic
        pass

# ============================================
# STEP 5: Permission Check (Unified)
# ============================================

def check_permission(required_roles: list):
    """
    Dependency for checking user permissions
    Works in both online and offline mode
    """
    async def permission_checker(current_user = Depends(get_current_user)):
        if IS_OFFLINE_MODE:
            # Offline permission check
            if not auth_service.check_permission(current_user, required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required roles: {required_roles}"
                )
        else:
            # Online permission check (existing logic)
            if current_user.get("role") not in required_roles:
                raise HTTPException(status_code=403, detail="Permission denied")
        
        return current_user
    
    return permission_checker

# ============================================
# STEP 6: Example Protected Endpoints
# ============================================

@app.get("/api/ships")
async def get_ships(current_user = Depends(get_current_user)):
    """
    Get ships - works in both modes
    
    - Online: Fetches from cloud database (filtered by company)
    - Offline: Fetches from local database (all ships in local DB)
    """
    
    if IS_OFFLINE_MODE:
        # Get ships from local database
        company_id = current_user.get("company")
        
        # In offline mode, local DB only contains current company's data
        # So no need to filter by company (but we do it for consistency)
        ships = await local_db.ships.find({"company": company_id}).to_list(length=None)
        
        return {
            "ships": ships,
            "mode": "offline",
            "count": len(ships)
        }
    else:
        # Online mode - use existing logic
        pass

@app.post("/api/ships")
async def create_ship(
    ship_data: dict,
    current_user = Depends(check_permission(["admin", "manager"]))
):
    """
    Create ship - works in both modes
    
    - Online: Saves to cloud, creates Google Drive folder
    - Offline: Saves to local DB, marks for sync
    """
    
    if IS_OFFLINE_MODE:
        # Save to local database
        ship_data["company"] = current_user.get("company")
        ship_data["created_by"] = current_user.get("username")
        ship_data["created_offline"] = True
        ship_data["synced"] = False
        
        result = await local_db.ships.insert_one(ship_data)
        
        # Log for sync
        await local_db.sync_queue.insert_one({
            "type": "create_ship",
            "data": ship_data,
            "timestamp": datetime.now(),
            "synced": False
        })
        
        return {
            "success": True,
            "message": "Ship created (Offline). Will sync when online.",
            "id": str(result.inserted_id),
            "mode": "offline"
        }
    else:
        # Online mode - use existing logic
        pass

# ============================================
# STEP 7: System Info Endpoint
# ============================================

@app.get("/api/system/info")
async def get_system_info(current_user = Depends(get_current_user)):
    """
    Get system information including mode status
    Useful for frontend to display offline indicator
    """
    
    unsynced_count = 0
    if IS_OFFLINE_MODE:
        # Count unsynced changes
        unsynced_count = await auth_service.get_unsynced_changes_count()
    
    return {
        "mode": "offline" if IS_OFFLINE_MODE else "online",
        "database": OFFLINE_DB_NAME if IS_OFFLINE_MODE else "cloud",
        "user": {
            "username": current_user.get("username"),
            "role": current_user.get("role"),
            "company": current_user.get("company")
        },
        "offline_info": {
            "enabled": IS_OFFLINE_MODE,
            "unsynced_changes": unsynced_count,
            "sync_pending": unsynced_count > 0
        } if IS_OFFLINE_MODE else None
    }

# ============================================
# STEP 8: Sync Endpoint (For when going online)
# ============================================

@app.post("/api/sync/push")
async def sync_offline_changes(current_user = Depends(get_current_user)):
    """
    Sync offline changes to cloud database
    Called when user goes online again
    """
    
    if not IS_OFFLINE_MODE:
        return {"message": "Already in online mode, no sync needed"}
    
    # Get all unsynced changes
    sync_queue = await local_db.sync_queue.find({"synced": False}).to_list(length=None)
    
    synced_count = 0
    errors = []
    
    for item in sync_queue:
        try:
            # Process each sync item
            # (Connect to online DB and push changes)
            # This is a simplified example
            
            item_type = item.get("type")
            data = item.get("data")
            
            # Mark as synced
            await local_db.sync_queue.update_one(
                {"_id": item["_id"]},
                {"$set": {"synced": True}}
            )
            
            synced_count += 1
            
        except Exception as e:
            errors.append({
                "item_id": str(item["_id"]),
                "error": str(e)
            })
    
    return {
        "success": True,
        "synced_count": synced_count,
        "total_items": len(sync_queue),
        "errors": errors
    }

# ============================================
# HOW TO RUN
# ============================================

"""
ONLINE MODE (Default):
    python -m uvicorn server:app --host 0.0.0.0 --port 8001

OFFLINE MODE:
    OFFLINE_MODE=true OFFLINE_DB_NAME=company_amcsc python -m uvicorn server:app --host 0.0.0.0 --port 8001

Or set in .env file:
    OFFLINE_MODE=true
    OFFLINE_DB_NAME=company_amcsc
    LOCAL_MONGO_URL=mongodb://localhost:27017
"""

# ============================================
# DOCKER COMPOSE FOR LOCAL MONGODB
# ============================================

"""
# docker-compose.yml

version: '3.8'

services:
  mongodb-local:
    image: mongo:7.0
    container_name: ship_management_offline
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - ./data/mongodb:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
    command: mongod --quiet

  backend-offline:
    build: ./backend
    container_name: ship_management_backend_offline
    restart: always
    ports:
      - "8001:8001"
    environment:
      - OFFLINE_MODE=true
      - OFFLINE_DB_NAME=company_amcsc
      - LOCAL_MONGO_URL=mongodb://admin:password@mongodb-local:27017
      - SECRET_KEY=your-secret-key
    depends_on:
      - mongodb-local
    volumes:
      - ./backend:/app
    command: uvicorn server:app --host 0.0.0.0 --port 8001

  frontend-offline:
    build: ./frontend
    container_name: ship_management_frontend_offline
    restart: always
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
      - REACT_APP_OFFLINE_MODE=true
    volumes:
      - ./frontend:/app
    command: npm start

# To run offline mode:
# docker-compose up -d
"""
