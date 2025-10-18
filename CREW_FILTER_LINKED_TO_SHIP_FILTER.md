# Crew Filter Linked to Ship Sign On Filter - Implementation

## Overview
Modified Crew filter dropdown to dynamically display crew members based on the selected Ship Sign On filter value, creating a hierarchical filtering system.

## User Request
"Tôi muốn lọc theo Crew List của Ship được lựa chọn trong Filter Ship Sign On"

Translation: "I want to filter by Crew List of the Ship selected in Ship Sign On filter"

## Implementation

### New Behavior

**Ship Sign On Filter Controls Crew Dropdown:**

1. **Ship Sign On = "All"**
   - Crew dropdown shows: ALL crew in company
   - No filtering applied

2. **Ship Sign On = Specific Ship (e.g., "BROTHER 36")**
   - Crew dropdown shows: Only crew with `ship_sign_on = "BROTHER 36"`
   - Filtered list

3. **Ship Sign On = "Standby"**
   - Crew dropdown shows: Only crew with `ship_sign_on = "-"`
   - Standby crew only

### Code Changes

**Location:** `/app/frontend/src/App.js`

#### 1. Crew Dropdown Logic (lines ~11538-11585)

**New Logic:**
```javascript
{(() => {
  // In Certificates View: Filter crew based on Ship Sign On filter selection
  if (showCertificatesView && crewList.length > 0) {
    let filteredCrew = crewList;
    
    // Apply Ship Sign On filter to crew list
    if (certFilters.shipSignOn !== 'all') {
      filteredCrew = crewList.filter(crew => {
        const crewShipSignOn = crew.ship_sign_on || '-';
        return crewShipSignOn === certFilters.shipSignOn;
      });
    }
    
    // Generate dropdown options from filtered crew
    return filteredCrew
      .map(crew => ({
        value: crew.full_name,
        displayName: language === 'en' && crew.full_name_en 
          ? crew.full_name_en 
          : crew.full_name
      }))
      .sort((a, b) => a.displayName.localeCompare(b.displayName))
      .map(item => (
        <option key={item.value} value={item.value}>
          {item.displayName}
        </option>
      ));
  }
  
  // In Crew List View: Filter by selected ship (original logic)
  // ... existing logic
  
  // Fallback: get from certificates
  // ... existing logic
})()}
```

**Key Points:**
- Only applies in Certificates View (`showCertificatesView = true`)
- Uses `certFilters.shipSignOn` instead of `selectedShip`
- Filters `crewList` based on `ship_sign_on` field
- Maintains bilingual support

#### 2. Auto-Reset Crew Filter (lines ~1006-1013)

**Added useEffect:**
```javascript
// Auto-reset crew filter when ship sign on filter changes
useEffect(() => {
  if (showCertificatesView && certFilters.shipSignOn !== 'all') {
    // Reset crew filter to 'all' when ship filter changes
    // User can then select specific crew from the filtered list
    setCertFilters(prev => ({ ...prev, crewName: 'all' }));
  }
}, [certFilters.shipSignOn, showCertificatesView]);
```

**Purpose:**
- Automatically resets Crew filter to "All" when Ship Sign On filter changes
- Prevents showing invalid selections (e.g., crew from different ship)
- User sees fresh, relevant crew list after changing ship filter

## User Flow Examples

### Example 1: Filter by Specific Ship

**Steps:**
1. User opens Crew Certificates View
2. Selects "BROTHER 36" from Ship Sign On filter
3. Crew dropdown automatically updates

**Result:**
```
Ship Sign On: BROTHER 36 ▼
Crew: All ▼  ← Auto-reset to "All"

Crew Dropdown Options:
- All
- John Doe (crew on BROTHER 36)
- Jane Smith (crew on BROTHER 36)
- Mike Johnson (crew on BROTHER 36)
```

**Certificate Table:**
- Shows only certificates for BROTHER 36 crew
- Further filterable by specific crew member

