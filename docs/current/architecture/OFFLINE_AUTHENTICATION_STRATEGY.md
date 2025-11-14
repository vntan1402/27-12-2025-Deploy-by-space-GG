# Offline Authentication & Authorization Strategy

## VẤN ĐỀ CỐT LÕI

Khi offline, hệ thống không thể:
- ❌ Connect đến master DB để verify credentials
- ❌ Validate JWT tokens với server
- ❌ Check user permissions từ online database
- ❌ Revoke access ngay lập tức khi có thay đổi

**→ Cần một cơ chế authentication & authorization hoàn toàn offline**

---

## PHƯƠNG ÁN 1: LOCAL USER DATABASE (Recommended) ⭐

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ONLINE MODE                                │
│                                                          │
│  Frontend → Backend → MongoDB Atlas                     │
│                       ├── Master DB (users, auth)       │
│                       └── Company DB (data)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              OFFLINE MODE                               │
│                                                          │
│  Frontend → Backend → Local MongoDB                     │
│                       └── Company DB (users + data)     │
│                           ├── users (copied)            │
│                           ├── ships                     │
│                           ├── certificates              │
│                           └── ...                       │
└─────────────────────────────────────────────────────────┘
```

### Implementation

#### 1. Export Users cùng Company Data

```python
# export_company_database.py (Enhanced)

async def export_company_data_with_users(self, company_id: str):
    """Export company data INCLUDING users for offline authentication"""
    
    export_data = {
        "company_id": company_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "offline_mode": True,
        "collections": {}
    }
    
    # 1. Export USERS của company (với password hash)
    users = await self.database.users.find({
        "company": company_id,
        "is_active": True  # Chỉ export active users
    }).to_list(None)
    
    # Serialize users (giữ nguyên password hash để verify offline)
    export_data["collections"]["users"] = {
        "description": "Company users (with hashed passwords for offline auth)",
        "count": len(users),
        "documents": [self._serialize_document(u) for u in users]
    }
    
    # 2. Export all other collections...
    # ships, certificates, crew_members, etc.
    
    # 3. Add offline authentication metadata
    export_data["offline_auth"] = {
        "enabled": True,
        "users_count": len(users),
        "auth_method": "local_password_hash",
        "session_duration_hours": 24,
        "note": "Users can login offline using their credentials"
    }
    
    return export_data
```

#### 2. Local Authentication Service

```python
# offline_auth_service.py

class OfflineAuthService:
    """
    Handle authentication in offline mode
    Uses local MongoDB with cached user data
    """
    
    def __init__(self, local_db):
        self.db = local_db
        self.is_offline_mode = True
    
    async def authenticate_offline(
        self, 
        username: str, 
        password: str
    ) -> dict:
        """
        Authenticate user using local database
        Same logic as online auth but uses local DB
        """
        
        # Find user in LOCAL database
        user = await self.db.users.find_one({
            "username": username,
            "is_active": True
        })
        
        if not user:
            raise HTTPException(
                status_code=401, 
                detail="Invalid credentials (offline mode)"
            )
        
        # Verify password using same hash algorithm
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials (offline mode)"
            )
        
        # Generate JWT token (local signing)
        # Token chỉ valid trong offline mode
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "company": user["company"],
            "department": user.get("department", []),
            "mode": "offline",  # Mark as offline token
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        from jose import jwt
        token = jwt.encode(
            token_data, 
            SECRET_KEY,  # Same secret key
            algorithm="HS256"
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "mode": "offline",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "full_name": user.get("full_name"),
                "company": user["company"]
            }
        }
    
    async def get_current_user_offline(self, token: str) -> dict:
        """
        Verify token and get user info in offline mode
        """
        try:
            # Decode JWT
            from jose import jwt, JWTError
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            user_id = payload.get("sub")
            mode = payload.get("mode")
            
            # Verify this is an offline token
            if mode != "offline":
                raise HTTPException(
                    status_code=401,
                    detail="Online token not valid in offline mode"
                )
            
            # Get user from local DB
            user = await self.db.users.find_one({"id": user_id})
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="User not found in offline database"
                )
            
            return user
            
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token (offline mode)"
            )
    
    def check_permission_offline(self, user: dict, required_roles: list) -> bool:
        """
        Check user permission in offline mode
        Uses local user data
        """
        user_role = user.get("role")
        return user_role in required_roles
```

#### 3. Backend Mode Detection & Routing

```python
# server.py (Enhanced)

import os

# Detect if running in offline mode
IS_OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"
OFFLINE_DB_NAME = os.getenv("OFFLINE_DB_NAME", "company_offline")

# Initialize appropriate auth service
if IS_OFFLINE_MODE:
    logger.info("🔴 Running in OFFLINE MODE")
    auth_service = OfflineAuthService(local_db)
else:
    logger.info("🟢 Running in ONLINE MODE")
    auth_service = OnlineAuthService(mongo_db)


