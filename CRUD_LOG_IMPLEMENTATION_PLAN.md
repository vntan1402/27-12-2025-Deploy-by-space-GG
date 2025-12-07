# 📋 CRUD Log System - Implementation Plan

**Feature:** Audit Trail cho tất cả Crew CRUD operations  
**Location:** System Settings > Admin Tools > Crew Audit Logs  
**Retention:** 1 năm  
**Priority:** HIGH

---

## 🎯 Objectives

### Primary Goals:
1. ✅ Track all CREATE, UPDATE, DELETE operations on Crew records
2. ✅ Track special actions: SIGN_ON, SIGN_OFF, SHIP_TRANSFER
3. ✅ Store detailed before/after values for audit compliance
4. ✅ Provide searchable, filterable UI for admins
5. ✅ Support 3-year retention with automatic cleanup

### Secondary Goals:
1. ⭐ Generic design để dễ mở rộng cho Ships, Certificates, Users
2. ⭐ Export functionality (CSV/Excel)
3. ⭐ Performance optimization cho large log volumes

---

## 🗄️ Database Schema

### Collection: `crew_audit_logs`

```javascript
{
  _id: ObjectId,
  
  // Entity info
  entity_type: "crew",              // Fixed for now, generic later
  entity_id: String,                // crew.id
  entity_name: String,              // crew.full_name (for display)
  company_id: String,               // Multi-tenant isolation
  
  // Action info
  action: String,                   // Enum: CREATE, UPDATE, DELETE, SIGN_ON, SIGN_OFF, SHIP_TRANSFER, BULK_UPDATE
  action_category: String,          // Enum: DATA_CHANGE, STATUS_CHANGE, LIFECYCLE
  
  // User info
  performed_by: String,             // user.username
  performed_by_id: String,          // user.id
  performed_by_name: String,        // user.full_name
  
  // Timestamp
  performed_at: DateTime,           // ISO timestamp (indexed)
  
  // Changes (array of field changes)
  changes: [
    {
      field: String,                // Field name (e.g., "ship_sign_on")
      field_label: String,          // Display label (e.g., "Ship Sign On")
      old_value: Any,               // Previous value (null for CREATE)
      new_value: Any,               // New value (null for DELETE)
      value_type: String            // data type: string, number, date, boolean
    }
  ],
  
  // Context
  notes: String,                    // Optional notes/reason
  source: String,                   // Source of action: WEB_UI, API, BULK_IMPORT, SYSTEM
  
  // Metadata
  created_at: DateTime,
  expires_at: DateTime              // Auto-delete after 3 years (TTL index)
}
```

### Indexes:

```javascript
// Multi-tenant + performance
db.crew_audit_logs.createIndex({ "company_id": 1, "performed_at": -1 })

// Entity lookup
db.crew_audit_logs.createIndex({ "entity_id": 1, "performed_at": -1 })

// User activity
db.crew_audit_logs.createIndex({ "company_id": 1, "performed_by": 1, "performed_at": -1 })

// Action type filter
db.crew_audit_logs.createIndex({ "company_id": 1, "action": 1, "performed_at": -1 })

// TTL index for 3-year retention
db.crew_audit_logs.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })

// Search by crew name
db.crew_audit_logs.createIndex({ "company_id": 1, "entity_name": "text" })
```

---

## 🎨 UI Design - Crew Audit Logs Page

### Location:
```
System Settings → Admin Tools → Crew Audit Logs
Route: /system-settings/admin-tools/crew-audit-logs
```

### Layout Structure:

