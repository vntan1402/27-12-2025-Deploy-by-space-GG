# ✅ Status Calculation Feature for Audit Certificates

## 📋 Overview
Implemented auto-calculated status for Audit Certificates based on `next_survey` (with window_close calculation) and `valid_date`, matching the logic used in Class & Flag Certificates.

## 🎯 What Was Done

### Files Modified

1. **`/app/frontend/src/components/AuditCertificate/AuditCertificateTable.jsx`**
   - Enhanced `getCertificateStatus()` to support ±6M annotation (lines 77-86)

2. **`/app/frontend/src/pages/IsmIspsMLc.jsx`**
   - Completely rewrote `getCertificateStatus()` to match Class & Flag logic (lines 528-584)
   - Added window_close calculation with annotation support
   - Added fallback to valid_date

3. **`/app/frontend/src/components/AuditCertificate/AuditCertificateFilters.jsx`**
   - Updated filter options: "Over Due" → "Due Soon" (line 68)
   - Added "Unknown" option (line 69)

## 📊 Status Calculation Logic

### Priority Order
```
1. next_survey_display or next_survey (with window_close calculation)
   ↓ If not available
2. valid_date (direct comparison)
   ↓ If not available
3. "Unknown"
```

### Window Close Calculation

#### Annotations Supported
```javascript
±6M  → window_close = next_survey_date + 6 months
±3M  → window_close = next_survey_date + 3 months
-6M  → window_close = next_survey_date (no adjustment)
-3M  → window_close = next_survey_date (no adjustment)
```

#### Example Calculations
```
Next Survey: 15/12/2024 (±6M)
→ window_close = 15/06/2025
→ Status valid until 15/06/2025

Next Survey: 15/12/2024 (-3M)
→ window_close = 15/12/2024
→ Status valid until 15/12/2024

Next Survey: 15/12/2024 (±3M)
→ window_close = 15/03/2025
→ Status valid until 15/03/2025
```

### Status Determination

```javascript
if (today > window_close)
  return 'Expired';

if (days_to_window_close <= 30)
  return 'Due Soon';

return 'Valid';
```

## 🎨 Status Display

### Status Values & Colors

| Status | Color | Badge | Meaning |
|--------|-------|-------|---------|
| **Valid** | Green | `bg-green-100 text-green-800` | Còn hạn > 30 ngày |
| **Due Soon** | Orange | `bg-orange-100 text-orange-800` | Còn ≤ 30 ngày |
| **Expired** | Red | `bg-red-100 text-red-800` | Đã hết hạn |
| **Unknown** | Gray | `bg-gray-100 text-gray-800` | Không có date |

### Localization

| Status | English | Vietnamese |
|--------|---------|------------|
| Valid | Valid | Hiệu lực |
| Due Soon | Due Soon | Sắp hết |
| Expired | Expired | Hết hạn |
| Unknown | Unknown | Không rõ |

## 📝 Examples

### Example 1: Certificate with Next Survey (±6M)
```
Certificate:
  next_survey_display: "15/12/2024 (±6M)"
  valid_date: 2025-12-15

Calculation:
  next_survey_date = 15/12/2024
  window_close = 15/12/2024 + 6 months = 15/06/2025
  today = 27/11/2024
  days_to_close = 200 days

Result: Status = "Valid" (green)
```

### Example 2: Certificate Near Expiry
```
Certificate:
  next_survey_display: "15/01/2025 (-3M)"
  valid_date: 2025-01-15

Calculation:
  next_survey_date = 15/01/2025
  window_close = 15/01/2025 (no adjustment for -3M)
  today = 27/11/2024
  days_to_close = 49 days → 20 days (assuming today is 26/12/2024)

Result: Status = "Due Soon" (orange)
```

### Example 3: Expired Certificate
```
Certificate:
  next_survey_display: "15/11/2024 (±3M)"
  valid_date: 2024-11-15

Calculation:
  next_survey_date = 15/11/2024
  window_close = 15/11/2024 + 3 months = 15/02/2025
  today = 27/11/2024 (assuming after 15/02/2025)
  today > window_close = true

Result: Status = "Expired" (red)
```

