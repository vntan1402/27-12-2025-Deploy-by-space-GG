# 📋 ENDPOINT MIGRATION CHECKLIST

**Mục đích:** Track tiến độ migration từng endpoint từ backend-v1 sang backend mới

**Cách sử dụng:** Đánh dấu ✅ khi endpoint đã được migrate và test thành công

---

## 🔐 AUTHENTICATION (2 endpoints)

- [ ] POST `/api/auth/login` - User login
- [ ] GET `/api/verify-token` - Verify JWT token

**Status:** 0/2 (0%)

---

## 👥 USER MANAGEMENT (8 endpoints)

- [ ] GET `/api/users` - Get all users (role-based)
- [ ] GET `/api/users/filtered` - Get filtered users
- [ ] GET `/api/users/query` - Query users
- [ ] POST `/api/users` - Create new user
- [ ] PUT `/api/users/{user_id}` - Update user
- [ ] DELETE `/api/users/{user_id}` - Delete user
- [ ] GET `/api/company` - Get current user's company info
- [ ] GET `/api/files/{folder}/{filename}` - Get uploaded files

**Status:** 0/8 (0%)

---

## 🏢 COMPANY MANAGEMENT (7 endpoints)

- [ ] GET `/api/companies` - Get all companies
- [ ] GET `/api/companies/{company_id}` - Get company by ID
- [ ] POST `/api/companies` - Create new company
- [ ] PUT `/api/companies/{company_id}` - Update company
- [ ] DELETE `/api/companies/{company_id}` - Delete company
- [ ] POST `/api/companies/{company_id}/upload-logo` - Upload company logo
- [ ] GET `/api/system-settings/base-fee` - Get base fee settings
- [ ] PUT `/api/system-settings/base-fee` - Update base fee

**Status:** 0/7 (0%)

---

## 🚢 SHIP MANAGEMENT (35+ endpoints)

### Basic CRUD
- [ ] GET `/api/ships` - Get all ships (company-filtered)
- [ ] GET `/api/ships/{ship_id}` - Get ship by ID
- [ ] POST `/api/ships` - Create new ship
- [ ] PUT `/api/ships/{ship_id}` - Update ship
- [ ] DELETE `/api/ships/{ship_id}` - Delete ship

### Ship Calculations
- [ ] POST `/api/ships/{ship_id}/calculate-anniversary-date` - Calculate anniversary date
- [ ] POST `/api/ships/{ship_id}/override-anniversary-date` - Override anniversary date
- [ ] POST `/api/ships/{ship_id}/calculate-next-docking` - Calculate next docking
- [ ] POST `/api/ships/{ship_id}/calculate-docking-dates` - Calculate docking dates
- [ ] POST `/api/ships/{ship_id}/calculate-special-survey-cycle` - Calculate special survey

### Ship Survey Status
- [ ] GET `/api/ships/{ship_id}/survey-status` - Get survey status
- [ ] POST `/api/ships/{ship_id}/survey-status` - Create survey status
- [ ] PUT `/api/ships/{ship_id}/survey-status` - Update survey status
- [ ] DELETE `/api/ships/{ship_id}/survey-status` - Delete survey status

### Google Drive Integration
- [ ] GET `/api/ships/{ship_id}/gdrive-folder-status` - Get GDrive folder status
- [ ] POST `/api/ships/{ship_id}/create-gdrive-folders` - Create GDrive folders
- [ ] POST `/api/ships/{ship_id}/sync-to-gdrive` - Sync to GDrive
- [ ] POST `/api/ships/{ship_id}/gdrive-sync-check` - Check GDrive sync
- [ ] POST `/api/ships/bulk-create-gdrive-folders` - Bulk create folders
- [ ] POST `/api/ships/test-gdrive-folder-creation` - Test GDrive creation

### Ship Certificates Summary
- [ ] GET `/api/ships/{ship_id}/certificates-summary` - Get certificates summary
- [ ] GET `/api/ships/{ship_id}/expiring-certificates` - Get expiring certificates
- [ ] GET `/api/ships/{ship_id}/expired-certificates` - Get expired certificates

### Other Ship Endpoints
- [ ] GET `/api/ship-types` - Get ship types
- [ ] GET `/api/class-societies` - Get class societies
- [ ] GET `/api/flags` - Get available flags
- [ ] POST `/api/ships/{ship_id}/bulk-export` - Bulk export ship data
- [ ] GET `/api/ships/{ship_id}/certificates/export` - Export certificates

**Status:** 0/35+ (0%)

---