```
┌────────────────────────────────────────────────────────────────┐
│  📊 Crew Audit Logs                                [Export ▼]  │
├────────────────────────────────────────────────────────────────┤
│  Filters:                                                       │
│  [Date Range: Last 30 days ▼] [Action: All ▼]                 │
│  [User: All ▼] [Search crew name...........................] 🔍│
├────────────────────────────────────────────────────────────────┤
│  Summary: 1,234 logs found                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Timeline View (Grouped by Date)                         │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                           │ │
│  │ 📅 Hôm nay, 19/01/2025                                   │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │ 🔄 UPDATE                          10:30:45          │ │ │
│  │ │ Crew: Nguyễn Văn A                                  │ │ │
│  │ │ By: admin1 (Admin User)                             │ │ │
│  │ │                                                       │ │ │
│  │ │ Changes:                                              │ │ │
│  │ │ • Ship Sign On: "Ship ABC" → "Ship XYZ"            │ │ │
│  │ │ • Status: "Sign on" → "Sign on"                     │ │ │
│  │ │ • Date Sign On: "2025-01-10" → "2025-01-15"        │ │ │
│  │ │                                                       │ │ │
│  │ │ 📝 Notes: Bulk ship transfer via modal              │ │ │
│  │ │                                         [View Details]│ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │ ➕ CREATE                          09:15:20          │ │ │
│  │ │ Crew: Trần Thị B                                    │ │ │
│  │ │ By: user2 (Editor User)                             │ │ │
│  │ │                                                       │ │ │
│  │ │ Created new crew member with:                        │ │ │
│  │ │ • Full Name: Trần Thị B                             │ │ │
│  │ │ • Passport: ABC123456                                │ │ │
│  │ │ • Rank: AB                                           │ │ │
│  │ │ • Status: Standby                                    │ │ │
│  │ │                                         [View Details]│ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │ 📅 18/01/2025                                            │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │ 🚢 SIGN_ON                         16:45:12          │ │ │
│  │ │ Crew: Lê Văn C                                      │ │ │
│  │ │ By: admin1                                           │ │ │
│  │ │                                                       │ │ │
│  │ │ Changes:                                              │ │ │
│  │ │ • Ship Sign On: "-" → "Ship MNO"                    │ │ │
│  │ │ • Status: "Standby" → "Sign on"                     │ │ │
│  │ │ • Date Sign On: null → "2025-01-18"                 │ │ │
│  │ │                                         [View Details]│ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [◄ Previous]  Page 1 of 25  [Next ►]                         │
└────────────────────────────────────────────────────────────────┘
```

### Detail Modal (when click "View Details"):

