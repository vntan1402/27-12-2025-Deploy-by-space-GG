# 🚀 MIGRATION QUICK START GUIDE

**Đây là guide nhanh để bắt đầu migration. Xem BACKEND_MIGRATION_PLAN.md cho chi tiết đầy đủ.**

---

## ⚡ QUICK COMMANDS

### 1. Backup Backend (2 phút)
```bash
cd /app
sudo supervisorctl stop backend
mv backend backend-v1
git add -A
git commit -m "Backup: Renamed backend to backend-v1"
```

### 2. Create New Structure (5 phút)
```bash
cd /app
mkdir -p backend/app/{core,models,api/v1,services,repositories,db,utils}
mkdir -p backend/{migrations,scripts,tests}
touch backend/app/{__init__.py,main.py}
touch backend/app/core/{__init__.py,config.py,security.py}
touch backend/app/models/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/services/__init__.py
touch backend/app/repositories/__init__.py
touch backend/app/db/{__init__.py,mongodb.py}
touch backend/app/utils/__init__.py
```

### 3. Copy Essential Files (2 phút)
```bash
# Copy environment and dependencies
cp backend-v1/.env backend/.env
cp backend-v1/requirements.txt backend/requirements.txt
echo "pydantic-settings>=2.0.0" >> backend/requirements.txt

# Copy database module
cp backend-v1/mongodb_database.py backend/app/db/mongodb.py

# Install dependencies
cd /app/backend
pip install -r requirements.txt
```

### 4. Test Basic Setup (1 phút)
```bash
cd /app/backend
python -c "from app.db.mongodb import mongo_db; print('✅ Import successful')"
```

---

## 📝 FILES TO CREATE FIRST

### Priority 1: Core Infrastructure

#### `backend/app/main.py`
- FastAPI app initialization
- CORS middleware
- Database connection
- Router inclusion
- ~100 lines

#### `backend/app/core/config.py`
- Environment variables
- Settings class
- ~50 lines

#### `backend/app/core/security.py`
- JWT functions
- Password hashing
- get_current_user dependency
- ~100 lines

#### `backend/app/db/mongodb.py`
- Copy from backend-v1/mongodb_database.py
- Update imports only

### Priority 2: Authentication

#### `backend/app/models/user.py`
- UserRole enum
- User models (Base, Create, Update, Response)
- Login models
- ~100 lines

#### `backend/app/repositories/user_repository.py`
- Data access functions
- ~80 lines

#### `backend/app/services/user_service.py`
- Business logic
- Authentication
- User CRUD
- ~150 lines

#### `backend/app/api/v1/auth.py`
- Login endpoint
- Verify token endpoint
- ~50 lines

#### `backend/app/api/v1/users.py`
- Users CRUD endpoints
- ~100 lines

---

## 🔄 DEVELOPMENT WORKFLOW

### For Each Module:

```
1. Create Models (models/*.py)
   ↓
2. Create Repository (repositories/*_repository.py)
   ↓
3. Create Service (services/*_service.py)
   ↓
4. Create API Routes (api/v1/*.py)
   ↓
5. Update api/v1/__init__.py to include router
   ↓
6. Test with curl or backend testing agent
   ↓
7. Git commit
```

### Example for Ships Module:

```bash
# 1. Create model
nano backend/app/models/ship.py
# Copy ShipBase, ShipCreate, ShipUpdate, ShipResponse from backend-v1

# 2. Create repository
nano backend/app/repositories/ship_repository.py
# Create ShipRepository class with CRUD methods

# 3. Create service
nano backend/app/services/ship_service.py
# Create ShipService class with business logic

# 4. Create API routes
nano backend/app/api/v1/ships.py
# Create router with endpoints

# 5. Register router
nano backend/app/api/v1/__init__.py
# Add: api_router.include_router(ships.router, prefix="/ships", tags=["ships"])

# 6. Test
sudo supervisorctl restart backend
curl http://localhost:8001/api/ships

# 7. Commit
git add -A
git commit -m "Added ships module"
```

---

## 🧪 TESTING COMMANDS

### Health Check
```bash
curl http://localhost:8001/health
```

### Test Login
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

### Test Protected Endpoint
```bash
TOKEN="your_jwt_token"
curl http://localhost:8001/api/users \
  -H "Authorization: Bearer $TOKEN"
```

### Check Logs
```bash
sudo supervisorctl tail -f backend
sudo supervisorctl tail -f backend stderr
```