## 📜 CERTIFICATE MANAGEMENT (45+ endpoints)

### Basic CRUD
- [ ] GET `/api/ships/{ship_id}/certificates` - Get ship certificates
- [ ] GET `/api/certificates/{cert_id}` - Get certificate by ID
- [ ] POST `/api/certificates` - Create certificate
- [ ] PUT `/api/certificates/{cert_id}` - Update certificate
- [ ] DELETE `/api/certificates/{cert_id}` - Delete certificate
- [ ] POST `/api/certificates/bulk-delete` - Bulk delete certificates

### AI Analysis
- [ ] POST `/api/certificates/analyze-file` - AI analyze certificate
- [ ] POST `/api/certificates/extract-dates` - Extract dates from file
- [ ] POST `/api/certificates/extract-text` - OCR text extraction
- [ ] POST `/api/certificates/analyze-image` - Analyze image
- [ ] GET `/api/certificates/{cert_id}/ai-analysis` - Get AI analysis

### Certificate Types & Categories
- [ ] GET `/api/certificate-types` - Get all certificate types
- [ ] POST `/api/certificate-types` - Create certificate type
- [ ] PUT `/api/certificate-types/{type_id}` - Update certificate type
- [ ] DELETE `/api/certificate-types/{type_id}` - Delete certificate type
- [ ] GET `/api/certificate-categories` - Get categories

### Certificate Abbreviations
- [ ] GET `/api/certificate-abbreviations` - Get abbreviation mappings
- [ ] POST `/api/certificate-abbreviations` - Create abbreviation
- [ ] PUT `/api/certificate-abbreviations/{id}` - Update abbreviation
- [ ] DELETE `/api/certificate-abbreviations/{id}` - Delete abbreviation
- [ ] POST `/api/certificate-abbreviations/normalize` - Normalize certificate name

### Special Certificates (ISM/ISPS/MLC)
- [ ] GET `/api/certificates/ism-isps-mlc` - Get ISM/ISPS/MLC certificates
- [ ] GET `/api/certificates/ism` - Get ISM certificates
- [ ] GET `/api/certificates/isps` - Get ISPS certificates
- [ ] GET `/api/certificates/mlc` - Get MLC certificates
- [ ] POST `/api/certificates/categorize` - Auto-categorize certificate

### Certificate Search & Filter
- [ ] GET `/api/certificates/search` - Search certificates
- [ ] GET `/api/certificates/expiring` - Get expiring certificates
- [ ] GET `/api/certificates/expired` - Get expired certificates
- [ ] GET `/api/certificates/by-date-range` - Filter by date range
- [ ] GET `/api/certificates/by-type` - Filter by type
- [ ] GET `/api/certificates/by-ship` - Filter by ship

### Certificate Files
- [ ] POST `/api/certificates/{cert_id}/upload-file` - Upload certificate file
- [ ] GET `/api/certificates/{cert_id}/download` - Download certificate
- [ ] DELETE `/api/certificates/{cert_id}/file` - Delete certificate file
- [ ] POST `/api/certificates/split-pdf` - Split PDF into pages

### Issued By (Authorities)
- [ ] GET `/api/issued-by` - Get all authorities
- [ ] POST `/api/issued-by` - Create authority
- [ ] PUT `/api/issued-by/{id}` - Update authority
- [ ] DELETE `/api/issued-by/{id}` - Delete authority
- [ ] GET `/api/issued-by/abbreviations` - Get authority abbreviations

**Status:** 0/45+ (0%)

---

## 👥 CREW MANAGEMENT (30+ endpoints)

### Crew CRUD
- [ ] GET `/api/crew` - Get all crew (company-filtered)
- [ ] GET `/api/crew/{crew_id}` - Get crew by ID
- [ ] POST `/api/crew` - Create new crew member
- [ ] PUT `/api/crew/{crew_id}` - Update crew member
- [ ] DELETE `/api/crew/{crew_id}` - Delete crew member
- [ ] POST `/api/crew/bulk-delete` - Bulk delete crew

### Crew Status & Assignment
- [ ] GET `/api/crew/by-ship/{ship_name}` - Get crew by ship
- [ ] GET `/api/crew/standby` - Get standby crew
- [ ] GET `/api/crew/sign-on` - Get signed-on crew
- [ ] POST `/api/crew/{crew_id}/change-status` - Change crew status
- [ ] POST `/api/crew/{crew_id}/assign-ship` - Assign to ship
- [ ] POST `/api/crew/{crew_id}/sign-off` - Sign off crew

