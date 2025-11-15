# 🔗 FRONTEND API USAGE MAPPING

**Mục đích:** Map tất cả endpoints mà frontend đang gọi để đảm bảo migration đầy đủ

**Source:** Analyzed from `/app/frontend/src/constants/api.js`

---

## 📊 TỔNG QUAN

**Tổng số endpoints frontend sử dụng:** ~80 endpoints
**Phân loại:**
- Authentication: 2 endpoints
- Ships: 7 endpoints
- Crew: 5 endpoints
- Certificates (Ship): 6 endpoints
- Crew Certificates: 6 endpoints
- Survey Reports: 6 endpoints
- Test Reports: 6 endpoints
- Drawings & Manuals: 6 endpoints
- Other Documents: 6 endpoints
- ISM Documents: 5 endpoints
- ISPS Documents: 5 endpoints
- MLC Documents: 5 endpoints
- Supply Documents: 5 endpoints
- Companies: 7 endpoints
- Users: 2 endpoints
- Google Drive: 2 endpoints
- AI Config: 1 endpoint

---

## 🔐 AUTHENTICATION (Priority: CRITICAL)

### 1. POST `/api/login`
- **Used in:** Login page
- **Purpose:** User authentication
- **Backend endpoint:** POST `/api/auth/login` (cần map)

### 2. GET `/api/verify-token`
- **Used in:** Auth context, protected routes
- **Purpose:** Verify JWT token validity
- **Backend endpoint:** GET `/api/verify-token`

**Note:** Frontend gọi `/api/login` nhưng backend có endpoint `/api/auth/login` - cần check!

---

## 🚢 SHIPS MANAGEMENT (Priority: HIGH)

### 1. GET `/api/ships`
- **Used in:** Ships list page
- **Purpose:** Get all ships for current user's company

### 2. GET `/api/ships/{id}`
- **Used in:** Ship details page
- **Purpose:** Get ship by ID

### 3. POST `/api/ships`
- **Used in:** Add ship modal
- **Purpose:** Create new ship

### 4. PUT `/api/ships/{id}`
- **Used in:** Edit ship modal
- **Purpose:** Update ship details

### 5. DELETE `/api/ships/{id}`
- **Used in:** Ship actions
- **Purpose:** Delete ship

### 6. POST `/api/ships/{id}/calculate-next-docking`
- **Used in:** Ship docking calculations
- **Purpose:** Calculate next docking date

### 7. POST `/api/ships/{id}/calculate-anniversary-date`
- **Used in:** Ship anniversary calculations
- **Purpose:** Calculate anniversary date from certificates

### 8. POST `/api/ships/{id}/calculate-special-survey-cycle`
- **Used in:** Special survey calculations
- **Purpose:** Calculate special survey cycle

---

## 👥 CREW MANAGEMENT (Priority: HIGH)

### 1. GET `/api/crew`
- **Used in:** Crew list page
- **Purpose:** Get all crew members

### 2. GET `/api/crew/{id}`
- **Used in:** Crew details
- **Purpose:** Get crew member by ID

### 3. POST `/api/crew`
- **Used in:** Add crew modal
- **Purpose:** Create new crew member

### 4. PUT `/api/crew/{id}`
- **Used in:** Edit crew modal
- **Purpose:** Update crew member

### 5. DELETE `/api/crew/{id}`
- **Used in:** Crew actions
- **Purpose:** Delete crew member

### 6. POST `/api/crew/bulk-delete`
- **Used in:** Bulk operations
- **Purpose:** Delete multiple crew members

### 7. POST `/api/crew/move-standby-files`
- **Used in:** Crew status changes
- **Purpose:** Move files when crew becomes standby

### 8. POST `/api/passport/analyze-file`
- **Used in:** Passport upload
- **Purpose:** AI analyze passport file

---

## 📜 SHIP CERTIFICATES (Priority: HIGH)

### 1. GET `/api/certificates`
- **Used in:** Certificates list
- **Purpose:** Get certificates (filtered by ship)

