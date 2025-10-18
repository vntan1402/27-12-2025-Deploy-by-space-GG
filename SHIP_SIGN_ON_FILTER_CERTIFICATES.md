# Ship Sign On Filter - Crew Certificates View

## Overview
Added "Ship Sign On" filter to Crew Certificates View, positioned before the Status filter, matching the filter functionality in Company Crew List.

## User Request
"Trong Crew Certificates View, thêm filter Ship Sign on vào trước filter Status giống như filter Ship Sign on của Company Crew List"

Translation: "In Crew Certificates View, add Ship Sign On filter before Status filter, similar to the Ship Sign On filter in Company Crew List"

## Implementation

### 1. State Update

**Location:** `/app/frontend/src/App.js` (lines ~1001-1004)

**Before:**
```javascript
const [certFilters, setCertFilters] = useState({
  status: 'all',     // all, Valid, Expiring Soon, Expired, Unknown
  crewName: 'all'    // all, or specific crew name
});
```

**After:**
```javascript
const [certFilters, setCertFilters] = useState({
  shipSignOn: 'all',  // all, specific ship name, or "-" for Standby
  status: 'all',      // all, Valid, Expiring Soon, Expired, Unknown
  crewName: 'all'     // all, or specific crew name
});
```

**Change:** Added `shipSignOn` filter field.

### 2. UI - Ship Sign On Filter Dropdown

**Location:** `/app/frontend/src/App.js` (lines ~11398-11430)

**Placement:** Between "Divider" and "Status Filter"

**Code:**
```jsx
{/* Ship Sign On Filter */}
<div className="flex items-center space-x-2">
  <label className="text-sm text-gray-600 whitespace-nowrap">
    {language === 'vi' ? 'Tàu:' : 'Ship:'}
  </label>
  <select
    value={certFilters.shipSignOn}
    onChange={(e) => setCertFilters({...certFilters, shipSignOn: e.target.value})}
    className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
  >
    <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
    {(() => {
      // Get unique ship sign on values from certificates via crew lookup
      const shipSignOnSet = new Set();
      crewCertificates.forEach(cert => {
        const shipStatus = getCertificateShipStatus(cert);
        if (shipStatus.isStandby) {
          shipSignOnSet.add('-');
        } else {
          shipSignOnSet.add(shipStatus.ship);
        }
      });
      
      // Convert to array and sort: "-" first, then ships alphabetically
      const shipSignOnArray = Array.from(shipSignOnSet).sort((a, b) => {
        if (a === '-') return -1;
        if (b === '-') return 1;
        return a.localeCompare(b);
      });
      
      return shipSignOnArray.map(shipSignOn => (
        <option key={shipSignOn} value={shipSignOn}>
          {shipSignOn === '-' ? (language === 'vi' ? 'Standby' : 'Standby') : shipSignOn}
        </option>
      ));
    })()}
  </select>
</div>
```

**Features:**
- **Label:** "Tàu:" (Vietnamese) / "Ship:" (English)
- **Options:** 
  - "Tất cả" / "All" (default)
  - "Standby" (for crew with ship_sign_on = "-")
  - Ship names (alphabetically sorted)
- **Sorting:** Standby first, then ships A-Z
- **Dynamic:** Options generated from actual certificate data

### 3. Filter Logic Update

**Location:** `/app/frontend/src/App.js` (lines ~11697-11728)

**Added Ship Sign On Filter:**
```javascript
// Apply ship sign on filter
if (certFilters.shipSignOn !== 'all') {
  const shipStatus = getCertificateShipStatus(cert);
  const certShipSignOn = shipStatus.isStandby ? '-' : shipStatus.ship;
  if (certShipSignOn !== certFilters.shipSignOn) {
    return false;
  }
}
```

**Filter Order:**
1. Search filter (by crew name, cert name, cert no, issued by)
2. **Ship Sign On filter** (NEW)
3. Status filter (Valid, Expiring Soon, Expired, etc.)
4. Crew Name filter

### 4. Reset Button Update

**Location:** `/app/frontend/src/App.js` (lines ~11464-11470)

**Before:**
```javascript
{(certFilters.status !== 'all' || certFilters.crewName !== 'all' || certificatesSearch) && (
  <button onClick={() => {
    setCertFilters({ status: 'all', crewName: 'all' });
    setCertificatesSearch('');
  }}>
```

**After:**
```javascript
{(certFilters.shipSignOn !== 'all' || certFilters.status !== 'all' || certFilters.crewName !== 'all' || certificatesSearch) && (
  <button onClick={() => {
    setCertFilters({ shipSignOn: 'all', status: 'all', crewName: 'all' });
    setCertificatesSearch('');
  }}>
```

**Changes:**
- Added `shipSignOn !== 'all'` to button visibility condition
- Added `shipSignOn: 'all'` to reset action

### 5. Helper Functions Updated

**handleCrewNameDoubleClick:**
```javascript
// Before
setCertFilters({ status: 'all', crewName: crew.full_name });

// After
setCertFilters({ shipSignOn: 'all', status: 'all', crewName: crew.full_name });
```