@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """
    Login endpoint - works in both online and offline mode
    """
    
    if IS_OFFLINE_MODE:
        # Offline authentication
        logger.info(f"🔴 Offline login attempt: {credentials.username}")
        result = await auth_service.authenticate_offline(
            credentials.username,
            credentials.password
        )
        result["mode"] = "offline"
        return result
    else:
        # Online authentication (existing code)
        logger.info(f"🟢 Online login attempt: {credentials.username}")
        result = await auth_service.authenticate_online(
            credentials.username,
            credentials.password
        )
        result["mode"] = "online"
        return result


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user - works in both modes
    """
    if IS_OFFLINE_MODE:
        return await auth_service.get_current_user_offline(token)
    else:
        return await auth_service.get_current_user_online(token)
```

#### 4. Frontend Mode Detection

```javascript
// AuthContext.jsx (Enhanced)

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    // Check if running in offline mode
    const offlineMode = localStorage.getItem('offline_mode') === 'true';
    setIsOfflineMode(offlineMode);
    
    // Show indicator
    if (offlineMode) {
      console.log('🔴 Running in OFFLINE MODE');
      // Show offline indicator in UI
    }
  }, []);
  
  const login = async (username, password) => {
    try {
      const response = await api.post('/api/auth/login', {
        username,
        password
      });
      
      const { access_token, user: userData, mode } = response.data;
      
      // Store token
      localStorage.setItem('token', access_token);
      setUser(userData);
      
      // Check if response indicates offline mode
      if (mode === 'offline') {
        setIsOfflineMode(true);
        localStorage.setItem('offline_mode', 'true');
        toast.info('🔴 Logged in (Offline Mode)');
      } else {
        setIsOfflineMode(false);
        localStorage.setItem('offline_mode', 'false');
        toast.success('🟢 Logged in (Online)');
      }
      
      return true;
    } catch (error) {
      toast.error('Login failed: ' + error.message);
      return false;
    }
  };
  
  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isOfflineMode
    }}>
      {/* Offline Mode Indicator */}
      {isOfflineMode && (
        <div className="fixed top-0 left-0 right-0 bg-orange-600 text-white text-center py-2 z-50">
          🔴 OFFLINE MODE - Changes will sync when online
        </div>
      )}
      {children}
    </AuthContext.Provider>
  );
};
```

---

## PHƯƠNG ÁN 2: EXTENDED JWT WITH LOCAL VALIDATION

### Concept
- Generate JWT tokens với expiry dài (7-30 days)
- Store user info & permissions trong token payload
- Validate token locally without server
- Refresh token khi online lại

### Pros & Cons
✅ Không cần local user database
✅ Đơn giản hơn
❌ Không thể revoke access ngay lập tức
❌ Token có thể bị stolen và dùng offline
❌ Không update được permissions trong offline period

### Implementation

```python
# Extended JWT for offline use

def generate_offline_token(user: dict, expiry_days: int = 30):
    """
    Generate long-lived JWT for offline use
    Include all necessary user data & permissions
    """
    
    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "company": user["company"],
        "department": user.get("department", []),
        "permissions": get_user_permissions(user),  # Full permissions
        "mode": "offline",
        "exp": datetime.utcnow() + timedelta(days=expiry_days),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expiry_days * 24 * 3600,
        "mode": "offline",
        "note": "This token is valid for offline use"
    }
```

---

## PHƯƠNG ÁN 3: PIN/BIOMETRIC LOCAL AUTH

### Concept
- User setup PIN code hoặc biometric (fingerprint, face ID)
- PIN stored encrypted locally
- Quick authentication without full credentials
- Optional: Require full password periodically

### Use Case
- Thiết bị cá nhân (laptop, tablet trên tàu)
- Quick access sau khi đã login lần đầu
- Enhanced security với device binding

### Implementation

```python
# Local PIN authentication

class LocalPINAuth:
    """
    PIN-based authentication for offline mode
    Device-specific, encrypted storage
    """
    
    def setup_pin(self, user_id: str, pin: str, device_id: str):
        """
        Setup PIN for offline access
        Encrypted and stored locally
        """
        from cryptography.fernet import Fernet
        
        # Generate device-specific key
        key = self._generate_device_key(device_id)
        cipher = Fernet(key)
        
        # Encrypt PIN
        encrypted_pin = cipher.encrypt(pin.encode())
        
        # Store in local secure storage
        local_storage = {
            "user_id": user_id,
            "encrypted_pin": encrypted_pin.decode(),
            "device_id": device_id,
            "created_at": datetime.now().isoformat()
        }
        
        # Save to local file/database
        with open(".local_auth", "w") as f:
            json.dump(local_storage, f)
    
    def verify_pin(self, user_id: str, pin: str, device_id: str) -> bool:
        """Verify PIN for offline access"""
        # Load and decrypt stored PIN
        # Compare with provided PIN
        # Return True if match
        pass
```

---

## SO SÁNH CÁC PHƯƠNG ÁN

| Feature | Phương án 1<br/>(Local User DB) | Phương án 2<br/>(Extended JWT) | Phương án 3<br/>(PIN/Biometric) |
|---------|------|------|------|
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Implementation** | Medium | Easy | Hard |
| **Permission Update** | ❌ Không (offline) | ❌ Không | ❌ Không |
| **Revoke Access** | ❌ Không (offline) | ❌ Không | ❌ Không |
| **User Management** | ✅ Full CRUD | ❌ Read-only | ❌ Read-only |
| **Multi-device** | ✅ Yes | ✅ Yes | ❌ Device-specific |

---

## KHUYẾN NGHỊ: HYBRID APPROACH ⭐

### Combine the Best of All

```
┌─────────────────────────────────────────────────┐
│     OFFLINE AUTHENTICATION SYSTEM               │
├─────────────────────────────────────────────────┤
│                                                  │
│  1️⃣ Export Phase (Online)                       │
│     • Export users với password hashes          │
│     • Generate extended JWT (30 days)           │
│     • Optional: Setup PIN for quick access      │
│                                                  │
│  2️⃣ Offline Authentication                      │
│     • Primary: Local User DB authentication     │
│     • Fallback: Extended JWT validation         │
│     • Quick access: PIN/Biometric (optional)    │
│                                                  │
│  3️⃣ Permission Check                            │
│     • Role-based access control (from token)    │
│     • Department-based filtering (from local DB)│
│     • Read-only restrictions for sensitive ops  │
│                                                  │
│  4️⃣ Sync Phase (Online)                         │
│     • Re-authenticate with master DB            │
│     • Update local user cache                   │
│     • Refresh JWT tokens                        │
│     • Sync pending changes                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Implementation Steps

1. **Export Phase:**
   ```python
   # When exporting company database
   export_data = {
       "users": users_with_hashed_passwords,
       "offline_token": generate_offline_token(current_user, 30),
       "collections": {...}
   }
   ```

2. **Offline Login:**
   ```python
   # Try local DB authentication first
   try:
       user = await offline_auth.authenticate(username, password)
   except:
       # Fallback to JWT validation
       user = await offline_auth.validate_jwt(stored_token)
   ```

3. **Quick Access:**
   ```python
   # Optional PIN for convenience
   if pin_enabled:
       user = await offline_auth.verify_pin(pin)
   ```

4. **Sync on Reconnect:**
   ```python
   # When online again
   await online_auth.re_authenticate(user)
   await sync_service.sync_changes()
   await local_cache.update_users()
   ```

---

## SECURITY CONSIDERATIONS

### ⚠️ Risks in Offline Mode

1. **Stolen Device:**
   - Local database chứa user credentials
   - JWT tokens có thể bị extract
   
   **Mitigation:**
   - Encrypt local database
   - Device binding (PIN tied to device)
   - Auto-lock after inactivity
   - Remote wipe capability

2. **Cannot Revoke Access:**
   - User bị disable trên online system
   - Vẫn access được trong offline mode
   
   **Mitigation:**
   - Limited offline token expiry (30 days max)
   - Require re-auth khi online
   - Log all offline activities for audit

3. **Password Changes:**
   - User đổi password online
   - Offline mode vẫn dùng password cũ
   
   **Mitigation:**
   - Force sync khi online
   - Show warning về outdated credentials
   - Periodic re-authentication

### ✅ Security Best Practices

```python
# Encrypted local database
from cryptography.fernet import Fernet

def encrypt_local_database(db_path: str, encryption_key: str):
    """Encrypt local MongoDB database file"""
    # Implement full-disk encryption
    # Or encrypt sensitive collections only
    pass

# Auto-lock after inactivity
@app.middleware("http")
async def auto_lock_middleware(request: Request, call_next):
    """Lock system after 15 minutes of inactivity"""
    last_activity = request.session.get("last_activity")
    if last_activity:
        idle_time = time.time() - last_activity
        if idle_time > 900:  # 15 minutes
            # Force re-authentication
            raise HTTPException(401, "Session expired - re-authenticate")
    
    request.session["last_activity"] = time.time()
    return await call_next(request)

# Audit logging
async def log_offline_activity(user_id: str, action: str, details: dict):
    """Log all activities in offline mode for later audit"""
    await local_db.audit_log.insert_one({
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(),
        "mode": "offline",
        "synced": False
    })
```

---

## DEMO IMPLEMENTATION

Tôi có thể implement phương án hybrid này cho bạn với:

1. ✅ Local user database in company export
2. ✅ Offline authentication service
3. ✅ Extended JWT for fallback
4. ✅ Mode detection (online/offline)
5. ✅ UI indicator for offline mode
6. ✅ Sync service khi reconnect

**Timeline:** 4-5 ngày
**Complexity:** Medium-High

---

## CÂU HỎI CHO BẠN

1. **Security Level:**
   - Có cần PIN/Biometric authentication không?
   - Device binding có cần thiết không?

2. **Token Expiry:**
   - Offline token expiry bao lâu? (7, 15, 30 days?)
   - Có cần require re-auth định kỳ không?

3. **User Management:**
   - Có cho phép thêm/xóa users trong offline mode không?
   - Hay chỉ authentication với existing users?

4. **Encryption:**
   - Có cần encrypt local database không?
   - Encryption level: full-disk hay collection-based?

Bạn muốn tôi implement phương án nào? Hoặc cần giải thích thêm chi tiết nào không?
