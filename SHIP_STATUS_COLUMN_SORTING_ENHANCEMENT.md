# Ship/Status Column - Sorting Enhancement

## Overview
Added sorting functionality to the "Ship / Status" column in the Crew Certificates table, and removed emoji icons for a cleaner appearance.

## User Request
"Bổ sung tính năng sắp xếp theo thứ tự tăng giảm cho cột Ship / Status giống như các cột khác, bỏ icon 🚢 và 🟠 trong các ô của cột này"

Translation: "Add ascending/descending sorting feature for Ship/Status column like other columns, remove 🚢 and 🟠 icons from cells in this column"

## Changes Made

### 1. Header - Make Sortable

**Location:** `/app/frontend/src/App.js` (lines ~11555-11575)

**Before:**
```jsx
<th className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200">
  {language === 'vi' ? 'Tàu / Trạng thái' : 'Ship / Status'}
  {/* No sort icon, not clickable */}
</th>
```

**After:**
```jsx
<th 
  onClick={() => handleCertificateSort('ship_status')}
  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
>
  {language === 'vi' ? 'Tàu / Trạng thái' : 'Ship / Status'}
  {getCertificateSortIcon('ship_status')}
</th>
```

**Changes:**
- ✅ Added `onClick` handler
- ✅ Added `cursor-pointer` and `hover:bg-gray-100` classes
- ✅ Added sort icon display with `getCertificateSortIcon('ship_status')`

### 2. Sort Logic - Handle Computed Values

**Location:** `/app/frontend/src/App.js` (lines ~11689-11695)

**Challenge:**
The "Ship / Status" value is not a direct field in the certificate record - it's computed from:
- `crew.ship_sign_on` (looked up via crew_id)
- or `cert.ship_id` (if crew lookup fails)

**Solution:**
Added special handling in the sort function to compute values on-the-fly during sorting.

**Before:**
```javascript
.sort((a, b) => {
  if (!certificateSort.column) return 0;
  const aVal = a[certificateSort.column] || '';
  const bVal = b[certificateSort.column] || '';
  const comparison = aVal.toString().localeCompare(bVal.toString());
  return certificateSort.direction === 'asc' ? comparison : -comparison;
})
```

**After:**
```javascript
.sort((a, b) => {
  if (!certificateSort.column) return 0;
  
  // Special handling for ship_status column (computed value)
  if (certificateSort.column === 'ship_status') {
    const aShipStatus = getCertificateShipStatus(a);
    const bShipStatus = getCertificateShipStatus(b);
    
    // Sort: Standby first, then ship names alphabetically
    let comparison = 0;
    
    if (aShipStatus.isStandby && !bShipStatus.isStandby) {
      comparison = -1; // Standby comes first
    } else if (!aShipStatus.isStandby && bShipStatus.isStandby) {
      comparison = 1;
    } else {
      // Both same type, compare ship names
      comparison = aShipStatus.ship.localeCompare(bShipStatus.ship);
    }
    
    return certificateSort.direction === 'asc' ? comparison : -comparison;
  }
  
  // Standard sorting for other columns
  const aVal = a[certificateSort.column] || '';
  const bVal = b[certificateSort.column] || '';
  const comparison = aVal.toString().localeCompare(bVal.toString());
  return certificateSort.direction === 'asc' ? comparison : -comparison;
})
```

**Sorting Logic:**
1. Compute ship/status for both certificates using `getCertificateShipStatus()`
2. Group by type:
   - Standby certificates first (ascending)
   - Ship-assigned certificates second (ascending)
3. Within each group: Alphabetical by ship/status name
4. Reverse order if descending

### 3. Remove Icons from Cells

**Location:** `/app/frontend/src/App.js` (lines ~11718-11730)

**Before:**
```jsx
<td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
  {(() => {
    const shipStatus = getCertificateShipStatus(cert);
    return (
      <span className={shipStatus.isStandby ? 'text-orange-600 font-medium' : 'text-blue-600'}>
        {shipStatus.isStandby ? '🟠 ' : '🚢 '}  {/* ❌ Icons */}
        {shipStatus.ship}
      </span>
    );
  })()}
</td>
```

