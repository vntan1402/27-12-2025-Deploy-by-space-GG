# MongoDB Summary - Nautical Records Application

## 🎯 Quick Overview

### **Current Setup (Development)**
```
Host:       localhost:27017
Database:   ship_management
Version:    MongoDB 7.0.25
Auth:       No (localhost exception)
Status:     ✅ Connected & Running
```

### **Production Setup (Emergent Managed)**
```
Host:       Managed by Emergent Platform
Database:   ship_management
Auth:       Yes (username/password)
SSL:        Enabled
Status:     Managed & Monitored
```

---

## 📊 Database Statistics

| Metric | Value |
|--------|-------|
| Collections | 21 |
| Documents | 326 |
| Indexes | 36 |
| Data Size | 277 KB |
| Storage Size | 832 KB |
| Index Size | 1.2 MB |

---

## 🗂️ Main Collections

### **Core Data (8 collections)**
- `users` (2) - User accounts với roles
- `companies` (1) - Company information
- `ships` (4) - Vessel details
- `certificates` (17) - Ship certificates
- `crew_members` (7) - Crew information
- `crew_certificates` (14) - Crew certifications
- `audit_certificates` (3) - Audit certs
- `audit_reports` (11) - Audit findings

### **Document Management (6 collections)**
- `test_reports` (6)
- `drawings_manuals` (4)
- `survey_reports` (1)
- `approval_documents` (1)
- `other_documents` (1)
- `other_audit_documents` (0)

### **Configuration (4 collections)**
- `ai_config` (1) - AI settings
- `gdrive_config` (1) - Google Drive config
- `company_gdrive_config` (1) - Per-company Drive
- `system_settings` (1) - Base fee, etc.

### **Tracking (2 collections)**
- `audit_logs` (211) - Activity logs
- `usage_tracking` (29) - AI usage stats

### **Mappings (1 collection)**
- `certificate_abbreviation_mappings` (12) - Cert name mappings

---

## 🔌 Connection Details

### **Connection String Format:**

**Development:**
```
mongodb://localhost:27017/ship_management
```

**Production (Typical):**
```
mongodb://username:password@host:port/ship_management?authSource=admin
```

### **Environment Variable:**
```bash
MONGO_URL=mongodb://localhost:27017/ship_management
```

---

## 🛠️ MongoDatabase Wrapper Class

### **Location:** `/app/backend/mongodb_database.py`

### **Main Features:**
- ✅ Async/await support (Motor driver)
- ✅ Auto-indexing on startup
- ✅ Error handling & logging
- ✅ Timezone-aware timestamps
- ✅ Connection pooling
- ✅ CRUD operations wrapper

### **Key Methods:**
```python
# Connection
await mongo_db.connect()
await mongo_db.disconnect()

# CRUD
await mongo_db.create(collection, data)
await mongo_db.find_one(collection, query)
await mongo_db.find_all(collection, query)
await mongo_db.update(collection, query, data)
await mongo_db.delete(collection, query)
await mongo_db.count(collection, query)
```

---

## 🔐 Authentication & Security

### **Development:**
- No authentication (localhost exception)
- Full read/write access
- Not exposed to network
- Safe for local development

### **Production:**
- Username/password authentication
- TLS/SSL encryption
- Network isolation
- Managed by Emergent
- Regular security updates

---

## 🚨 Common Issues & Solutions

### **1. Permission Error in Production**

**Error:**
```
"not authorized on ship_management to execute command { insert: 'collection' }"
```

**Cause:** Using direct MongoDB operations instead of wrapper

**Solution:**
```python
# ❌ Don't do this
db['collection'].insert_one(data)

# ✅ Do this
await mongo_db.create('collection', data)
```

### **2. Connection Timeout**

**Solution:**
- Check `MONGO_URL` environment variable
- Verify MongoDB service is running
- Check network connectivity

### **3. Duplicate Key Error**

**Cause:** Trying to insert document with existing unique field

**Solution:**
- Check unique indexes (username, email, tax_id, etc.)
- Use `update` instead of `create` for existing documents

---

## 📈 Performance Optimization

### **Indexes Created:**

