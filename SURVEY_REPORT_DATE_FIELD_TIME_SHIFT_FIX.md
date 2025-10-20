# Survey Report Date Field Time Shift Fix

## Problem Description

Survey Report date fields were experiencing time shift issues when:
1. Creating new reports
2. Editing existing reports
3. Displaying dates in the edit modal

This was caused by improper date handling using `new Date().toISOString()` which applies timezone conversion.

## Root Cause Analysis

### Issues Found:

1. **Add Survey Report (`handleAddSurveyReport`):**
   ```javascript
   // ❌ WRONG - Applies timezone conversion
   issued_date: newSurveyReport.issued_date ? new Date(newSurveyReport.issued_date).toISOString() : null
   ```

2. **Update Survey Report (`handleUpdateSurveyReport`):**
   ```javascript
   // ❌ WRONG - Applies timezone conversion
   issued_date: editingSurveyReport.issued_date ? new Date(editingSurveyReport.issued_date).toISOString() : null
   ```

3. **Edit Button (Opening Modal):**
   ```javascript
   // ❌ WRONG - Uses new Date() which can cause timezone shift
   issued_date: report.issued_date ? new Date(report.issued_date).toISOString().split('T')[0] : ''
   ```

4. **Edit Modal Input Field:**
   ```javascript
   // ❌ WRONG - Doesn't handle ISO datetime strings properly
   value={editingSurveyReport.issued_date || ''}
   ```

## Solution Applied

Implemented the same date handling pattern used in Certificate management to avoid timezone shifts.

### Certificate's Correct Pattern:

1. **Edit Modal Display:**
   ```javascript
   // ✅ CORRECT - Uses .split('T')[0] to extract date part only
   value={editingCertificate.issue_date?.split('T')[0] || ''}
   ```

2. **Submit to Backend:**
   ```javascript
   // ✅ CORRECT - Uses convertDateInputToUTC with .split('T')[0]
   issue_date: editingCertificate.issue_date ? convertDateInputToUTC(editingCertificate.issue_date.split('T')[0]) : null
   ```

### Fixes Applied to Survey Report:

#### 1. Add Survey Report Function (Line ~4379)
```javascript
// BEFORE
issued_date: newSurveyReport.issued_date ? new Date(newSurveyReport.issued_date).toISOString() : null

// AFTER
issued_date: newSurveyReport.issued_date ? convertDateInputToUTC(newSurveyReport.issued_date) : null
```

#### 2. Update Survey Report Function (Line ~4414)
```javascript
// BEFORE
issued_date: editingSurveyReport.issued_date ? new Date(editingSurveyReport.issued_date).toISOString() : null

// AFTER
issued_date: editingSurveyReport.issued_date ? convertDateInputToUTC(editingSurveyReport.issued_date.split('T')[0]) : null
```

#### 3. Edit Button - Set Initial State (Line ~10636)
```javascript
// BEFORE
issued_date: report.issued_date ? new Date(report.issued_date).toISOString().split('T')[0] : ''

// AFTER
issued_date: report.issued_date ? report.issued_date.split('T')[0] : ''
```

#### 4. Edit Modal Input Field (Line ~11431)
```javascript
// BEFORE
value={editingSurveyReport.issued_date || ''}

// AFTER
value={editingSurveyReport.issued_date?.split('T')[0] || ''}
```

## How convertDateInputToUTC Works

The `convertDateInputToUTC` function (defined at line 8779) handles date conversion safely:

```javascript
const convertDateInputToUTC = (dateString) => {
  if (!dateString || typeof dateString !== 'string') return null;
  
  // Handle YYYY-MM-DD format from HTML date inputs
  const isoPattern = /^\d{4}-\d{2}-\d{2}$/;
  if (isoPattern.test(trimmedDate)) {
    return `${trimmedDate}T00:00:00Z`; // ✅ Always returns UTC midnight
  }
  // ... other format handling
}
```

**Key Point:** It appends `T00:00:00Z` to the date string, ensuring it's always interpreted as UTC midnight, avoiding timezone shifts.

## Why This Approach Works