### 2. GET `/api/certificates/{id}`
- **Used in:** Certificate details
- **Purpose:** Get certificate by ID

### 3. POST `/api/certificates`
- **Used in:** Add certificate modal
- **Purpose:** Create new certificate

### 4. PUT `/api/certificates/{id}`
- **Used in:** Edit certificate modal
- **Purpose:** Update certificate

### 5. DELETE `/api/certificates/{id}`
- **Used in:** Certificate actions
- **Purpose:** Delete certificate

### 6. POST `/api/certificates/analyze-file`
- **Used in:** Certificate upload modal
- **Purpose:** AI analyze certificate file

### 7. POST `/api/certificates/bulk-delete`
- **Used in:** Bulk operations
- **Purpose:** Delete multiple certificates

### 8. POST `/api/certificates/check-duplicate`
- **Used in:** Before upload
- **Purpose:** Check if certificate already exists

---

## 👔 CREW CERTIFICATES (Priority: HIGH)

### 1. GET `/api/crew-certificates`
- **Used in:** Crew certificates list
- **Purpose:** Get crew certificates

### 2. GET `/api/crew-certificates/{id}`
- **Used in:** Crew certificate details
- **Purpose:** Get crew certificate by ID

### 3. POST `/api/crew-certificates`
- **Used in:** Add crew certificate modal
- **Purpose:** Create new crew certificate

### 4. PUT `/api/crew-certificates/{id}`
- **Used in:** Edit crew certificate modal
- **Purpose:** Update crew certificate

### 5. DELETE `/api/crew-certificates/{id}`
- **Used in:** Crew certificate actions
- **Purpose:** Delete crew certificate

### 6. POST `/api/crew-certificates/analyze-file`
- **Used in:** Crew certificate upload
- **Purpose:** AI analyze crew certificate file

### 7. POST `/api/crew-certificates/bulk-delete`
- **Used in:** Bulk operations
- **Purpose:** Delete multiple crew certificates

### 8. POST `/api/crew-certificates/check-duplicate`
- **Used in:** Before upload
- **Purpose:** Check if crew certificate exists

---

## 📋 SURVEY REPORTS (Priority: MEDIUM)

### 1. GET `/api/survey-reports`
- **Used in:** Survey reports page
- **Purpose:** Get survey reports

### 2. GET `/api/survey-reports/{id}`
- **Used in:** Report details
- **Purpose:** Get survey report by ID

### 3. POST `/api/survey-reports`
- **Used in:** Add report modal
- **Purpose:** Create new survey report

### 4. PUT `/api/survey-reports/{id}`
- **Used in:** Edit report modal
- **Purpose:** Update survey report

### 5. DELETE `/api/survey-reports/{id}`
- **Used in:** Report actions
- **Purpose:** Delete survey report

### 6. POST `/api/survey-reports/analyze-file`
- **Used in:** Report upload
- **Purpose:** AI analyze survey report

### 7. POST `/api/survey-reports/bulk-delete`
- **Used in:** Bulk operations
- **Purpose:** Delete multiple reports

### 8. POST `/api/survey-reports/check-duplicate`
- **Used in:** Before upload
- **Purpose:** Check duplicate

---

## 🧪 TEST REPORTS (Priority: MEDIUM)

Similar structure to Survey Reports:
- GET `/api/test-reports`
- GET `/api/test-reports/{id}`
- POST `/api/test-reports`
- PUT `/api/test-reports/{id}`
- DELETE `/api/test-reports/{id}`
- POST `/api/test-reports/analyze-file`
- POST `/api/test-reports/bulk-delete`
- POST `/api/test-reports/check-duplicate`

---

## 📐 DRAWINGS & MANUALS (Priority: MEDIUM)

