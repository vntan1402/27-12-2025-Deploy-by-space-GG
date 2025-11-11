# Thông Tin Chi Tiết MongoDB - Nautical Records

## 📋 Tổng Quan

### **Environment: Development (Local)**
- **Connection URL:** `mongodb://localhost:27017/ship_management`
- **Host:** localhost
- **Port:** 27017
- **Database Name:** ship_management
- **Authentication:** No (localhost exception - full access)

---

## 🖥️ Server Information

| Thông tin | Giá trị |
|-----------|---------|
| **MongoDB Version** | 7.0.25 |
| **Git Version** | 96dce3da49b8d2e9e0d328048cb56930eb1bdb2b |
| **OpenSSL Version** | 3.0.2 (15 Mar 2022) |
| **Architecture** | 64-bit |
| **Max BSON Object Size** | 16.0 MB |
| **JavaScript Engine** | mozjs |
| **Memory Allocator** | tcmalloc |

---

## 📊 Database Statistics

| Metric | Value |
|--------|-------|
| **Database Name** | ship_management |
| **Total Collections** | 21 |
| **Total Indexes** | 36 |
| **Total Documents** | 326 |
| **Data Size** | 277.20 KB |
| **Storage Size** | 832.00 KB |
| **Index Size** | 1,212.00 KB |
| **Average Object Size** | 870.71 bytes |
| **Views** | 0 |

---

## 📁 Collections Detail

### **Core Collections**

#### 1. **users** (2 documents, 5 indexes)
- Lưu thông tin user accounts
- Indexes:
  - Primary key (id)
  - Username (unique)
  - Email (unique)
  - Role
  - Company

**Sample Structure:**
```json
{
  "id": "uuid",
  "username": "system_admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "password_hash": "$2b$12$...",
  "role": "system_admin",
  "department": ["technical", "operations"],
  "company": "company_uuid",
  "is_active": true,
  "created_at": "ISO date"
}
```

#### 2. **companies** (1 document, 3 indexes)
- Lưu thông tin công ty
- Indexes:
  - Primary key (id)
  - Name
  - Tax ID

**Sample Structure:**
```json
{
  "id": "uuid",
  "name": "Maritime Technology Development Co., Ltd.",
  "email": "company@example.com",
  "phone": "+84 123 456 789",
  "address": "Company address",
  "logo_url": "https://drive.google.com/...",
  "tax_id": "0123456789",
  "created_at": "ISO date",
  "updated_at": "ISO date"
}
```

#### 3. **ships** (4 documents, 3 indexes)
- Quản lý thông tin tàu
- Indexes: id, name, company

#### 4. **certificates** (17 documents, 3 indexes)
- Ship certificates (Class & Flag)
- Indexes: id, ship_id, company

#### 5. **crew_members** (7 documents, 1 index)
- Thông tin thuyền viên

#### 6. **crew_certificates** (14 documents, 1 index)
- Chứng chỉ của thuyền viên

---

### **Document Management Collections**

#### 7. **audit_certificates** (3 documents)
- Audit certificates

#### 8. **audit_reports** (11 documents)
- Audit reports và findings

#### 9. **test_reports** (6 documents)
- Test reports và kết quả

#### 10. **drawings_manuals** (4 documents)
- Technical drawings và manuals

#### 11. **survey_reports** (1 document)
- Survey reports

#### 12. **other_documents** (1 document)
- Other miscellaneous documents

#### 13. **approval_documents** (1 document)
- Approval documents

---

### **Configuration Collections**

#### 14. **ai_config** (1 document)
- AI configuration (OpenAI, models, etc.)

#### 15. **gdrive_config** (1 document)
- Google Drive configuration chung

#### 16. **company_gdrive_config** (1 document)
- Google Drive config theo company

#### 17. **system_settings** (1 document)
- System-wide settings (base fee, etc.)

#### 18. **certificate_abbreviation_mappings** (12 documents, 4 indexes)
- Mapping between certificate abbreviations and full names
- Indexes: id, abbreviation, issued_by, category

---

### **Audit & Tracking Collections**

#### 19. **audit_logs** (211 documents)
- System audit logs
- Track user actions, changes, etc.

#### 20. **usage_tracking** (29 documents, 3 indexes)
- AI usage tracking
- Indexes: id, date, company

#### 21. **other_audit_documents** (0 documents)
- Additional audit documents (empty)

---

## 🔌 Connection Status

| Metric | Value |
|--------|-------|
| **Status** | ✅ Connected |
| **Latency** | < 1ms (local) |
| **Connection Type** | Direct connection (no replica set) |
| **Read Preference** | Primary |
| **Write Concern** | Acknowledged |

---

## 👤 Authentication & Permissions

### **Local Development:**
- **Authentication:** None (localhost exception)
- **Permissions:** Full access (readWrite on all databases)
- **Security:** No password required for localhost

### **Production (Emergent Managed):**
- **Authentication:** Yes (managed by Emergent)
- **Connection String:** Provided via `MONGO_URL` environment variable
- **Permissions:** Controlled by Emergent platform
- **Security:** TLS/SSL enabled, username/password authentication

---

## 🔐 Security Considerations

### **Local Development:**
✅ **Advantages:**
- Fast development
- No authentication overhead
- Easy debugging

⚠️ **Considerations:**
- No authentication (OK for local dev)
- Accessible only from localhost
- Not exposed to network

