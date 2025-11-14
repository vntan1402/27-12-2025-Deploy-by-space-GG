# Phân Tích Cấu Trúc Database & Đề Xuất Multi-Company Architecture

## 1. CẤU TRÚC DATABASE HIỆN TẠI

### 1.1. Kiến trúc Single Database (Multi-Tenant)
```
MongoDB Atlas
└── ship_management (database)
    ├── users (collection)
    │   ├── id
    │   ├── username
    │   ├── company (company_id - UUID)
    │   ├── role
    │   └── ...
    │
    ├── companies (collection)
    │   ├── id (UUID)
    │   ├── name_en
    │   ├── name_vn
    │   ├── tax_id
    │   └── ...
    │
    ├── ships (collection)
    │   ├── id (UUID)
    │   ├── company (company_id - UUID)
    │   ├── name
    │   ├── imo
    │   └── ...
    │
    ├── certificates (collection)
    │   ├── id (UUID)
    │   ├── ship_id
    │   ├── company_id
    │   └── ...
    │
    ├── crew_members (collection)
    │   ├── id (UUID)
    │   ├── company_id
    │   ├── ship_sign_on
    │   └── ...
    │
    ├── crew_certificates (collection)
    │   ├── id (UUID)
    │   ├── company_id
    │   ├── ship_id (nullable)
    │   └── ...
    │
    ├── audit_certificates (collection)
    ├── survey_reports (collection)
    ├── test_reports (collection)
    ├── drawings_manuals (collection)
    ├── approval_documents (collection)
    └── ...
```

### 1.2. Đặc điểm Hiện Tại
✅ **Ưu điểm:**
- Dễ quản lý: 1 database duy nhất
- Backup đơn giản: Backup toàn bộ database
- Cost-effective: Chia sẻ resources
- Cross-company queries dễ dàng (cho system admin)

❌ **Nhược điểm:**
- Không thể tách riêng database cho từng company
- Không hỗ trợ offline mode
- Data isolation không hoàn toàn
- Khó scale cho một company cụ thể

---

## 2. PHƯƠNG ÁN 1: DATABASE PER COMPANY (Recommended)

### 2.1. Kiến Trúc Mới
```
MongoDB Atlas
├── ship_management_master (Main Database)
│   ├── companies (Company registry)
│   │   ├── id (UUID)
│   │   ├── name_en
│   │   ├── database_name (e.g., "company_amcsc")
│   │   └── ...
│   │
│   └── system_settings (Global settings)
│       └── ...
│
├── company_amcsc (Company-specific DB)
│   ├── users
│   ├── ships
│   ├── certificates
│   ├── crew_members
│   ├── crew_certificates
│   └── ...
│
├── company_vosco (Company-specific DB)
│   ├── users
│   ├── ships
│   ├── certificates
│   └── ...
│
└── company_xyz (Company-specific DB)
    └── ...
```

### 2.2. Lợi Ích
✅ **Data Isolation:** Mỗi company có database riêng biệt hoàn toàn
✅ **Offline Support:** Có thể export/import database cho từng company
✅ **Scalability:** Scale độc lập cho từng company
✅ **Security:** Tăng cường bảo mật, data không bị mix
✅ **Backup/Restore:** Backup và restore theo từng company
✅ **Performance:** Queries nhanh hơn (không cần filter company_id)

### 2.3. Implementation Plan

#### Step 1: Tạo Master Database
```python
# mongodb_multi_tenant.py
class MultiTenantDatabase:
    def __init__(self):
        self.master_db = None  # ship_management_master
        self.company_dbs = {}   # Cache company databases
        
    async def get_company_database(self, company_id: str):
        """Get or create company-specific database"""
        if company_id in self.company_dbs:
            return self.company_dbs[company_id]
            
        # Get company info from master DB
        company = await self.master_db.companies.find_one({"id": company_id})
        if not company:
            raise Exception("Company not found")
            
        # Get company database name
        db_name = company.get("database_name", f"company_{company_id[:8]}")
        
        # Connect to company database
        company_db = self.client[db_name]
        self.company_dbs[company_id] = company_db
        
        return company_db
```

