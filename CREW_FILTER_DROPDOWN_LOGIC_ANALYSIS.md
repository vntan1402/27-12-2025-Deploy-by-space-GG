# Crew Filter Dropdown Logic in Crew Certificates View

## Current Implementation

### Location
**File:** `/app/frontend/src/App.js` (lines 11538-11567)

### Logic Flow

```javascript
{(() => {
  // Option 1: Get crew names from crew list (filtered by selectedShip)
  if (selectedShip && crewList.length > 0) {
    return crewList
      .filter(crew => crew.ship_sign_on === selectedShip.name)
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
  
  // Option 2 (Fallback): Get from certificates if no crew list
  return [...new Set(crewCertificates.map(cert => cert.crew_name))]
    .sort()
    .map(crewName => {
      const cert = crewCertificates.find(c => c.crew_name === crewName);
      const displayName = language === 'en' && cert?.crew_name_en 
        ? cert.crew_name_en 
        : crewName;
      return (
        <option key={crewName} value={crewName}>
          {displayName}
        </option>
      );
    });
})()}
```

## Data Sources

### Option 1: From Crew List (Ship-Filtered)

**Condition:** `selectedShip && crewList.length > 0`

**Source:** `crewList` state
- Populated by: `fetchCrewMembers()` API call
- Contains: All crew members in company

**Filter:** `crew.ship_sign_on === selectedShip.name`
- Only shows crew on selected ship
- Excludes Standby and other ships

**Display:**
- Value: `crew.full_name` (Vietnamese name)
- Display: English name if available and language = English

**Sorting:** Alphabetical by display name

### Option 2 (Fallback): From Certificates

**Condition:** No selectedShip OR empty crewList

**Source:** `crewCertificates` state
- Populated by: `fetchCrewCertificates()` API call
- Contains: All certificates (company-wide after recent changes)

**Extract:** Unique `crew_name` values from certificates
- Uses `Set` for uniqueness
- Only shows crew who have certificates

**Display:**
- Value: `cert.crew_name` (Vietnamese name)
- Display: English name if available and language = English

**Sorting:** Alphabetical

## Current Behavior

### In Crew List View
**Scenario:** User has selectedShip

**Result:**
- Uses Option 1 (Crew List source)
- Shows only crew on selected ship
- Example: Select "BROTHER 36" → Only show crew on BROTHER 36

### In Crew Certificates View (After Recent Changes)
**Scenario:** Ship Select hidden, no selectedShip change

**Result:**
- If `selectedShip` still exists from previous navigation → Uses Option 1
- Shows crew filtered by old ship selection (outdated)
- **Problem:** Doesn't match company-wide certificate display

**If no selectedShip:**
- Uses Option 2 (Fallback)
- Shows crew who have certificates
- Better aligned with company-wide view

## Issues with Current Logic

### Issue 1: Outdated Ship Filter
When in Certificates View:
- Certificates show company-wide (all ships)
- But Crew filter still filtered by `selectedShip` if it exists
- **Mismatch:** User sees all certificates but limited crew options

### Issue 2: Dependent on selectedShip State
- `selectedShip` may persist from Crew List navigation
- Hidden Ship Select doesn't clear `selectedShip`
- Creates confusion about available crew options

### Issue 3: Incomplete Crew List (Fallback)
- Fallback only shows crew who have certificates
- Misses crew without certificates
- Different behavior than Option 1

## Expected Behavior for Certificates View

Since certificates are now company-wide, Crew filter should:
1. Show ALL crew in company (not filtered by ship)
2. Or show crew who have certificates (if using fallback)
3. Not depend on `selectedShip` state

## Recommended Fix

### Option A: Always Use Fallback in Certificates View
```javascript
{(() => {
  // In Certificates View: Always use certificate-based list
  if (showCertificatesView) {
    return [...new Set(crewCertificates.map(cert => cert.crew_name))]
      .sort()
      .map(crewName => {
        const cert = crewCertificates.find(c => c.crew_name === crewName);
        const displayName = language === 'en' && cert?.crew_name_en 
          ? cert.crew_name_en 
          : crewName;
        return (
          <option key={crewName} value={crewName}>
            {displayName}
          </option>
        );
      });
  }
  
  // In Crew List View: Use ship-filtered crew list
  if (selectedShip && crewList.length > 0) {
    return crewList
      .filter(crew => crew.ship_sign_on === selectedShip.name)
      // ... existing logic
  }
  
  // Fallback
  return [...];
})()}
```

**Pros:**
- Only shows crew who have certificates
- No dependency on selectedShip
- Consistent with certificate display