### Restart Backend
```bash
sudo supervisorctl restart backend
```

---

## 🔧 SUPERVISOR CONFIG

### Update: `/etc/supervisor/conf.d/backend.conf`

```ini
[program:backend]
command=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
user=root
environment=PYTHONUNBUFFERED="1"
```

### Apply changes:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart backend
```

---

## 📊 PROGRESS TRACKING

### Daily checklist:

#### Day 1:
- [ ] Phase 0: Backup complete
- [ ] Phase 1: Infrastructure setup
- [ ] Phase 2: Auth working
- [ ] Login tested successfully

#### Day 2-3:
- [ ] Phase 3: Company management
- [ ] Phase 4: Ships basic CRUD
- [ ] Testing with backend agent

#### Day 4-7:
- [ ] Phase 4: Complete ship features
- [ ] Phase 5: Certificates basic
- [ ] Phase 5: AI analysis working

#### Week 2:
- [ ] Phase 5: Complete certificates
- [ ] Phase 6: Crew management
- [ ] Phase 7: GDrive integration

#### Week 3:
- [ ] Phase 7: System settings
- [ ] Phase 8: Comprehensive testing
- [ ] Frontend integration verified

#### Week 4:
- [ ] Phase 9: Documentation
- [ ] Performance optimization
- [ ] Delete backend-v1

---

## 🆘 TROUBLESHOOTING

### Backend won't start
```bash
# Check logs
sudo supervisorctl tail -f backend stderr

# Common issues:
# - Import errors: Check file paths and __init__.py files
# - Syntax errors: Run python -m py_compile app/main.py
# - Port conflict: Check if port 8001 is free
```

### Import errors
```bash
# Verify Python path
cd /app/backend
python -c "import sys; print(sys.path)"

# Test imports individually
python -c "from app.core.config import settings"
python -c "from app.db.mongodb import mongo_db"
```

### Database connection fails
```bash
# Verify MONGO_URL
cd /app/backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('MONGO_URL'))"

# Test connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; import os; from dotenv import load_dotenv; load_dotenv(); asyncio.run(AsyncIOMotorClient(os.getenv('MONGO_URL')).admin.command('ismaster')); print('✅ Connected')"
```

---

## 🎯 MILESTONE GOALS

### Milestone 1: Auth Working (Day 1)
- Backend starts without errors
- Can login and get token
- Can access protected endpoints

### Milestone 2: Core CRUD (Day 3)
- Users, Companies, Ships basic operations work
- Frontend can communicate with backend

### Milestone 3: AI Features (Week 1)
- Certificate AI analysis works
- File uploads work
- OCR processing works

### Milestone 4: Complete Features (Week 2)
- All modules migrated
- All endpoints working
- GDrive integration works

### Milestone 5: Production Ready (Week 3-4)
- All tests passing
- Performance verified
- Documentation complete
- backend-v1 deleted

---

## 📞 WHEN TO ASK FOR HELP

Ask user if:
- [ ] Database schema needs changes
- [ ] API contract needs to change
- [ ] Stuck on complex business logic
- [ ] Need clarification on requirements
- [ ] Testing reveals major issues

Use troubleshoot_agent if:
- [ ] Service won't start after 3 attempts
- [ ] Import errors persist
- [ ] Database connection issues
- [ ] Performance degradation

---

## 🔄 ROLLBACK PLAN

If things go wrong:

### Quick Rollback (2 minutes):
```bash
sudo supervisorctl stop backend
cd /app
rm -rf backend
mv backend-v1 backend
sudo nano /etc/supervisor/conf.d/backend.conf
# Change: directory=/app/backend
# Change: command to old format
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl restart backend
```

### Verify rollback:
```bash
curl http://localhost:8001/api/auth/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass"}'
```

---

## ✅ SUCCESS CRITERIA

### Phase 1 Success:
- ✅ Backend starts without errors
- ✅ Health check returns 200
- ✅ Can import all core modules

### Phase 2 Success:
- ✅ Can login successfully
- ✅ Token verification works
- ✅ Get users endpoint works

### Final Success:
- ✅ All 179 endpoints migrated
- ✅ All tests passing
- ✅ Frontend working perfectly
- ✅ Production stable for 1 week
- ✅ backend-v1 deleted

---

**Ready to start? Begin with Phase 0 in BACKEND_MIGRATION_PLAN.md**

**Next step:** 
```bash
cd /app
sudo supervisorctl stop backend
mv backend backend-v1
```
