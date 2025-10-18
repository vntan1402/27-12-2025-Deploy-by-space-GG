# Add Crew Form - Grouped Layout Implementation

## Summary
Reorganized "Add New Crew Member" form with logical grouping of fields into 3 main sections: Personal Information, Passport Information, and Employment Information.

## New Layout Structure

### GROUP 1: PERSONAL INFORMATION
**Row 1:** (2 fields)
- Full Name (Vietnamese) - `col-span-2` - Required
- Full Name (English) - `col-span-2` - Optional, Auto-filled

**Row 2:** (4 fields)
- Sex - `col-span-1` - Required
- Date of Birth - `col-span-1` - Required
- Place of Birth (Vietnamese) - `col-span-1` - Required
- Place of Birth (English) - `col-span-1` - Optional, Auto-filled

### GROUP 2: PASSPORT INFORMATION
**Row 3:** (4 fields)
- Passport No. - `col-span-1` - Required
- Nationality - `col-span-1` - Optional
- Passport Expiry - `col-span-1` - Optional
- Rank - `col-span-1` - Optional

### GROUP 3: EMPLOYMENT INFORMATION
**Row 4:** (4 fields, 1 empty)
- Status - `col-span-1` - Optional (Sign on/Standby/Leave)
- Ship Sign On - `col-span-1` - Optional (disabled when Standby)
- Seaman Book - `col-span-1` - Optional
- [Empty] - `col-span-1` - Placeholder

**Row 5:** (4 fields, 1 empty) - **Conditional - Hidden when Standby**
- Place Sign On - `col-span-1` - Optional
- Date Sign On - `col-span-1` - Optional
- Date Sign Off - `col-span-1` - Optional
- [Empty] - `col-span-1` - Placeholder

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│  GROUP 1: PERSONAL INFORMATION                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Row 1:                                                      │
│  ┌──────────────────────┬──────────────────────┐           │
│  │ * Full Name (VN)     │ Full Name (EN)       │           │
│  │   [____________]     │ [____________]       │           │
│  │   span-2             │ span-2               │           │
│  └──────────────────────┴──────────────────────┘           │
│                                                              │
│  Row 2:                                                      │
│  ┌──────┬──────┬──────────┬──────────┐                    │
│  │* Sex │* DOB │* Place   │  Place   │                    │
│  │[___] │[___] │  Birth   │  Birth   │                    │
│  │      │      │  (VN)    │  (EN)    │                    │
│  │span-1│span-1│  [____]  │  [____]  │                    │
│  │      │      │  span-1  │  span-1  │                    │
│  └──────┴──────┴──────────┴──────────┘                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  GROUP 2: PASSPORT INFORMATION                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Row 3:                                                      │
│  ┌─────────┬──────────┬──────────┬──────┐                 │
│  │* Pass-  │ Nation-  │ Passport │ Rank │                 │
│  │  port   │  ality   │ Expiry   │      │                 │
│  │  No.    │          │          │      │                 │
│  │ [____]  │ [_____]  │ [_____]  │[___] │                 │
│  │ span-1  │ span-1   │ span-1   │span-1│                 │
│  └─────────┴──────────┴──────────┴──────┘                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  GROUP 3: EMPLOYMENT INFORMATION                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Row 4:                                                      │
│  ┌────────┬──────────┬─────────┬────────┐                 │
│  │ Status │ Ship     │ Seaman  │ [Empty]│                 │
│  │        │ Sign On  │ Book    │        │                 │
│  │ [____] │ [______] │ [_____] │        │                 │
│  │ span-1 │ span-1   │ span-1  │ span-1 │                 │
│  └────────┴──────────┴─────────┴────────┘                 │
│                                                              │
│  Row 5: (Hidden when Standby)                              │
│  ┌──────────┬──────────┬──────────┬────────┐             │
│  │ Place    │ Date     │ Date     │ [Empty]│             │
│  │ Sign On  │ Sign On  │ Sign Off │        │             │
│  │ [______] │ [______] │ [______] │        │             │
│  │ span-1   │ span-1   │ span-1   │ span-1 │             │
│  └──────────┴──────────┴──────────┴────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~14668-14980

### 1. Reordered Fields

**GROUP 1 - Personal Info:**
- Kept names together (Row 1)
- Moved Sex to start of Row 2
- Moved Date of Birth next to Sex
- Moved Place of Birth fields to end of Row 2

**GROUP 2 - Passport Info:**
- Grouped passport-related fields (Row 3)
- Moved Rank to this group (logical fit for crew profile)

**GROUP 3 - Employment Info:**
- Status, Ship Sign On, Seaman Book (Row 4)
- Conditional sign on/off dates (Row 5)

### 2. Field Size Changes