```
┌─────────────────────────────────────────────────────┐
│  Audit Log Detail                            [✕]    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔄 UPDATE - Crew Record Modified                   │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ 📋 Basic Info                                │  │
│  ├──────────────────────────────────────────────┤  │
│  │ Log ID: log_abc123                           │  │
│  │ Crew: Nguyễn Văn A (crew_456)                │  │
│  │ Action: UPDATE                                │  │
│  │ Performed by: admin1 (Admin User)            │  │
│  │ Timestamp: 19/01/2025 10:30:45               │  │
│  │ Source: WEB_UI                                │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ 📝 Changes (3 fields modified)               │  │
│  ├──────────────────────────────────────────────┤  │
│  │                                               │  │
│  │ 1. Ship Sign On                              │  │
│  │    Before: Ship ABC                          │  │
│  │    After:  Ship XYZ                          │  │
│  │                                               │  │
│  │ 2. Status                                     │  │
│  │    Before: Sign on                           │  │
│  │    After:  Sign on                           │  │
│  │                                               │  │
│  │ 3. Date Sign On                              │  │
│  │    Before: 2025-01-10                        │  │
│  │    After:  2025-01-15                        │  │
│  │                                               │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ 💬 Notes                                     │  │
│  ├──────────────────────────────────────────────┤  │
│  │ Bulk ship transfer via Ship Sign On modal   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [Close]                                             │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ Implementation Steps

### Phase 1: UI Development (Priority: HIGH) ✅

#### Step 1.1: Create Navigation Menu Item
**Files:** `/app/frontend/src/components/SystemSettings/SystemSettings.jsx`

- Add "Admin Tools" section in sidebar
- Add "Crew Audit Logs" menu item
- Icon: 📋 or 📊
- Route: `/system-settings/admin-tools/crew-audit-logs`
- Permission check: Only show for admin/super_admin roles

**Estimated time:** 30 minutes

---

#### Step 1.2: Create Main Audit Logs Page Component
**File:** `/app/frontend/src/components/SystemSettings/CrewAuditLogs/CrewAuditLogsPage.jsx`

**Features:**
- Layout structure (header, filters, content, pagination)
- State management for filters, pagination, data
- Mock data for initial development
- Responsive design

**Components to create:**
- `CrewAuditLogsPage.jsx` (main page)
- `AuditLogFilters.jsx` (filter section)
- `AuditLogList.jsx` (timeline list)
- `AuditLogCard.jsx` (individual log card)
- `AuditLogDetailModal.jsx` (detail modal)

**Estimated time:** 4-5 hours

---

#### Step 1.3: Implement Filters
**Components:** `AuditLogFilters.jsx`

**Filters:**
1. Date Range Picker
   - Presets: Today, Yesterday, Last 7 days, Last 30 days, Last 3 months, Custom
   - Date picker component (use existing date picker or add new)
   
2. Action Type Dropdown
   - Options: All, CREATE, UPDATE, DELETE, SIGN_ON, SIGN_OFF, SHIP_TRANSFER, BULK_UPDATE
   
3. User Dropdown
   - Load from users collection (company users only)
   - Options: All, + list of users
   
4. Search Input
   - Search by crew name
   - Debounced search (500ms delay)

**Estimated time:** 2-3 hours

---

#### Step 1.4: Create Timeline View
**Component:** `AuditLogList.jsx`

**Features:**
- Group logs by date
- Show date headers (Hôm nay, Hôm qua, date format)
- Card for each log entry
- Expandable/collapsible details
- Infinite scroll or pagination

**Estimated time:** 2-3 hours

---

#### Step 1.5: Create Log Card Component
**Component:** `AuditLogCard.jsx`

**Display:**
- Action icon (🔄 UPDATE, ➕ CREATE, 🗑️ DELETE, 🚢 SIGN_ON, etc.)
- Crew name (bold)
- Performed by (user name)
- Timestamp
- Changes summary (top 3 changes, rest hidden)
- "View Details" button
- Color coding by action type

**Estimated time:** 2 hours

---

#### Step 1.6: Create Detail Modal
**Component:** `AuditLogDetailModal.jsx`

**Sections:**
- Basic Info (log ID, crew, action, user, timestamp, source)
- Changes Table (field, before, after)
- Notes section
- Close button

**Estimated time:** 2 hours

---

#### Step 1.7: Export Functionality
**Component:** `ExportButton.jsx` (within CrewAuditLogsPage)

**Features:**
- Export current filtered results
- Formats: CSV, Excel (XLSX)
- Include all fields
- File name: `crew_audit_logs_YYYYMMDD_HHMMSS.csv`

**Estimated time:** 2 hours

---

#### Step 1.8: Styling & Responsiveness
**Files:** All component files

**Tasks:**
- Tailwind CSS styling
- Mobile responsive design
- Loading states
- Empty states
- Error states
- Dark mode support (if applicable)

**Estimated time:** 2-3 hours

---

### Phase 2: Backend Development (After UI approval)

#### Step 2.1: Create Data Model
**File:** `/app/backend/app/models/crew_audit_log.py`

- Pydantic models: `CrewAuditLogBase`, `CrewAuditLogCreate`, `CrewAuditLogResponse`
- Validation rules
- Type definitions

**Estimated time:** 1 hour

---

#### Step 2.2: Create Repository Layer
**File:** `/app/backend/app/repositories/crew_audit_log_repository.py`

**Methods:**
- `create_log(log_data)` - Create new log entry
- `get_logs(filters, pagination)` - Get filtered logs
- `get_log_by_id(log_id)` - Get single log
- `get_logs_by_crew(crew_id)` - Get all logs for a crew
- `get_logs_by_user(user_id)` - Get all logs by user
- `count_logs(filters)` - Count for pagination
- `delete_expired_logs()` - Cleanup old logs (3+ years)

**Estimated time:** 2-3 hours

---

#### Step 2.3: Create Service Layer
**File:** `/app/backend/app/services/crew_audit_log_service.py`

**Features:**
- `log_crew_create(crew_data, user)` - Log CREATE action
- `log_crew_update(crew_id, old_data, new_data, user, notes)` - Log UPDATE
- `log_crew_delete(crew_data, user)` - Log DELETE
- `log_crew_sign_on(crew_id, ship_name, user)` - Log SIGN_ON
- `log_crew_sign_off(crew_id, ship_name, user)` - Log SIGN_OFF
- Business logic for change detection
- Field label mapping (ship_sign_on → "Ship Sign On")

**Estimated time:** 3-4 hours

---

#### Step 2.4: Create API Endpoints
**File:** `/app/backend/app/api/v1/crew_audit_logs.py`

**Endpoints:**
- `GET /api/crew-audit-logs` - Get paginated logs with filters
- `GET /api/crew-audit-logs/{log_id}` - Get single log detail
- `GET /api/crew-audit-logs/crew/{crew_id}` - Get logs for specific crew
- `GET /api/crew-audit-logs/export` - Export logs as CSV/Excel
- `DELETE /api/crew-audit-logs/cleanup` - Manual cleanup old logs (admin only)

**Estimated time:** 2-3 hours

---

#### Step 2.5: Integrate Logging into Crew Service
**File:** `/app/backend/app/services/crew_service.py` (modify existing)

**Integration points:**
- `create_crew()` → Call `log_crew_create()`
- `update_crew()` → Call `log_crew_update()`
- `delete_crew()` → Call `log_crew_delete()`
- `sign_on()` → Call `log_crew_sign_on()`
- `sign_off()` → Call `log_crew_sign_off()`

**Estimated time:** 2-3 hours

---

#### Step 2.6: Create Database Indexes
**File:** `/app/backend/scripts/add_audit_log_indexes.py`

- Create all indexes as defined in schema
- Verify index creation
- Test query performance

**Estimated time:** 1 hour

---

#### Step 2.7: Create Cleanup Cron Job
**File:** `/app/backend/app/jobs/cleanup_old_logs.py`

**Features:**
- Run daily (e.g., 2 AM)
- Delete logs older than 3 years
- Log cleanup statistics
- Error handling

**Estimated time:** 1-2 hours

---

### Phase 3: Testing & Integration

#### Step 3.1: Unit Tests (Backend)
**Files:** `/app/backend/tests/test_crew_audit_logs.py`

**Test cases:**
- Create log entry
- Retrieve logs with filters
- Pagination
- TTL expiry (mock time)
- Export functionality

**Estimated time:** 3-4 hours

---

#### Step 3.2: Integration Tests
**Testing scenarios:**
- Create crew → verify log created
- Update crew → verify log with changes
- Delete crew → verify log created
- Sign on/off → verify logs
- Bulk operations → verify multiple logs

**Estimated time:** 2-3 hours

---

#### Step 3.3: Frontend Testing
**Tools:** Screenshot tool, Manual testing

**Test cases:**
- Page loads correctly
- Filters work
- Pagination works
- Detail modal opens
- Export works
- Responsive design
- Different user roles

**Estimated time:** 2-3 hours

---

#### Step 3.4: Performance Testing
**Scenarios:**
- Load page with 10k logs
- Filter with 100k logs
- Export 50k logs
- Query optimization
- Index usage verification

**Estimated time:** 2 hours

---

### Phase 4: Documentation & Deployment

#### Step 4.1: Documentation
**Files:**
- `/app/CREW_AUDIT_LOGS.md` - User guide
- Update `/app/DATABASE_INDEXES.md` - Add new indexes
- API documentation

**Estimated time:** 2 hours

---

#### Step 4.2: Deployment
**Tasks:**
- Run index creation script
- Deploy backend changes
- Deploy frontend changes
- Verify production
- Monitor for errors

**Estimated time:** 1 hour

---

## 📊 Timeline Summary

### Phase 1: UI Development (Focus)
```
Step 1.1: Navigation         → 0.5 hours
Step 1.2: Main Page          → 4-5 hours
Step 1.3: Filters            → 2-3 hours
Step 1.4: Timeline View      → 2-3 hours
Step 1.5: Log Card           → 2 hours
Step 1.6: Detail Modal       → 2 hours
Step 1.7: Export             → 2 hours
Step 1.8: Styling            → 2-3 hours
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL PHASE 1:               → 17-22 hours (2-3 working days)
```

### Phase 2: Backend Development
```
Step 2.1-2.7:                → 12-17 hours (2 working days)
```

### Phase 3: Testing
```
Step 3.1-3.4:                → 9-12 hours (1-2 working days)
```

### Phase 4: Documentation & Deployment
```
Step 4.1-4.2:                → 3 hours (0.5 working day)
```

### **TOTAL ESTIMATED TIME: 41-54 hours (5-7 working days)**

---

## 🎯 Execution Plan

### Current Session: Phase 1 (UI Development)

**Immediate Next Steps:**
1. ✅ Get user approval on this plan
2. ✅ Create navigation menu item in System Settings
3. ✅ Create main page component structure
4. ✅ Implement filters
5. ✅ Create timeline view with mock data
6. ✅ Create log card component
7. ✅ Create detail modal
8. ✅ Polish styling
9. ✅ Get user feedback on UI
10. ⏸️ Pause for user approval before Phase 2

**Mock Data for Phase 1:**
```javascript
const mockLogs = [
  {
    id: 'log_1',
    entity_name: 'Nguyễn Văn A',
    entity_id: 'crew_123',
    action: 'UPDATE',
    performed_by: 'admin1',
    performed_by_name: 'Admin User',
    performed_at: '2025-01-19T10:30:45Z',
    changes: [
      {field: 'ship_sign_on', field_label: 'Ship Sign On', old_value: 'Ship ABC', new_value: 'Ship XYZ'},
      {field: 'date_sign_on', field_label: 'Date Sign On', old_value: '2025-01-10', new_value: '2025-01-15'}
    ],
    notes: 'Bulk ship transfer via modal'
  },
  // ... more mock data
];
```

---

## 🔐 Security Considerations

1. **Permission Check:**
   - Only admin/super_admin can access audit logs page
   - Check both frontend (hide menu) and backend (API auth)

2. **Multi-tenant Isolation:**
   - Always filter logs by company_id
   - Never show other company's logs

3. **Sensitive Data:**
   - Don't log passwords or API keys
   - Hash sensitive fields if needed

4. **Export Limits:**
   - Max 10,000 records per export
   - Rate limiting for export endpoint

---

## 📝 Notes

### Decisions Made:
1. ✅ Separate page in Admin Tools (not modal)
2. ✅ 3-year retention with TTL index
3. ✅ UI first, backend after approval
4. ✅ Generic design for future expansion
5. ✅ Mock data for UI development

### Open Questions:
- [ ] Do we need real-time updates? (WebSocket for new logs)
- [ ] Should we log READ operations? (Typically not needed)
- [ ] Color scheme preferences?
- [ ] Export file format preferences? (CSV sufficient or need Excel?)

---

## ✅ Checklist Before Starting

- [x] Plan approved by user
- [x] UI wireframe clear
- [x] Database schema defined
- [x] Timeline understood
- [x] Mock data prepared
- [ ] Begin implementation ⏳

---

**Ready to start Phase 1: UI Development?** 🚀