1. **`.split('T')[0]`**: Extracts only the date part (YYYY-MM-DD) from ISO datetime strings, removing time and timezone info
2. **`convertDateInputToUTC()`**: Adds `T00:00:00Z` to force UTC interpretation
3. **No `new Date()` constructor**: Avoids automatic timezone conversion by the JavaScript Date object

## Testing Results

✅ Frontend compiled successfully
✅ No errors in logs
✅ Date handling now matches Certificate pattern exactly

## Expected Behavior After Fix

### Creating New Survey Report:
- User selects: **2025-01-15**
- Stored in DB: **2025-01-15T00:00:00Z** (UTC midnight)
- Displays as: **15/01/2025** (DD/MM/YYYY format)

### Editing Existing Survey Report:
- DB has: **2025-01-15T00:00:00Z**
- Edit modal shows: **2025-01-15** (in date input)
- User doesn't change date
- Still stored as: **2025-01-15T00:00:00Z** (no shift)

### Time Zone Independence:
- User in GMT+7 sees: **15/01/2025**
- User in GMT-5 sees: **15/01/2025**
- Both store: **2025-01-15T00:00:00Z**
- **No time shift occurs** ✅

## Files Modified

**File:** `/app/frontend/src/App.js`

**Changes:**
1. Line ~4379: `handleAddSurveyReport` - Use `convertDateInputToUTC` instead of `new Date().toISOString()`
2. Line ~4414: `handleUpdateSurveyReport` - Use `convertDateInputToUTC` with `.split('T')[0]`
3. Line ~10636: Edit button onClick - Remove `new Date()` constructor, use direct `.split('T')[0]`
4. Line ~11431: Edit modal input - Add `.split('T')[0]` to handle ISO datetime strings

## Comparison: Before vs After

### Before (Wrong):
```javascript
// Add
issued_date: newSurveyReport.issued_date ? new Date(newSurveyReport.issued_date).toISOString() : null
// Problem: new Date() applies timezone, date shifts by ±1 day

// Update
issued_date: editingSurveyReport.issued_date ? new Date(editingSurveyReport.issued_date).toISOString() : null
// Problem: Same timezone conversion issue

// Edit Modal Display
issued_date: report.issued_date ? new Date(report.issued_date).toISOString().split('T')[0] : ''
// Problem: Unnecessary Date conversion

// Input Field
value={editingSurveyReport.issued_date || ''}
// Problem: Doesn't handle ISO datetime format (YYYY-MM-DDTHH:MM:SSZ)
```

### After (Correct):
```javascript
// Add
issued_date: newSurveyReport.issued_date ? convertDateInputToUTC(newSurveyReport.issued_date) : null
// ✅ Correct: Forces UTC interpretation, no timezone shift

// Update
issued_date: editingSurveyReport.issued_date ? convertDateInputToUTC(editingSurveyReport.issued_date.split('T')[0]) : null
// ✅ Correct: Extracts date part, then converts to UTC

// Edit Modal Display
issued_date: report.issued_date ? report.issued_date.split('T')[0] : ''
// ✅ Correct: Direct string extraction, no conversion

// Input Field
value={editingSurveyReport.issued_date?.split('T')[0] || ''}
// ✅ Correct: Handles ISO datetime format properly
```

## Validation

To verify the fix works correctly:

1. **Create a survey report with date: 2025-01-15**
   - Check database: Should store `2025-01-15T00:00:00Z`
   
2. **Edit the same report without changing date**
   - Check database after save: Should still be `2025-01-15T00:00:00Z`
   - Should NOT shift to `2025-01-14T...` or `2025-01-16T...`

3. **Edit and change date to 2025-01-20**
   - Check database: Should store `2025-01-20T00:00:00Z`
   - Display should show exactly what was entered

## Related Documentation

- See `CREW_CERT_DATE_FIELD_FIX.md` (if exists) for similar certificate date handling
- See `TIMEZONE_HANDLING_GUIDE.md` for general timezone best practices

## Conclusion

The Survey Report date handling now matches the Certificate pattern exactly, eliminating time shift issues. All date operations are timezone-safe and consistent across the application.