### Example 4: Fallback to valid_date
```
Certificate:
  next_survey_display: null
  valid_date: 2025-03-15

Calculation:
  No next_survey → Use valid_date
  valid_date = 15/03/2025
  today = 27/11/2024
  days = 108 days

Result: Status = "Valid" (green)
```

### Example 5: No Date Information
```
Certificate:
  next_survey_display: "N/A"
  valid_date: null

Result: Status = "Unknown" (gray)
```

## 🔄 Comparison: Before vs After

### Before Implementation
```
All Audit Certificates:
└─ Status = "Valid" (always)
   - Certificate expired 2 years ago: "Valid" ❌
   - Certificate expiring tomorrow: "Valid" ❌
   - No visual warning
```

### After Implementation
```
Audit Certificates:
├─ Valid certificate (150 days): "Valid" ✅ (green)
├─ Expiring soon (20 days): "Due Soon" ⚠️ (orange)
├─ Expired certificate: "Expired" ❌ (red)
└─ No date info: "Unknown" ❓ (gray)
```

## ✅ Features

### 1. **Smart Status Calculation**
- Priority: next_survey > valid_date
- Window close annotation support (±6M, ±3M, -6M, -3M)
- Real-time calculation (no backend storage)

### 2. **Visual Alerts**
- Color-coded badges
- Clear visual distinction
- Immediate recognition of status

### 3. **Filter Integration**
- Status filter works with calculated values
- Options: All, Valid, Due Soon, Expired, Unknown

### 4. **Consistency**
- Matches Class & Flag Certificate logic
- Same status values and colors
- Unified user experience

## 🧪 Testing

### Test Scenarios

#### Scenario 1: Certificate with ±6M
```
Input:
  next_survey_display: "15/12/2024 (±6M)"

Expected:
  window_close: 15/06/2025
  Status: "Valid" (if today < 15/05/2025)
          "Due Soon" (if 15/05/2025 < today < 15/06/2025)
          "Expired" (if today > 15/06/2025)
```

#### Scenario 2: Certificate with -3M
```
Input:
  next_survey_display: "15/12/2024 (-3M)"

Expected:
  window_close: 15/12/2024
  Status: "Valid" (if today < 15/11/2024)
          "Due Soon" (if 15/11/2024 < today < 15/12/2024)
          "Expired" (if today > 15/12/2024)
```

#### Scenario 3: No Next Survey
```
Input:
  next_survey_display: null
  valid_date: "2025-03-15"

Expected:
  Use valid_date
  Status: calculated based on valid_date
```

#### Scenario 4: Filter by Status
```
Action: Select "Expired" in status filter
Expected: Only show certificates with status = "Expired"
```

## 📊 Performance

### Calculation Speed
- ✅ Frontend calculation (no backend call)
- ✅ Instant status updates
- ✅ Real-time filtering

### Impact
- Minimal: O(n) where n = number of certificates
- Runs only when:
  - Certificates list rendered
  - Status filter applied
  - Table sorted

## 🎯 Benefits

### For Users
1. **Visual Clarity** - Immediate recognition of certificate status
2. **Early Warning** - "Due Soon" alerts for proactive renewal
3. **Accurate Information** - Status reflects actual expiry state
4. **Better Planning** - Can prioritize based on status

### For Admins
1. **Consistency** - Same logic across all certificate types
2. **Reduced Errors** - Auto-calculated, no manual updates
3. **Better Insights** - Status filters for reporting

## 🔍 How to Verify

### Visual Check
1. Open Audit Certificates page
2. Look for color-coded status badges
3. Check if expired certificates show red badge

### Filter Test
1. Select "Due Soon" in status filter
2. Verify only certificates expiring within 30 days are shown

### Date Logic Test
1. Find certificate with next_survey containing (±6M)
2. Calculate expected window_close manually
3. Verify status matches expectation

## 📝 Future Enhancements

### Possible Additions
1. **Configurable Threshold** - Allow changing 30-day threshold
2. **Status Notifications** - Email alerts for "Due Soon" status
3. **Dashboard Widget** - Count of certificates by status
4. **Export with Status** - Include calculated status in exports

---

**Summary:** Audit Certificates now have intelligent status calculation based on next_survey windows and valid_date, providing real-time visual feedback consistent with Class & Flag Certificates.