**No changes** - All fields maintained their sizes:
- Row 1: 2 fields at `col-span-2` each
- Row 2-5: All fields at `col-span-1` (4 per row)

### 3. Logical Grouping Benefits

**Personal Info:**
- ✅ Basic identity information together
- ✅ Easy to fill sequentially
- ✅ Clear separation from documents

**Passport Info:**
- ✅ All document-related fields grouped
- ✅ Rank included as part of crew profile
- ✅ Logical flow: document number → nationality → expiry → position

**Employment Info:**
- ✅ Ship assignment and status together
- ✅ Seaman Book with employment data
- ✅ Sign on/off dates conditional on status

## Comparison: Before vs After

### Before (Previous Layout)
```
Row 1: Full Name (VN) | Full Name (EN)
Row 2: Sex | Rank | Date of Birth | Place of Birth (VN)
Row 3: Place of Birth (EN) | Passport | Nationality | Passport Expiry
Row 4: Status | Ship Sign On | Seaman Book | [Empty]
Row 5: Place Sign On | Date Sign On | Date Sign Off
```

### After (New Grouped Layout)
```
[Personal Info]
Row 1: Full Name (VN) | Full Name (EN)
Row 2: Sex | Date of Birth | Place of Birth (VN) | Place of Birth (EN)

[Passport Info]
Row 3: Passport | Nationality | Passport Expiry | Rank

[Employment Info]
Row 4: Status | Ship Sign On | Seaman Book | [Empty]
Row 5: Place Sign On | Date Sign On | Date Sign Off | [Empty]
```

**Key Differences:**
1. ✅ Rank moved from Row 2 to Row 3 (with Passport info)
2. ✅ Place of Birth (EN) moved from Row 3 to Row 2 (with Personal info)
3. ✅ Ship Sign On and Seaman Book swapped positions in Row 4
4. ✅ Clearer logical grouping

## User Experience Benefits

### 1. Logical Flow
- Users fill out related information together
- Natural progression: Personal → Documents → Employment

### 2. Reduced Cognitive Load
- Clear mental model of information groups
- Easier to remember which fields are where
- Related fields visually close

### 3. Better Scanning
- Can quickly locate group needed
- Less back-and-forth between rows
- Visual separation helps navigation

### 4. Improved Standby Mode
- Employment section clearly separate
- Conditional fields still in same group
- Status change affects only Group 3

## Field Distribution

**Total Fields:** 16
- **Required:** 5 (marked with *)
- **Optional:** 11
- **Conditional:** 3 (hidden when Standby)

**By Group:**
- Group 1 (Personal): 6 fields
- Group 2 (Passport): 4 fields
- Group 3 (Employment): 6 fields (3 conditional)

## Standby Mode Behavior

**When Status = "Standby":**

**Row 4 Changes:**
- Status: Shows "🟠 Chế độ Standby" badge
- Ship Sign On: Disabled, locked to "-", shows "(Auto: -)"
- Seaman Book: No change

**Row 5:**
- ❌ Completely hidden (all 3 date/place fields)

**Visual Impact:**
- Form becomes 4 rows instead of 5
- Cleaner interface for Standby crew
- Only relevant fields visible

## Code Comments

Added clear section markers:
```javascript
{/* ===== GROUP 1: PERSONAL INFORMATION ===== */}
{/* ===== GROUP 2: PASSPORT INFORMATION ===== */}
{/* ===== GROUP 3: EMPLOYMENT INFORMATION ===== */}
```

**Benefits:**
- Easy to locate sections in code
- Clear structure for maintenance
- Helps future developers understand layout

## Testing Recommendations

### Test Case 1: Field Locations
1. Open Add Crew modal
2. Verify groups visible
3. Check field order matches specification

### Test Case 2: Required Fields
1. Try to submit empty form
2. Verify validation on required fields:
   - Full Name (VN)
   - Sex
   - Date of Birth
   - Place of Birth (VN)
   - Passport No.

### Test Case 3: Auto-fill
1. Type Vietnamese name
2. Verify English name auto-fills
3. Type Vietnamese place of birth
4. Verify English place auto-fills

### Test Case 4: Standby Mode
1. Select Status = "Standby"
2. Verify:
   - Ship Sign On disabled
   - Row 5 hidden
   - Badge appears
3. Change back to "Sign on"
4. Verify Row 5 reappears

### Test Case 5: Form Submission
1. Fill all required fields
2. Submit form
3. Verify crew created with correct data
4. Check all field values saved properly

## Related Features

Works with:
- Standby mode toggle button
- Auto-fill functionality
- Form validation
- Passport AI analysis
- Batch upload
- Modal minimize

## Future Enhancements

**Potential additions:**
- Visual separators between groups (borders/spacing)
- Collapsible groups
- Group-level validation indicators
- Progress indicator by group
- Keyboard navigation between groups