#### Step 2: Migrate Existing Data
```python
# migration_script.py
async def migrate_to_multi_tenant():
    """Migrate from single DB to multi-tenant architecture"""
    
    # 1. Get all companies
    companies = await old_db.companies.find().to_list(None)
    
    for company in companies:
        company_id = company["id"]
        db_name = f"company_{company_id[:8]}"
        
        print(f"Migrating {company['name_en']} to {db_name}...")
        
        # 2. Create company database
        company_db = client[db_name]
        
        # 3. Migrate users
        users = await old_db.users.find({"company": company_id}).to_list(None)
        if users:
            await company_db.users.insert_many(users)
            
        # 4. Migrate ships
        ships = await old_db.ships.find({"company": company_id}).to_list(None)
        if ships:
            await company_db.ships.insert_many(ships)
            
        # 5. Migrate certificates
        ship_ids = [s["id"] for s in ships]
        certificates = await old_db.certificates.find({
            "ship_id": {"$in": ship_ids}
        }).to_list(None)
        if certificates:
            await company_db.certificates.insert_many(certificates)
            
        # 6. Migrate crew members
        crew = await old_db.crew_members.find({"company_id": company_id}).to_list(None)
        if crew:
            await company_db.crew_members.insert_many(crew)
            
        # 7. Migrate all other collections...
        # crew_certificates, audit_certificates, survey_reports, etc.
        
        print(f"✅ Migrated {company['name_en']} successfully")
```

#### Step 3: Update Backend Code
```python
# server.py
@app.get("/api/ships")
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    # Get company database
    company_db = await multi_tenant_db.get_company_database(current_user.company)
    
    # Query ships (no need to filter by company_id anymore!)
    ships = await company_db.ships.find().to_list(None)
    
    return ships
```

---

## 3. PHƯƠNG ÁN 2: OFFLINE MODE SUPPORT

### 3.1. Export Database cho Company
```python
# export_company_db.py
@app.get("/api/admin/export-database")
async def export_company_database(
    company_id: str,
    current_user: UserResponse = Depends(check_permission([UserRole.SUPER_ADMIN]))
):
    """Export entire company database for offline use"""
    
    company_db = await multi_tenant_db.get_company_database(company_id)
    
    export_data = {
        "company_id": company_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "collections": {}
    }
    
    # Export all collections
    collections = [
        "users", "ships", "certificates", 
        "crew_members", "crew_certificates",
        "audit_certificates", "survey_reports",
        "test_reports", "drawings_manuals",
        "approval_documents"
    ]
    
    for collection_name in collections:
        documents = await company_db[collection_name].find().to_list(None)
        
        # Convert ObjectId and datetime to string
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            # Convert datetime fields...
        
        export_data["collections"][collection_name] = documents
    
    # Create ZIP file
    import zipfile
    import json
    
    filename = f"company_{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    filepath = f"/tmp/{filename}"
    
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add database JSON
        zipf.writestr(
            "database.json", 
            json.dumps(export_data, indent=2, ensure_ascii=False)
        )
        
        # Add metadata
        zipf.writestr(
            "metadata.json",
            json.dumps({
                "company_id": company_id,
                "exported_at": export_data["exported_at"],
                "version": "1.0",
                "total_documents": sum(len(docs) for docs in export_data["collections"].values())
            }, indent=2)
        )
    
    # Return file for download
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/zip"
    )
```

### 3.2. Import Database (Restore)
```python
@app.post("/api/admin/import-database")
async def import_company_database(
    file: UploadFile,
    current_user: UserResponse = Depends(check_permission([UserRole.SUPER_ADMIN]))
):
    """Import/restore company database from backup"""
    
    # Extract ZIP
    import zipfile
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = f"{tmpdir}/upload.zip"
        
        # Save uploaded file
        with open(zip_path, "wb") as f:
            f.write(await file.read())
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(tmpdir)
        
        # Read database.json
        with open(f"{tmpdir}/database.json", "r") as f:
            import_data = json.load(f)
        
        company_id = import_data["company_id"]
        company_db = await multi_tenant_db.get_company_database(company_id)
        
        # Import all collections
        for collection_name, documents in import_data["collections"].items():
            if documents:
                # Clear existing data (optional)
                # await company_db[collection_name].delete_many({})
                
                # Insert documents
                await company_db[collection_name].insert_many(documents)
        
        return {
            "success": True,
            "message": f"Imported {len(import_data['collections'])} collections",
            "company_id": company_id
        }
```