### **Production:**
✅ **Security Features:**
- MongoDB user authentication
- TLS/SSL encryption
- Network isolation
- Managed by Emergent platform
- Regular backups

---

## 🔧 MongoDB Wrapper Usage

The application uses a custom MongoDB wrapper class: `MongoDatabase`

### **Key Methods:**

```python
# Connection
await mongo_db.connect()
await mongo_db.disconnect()

# CRUD Operations
await mongo_db.create('collection_name', data)
await mongo_db.find_one('collection_name', query)
await mongo_db.find_all('collection_name', query)
await mongo_db.update('collection_name', query, update_data)
await mongo_db.delete('collection_name', query)

# Counting
await mongo_db.count('collection_name', query)
```

### **Why Use Wrapper?**

1. **Consistency:** Same interface across all code
2. **Error Handling:** Centralized error management
3. **Logging:** Automatic query logging
4. **Permissions:** Handles permission issues gracefully
5. **Testing:** Easier to mock for unit tests

---

## 📈 Performance Metrics

### **Index Usage:**
- **Total Indexes:** 36
- **Index Size:** 1.2 MB
- **Collections with Multiple Indexes:** 7

### **Most Indexed Collections:**
1. users (5 indexes)
2. certificate_abbreviation_mappings (4 indexes)
3. certificates (3 indexes)
4. ships (3 indexes)
5. companies (3 indexes)
6. usage_tracking (3 indexes)

### **Optimization:**
- Proper indexes for frequently queried fields
- Compound indexes for complex queries
- Regular index maintenance

---

## 🔄 Backup & Recovery

### **Local Development:**
- Manual backups via `mongodump`
- No automatic backup (not needed for dev)

### **Production:**
- Managed by Emergent platform
- Automatic daily backups at 21:00 (9 PM)
- Google Drive integration for backup storage

**Backup Script Location:** `/app/backend/server.py` (auto_backup_to_google_drive)

---

## 🌐 Production vs Development

| Feature | Development (Local) | Production (Emergent) |
|---------|---------------------|----------------------|
| **Host** | localhost:27017 | Emergent managed host |
| **Authentication** | None | Username/Password |
| **SSL/TLS** | No | Yes |
| **Backup** | Manual | Automatic (daily) |
| **Monitoring** | None | Emergent platform |
| **Scaling** | Single instance | Managed by Emergent |
| **Permissions** | Full access | Controlled access |
| **Connection URL** | mongodb://localhost:27017/ship_management | mongodb://[managed-host]/ship_management |

---

## 🚨 Known Issues & Solutions

### **Issue 1: Direct insert_one() in Production**

**Problem:**
```python
db = mongo_db.client['ship_management']
await db['collection'].insert_one(data)  # ❌ Permission error
```

**Solution:**
```python
await mongo_db.create('collection', data)  # ✅ Use wrapper
```

### **Issue 2: DateTime Serialization**

**Problem:** MongoDB doesn't directly serialize Python datetime objects to JSON

**Solution:**
```python
# Convert to ISO string before storing
data['created_at'] = datetime.now().isoformat()
```

### **Issue 3: ObjectId vs UUID**

**Problem:** MongoDB default `_id` is ObjectId (not JSON serializable)

**Solution:**
- Use custom UUID `id` field
- Ignore `_id` field in responses
- Configure Pydantic models to exclude `_id`

---

## 📝 Connection String Formats

### **Local Development:**
```
mongodb://localhost:27017/ship_management
```

### **Production (Example):**
```
mongodb://username:password@host:port/ship_management?authSource=admin&ssl=true
```

### **MongoDB Atlas (Cloud):**
```
mongodb+srv://username:password@cluster.mongodb.net/ship_management?retryWrites=true&w=majority
```

---

## 🔍 Debugging Commands

### **Check Connection:**
```python
await mongo_db.client.admin.command('ping')
```

### **Get Database Stats:**
```python
stats = await mongo_db.client['ship_management'].command('dbStats')
```

### **List Collections:**
```python
collections = await mongo_db.client['ship_management'].list_collection_names()
```

### **Count Documents:**
```python
count = await mongo_db.client['ship_management']['users'].count_documents({})
```

---

## 📞 Support

### **MongoDB Issues in Production:**
- Contact: Emergent Support
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

### **Local Development Issues:**
- Check MongoDB service: `sudo systemctl status mongod`
- View logs: `sudo tail -f /var/log/mongodb/mongod.log`
- Restart: `sudo systemctl restart mongod`

---

## ✅ Health Check

**To verify MongoDB is working:**

```bash
# 1. Check if service is running
sudo systemctl status mongod

# 2. Check connection via Python
cd /app/backend && python3 -c "
import asyncio
from mongodb_database import MongoDatabase
async def test():
    db = MongoDatabase()
    await db.connect()
    print('✅ MongoDB connected successfully')
    await db.disconnect()
asyncio.run(test())
"

# 3. Check via API
curl http://localhost:8001/api/admin/status
```

---

## 📊 Summary

- **Version:** MongoDB 7.0.25
- **Database:** ship_management
- **Collections:** 21 active collections
- **Total Documents:** 326
- **Storage:** ~2 MB (data + indexes)
- **Performance:** Excellent (local, < 1ms latency)
- **Security:** Development (no auth), Production (managed)
- **Backup:** Automatic daily backup to Google Drive

The MongoDB setup is optimized for the maritime document management application with proper indexing, efficient storage, and scalable architecture ready for production deployment.