Similar structure:
- GET `/api/drawings-manuals`
- GET `/api/drawings-manuals/{id}`
- POST `/api/drawings-manuals`
- PUT `/api/drawings-manuals/{id}`
- DELETE `/api/drawings-manuals/{id}`
- POST `/api/drawings-manuals/bulk-delete`
- POST `/api/drawings-manuals/check-duplicate`

---

## 📄 OTHER DOCUMENTS (Priority: MEDIUM)

Similar structure:
- GET `/api/other-documents`
- GET `/api/other-documents/{id}`
- POST `/api/other-documents`
- PUT `/api/other-documents/{id}`
- DELETE `/api/other-documents/{id}`
- POST `/api/other-documents/bulk-delete`
- POST `/api/other-documents/check-duplicate`

---

## 📑 ISM/ISPS/MLC/SUPPLY DOCUMENTS (Priority: MEDIUM)

Each category has similar endpoints:
- GET `/api/{category}-documents`
- GET `/api/{category}-documents/{id}`
- POST `/api/{category}-documents`
- PUT `/api/{category}-documents/{id}`
- DELETE `/api/{category}-documents/{id}`
- POST `/api/{category}-documents/bulk-delete`

Categories:
- `ism-documents` (ISM)
- `isps-documents` (ISPS)
- `mlc-documents` (MLC)
- `supply-documents` (Supply)

---

## 🏢 COMPANIES (Priority: HIGH)

### 1. GET `/api/companies`
- **Used in:** Company management page
- **Purpose:** Get all companies

### 2. GET `/api/companies/{id}`
- **Used in:** Company details
- **Purpose:** Get company by ID

### 3. POST `/api/companies`
- **Used in:** Add company modal
- **Purpose:** Create new company

### 4. PUT `/api/companies/{id}`
- **Used in:** Edit company modal
- **Purpose:** Update company

### 5. DELETE `/api/companies/{id}`
- **Used in:** Company actions
- **Purpose:** Delete company

### 6. POST `/api/companies/{id}/upload-logo`
- **Used in:** Company logo upload
- **Purpose:** Upload company logo

### 7. GET `/api/companies/{id}/gdrive/config`
- **Used in:** GDrive settings
- **Purpose:** Get GDrive configuration

### 8. POST `/api/companies/{id}/gdrive/configure`
- **Used in:** GDrive setup
- **Purpose:** Configure GDrive

### 9. POST `/api/companies/{id}/gdrive/configure-proxy`
- **Used in:** GDrive proxy setup
- **Purpose:** Test proxy configuration

### 10. GET `/api/companies/{id}/gdrive/status`
- **Used in:** GDrive status check
- **Purpose:** Get GDrive sync status

---

## 👥 USERS (Priority: HIGH)

### 1. GET `/api/users`
- **Used in:** User management page
- **Purpose:** Get users (role-based filtering)

### 2. GET `/api/users/{id}`
- **Used in:** User details
- **Purpose:** Get user by ID

### 3. POST `/api/users`
- **Used in:** Add user modal
- **Purpose:** Create new user

### 4. PUT `/api/users/{id}`
- **Used in:** Edit user modal
- **Purpose:** Update user

### 5. DELETE `/api/users/{id}`
- **Used in:** User actions
- **Purpose:** Delete user

---

## 🔄 GOOGLE DRIVE (Priority: MEDIUM)

### 1. GET `/api/gdrive-config`
- **Used in:** GDrive settings page
- **Purpose:** Get global GDrive config

### 2. POST `/api/gdrive/upload`
- **Used in:** File upload
- **Purpose:** Upload file to GDrive

---

## 🤖 AI CONFIGURATION (Priority: MEDIUM)

### 1. GET `/api/ai-config`
- **Used in:** AI settings page
- **Purpose:** Get AI configuration

### 2. PUT `/api/ai-config`
- **Used in:** AI settings
- **Purpose:** Update AI config

---

## ⚠️ CRITICAL OBSERVATIONS

### 1. **Login Endpoint Mismatch**
- Frontend calls: `/api/login`
- Backend has: `/api/auth/login`
- **Action:** Cần thêm route `/api/login` hoặc update frontend