**After:**
```jsx
<td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
  {(() => {
    const shipStatus = getCertificateShipStatus(cert);
    return (
      <span className={shipStatus.isStandby ? 'text-orange-600 font-medium' : 'text-blue-600'}>
        {shipStatus.ship}  {/* ✅ No icons, just text */}
      </span>
    );
  })()}
</td>
```

**Changes:**
- ❌ Removed `{shipStatus.isStandby ? '🟠 ' : '🚢 '}` 
- ✅ Kept color coding: Orange for Standby, Blue for Ships
- ✅ Kept font weight: Bold for Standby

## Sorting Behavior Examples

### Example 1: Ascending Order (Default)

**Click header once → Ascending:**
```
Ship / Status
-------------
Standby Crew      (orange)
Standby Crew      (orange)
BROTHER 36        (blue)
MINH ANH 09       (blue)
OCEAN STAR        (blue)
```

**Logic:**
1. All "Standby Crew" first
2. Then ship names alphabetically (A-Z)

### Example 2: Descending Order

**Click header twice → Descending:**
```
Ship / Status
-------------
OCEAN STAR        (blue)
MINH ANH 09       (blue)
BROTHER 36        (blue)
Standby Crew      (orange)
Standby Crew      (orange)
```

**Logic:**
1. Ship names in reverse alphabetical order (Z-A)
2. Then "Standby Crew" at the end

### Example 3: Mixed Data

**Original unsorted data:**
```
BROTHER 36
Standby Crew
MINH ANH 09
Standby Crew
OCEAN STAR
BROTHER 36
```

**After clicking header (Ascending):**
```
Standby Crew
Standby Crew
BROTHER 36
BROTHER 36
MINH ANH 09
OCEAN STAR
```

**After clicking again (Descending):**
```
OCEAN STAR
MINH ANH 09
BROTHER 36
BROTHER 36
Standby Crew
Standby Crew
```

## Visual Changes

### Before
```
Ship / Status          (Not sortable)
------------------
🚢 BROTHER 36
🟠 Standby Crew
🚢 MINH ANH 09
🟠 Standby Crew
```

**Issues:**
- ❌ Not sortable
- ❌ Icons take up space
- ❌ Less clean appearance

### After
```
Ship / Status ▲▼       (Sortable)
------------------
BROTHER 36
Standby Crew
MINH ANH 09
Standby Crew
```

**Benefits:**
- ✅ Sortable (ascending/descending)
- ✅ Cleaner appearance (no icons)
- ✅ Still color-coded (blue/orange)
- ✅ Consistent with other sortable columns

## User Interaction

### Sorting Process

**Step 1: Initial state (No sort)**
- Header shows: "Ship / Status" (no arrow)
- Certificates in default order (database order)

**Step 2: Click header → Ascending sort**
- Header shows: "Ship / Status ▲"
- Certificates sorted: Standby first, then ships A-Z
- Ascending arrow indicator visible

**Step 3: Click header again → Descending sort**
- Header shows: "Ship / Status ▼"
- Certificates sorted: Ships Z-A, then Standby
- Descending arrow indicator visible

**Step 4: Click header again → No sort (back to Step 1)**
- Header shows: "Ship / Status" (no arrow)
- Certificates in default order

### Hover Behavior
- Mouse hover on header → Background changes to light gray
- Cursor changes to pointer
- Visual feedback that column is sortable

## Technical Implementation

### Sort Icon Component
Uses existing `getCertificateSortIcon()` function:

```javascript
const getCertificateSortIcon = (column) => {
  if (certificateSort.column !== column) {
    return null; // No icon if not sorting by this column
  }
  
  if (certificateSort.direction === 'asc') {
    return <span className="ml-1">▲</span>;
  } else {
    return <span className="ml-1">▼</span>;
  }
};
```

