"""
Offline Authentication Service
Handles user authentication and authorization in offline mode
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
OFFLINE_TOKEN_EXPIRE_DAYS = 30

class OfflineAuthService:
    """
    Authentication service for offline mode
    
    Features:
    - Local user database authentication
    - Password hash verification
    - JWT token generation & validation
    - Role-based access control
    - Audit logging
    """
    
    def __init__(self, local_database):
        """
        Initialize offline auth service
        
        Args:
            local_database: MongoDB database instance (local)
        """
        self.db = local_database
        self.is_offline_mode = True
        logger.info("🔴 Offline Authentication Service initialized")
    
    async def authenticate(
        self, 
        username: str, 
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate user with username/password in offline mode
        
        Args:
            username: User's username
            password: User's plain password
            
        Returns:
            dict: Authentication result with token and user info
            
        Raises:
            HTTPException: If authentication fails
        """
        logger.info(f"🔴 [OFFLINE] Authentication attempt: {username}")
        
        # 1. Find user in local database
        user = await self.db.users.find_one({
            "username": username,
            "is_active": True
        })
        
        if not user:
            logger.warning(f"❌ [OFFLINE] User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password (offline mode)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. Verify password
        if not self._verify_password(password, user.get("hashed_password", "")):
            logger.warning(f"❌ [OFFLINE] Invalid password for user: {username}")
            await self._log_failed_attempt(username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password (offline mode)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 3. Generate offline token
        access_token = self._create_offline_token(user)
        
        # 4. Log successful login
        await self._log_successful_login(user)
        
        logger.info(f"✅ [OFFLINE] User authenticated: {username} ({user.get('role')})")
        
        # 5. Return authentication result
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "mode": "offline",
            "expires_in": OFFLINE_TOKEN_EXPIRE_DAYS * 24 * 3600,
            "user": {
                "id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "role": user.get("role"),
                "company": user.get("company"),
                "department": user.get("department", []),
                "email": user.get("email"),
                "zalo": user.get("zalo")
            }
        }
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def _create_offline_token(self, user: Dict[str, Any]) -> str:
        """
        Create JWT token for offline use
        
        Token includes:
        - User ID, username, role
        - Company and department info
        - Permissions (role-based)
        - Offline mode flag
        - Extended expiration (30 days)
        """
        token_data = {
            "sub": user.get("id"),
            "username": user.get("username"),
            "role": user.get("role"),
            "company": user.get("company"),
            "department": user.get("department", []),
            "mode": "offline",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=OFFLINE_TOKEN_EXPIRE_DAYS)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Validate token and get current user info in offline mode
        
        Args:
            token: JWT token
            
        Returns:
            dict: User information
            
        Raises:
            HTTPException: If token is invalid
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (offline mode)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            user_id: str = payload.get("sub")
            mode: str = payload.get("mode")
            
            if user_id is None:
                raise credentials_exception
            
            # Verify this is an offline token
            if mode != "offline":
                logger.warning("⚠️ [OFFLINE] Attempted to use online token in offline mode")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Online token not valid in offline mode. Please re-authenticate.",
                )
            
            # Get user from local database
            user = await self.db.users.find_one({"id": user_id})
            
            if user is None:
                logger.warning(f"⚠️ [OFFLINE] Token valid but user not found: {user_id}")
                raise credentials_exception
            
            if not user.get("is_active", False):
                logger.warning(f"⚠️ [OFFLINE] Inactive user attempted access: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            return user
            
        except JWTError as e:
            logger.error(f"❌ [OFFLINE] JWT error: {e}")
            raise credentials_exception
    
    def check_permission(
        self, 
        user: Dict[str, Any], 
        required_roles: list
    ) -> bool:
        """
        Check if user has required permission (role-based)
        
        Args:
            user: User object from database
            required_roles: List of allowed roles
            
        Returns:
            bool: True if user has permission
        """
        user_role = user.get("role")
        has_permission = user_role in required_roles
        
        if not has_permission:
            logger.warning(
                f"⚠️ [OFFLINE] Permission denied for {user.get('username')}: "
                f"required {required_roles}, has {user_role}"
            )
        
        return has_permission
    
    async def _log_successful_login(self, user: Dict[str, Any]):
        """Log successful login for audit"""
        try:
            await self.db.audit_log.insert_one({
                "event": "login_success",
                "user_id": user.get("id"),
                "username": user.get("username"),
                "role": user.get("role"),
                "mode": "offline",
                "timestamp": datetime.now(timezone.utc),
                "synced": False  # Will sync when online
            })
        except Exception as e:
            logger.error(f"Error logging successful login: {e}")
    
    async def _log_failed_attempt(self, username: str):
        """Log failed login attempt for security"""
        try:
            await self.db.audit_log.insert_one({
                "event": "login_failed",
                "username": username,
                "mode": "offline",
                "timestamp": datetime.now(timezone.utc),
                "synced": False
            })
        except Exception as e:
            logger.error(f"Error logging failed attempt: {e}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from local database"""
        return await self.db.users.find_one({"id": user_id})
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username from local database"""
        return await self.db.users.find_one({"username": username})
    
    async def validate_company_access(
        self, 
        user: Dict[str, Any], 
        company_id: str
    ) -> bool:
        """
        Validate if user has access to specific company
        
        In offline mode, user can only access their own company's data
        """
        user_company = user.get("company")
        
        # System admin can access any company (but data might not be in local DB)
        if user.get("role") in ["system_admin", "super_admin"]:
            logger.info(f"✅ [OFFLINE] Admin access granted: {user.get('username')}")
            return True
        
        # Regular users can only access their company
        if user_company == company_id:
            return True
        
        logger.warning(
            f"⚠️ [OFFLINE] Company access denied for {user.get('username')}: "
            f"user company={user_company}, requested={company_id}"
        )
        return False
    
    async def get_audit_logs(
        self, 
        limit: int = 100
    ) -> list:
        """
        Get recent audit logs for monitoring
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            list: Audit log entries
        """
        cursor = self.db.audit_log.find().sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        return logs
    
    async def get_unsynced_changes_count(self) -> int:
        """Get count of changes not yet synced to server"""
        count = await self.db.audit_log.count_documents({"synced": False})
        return count


class OnlineAuthService:
    """
    Authentication service for online mode
    
    Placeholder for online authentication logic
    (Keep existing online auth implementation)
    """
    
    def __init__(self, online_database):
        self.db = online_database
        self.is_offline_mode = False
        logger.info("🟢 Online Authentication Service initialized")
    
    async def authenticate(self, username: str, password: str):
        """Online authentication - use existing implementation"""
        # Your existing online auth logic here
        pass


def get_auth_service(is_offline: bool = False):
    """
    Factory function to get appropriate auth service
    
    Args:
        is_offline: True for offline mode, False for online
        
    Returns:
        OfflineAuthService or OnlineAuthService
    """
    if is_offline:
        # Return offline auth service with local DB
        from mongodb_database import mongo_db  # Local DB
        return OfflineAuthService(mongo_db.database)
    else:
        # Return online auth service with cloud DB
        from mongodb_database import mongo_db  # Cloud DB
        return OnlineAuthService(mongo_db.database)