**handleBackToCrewList:**
```javascript
// Before
setCertFilters({ status: 'all', crewName: 'all' });

// After
setCertFilters({ shipSignOn: 'all', status: 'all', crewName: 'all' });
```

## Filter Bar Layout

### Visual Structure

**Before:**
```
[🔍 Search] | [Status ▼] [Crew ▼] [🔄 Reset]
```

**After:**
```
[🔍 Search] | [Ship ▼] [Status ▼] [Crew ▼] [🔄 Reset]
```

### Complete Filter Bar

```
┌────────────────────────────────────────────────────────────────┐
│ [🔍 Search box...........]  |  [Ship: All ▼]  [Status: All ▼]  │
│                                  [Crew: All ▼]  [🔄 Reset]      │
└────────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Filter by Ship

**Action:** User selects "BROTHER 36" from Ship dropdown

**Result:**
- Only certificates for crew on BROTHER 36 are shown
- Status and Crew filters still available
- Certificate count updates

**Display:**
```
Ship: BROTHER 36 ▼  |  Status: All  |  Crew: All
----------------------------------------------------
John Doe    | BROTHER 36 | Captain  | COC Certificate
Jane Smith  | BROTHER 36 | Engineer | STCW Certificate
```

### Example 2: Filter by Standby

**Action:** User selects "Standby" from Ship dropdown

**Result:**
- Only Standby crew certificates shown
- Shows certificates with ship_sign_on = "-"

**Display:**
```
Ship: Standby ▼  |  Status: All  |  Crew: All
----------------------------------------------------
Mike Johnson  | Standby Crew | Officer | Medical Cert
Sarah Lee     | Standby Crew | Cook    | Food Safety
```

### Example 3: Combined Filters

**Action:** 
1. Select "BROTHER 36" from Ship
2. Select "Expired" from Status

**Result:**
- Only expired certificates for BROTHER 36 crew

**Display:**
```
Ship: BROTHER 36  |  Status: Expired ▼  |  Crew: All
----------------------------------------------------
John Doe | BROTHER 36 | Captain | Expired COC (2023-01-15)
```

### Example 4: All Filters Combined

**Action:**
1. Ship: MINH ANH 09
2. Status: Expiring Soon
3. Crew: Nguyễn Văn A

**Result:**
- Only certificates for Nguyễn Văn A on MINH ANH 09 that are expiring soon

**Display:**
```
Ship: MINH ANH 09  |  Status: Expiring Soon  |  Crew: Nguyễn Văn A
--------------------------------------------------------------------
Nguyễn Văn A | MINH ANH 09 | Engineer | STCW (expires 2025-03-15)
```

## Filter Options Generation

### Ship Sign On Options Logic

```javascript
// Step 1: Collect unique ship sign on values
const shipSignOnSet = new Set();
crewCertificates.forEach(cert => {
  const shipStatus = getCertificateShipStatus(cert);
  if (shipStatus.isStandby) {
    shipSignOnSet.add('-');
  } else {
    shipSignOnSet.add(shipStatus.ship);
  }
});

// Step 2: Sort (Standby first, then ships alphabetically)
const shipSignOnArray = Array.from(shipSignOnSet).sort((a, b) => {
  if (a === '-') return -1;  // Standby first
  if (b === '-') return 1;
  return a.localeCompare(b);  // Alphabetical
});