### 2. **Document Types Pattern**
Frontend có nhiều loại documents với cùng pattern:
- Survey Reports
- Test Reports
- Drawings & Manuals
- Other Documents
- ISM/ISPS/MLC/Supply Documents

**Backend cần có tất cả các endpoints này!**

### 3. **File Upload Pattern**
Tất cả document types đều có:
- `analyze-file` endpoint (AI analysis)
- `check-duplicate` endpoint
- `bulk-delete` endpoint
- Individual file link endpoints

---

## 📋 MIGRATION PRIORITY (Revised)

### Phase 1: Authentication & Core (CRITICAL)
1. ✅ POST `/api/login` hoặc `/api/auth/login`
2. ✅ GET `/api/verify-token`
3. ✅ GET `/api/users`
4. ✅ POST `/api/users`
5. ✅ PUT `/api/users/{id}`
6. ✅ DELETE `/api/users/{id}`

### Phase 2: Companies & Ships (HIGH)
1. ✅ Companies CRUD (5 endpoints)
2. ✅ Ships CRUD + calculations (8 endpoints)

### Phase 3: Certificates & Crew (HIGH)
1. ✅ Ship Certificates + AI analysis (8 endpoints)
2. ✅ Crew CRUD (8 endpoints)
3. ✅ Crew Certificates + AI analysis (8 endpoints)

### Phase 4: Document Types (MEDIUM)
1. ✅ Survey Reports (8 endpoints)
2. ✅ Test Reports (8 endpoints)
3. ✅ Drawings & Manuals (7 endpoints)
4. ✅ Other Documents (7 endpoints)
5. ✅ ISM/ISPS/MLC/Supply Documents (20 endpoints)

### Phase 5: Additional Features (MEDIUM)
1. ✅ Google Drive integration (10 endpoints)
2. ✅ AI Configuration (2 endpoints)

---

## 🔍 VERIFICATION CHECKLIST

Sau mỗi phase, verify:

### Frontend Connection Test
```bash
# Check if frontend can call the endpoint
curl -X GET http://localhost:8001/api/ships \
  -H "Authorization: Bearer $TOKEN"
```

### Frontend Console Check
1. Open browser DevTools
2. Go to Network tab
3. Trigger action in UI
4. Check if API call succeeds (200 OK)
5. Verify response data structure

### Common Issues to Watch
- [ ] CORS errors
- [ ] 404 Not Found (endpoint missing)
- [ ] 422 Validation Error (request body mismatch)
- [ ] 401 Unauthorized (auth not working)
- [ ] 500 Internal Error (backend logic error)

---

## 📊 TRACKING PROGRESS

| Category | Endpoints | Status | Priority |
|----------|-----------|--------|----------|
| Auth | 2 | ⬜ Not Started | CRITICAL |
| Users | 5 | ⬜ Not Started | HIGH |
| Companies | 10 | ⬜ Not Started | HIGH |
| Ships | 8 | ⬜ Not Started | HIGH |
| Certificates | 8 | ⬜ Not Started | HIGH |
| Crew | 8 | ⬜ Not Started | HIGH |
| Crew Certs | 8 | ⬜ Not Started | HIGH |
| Survey Reports | 8 | ⬜ Not Started | MEDIUM |
| Test Reports | 8 | ⬜ Not Started | MEDIUM |
| Drawings | 7 | ⬜ Not Started | MEDIUM |
| Other Docs | 7 | ⬜ Not Started | MEDIUM |
| ISM/ISPS/MLC/Supply | 20 | ⬜ Not Started | MEDIUM |
| Google Drive | 10 | ⬜ Not Started | MEDIUM |
| AI Config | 2 | ⬜ Not Started | MEDIUM |

**Total:** ~110 endpoints actively used by frontend

---

**Last Updated:** $(date)
**Next Step:** Begin Phase 1 infrastructure setup with focus on endpoints frontend actually uses