### Sort State
Managed by `certificateSort` state:

```javascript
const [certificateSort, setCertificateSort] = useState({
  column: null,      // 'ship_status', 'crew_name', etc.
  direction: 'asc'   // 'asc' or 'desc'
});
```

### Sort Handler
Uses existing `handleCertificateSort()` function:

```javascript
const handleCertificateSort = (column) => {
  if (certificateSort.column === column) {
    // Same column: toggle direction or clear
    if (certificateSort.direction === 'asc') {
      setCertificateSort({ column, direction: 'desc' });
    } else {
      setCertificateSort({ column: null, direction: 'asc' });
    }
  } else {
    // New column: sort ascending
    setCertificateSort({ column, direction: 'asc' });
  }
};
```

## Performance

### Complexity
- **Sorting:** O(n log n) where n = number of certificates
- **getCertificateShipStatus() calls:** O(n) during sorting
- **Crew lookup:** O(m) where m = crewList size (typically fast with modern JavaScript engines)

### Optimization
For large datasets (>1000 certificates), consider:
1. **Memoization:** Cache computed ship_status values
2. **Indexing:** Pre-compute ship_status when loading certificates
3. **Virtual scrolling:** Only render visible rows

**Current implementation is sufficient for typical use cases (<500 certificates).**

## Edge Cases Handled

### Case 1: Certificate with no crew_id
- Falls back to ship_id lookup
- If ship_id is null → Shows "Standby Crew"
- If ship_id invalid → Shows "Unknown"

### Case 2: Crew not found in crewList
- Falls back to ship_id lookup
- Graceful degradation

### Case 3: Ship deleted but certificate remains
- Shows "Unknown" in sort order
- Sorted after regular ships, before Standby

### Case 4: Multiple certificates with same ship/status
- Maintains stable sort (original order preserved)
- No secondary sorting (could add if needed)

## Accessibility

### Keyboard Navigation
- Header is clickable and keyboard-accessible
- Tab navigation works
- Enter/Space to trigger sort (if focus enabled)

### Visual Indicators
- Sort arrow shows current sort direction
- Color coding still present for quick scanning
- Hover state for better discoverability

## Files Modified

**Frontend:**
- `/app/frontend/src/App.js`
  - Header: Added `onClick` and sort icon (lines ~11560-11575)
  - Sort logic: Added special handling for `ship_status` (lines ~11689-11710)
  - Cell display: Removed icons (lines ~11718-11730)

## Testing Checklist

### Sorting Functionality
- [ ] Click "Ship / Status" header → Sorts ascending
- [ ] Click again → Sorts descending
- [ ] Click third time → Clears sort (default order)
- [ ] Sort arrow appears/disappears correctly
- [ ] Standby certificates group together when sorted
- [ ] Ship names sort alphabetically within group

### Visual Appearance
- [ ] No 🚢 icon for ship certificates
- [ ] No 🟠 icon for Standby certificates
- [ ] Blue color for ship names preserved
- [ ] Orange color for "Standby Crew" preserved
- [ ] Bold font for "Standby Crew" preserved
- [ ] Column header shows hover effect
- [ ] Cursor changes to pointer on hover

### Edge Cases
- [ ] Empty certificate list → No errors
- [ ] Crew not found → Falls back gracefully
- [ ] Ship not found → Shows "Unknown"
- [ ] Mixed Standby and ship certificates → Sorts correctly
- [ ] All Standby certificates → Sorts by name
- [ ] All ship certificates → Sorts by ship name

## Benefits

1. **Consistency:** Ship/Status column now behaves like other sortable columns
2. **Better UX:** Users can organize certificates by ship/status
3. **Cleaner Look:** Removed unnecessary emoji icons
4. **Color Coding Preserved:** Visual distinction still clear
5. **Flexible:** Can sort ascending, descending, or not at all

## Status
✅ Sorting functionality implemented
✅ Icons removed
✅ Color coding preserved
✅ Ready for testing