**Cons:**
- Won't show crew without certificates
- Different data source than Crew List view

### Option B: Show All Company Crew in Certificates View
```javascript
{(() => {
  // In Certificates View: Show all company crew
  if (showCertificatesView && crewList.length > 0) {
    return crewList
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
  
  // In Crew List View: Use ship-filtered crew list
  if (selectedShip && crewList.length > 0) {
    return crewList
      .filter(crew => crew.ship_sign_on === selectedShip.name)
      // ... existing logic
  }
  
  // Fallback
  return [...];
})()}
```

**Pros:**
- Shows all crew (with or without certificates)
- Consistent data source (crewList)
- User can filter by any crew

**Cons:**
- May show crew with 0 certificates (will result in empty table)
- Longer dropdown list

### Option C: Hybrid Approach
```javascript
{(() => {
  // In Certificates View: Show crew from certificates (most relevant)
  if (showCertificatesView) {
    // Get unique crew from certificates
    const crewWithCerts = [...new Set(crewCertificates.map(cert => cert.crew_name))];
    
    // Enhance with crew list data if available
    if (crewList.length > 0) {
      return crewWithCerts
        .map(crewName => {
          const crewData = crewList.find(c => c.full_name === crewName);
          return {
            value: crewName,
            displayName: language === 'en' && crewData?.full_name_en 
              ? crewData.full_name_en 
              : crewName
          };
        })
        .sort((a, b) => a.displayName.localeCompare(b.displayName))
        .map(item => (
          <option key={item.value} value={item.value}>
            {item.displayName}
          </option>
        ));
    }
    
    // Fallback: Use certificate data only
    return crewWithCerts.sort().map(crewName => {
      const cert = crewCertificates.find(c => c.crew_name === crewName);
      const displayName = language === 'en' && cert?.crew_name_en 
        ? cert.crew_name_en 
        : crewName;
      return (
        <option key={crewName} value={crewName}>
          {displayName}
        </option>
      );
    });
  }
  
  // ... existing logic for Crew List view
})()}
```

**Pros:**
- Only shows crew with certificates (relevant)
- Uses crew list for better bilingual support
- Falls back gracefully
- No dependency on selectedShip

**Cons:**
- Slightly more complex logic
- Still won't show crew without certificates

## Recommendation

**Option C (Hybrid)** is recommended because:
1. ✅ Only shows crew who have certificates (most relevant)
2. ✅ No dependency on `selectedShip` state
3. ✅ Better bilingual support using crewList
4. ✅ Graceful fallback if crewList unavailable
5. ✅ Matches company-wide certificate display logic

## Implementation Priority

**High Priority** - Should be fixed because:
- Current logic creates user confusion
- Mismatch between certificate display (all) and crew filter (ship-specific)
- Depends on hidden `selectedShip` state

## Current Workaround

Users can still filter by typing in search box, but dropdown may show incomplete options.

## Testing Scenarios

### Scenario 1: Navigate from Crew List to Certificates
1. User selects ship "BROTHER 36" in Crew List
2. Double-clicks crew member to view certificates
3. **Current:** Crew dropdown shows only BROTHER 36 crew
4. **Expected:** Should show all crew with certificates

### Scenario 2: Direct Navigation to Certificates
1. User directly opens Certificates View (if possible)
2. No selectedShip set
3. **Current:** Uses fallback (crew from certificates)
4. **Expected:** Same behavior

### Scenario 3: Back and Forth Navigation
1. Crew List (ship A) → Certificates → Back → Crew List (ship B) → Certificates
2. **Current:** Crew dropdown may show ship A or ship B crew
3. **Expected:** Should always show all crew with certificates

## Related Code

### State Variables
```javascript
const [selectedShip, setSelectedShip] = useState(null);
const [showCertificatesView, setShowCertificatesView] = useState(false);
const [crewList, setCrewList] = useState([]);
const [crewCertificates, setCrewCertificates] = useState([]);
const [certFilters, setCertFilters] = useState({
  shipSignOn: 'all',
  status: 'all',
  crewName: 'all'
});
```

### Navigation Functions
```javascript
// Opens Certificates View
handleCrewNameDoubleClick(crew) {
  setShowCertificatesView(true);
  // Does NOT clear selectedShip
}

// Returns to Crew List
handleBackToCrewList() {
  setShowCertificatesView(false);
  // Does NOT clear selectedShip
}
```

## Files Involved
- `/app/frontend/src/App.js` (lines 11538-11567) - Crew filter dropdown logic

## Status
📋 Documentation Complete
⚠️ Implementation Pending
🔍 Needs User Confirmation on Preferred Approach
