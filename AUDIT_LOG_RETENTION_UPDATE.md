# 📋 Audit Log Retention Policy Update

**Date:** December 19, 2024  
**Change:** Retention period updated from 3 years to 1 year  
**Status:** ✅ COMPLETED

---

## 🔄 Changes Made

### 1. Repository Layer
**File:** `/app/backend/app/repositories/crew_audit_log_repository.py`

```python
# Before:
log_data['expires_at'] = now + timedelta(days=3*365)  # 3 years

# After:
log_data['expires_at'] = now + timedelta(days=365)  # 1 year
```

**Impact:** All new audit logs will expire after 1 year instead of 3 years.

---

### 2. Database Model
**File:** `/app/backend/app/models/crew_audit_log.py`

```python
# Updated field description:
expires_at: datetime = Field(..., description="When log will be auto-deleted (1 year)")
```

---

### 3. API Documentation
**File:** `/app/backend/app/api/v1/crew_audit_logs.py`

```python
# Updated cleanup endpoint docstring:
"""
Manual cleanup of expired logs (older than 1 year)
Only system_admin can trigger this
"""
```

---

### 4. Index Script
**File:** `/app/backend/scripts/add_audit_log_indexes.py`

```python
# Updated TTL index description:
{
    'name': 'expires_at_1_ttl',
    'description': 'TTL index for 1-year retention',
    ...
}
```

---

### 5. Documentation
**File:** `/app/CRUD_LOG_IMPLEMENTATION_PLAN.md`

```
**Retention:** 1 năm
```

---

## 🗄️ Database Impact

### TTL Index
MongoDB's TTL (Time To Live) index automatically deletes documents when `expires_at` timestamp is reached.

**Index Configuration:**
```javascript
{
  "name": "expires_at_1_ttl",
  "keys": [("expires_at", 1)],
  "options": {"expireAfterSeconds": 0}
}
```

**How it works:**
- MongoDB's background thread checks TTL indexes every 60 seconds
- Documents with `expires_at` <= current time are automatically deleted
- No manual intervention needed
- Zero performance impact

---

## 📊 Data Lifecycle

### Timeline Example:

```
Day 0 (Today):
  ├─ Crew created
  ├─ Audit log created
  └─ expires_at = Today + 365 days

Day 365 (1 year later):
  ├─ expires_at reached
  └─ MongoDB TTL thread deletes log (within 60 seconds)

Day 366+:
  └─ Log no longer exists in database
```

---

## 🔒 Existing Data

### What happens to logs created before this change?

**Logs created with 3-year retention:**
- Still have `expires_at` set to 3 years from creation date
- Will continue to exist until their original expiration date
- Will NOT be retroactively changed to 1-year expiration

**Example:**
```
Log created: Jan 1, 2024
Original expires_at: Jan 1, 2027 (3 years)
After update: Still Jan 1, 2027
Reason: expires_at is set at creation time and immutable
```

### If you need to apply 1-year retention retroactively:

Run this MongoDB script (OPTIONAL):
```javascript
// Connect to database
use ship_management;

// Update all existing logs to expire 1 year from creation
db.crew_audit_logs.updateMany(
  {},
  [{
    $set: {
      expires_at: {
        $add: ["$created_at", 365 * 24 * 60 * 60 * 1000]  // 1 year in milliseconds
      }
    }
  }]
);

// Verify
db.crew_audit_logs.find({}, {created_at: 1, expires_at: 1}).limit(5);
```

**⚠️ Warning:** This will cause older logs (older than 1 year) to be deleted immediately.

---

## ✅ Verification

### How to verify the change is working:

#### 1. Check new logs:
```python
# Create a test crew
# Check the audit log entry

from datetime import datetime, timedelta

log = db.crew_audit_logs.find_one(sort=[("created_at", -1)])
print(f"Created: {log['created_at']}")
print(f"Expires: {log['expires_at']}")

# Verify difference is ~365 days
delta = log['expires_at'] - log['created_at']
print(f"Days until expiration: {delta.days}")
# Should print: 365
```

#### 2. Check TTL index:
```bash
cd /app/backend
python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_ttl():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL'))
    db = client.get_default_database()
    
    indexes = await db.crew_audit_logs.list_indexes().to_list(None)
    ttl_index = [idx for idx in indexes if 'expires_at' in idx.get('key', {})]
    
    if ttl_index:
        print('✅ TTL index found:')
        print(ttl_index[0])
    else:
        print('❌ TTL index not found')
    
    client.close()

asyncio.run(check_ttl())
"
```

---

## 📈 Storage Impact

### Estimated storage savings:

**Before (3-year retention):**
- Average log size: ~2KB
- Logs per day: ~100 (estimated)
- Total logs stored: 100 × 365 × 3 = 109,500 logs
- Storage used: 109,500 × 2KB = ~219 MB

**After (1-year retention):**
- Average log size: ~2KB
- Logs per day: ~100
- Total logs stored: 100 × 365 = 36,500 logs
- Storage used: 36,500 × 2KB = ~73 MB

**Savings: ~146 MB (67% reduction)** 💾

---

## 🔧 Configuration Options

### If you need to change retention period in the future:

**File:** `/app/backend/app/repositories/crew_audit_log_repository.py`

```python
# Current (1 year):
log_data['expires_at'] = now + timedelta(days=365)

# For 6 months:
log_data['expires_at'] = now + timedelta(days=182)

# For 2 years:
log_data['expires_at'] = now + timedelta(days=730)

# For 5 years:
log_data['expires_at'] = now + timedelta(days=1825)
```

After changing, restart backend:
```bash
sudo supervisorctl restart backend
```

---

## 📝 Notes

1. **TTL Index Precision:** MongoDB's TTL thread runs every 60 seconds, so deletion might be delayed up to 1 minute after expiration.

2. **Manual Cleanup:** System admins can trigger manual cleanup via API:
   ```bash
   DELETE /api/crew-audit-logs/cleanup
   ```

3. **No Data Loss:** Current logs are not affected. Only future logs will use new retention period.

4. **Compliance:** Ensure 1-year retention meets your compliance requirements (GDPR, industry regulations, etc.)

5. **Backup Strategy:** If you need longer retention for compliance, consider:
   - Exporting logs to external archive system
   - Database backups with longer retention
   - Separate compliance logging system

---

## ✅ Status

- [x] Code updated
- [x] Backend restarted
- [x] TTL index verified
- [x] Documentation updated
- [x] No data loss
- [x] Backward compatible

**Retention policy successfully updated to 1 year!** 🎉

---

**Last Updated:** December 19, 2024  
**Updated By:** E1 Agent