**users (5 indexes):**
- username (unique)
- email (unique, sparse)
- role + is_active (compound)
- company

**companies (2 indexes):**
- tax_id (unique)
- name_en + name_vn (compound)

**ships (2 indexes):**
- imo + company (unique compound)
- name

**certificates (2 indexes):**
- ship_id + type (compound)
- expiry_date

**certificate_abbreviation_mappings (3 indexes):**
- cert_name (unique)
- created_by
- usage_count (descending)

**usage_tracking (2 indexes):**
- timestamp (descending)
- user_id

---

## 🔄 Backup & Recovery

### **Development:**
Manual backup:
```bash
mongodump --db=ship_management --out=/backup/$(date +%Y%m%d)
```

Restore:
```bash
mongorestore --db=ship_management /backup/20250111/ship_management
```

### **Production:**
- ✅ Automatic daily backup at 21:00 (9 PM)
- ✅ Backup to Google Drive
- ✅ Managed by Emergent platform
- ✅ Point-in-time recovery available

---

## 🔍 Monitoring & Debugging

### **Check Connection:**
```bash
curl http://localhost:8001/api/admin/status
```

### **Check Database Stats:**
```python
cd /app/backend && python3 << EOF
import asyncio
from mongodb_database import MongoDatabase
async def stats():
    db = MongoDatabase()
    await db.connect()
    stats = await db.client['ship_management'].command('dbStats')
    print(f"Collections: {stats['collections']}")
    print(f"Objects: {stats['objects']}")
    print(f"Data Size: {stats['dataSize']/1024:.2f} KB")
    await db.disconnect()
asyncio.run(stats())
EOF
```

### **View Logs:**
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log | grep -i mongo

# MongoDB service logs (if applicable)
sudo tail -f /var/log/mongodb/mongod.log
```

---

## 📝 Key Differences: Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Host** | localhost:27017 | Emergent managed |
| **Auth** | None | Username/Password |
| **SSL** | No | Yes |
| **Backup** | Manual | Automatic |
| **Monitoring** | None | Platform-managed |
| **Permissions** | Full | Controlled |
| **Connection** | Direct | Connection pool |
| **Latency** | < 1ms | 5-20ms (network) |

---

## ✅ Health Check Checklist

- [ ] MongoDB service running
- [ ] Connection successful
- [ ] All 21 collections present
- [ ] Indexes created (36 total)
- [ ] Users collection has data (2+ users)
- [ ] Companies collection has data (1+ companies)
- [ ] Backup job scheduled (production)
- [ ] No permission errors in logs

---

## 🎓 Best Practices

### **1. Always Use Wrapper Methods**
```python
# ✅ Good
await mongo_db.create('users', user_data)

# ❌ Avoid
await db['users'].insert_one(user_data)
```

### **2. Use Timezone-Aware Datetimes**
```python
# ✅ Good
from datetime import datetime, timezone
data['created_at'] = datetime.now(timezone.utc)

# ❌ Avoid
data['created_at'] = datetime.now()  # naive datetime
```

### **3. Handle Duplicate Key Errors**
```python
try:
    await mongo_db.create('users', user_data)
except Exception as e:
    if "duplicate" in str(e).lower():
        # Handle duplicate user
        pass
```

### **4. Use Proper Indexes**
- Index frequently queried fields
- Use compound indexes for multi-field queries
- Mark unique fields as unique indexes
- Use sparse indexes for optional unique fields

---

## 📞 Support & Resources

### **MongoDB Issues:**
- **Emergent Support:** support@emergent.sh
- **Discord:** https://discord.gg/VzKfwCXC4A

### **MongoDB Documentation:**
- **Official Docs:** https://docs.mongodb.com/
- **Motor (Async):** https://motor.readthedocs.io/
- **PyMongo:** https://pymongo.readthedocs.io/

---

## 🎉 Summary

The Nautical Records application uses **MongoDB 7.0.25** as its primary database, managing:
- ✅ 21 collections for various document types
- ✅ 326 total documents with proper indexing
- ✅ Custom async wrapper for consistent operations
- ✅ Automatic backups and monitoring in production
- ✅ Optimized for maritime document management

**Status:** Fully functional and production-ready! 🚀