### Crew Certificates
- [ ] GET `/api/crew/{crew_id}/certificates` - Get crew certificates
- [ ] POST `/api/crew-certificates/analyze-file` - AI analyze crew certificate
- [ ] POST `/api/crew-certificates` - Create crew certificate
- [ ] PUT `/api/crew-certificates/{cert_id}` - Update crew certificate
- [ ] DELETE `/api/crew-certificates/{cert_id}` - Delete crew certificate
- [ ] GET `/api/crew-certificates/expiring` - Get expiring crew certificates

### Crew Files
- [ ] POST `/api/crew/{crew_id}/upload-passport` - Upload passport
- [ ] POST `/api/crew/{crew_id}/upload-summary` - Upload summary
- [ ] GET `/api/crew/{crew_id}/files` - Get crew files
- [ ] DELETE `/api/crew/{crew_id}/files/{file_id}` - Delete crew file

### Crew Reports
- [ ] GET `/api/crew/report/by-rank` - Crew report by rank
- [ ] GET `/api/crew/report/by-nationality` - Crew report by nationality
- [ ] GET `/api/crew/expiring-documents` - Get expiring crew documents
- [ ] POST `/api/crew/export` - Export crew list

### Ranks & Positions
- [ ] GET `/api/crew-ranks` - Get all crew ranks
- [ ] GET `/api/nationalities` - Get nationalities list

**Status:** 0/30+ (0%)

---

## 🔄 GOOGLE DRIVE INTEGRATION (10+ endpoints)

- [ ] GET `/api/gdrive/config` - Get GDrive configuration
- [ ] POST `/api/gdrive/config` - Update GDrive config
- [ ] POST `/api/gdrive/authorize` - Authorize GDrive
- [ ] GET `/api/gdrive/status` - Get sync status
- [ ] POST `/api/gdrive/sync-all` - Sync all to GDrive
- [ ] POST `/api/gdrive/test-connection` - Test GDrive connection
- [ ] GET `/api/gdrive/folders` - List GDrive folders
- [ ] POST `/api/gdrive/create-folder` - Create folder
- [ ] POST `/api/gdrive/upload-file` - Upload file
- [ ] GET `/api/gdrive/company-config` - Get company GDrive config

**Status:** 0/10+ (0%)

---

## ⚙️ SYSTEM SETTINGS (8+ endpoints)

- [ ] GET `/api/system-settings` - Get all system settings
- [ ] PUT `/api/system-settings` - Update system settings
- [ ] GET `/api/system-settings/ai-config` - Get AI configuration
- [ ] PUT `/api/system-settings/ai-config` - Update AI config
- [ ] POST `/api/system-settings/test-ai` - Test AI connection
- [ ] GET `/api/usage-tracking` - Get usage statistics
- [ ] POST `/api/usage-tracking` - Log usage
- [ ] GET `/api/usage-tracking/report` - Usage report

**Status:** 0/8+ (0%)

---

## 🔧 ADMIN API (5+ endpoints)

- [ ] POST `/api/admin/create-admin` - Create admin user
- [ ] GET `/api/admin/users` - Get all users (admin view)
- [ ] PUT `/api/admin/users/{user_id}` - Update user (admin)
- [ ] DELETE `/api/admin/users/{user_id}` - Delete user (admin)
- [ ] POST `/api/admin/export-data` - Export all data

**Status:** 0/5+ (0%)

---

## 📊 OVERALL PROGRESS

**Total Endpoints:** 179+
**Migrated:** 0
**Remaining:** 179+
**Progress:** 0%

---

## 🎯 PRIORITY ORDER

### Phase 1: Critical (Must have)
1. Authentication (2)
2. Users (8)
3. Companies (7)
4. Ships Basic CRUD (5)
5. Certificates Basic CRUD (6)

**Total Phase 1:** 28 endpoints

### Phase 2: Core Features
1. Ship Calculations (5)
2. Certificate AI Analysis (5)
3. Crew Basic CRUD (6)
4. Crew Certificates (6)

**Total Phase 2:** 22 endpoints

### Phase 3: Additional Features
1. Google Drive Integration (10)
2. System Settings (8)
3. Advanced Certificate Features (20)
4. Advanced Ship Features (20)
5. Advanced Crew Features (15)

**Total Phase 3:** 73 endpoints

### Phase 4: Admin & Reports
1. Admin API (5)
2. Reports & Analytics (10)
3. Bulk Operations (10)

**Total Phase 4:** 25 endpoints

---

**Last Updated:** $(date)