### 3.3. Offline Mode Architecture
```
┌─────────────────────────────────────────┐
│         ONLINE MODE                     │
│  ┌─────────────────────────────────┐   │
│  │   Frontend (React)              │   │
│  │   ↓                              │   │
│  │   Backend (FastAPI)             │   │
│  │   ↓                              │   │
│  │   MongoDB Atlas (Cloud)         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         OFFLINE MODE                    │
│  ┌─────────────────────────────────┐   │
│  │   Frontend (React)              │   │
│  │   ↓                              │   │
│  │   Backend (FastAPI)             │   │
│  │   ↓                              │   │
│  │   MongoDB Local (Docker)        │   │
│  │   (Imported company DB)         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 4. PHƯƠNG ÁN 3: HYBRID APPROACH (Best of Both Worlds)

### 4.1. Architecture
- **Master Database:** Quản lý companies, system settings
- **Company Databases:** Mỗi company có database riêng
- **Sync Service:** Đồng bộ online ↔ offline
- **Conflict Resolution:** Xử lý conflicts khi sync

### 4.2. Features
✅ Multi-database support
✅ Offline mode with local MongoDB
✅ Auto-sync when online
✅ Conflict detection & resolution
✅ Export/Import database
✅ Incremental backup

---

## 5. IMPLEMENTATION ROADMAP

### Phase 1: Preparation (1-2 days)
- [ ] Backup toàn bộ database hiện tại
- [ ] Tạo master database structure
- [ ] Test migration script trên development

### Phase 2: Migration (2-3 days)
- [ ] Chạy migration script để tách database
- [ ] Verify data integrity sau migration
- [ ] Update backend code để sử dụng multi-tenant DB
- [ ] Test all APIs với multi-database

### Phase 3: Export/Import Feature (2-3 days)
- [ ] Implement export endpoint
- [ ] Implement import endpoint
- [ ] Tạo UI cho export/import
- [ ] Test offline mode

### Phase 4: Testing & Deployment (2-3 days)
- [ ] Full system testing
- [ ] Performance testing
- [ ] Security audit
- [ ] Production deployment

### Phase 5: Offline Mode Setup (Optional, 3-5 days)
- [ ] Docker compose với MongoDB local
- [ ] Sync service implementation
- [ ] Conflict resolution logic
- [ ] Desktop app packaging (Electron)

---

## 6. CHI PHÍ & LỢI ÍCH

### Chi phí
- **Development:** 1-2 tuần
- **MongoDB Storage:** Có thể tăng (mỗi DB có overhead)
- **Maintenance:** Cần monitoring nhiều databases

### Lợi ích
- **Data isolation:** 100% tách biệt
- **Offline capability:** Làm việc không cần internet
- **Scalability:** Dễ scale cho từng company
- **Security:** Bảo mật tốt hơn
- **Performance:** Queries nhanh hơn

---

## 7. KẾT LUẬN & KHUYẾN NGHỊ

### Khuyến nghị: PHƯƠNG ÁN 1 + PHƯƠNG ÁN 2 (Hybrid)

**Lý do:**
1. ✅ Tách database cho từng company (data isolation)
2. ✅ Hỗ trợ export/import database
3. ✅ Có thể chạy offline với local MongoDB
4. ✅ Dễ maintain và scale
5. ✅ Bảo mật tốt hơn

**Next Steps:**
1. Confirm với bạn về approach
2. Backup production database
3. Chạy migration trên development
4. Test thoroughly
5. Deploy to production

---

## 8. OFFLINE MODE SETUP GUIDE (For Companies)

### Cài đặt Offline Mode cho Company:

1. **Export Database từ Online System:**
   - Login as Super Admin
   - Vào System Settings → Export Database
   - Download file ZIP chứa toàn bộ dữ liệu

2. **Setup Local Environment:**
   ```bash
   # Install Docker Desktop
   # Download app source code
   
   # Run MongoDB locally
   docker-compose up -d mongodb
   
   # Import database
   # Use import API endpoint
   ```

3. **Switch Mode:**
   - Online: Connect to MongoDB Atlas
   - Offline: Connect to Local MongoDB
   - Auto-detect internet và switch mode

4. **Sync Data:**
   - Khi online lại, sync changes lên cloud
   - Resolve conflicts nếu có
   - Backup offline changes

---

**QUESTIONS FOR YOU:**

1. Bạn có muốn implement full offline mode hay chỉ cần export/import?
2. Bao nhiêu companies dự kiến sử dụng hệ thống?
3. Tần suất offline work expected là bao nhiêu?
4. Budget và timeline cho feature này?