// Step 3: Render options
shipSignOnArray.map(shipSignOn => (
  <option key={shipSignOn} value={shipSignOn}>
    {shipSignOn === '-' ? 'Standby' : shipSignOn}
  </option>
));
```

**Result:**
```
All
Standby          ← Always first if present
BROTHER 36       ← Alphabetical
MINH ANH 09
OCEAN STAR
```

## Comparison with Company Crew List

### Company Crew List Filter

**Location:** Crew List table header
**Options:** All, Ship names, "-" (Standby)
**Functionality:** Filters crew members by ship_sign_on field

### Crew Certificates View Filter (NEW)

**Location:** Certificates table header
**Options:** All, Ship names, "Standby"
**Functionality:** Filters certificates by crew's ship_sign_on

### Similarities

✅ Same data source (crew.ship_sign_on)
✅ Same filter logic (exact match)
✅ Same option display ("Standby" for "-")
✅ Same sorting (Standby first, then alphabetical)
✅ Same UI position (before Status filter)
✅ Same styling and behavior

### Differences

| Feature | Crew List | Certificates View |
|---------|-----------|-------------------|
| Filters | Crew records | Certificate records |
| Data lookup | Direct field | Via crew_id → crew.ship_sign_on |
| Reset behavior | Resets to "All" | Resets all filters |

## Filter Interaction

### Single Filter Active

**Ship Filter Only:**
- Shows all certificates for selected ship
- All statuses included
- All crew included

### Multiple Filters Active

**Ship + Status:**
- Shows certificates matching BOTH conditions
- Example: BROTHER 36 + Expired = Only expired certs on BROTHER 36

**Ship + Crew:**
- Shows certificates matching BOTH conditions
- Example: MINH ANH 09 + Nguyễn Văn A = Only A's certs on MINH ANH 09

**All Filters:**
- Most restrictive
- Only certificates matching ALL conditions
- Example: BROTHER 36 + Valid + John Doe = John's valid certs on BROTHER 36

## Reset Button Behavior

### Visibility Condition

Shows when ANY filter is active:
- `shipSignOn !== 'all'` OR
- `status !== 'all'` OR
- `crewName !== 'all'` OR
- `certificatesSearch` has value

### Reset Action

Clears ALL filters:
```javascript
setCertFilters({ 
  shipSignOn: 'all', 
  status: 'all', 
  crewName: 'all' 
});
setCertificatesSearch('');
```

**Result:** Table shows all certificates (no filters applied)

## Benefits

### 1. Consistent UX
- Matches Company Crew List filter behavior
- Users already familiar with Ship filter
- Same position, same styling

### 2. Better Organization
- Quickly view certificates by ship
- Separate Standby from ship-assigned
- Combine with other filters for precise queries

### 3. Performance
- Client-side filtering (fast)
- No additional API calls
- Real-time updates

### 4. Flexibility
- Works with existing filters
- Can be used alone or combined
- Easy to clear with Reset button

## Technical Notes

### Filter Execution Order

```javascript
certificates
  .filter(cert => {
    // 1. Search filter
    if (search && !matches) return false;
    
    // 2. Ship Sign On filter (NEW)
    if (shipSignOn !== 'all' && !matches) return false;
    
    // 3. Status filter
    if (status !== 'all' && !matches) return false;
    
    // 4. Crew Name filter
    if (crewName !== 'all' && !matches) return false;
    
    return true;
  })
```

**Why this order?**
1. Search: Broadest filter, eliminates most records
2. Ship: Groups certificates logically
3. Status: Further refinement within ship
4. Crew: Most specific filter

### Performance Considerations

**Filter Performance:**
- O(n) for each filter pass
- Total: O(4n) = O(n)
- Fast for typical dataset sizes (<500 certs)

**Option Generation:**
- Computed on every render
- Uses Set for uniqueness (O(n))
- Sorts result (O(m log m) where m = unique ships)
- Consider memoization if performance issues

**Optimization (if needed):**
```javascript
const shipOptions = useMemo(() => {
  // Generate options
}, [crewCertificates]);
```

## Edge Cases

### Case 1: No certificates
- Filter dropdown shows only "All"
- No ship options available
- Table shows empty state

### Case 2: All certificates from one ship
- Filter dropdown shows: All, that ship
- No "Standby" option if no standby certs
- Filtering has minimal effect

### Case 3: Certificate with unknown ship
- getCertificateShipStatus returns "Unknown"
- Appears in filter dropdown
- Can be filtered

### Case 4: Crew changes ships
- Filter uses CURRENT ship_sign_on
- Old certificates may not match crew's current ship
- This is correct behavior (historical data)

## Files Modified

**Frontend:**
- `/app/frontend/src/App.js`
  - State: Added `shipSignOn` to `certFilters` (lines ~1001-1004)
  - UI: Added Ship Sign On filter dropdown (lines ~11400-11430)
  - Logic: Added ship filter in table filter (lines ~11709-11717)
  - Reset: Updated reset button (lines ~11464-11470)
  - Helpers: Updated filter initialization functions

**Documentation:**
- This file: `/app/SHIP_SIGN_ON_FILTER_CERTIFICATES.md`

## Testing Checklist

### Basic Functionality
- [ ] Ship filter dropdown appears before Status filter
- [ ] Dropdown shows "All" by default
- [ ] Options include "Standby" and ship names
- [ ] Options sorted: Standby first, then ships A-Z
- [ ] Selecting ship filters certificates correctly
- [ ] Selecting "Standby" shows only standby certificates

### Combined Filters
- [ ] Ship + Status filters work together
- [ ] Ship + Crew filters work together
- [ ] All three filters work together
- [ ] Search + Ship filter work together

### Reset Button
- [ ] Reset button appears when Ship filter active
- [ ] Reset button clears Ship filter
- [ ] Reset button clears all filters simultaneously

### Edge Cases
- [ ] Empty certificate list → Filter dropdown shows only "All"
- [ ] All same ship → Filter works correctly
- [ ] Certificate with unknown ship → Handles gracefully
- [ ] Dynamic option generation → Updates when certs change

### UI/UX
- [ ] Filter dropdown styling matches other filters
- [ ] Labels in correct language (Vietnamese/English)
- [ ] Hover effects work
- [ ] Dropdown width appropriate

## Status
✅ State updated with shipSignOn field
✅ UI filter dropdown added before Status
✅ Filter logic implemented
✅ Reset button updated
✅ Helper functions updated
✅ Consistent with Company Crew List
✅ Ready for testing