### Example 2: Filter by Standby

**Steps:**
1. User selects "Standby" from Ship Sign On filter
2. Crew dropdown updates to show only Standby crew

**Result:**
```
Ship Sign On: Standby ▼
Crew: All ▼

Crew Dropdown Options:
- All
- Sarah Lee (Standby)
- Tom Brown (Standby)
- Alice Wong (Standby)
```

**Certificate Table:**
- Shows only certificates for Standby crew
- Further filterable by specific crew member

### Example 3: View All Certificates

**Steps:**
1. User selects "All" from Ship Sign On filter
2. Crew dropdown shows ALL crew in company

**Result:**
```
Ship Sign On: All ▼
Crew: All ▼

Crew Dropdown Options:
- All
- John Doe (BROTHER 36)
- Jane Smith (BROTHER 36)
- Mike Johnson (MINH ANH 09)
- Sarah Lee (Standby)
- Tom Brown (Standby)
- ... (all crew)
```

**Certificate Table:**
- Shows ALL certificates (all ships + standby)
- Further filterable by specific crew member

### Example 4: Hierarchical Filtering

**Steps:**
1. Ship Sign On: "BROTHER 36"
2. Status: "Expired"
3. Crew: "John Doe"

**Result:**
```
Ship Sign On: BROTHER 36
Status: Expired
Crew: John Doe

Table shows: Only John Doe's expired certificates on BROTHER 36
```

## Comparison

### Before (Old Logic)

**Crew Dropdown Source:**
- Filtered by `selectedShip` (hidden Ship Select button)
- Out of sync with Ship Sign On filter
- Confusing: Ship filter shows all, crew filter shows limited

**Example Issue:**
```
Ship Sign On Filter: All (showing all certificates)
Crew Dropdown: Only BROTHER 36 crew (if selectedShip = BROTHER 36)
❌ Mismatch!
```

### After (New Logic)

**Crew Dropdown Source:**
- Controlled by Ship Sign On filter
- Always in sync
- Clear: Ship filter drives crew options

**Example:**
```
Ship Sign On Filter: All
Crew Dropdown: All crew
✅ Consistent!

Ship Sign On Filter: BROTHER 36
Crew Dropdown: Only BROTHER 36 crew
✅ Consistent!
```

## Technical Details

### Filtering Logic

**Ship Sign On = "All":**
```javascript
let filteredCrew = crewList; // No filtering
```

**Ship Sign On = Specific Value:**
```javascript
filteredCrew = crewList.filter(crew => {
  const crewShipSignOn = crew.ship_sign_on || '-';
  return crewShipSignOn === certFilters.shipSignOn;
});
```

**Handles:**
- Normal ship names: Direct match
- Standby crew: `ship_sign_on = "-"`
- Missing ship_sign_on: Defaults to "-"

### Auto-Reset Behavior

**Trigger:** `certFilters.shipSignOn` changes

**Condition:** Only in Certificates View

**Action:** Reset `crewName` to "all"

**Why:**
- Previous crew selection may be invalid for new ship
- Example: Selected "John Doe" (BROTHER 36), then change ship to "MINH ANH 09"
- John Doe not on MINH ANH 09 → Reset to "All"

**User Experience:**
1. User changes Ship filter
2. Crew automatically resets to "All"
3. User can select from new, relevant crew list

## Dependencies

### State Variables
```javascript
const [certFilters, setCertFilters] = useState({
  shipSignOn: 'all',  // Controls crew dropdown
  status: 'all',
  crewName: 'all'     // Controlled by shipSignOn
});

const [crewList, setCrewList] = useState([]);  // Source of crew data
const [showCertificatesView, setShowCertificatesView] = useState(false);
```

### Data Flow
```
User selects Ship Sign On
         ↓
certFilters.shipSignOn updates
         ↓
useEffect triggers → Reset crewName to 'all'
         ↓
Crew dropdown re-renders with filtered options
         ↓
User can select specific crew from filtered list
         ↓
Certificate table filters by both ship and crew
```

