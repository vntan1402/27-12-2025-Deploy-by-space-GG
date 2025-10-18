# Filter Reorder and Crew Info Update

## Summary
Two UI enhancements implemented in the Crew Certificates View:
1. Reordered filters: Swapped positions of "Crew" and "Status" filters
2. Updated Crew Member Information section to display data based on filter selection

## Changes Made

### 1. Filter Position Swap
**File:** `frontend/src/App.js`
**Lines:** ~11517-11607

**Change:**
- Moved "Crew Name Filter" to appear before "Status Filter"

**New Filter Order:**
1. Ship Sign On Filter
2. **Crew Name Filter** (moved up)
3. **Status Filter** (moved down)

### 2. Crew Member Information Display Logic
**File:** `frontend/src/App.js`
**Lines:** ~9529-9591

**Previous Behavior:**
- Displayed information from `selectedCrewForCertificates` (set when double-clicking a crew name)
- Date of Birth formatted using `toLocaleDateString()` which varied by locale

**New Behavior:**
- Displays information based on the crew selected in the "Crew" filter (`certFilters.crewName`)
- Only shows the section when a specific crew member is selected (not when filter is "All")
- Date of Birth now formatted consistently as **DD/MM/YYYY**

**Implementation Details:**
- Created an IIFE to dynamically determine which crew to display
- Finds crew from `crewList` matching `certFilters.crewName`
- Added `formatDobToDDMMYYYY()` function to format date consistently
- Returns `null` when no specific crew is selected

**Date Format Function:**
```javascript
const formatDobToDDMMYYYY = (dateStr) => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  } catch (e) {
    return '-';
  }
};
```

## User Experience Impact

### Filter Reorder
- Users will now see "Crew" filter before "Status" filter
- Provides a more logical flow: Ship → Crew → Status

### Crew Info Display
- **Before:** Crew info persisted from the crew member that was double-clicked to enter Certificates View
- **After:** Crew info dynamically updates based on the current "Crew" filter selection
- **Benefit:** More intuitive - displayed info matches the selected filter
- **Date Format:** Consistent DD/MM/YYYY format regardless of browser locale

## Testing Recommendations

1. **Filter Order:**
   - Navigate to Crew Certificates View
   - Verify filter order: Ship → Crew → Status

2. **Crew Info Display:**
   - Enter Crew Certificates View
   - Select different crew members from "Crew" filter
   - Verify displayed information updates to match selected crew
   - Check Date of Birth displays in DD/MM/YYYY format
   - Select "All" in Crew filter → Crew Info section should disappear

## Technical Notes

- Used IIFE pattern to encapsulate crew selection logic
- Maintains backward compatibility with existing state management
- No changes to backend or data structure
- Frontend hot-reload will apply changes automatically
