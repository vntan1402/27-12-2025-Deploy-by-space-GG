# 📋 BACKEND-V1 FILES ANALYSIS

## Utility & Helper Files (Sorted by Priority)

### ✅ ALREADY MIGRATED
1. `document_name_normalization.py` - Document name standardization
2. `issued_by_abbreviation.py` - Company name abbreviation

### 🔴 HIGH PRIORITY - Need Migration

#### 1. Google Drive Integration
- `google_drive_manager.py` - Main Google Drive operations
- `company_google_drive_manager.py` - Company-specific GDrive
- `dual_apps_script_manager.py` - Dual app script management

#### 2. OCR & PDF Processing
- `ocr_processor.py` - OCR processing utilities
- `targeted_ocr.py` - Targeted OCR extraction
- `pdf_splitter.py` - PDF splitting functionality

#### 3. Database & Authentication
- `mongodb_database.py` - MongoDB utilities
- `offline_auth_service.py` - Offline authentication
- `file_database.py` - File database operations

### 🟡 MEDIUM PRIORITY - Admin/Setup Scripts

#### Admin Management
- `admin_api_helper.py` - Admin API helpers
- `create_first_admin.py` - First admin creation
- `init_admin_startup.py` - Admin initialization
- `quick_create_admin.py` - Quick admin creation

#### Data Migration Scripts
- `migrate_ships_to_uuid.py` - Ship UUID migration
- `migrate_system_to_software_expiry.py` - Software expiry migration
- `fix_ships_company_id.py` - Fix company IDs

#### Database Maintenance
- `fix_email_index.py` - Email index fixes
- `fix_email_index_partial.py` - Partial email fix
- `recreate_email_index.py` - Recreate indexes
- `remove_email_unique_index.py` - Remove unique index

### 🟢 LOW PRIORITY - One-time/Development Scripts

#### Data Import/Export
- `export_company_database.py` - Export company data
- `export_production_data.py` - Export production data
- `import_production_data.py` - Import production data
- `seed_database.py` - Database seeding

#### Configuration
- `check_ai_config.py` - AI config checker

#### Legacy/Examples
- `offline_mode_example.py` - Example code
- `server_mongodb.py` - Legacy MongoDB server

### 🔵 MAIN APPLICATION
- `server.py` - Main monolithic server (28,000+ lines)