## View Context

### In Crew List View
- Uses original logic (filter by `selectedShip`)
- Not affected by this change

### In Crew Certificates View
- Uses new logic (filter by `certFilters.shipSignOn`)
- Hierarchical filtering: Ship → Crew

## Benefits

### 1. Consistency
- Crew options always match Ship Sign On filter
- No mismatch between filters
- Clear relationship: Ship controls Crew

### 2. User-Friendly
- Intuitive: Select ship first, then crew
- No irrelevant crew options shown
- Auto-reset prevents confusion

### 3. Flexibility
- Can view all crew (Ship = All)
- Can narrow down to specific ship
- Can further filter by crew member

### 4. Performance
- Filters on client-side (fast)
- No additional API calls
- Real-time updates

### 5. Clean Dependencies
- No dependency on hidden `selectedShip`
- Uses visible Ship Sign On filter
- Self-contained logic

## Edge Cases

### Case 1: Ship with No Crew
**Scenario:** Ship Sign On = "OCEAN STAR", but no crew on that ship

**Result:**
- Crew dropdown shows: "All" only
- No crew options to select
- Certificate table empty (no certs for non-existent crew)

### Case 2: Crew Changes Ship
**Scenario:** 
- Filter by "BROTHER 36"
- Select crew "John Doe"
- John moves to "MINH ANH 09" (ship_sign_on updated)

**Result:**
- On next page refresh, John Doe no longer in BROTHER 36 filter
- Appears in MINH ANH 09 filter
- Certificate history unchanged

### Case 3: Standby to Ship
**Scenario:**
- Filter by "Standby"
- Select crew "Sarah Lee"
- Sarah assigned to ship (ship_sign_on = "BROTHER 36")

**Result:**
- On next refresh, Sarah no longer in Standby filter
- Appears in BROTHER 36 filter

### Case 4: Empty Crew List
**Scenario:** `crewList` is empty

**Result:**
- Falls back to certificate-based crew list
- Shows crew who have certificates
- Less ideal but functional

## Testing Checklist

### Basic Functionality
- [ ] Ship Sign On "All" → Crew shows all crew
- [ ] Ship Sign On "BROTHER 36" → Crew shows only BROTHER 36 crew
- [ ] Ship Sign On "Standby" → Crew shows only Standby crew
- [ ] Crew dropdown updates when Ship filter changes

### Auto-Reset
- [ ] Change Ship filter → Crew resets to "All"
- [ ] Select crew → Change ship → Crew resets
- [ ] No errors when resetting

### Certificate Filtering
- [ ] Ship + Crew filters work together
- [ ] Certificates match selected filters
- [ ] Status filter still works

### Navigation
- [ ] Logic only applies in Certificates View
- [ ] Crew List View uses original logic
- [ ] Back and forth navigation works

### Bilingual
- [ ] English names shown when available
- [ ] Vietnamese names as fallback
- [ ] Sorting works for both languages

### Edge Cases
- [ ] Ship with no crew → Shows "All" only
- [ ] Empty crew list → Falls back gracefully
- [ ] Crew without ship_sign_on → Treated as Standby

## Files Modified

**Frontend:**
- `/app/frontend/src/App.js`
  - Crew dropdown logic (lines ~11538-11585): Added Ship Sign On filter dependency
  - Auto-reset useEffect (lines ~1006-1013): Reset crew on ship change

**Documentation:**
- This file: `/app/CREW_FILTER_LINKED_TO_SHIP_FILTER.md`
- Updated: `/app/CREW_FILTER_DROPDOWN_LOGIC_ANALYSIS.md` (now outdated)

## Status
✅ Crew dropdown now controlled by Ship Sign On filter
✅ Auto-reset on ship filter change
✅ Hierarchical filtering (Ship → Crew)
✅ Consistent behavior across all scenarios
✅ No dependency on hidden selectedShip
✅ Ready for testing
