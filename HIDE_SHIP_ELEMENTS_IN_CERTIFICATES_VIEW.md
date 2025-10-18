# Hide Ship Select Button and Ship Basic Info in Crew Certificates View

## Overview
Hidden the "Ship Select" button and "Ship Basic Info" section when viewing Crew Certificates, as these are no longer relevant since certificates now display company-wide (not ship-filtered).

## User Request
"Trong Crew Certificates View, hãy ẩn nút Ship Select và Section Ship Basic Info"

Translation: "In Crew Certificates View, hide the Ship Select button and Ship Basic Info section"

## Reason for Change

### Context
After implementing the "Show All Certificates" feature:
- Certificates are fetched company-wide (not ship-filtered)
- Ship selection is no longer needed to view certificates
- Ship info is irrelevant when viewing all certificates

### Problem
- Ship Select button still visible but serves no purpose
- Ship Basic Info section displays a single ship's info, but certificates are from all ships
- Confusing UX: User sees one ship's info but certificates from all ships

### Solution
Hide both UI elements when in Crew Certificates View.

## Implementation

### 1. Hide Ship Select Button

**Location:** `/app/frontend/src/App.js` (lines ~9201-9273)

**Before:**
```jsx
{/* Ship Select Dropdown */}
<div className="relative" ref={shipSelectorRef}>
  <button>...</button>
</div>
```

**After:**
```jsx
{/* Ship Select Dropdown - Hidden in Crew Certificates View */}
{!showCertificatesView && (
  <div className="relative" ref={shipSelectorRef}>
    <button>...</button>
  </div>
)}
```

**Change:** Wrapped entire Ship Select dropdown in `{!showCertificatesView && (...)}` condition.

### 2. Hide Ship Basic Info Section

**Location:** `/app/frontend/src/App.js` (lines ~9374-9513)

**Before:**
```jsx
{/* Ship Information */}
<div className="mb-6">
  {/* Basic Ship Info */}
  <div className="grid grid-cols-3 gap-4 text-sm mb-4">
    {/* Ship Name, IMO, Gross Tonnage, etc. */}
  </div>
  
  {/* Full Ship Info (Toggle) */}
  {showFullShipInfo && (...)}
</div>
```

**After:**
```jsx
{/* Ship Information - Hidden in Crew Certificates View */}
{!showCertificatesView && (
  <div className="mb-6">
    {/* Basic Ship Info */}
    <div className="grid grid-cols-3 gap-4 text-sm mb-4">
      {/* Ship Name, IMO, Gross Tonnage, etc. */}
    </div>
    
    {/* Full Ship Info (Toggle) */}
    {showFullShipInfo && (...)}
  </div>
)}
```

**Change:** Wrapped entire Ship Information section in `{!showCertificatesView && (...)}` condition.

## Visual Comparison

### Before (With Ship Select & Ship Info)

```
┌────────────────────────────────────────────────────────┐
│  CREW RECORD                                           │
│  [Ship Particular ▼] [Ship Select ▼] [Edit Ship]      │ ← Ship Select visible
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Ship Name: BROTHER 36      Class Society: DNV        │
│  IMO: 9876543              Built Year: 2015           │ ← Ship Info visible
│  Gross Tonnage: 5000        Deadweight: 8000          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  ← Back  |  Crew Certificates                         │
│  [Search] | [Ship ▼] [Status ▼] [Crew ▼]             │
│  Certificates from ALL ships...                        │
└────────────────────────────────────────────────────────┘
```

**Problem:** Shows BROTHER 36 info, but certificates are from all ships!

### After (Hidden Ship Select & Ship Info)

```
┌────────────────────────────────────────────────────────┐
│  CREW RECORD                                           │
│  [Ship Particular ▼]                                   │ ← Ship Select hidden
└────────────────────────────────────────────────────────┘

                                                          ← Ship Info hidden

┌────────────────────────────────────────────────────────┐
│  ← Back  |  Crew Certificates                         │
│  [Search] | [Ship ▼] [Status ▼] [Crew ▼]             │
│  Certificates from ALL ships...                        │
└────────────────────────────────────────────────────────┘
```

**Result:** Clean view, no conflicting ship information!

## Behavior Details

### Conditional Display

**Condition:** `!showCertificatesView`

**When `showCertificatesView = false` (Company Crew List):**
- ✅ Ship Select button visible
- ✅ Ship Basic Info section visible
- Normal crew list view

**When `showCertificatesView = true` (Crew Certificates View):**
- ❌ Ship Select button hidden
- ❌ Ship Basic Info section hidden
- Clean certificates view

### State Variable

```javascript
const [showCertificatesView, setShowCertificatesView] = useState(false);

// Set to true when viewing certificates
setShowCertificatesView(true);   // Opens Crew Certificates View

// Set to false when going back
setShowCertificatesView(false);  // Returns to Crew List
```

### Toggle Functions

**Open Certificates View:**
```javascript
const handleCrewNameDoubleClick = (crew) => {
  setShowCertificatesView(true);  // Hide ship elements
  // ...
};
```

**Close Certificates View:**
```javascript
const handleBackToCrewList = () => {
  setShowCertificatesView(false);  // Show ship elements
  // ...
};
```

## What Remains Visible

### In Crew Certificates View

**Still Visible:**
- ✅ "Ship Particular" button (if not in crew category)
- ✅ "Edit Ship" button (if not in crew category)
- ✅ Page title: "CREW RECORD"
- ✅ Sub menu navigation
- ✅ Certificates table with Ship/Status column
- ✅ All certificate filters

**Hidden:**
- ❌ "Ship Select" button
- ❌ Ship Basic Info (Name, IMO, Tonnage, etc.)
- ❌ Ship Detailed Info (Docking, Survey, Anniversary)

### Why Some Ship Elements Remain

**"Ship Particular" button:**
- Only shows when `selectedCategory !== 'crew'`
- Already hidden in crew section
- No additional hiding needed

**"Edit Ship" button:**
- Only shows when `selectedCategory !== 'crew'`
- Already hidden in crew section
- No additional hiding needed

**These buttons are already conditionally hidden based on `selectedCategory`, so they don't appear in Crew Records view.**

## User Experience

### Before Change

**User in Crew Certificates View:**
1. Sees "Ship Select" button (clicks it)
2. Selects a different ship
3. Expects to see only that ship's certificates
4. **But sees ALL certificates** (because of new logic)
5. **Confusion:** "Why do I still see other ships' certificates?"

**User sees Ship Info:**
1. Views BROTHER 36 ship info at top
2. Scrolls to certificates table
3. **Sees certificates from BROTHER 36, MINH ANH 09, Standby crew**
4. **Confusion:** "Why are these other ships here?"

### After Change

**User in Crew Certificates View:**
1. No "Ship Select" button visible
2. No specific ship info shown
3. Sees Ship/Status column in table clearly showing each certificate's ship
4. **Clear understanding:** "These are all company certificates"
5. Uses Ship filter dropdown to narrow down if needed

**Result:** Consistent, clear user experience!

## Edge Cases

### Case 1: User Already Selected Ship Before Viewing Certificates

**Scenario:**
1. User selects BROTHER 36 in crew list
2. Double-clicks crew name to view certificates
3. **Ship info hidden automatically**

**Expected:** Ship Select and Ship Info hidden regardless of `selectedShip` state.

### Case 2: User Goes Back to Crew List

**Scenario:**
1. User in Crew Certificates View (ship elements hidden)
2. Clicks "Back" button
3. Returns to Crew List

**Expected:** Ship Select and Ship Info reappear.

**Implementation:**
```javascript
handleBackToCrewList() {
  setShowCertificatesView(false);  // Triggers re-show
}
```

### Case 3: Direct Navigation

**Scenario:**
- User bookmarks or directly navigates to page
- `showCertificatesView` defaults to `false`

**Expected:** Ship elements visible (default crew list view).

### Case 4: Multiple Ship Info Sections

**Note:** There's only ONE ship info section in the layout, and it's now properly hidden when `showCertificatesView = true`.

## Related Features

### Ship/Status Column in Certificates Table

With ship info hidden, the **Ship/Status column** becomes even more important:
- Shows which ship each certificate belongs to
- Color-coded (blue for ships, orange for Standby)
- Sortable
- Filterable via Ship filter dropdown

**This column provides ship context without needing the ship info section.**

### Ship Filter Dropdown

The **Ship Sign On filter** in certificates:
- Allows filtering by specific ship
- Shows all available ships in dropdown
- Replaces the need for Ship Select button
- More appropriate for certificate filtering

## Testing Checklist

### Basic Functionality
- [ ] Open Crew List → Ship Select visible
- [ ] Open Crew List → Ship Info visible
- [ ] Double-click crew name → Switches to Certificates View
- [ ] In Certificates View → Ship Select hidden
- [ ] In Certificates View → Ship Info hidden
- [ ] Click Back button → Returns to Crew List
- [ ] After returning → Ship Select visible again
- [ ] After returning → Ship Info visible again

### Navigation
- [ ] Crew List → Certificates → Back → Crew List (cycle test)
- [ ] Ship elements toggle correctly on each transition
- [ ] No UI glitches or layout shifts

### Other Categories
- [ ] Switch to Ships category → Ship elements visible
- [ ] Switch to Certificates category → Ship elements visible
- [ ] Switch back to Crew → Ship elements hidden in Certs View

### Edge Cases
- [ ] Certificates View with no ship selected → Elements still hidden
- [ ] Certificates View with ship selected → Elements still hidden
- [ ] Multiple rapid toggles → No errors

## Performance Notes

### Conditional Rendering

**Impact:** Minimal
- Uses React conditional rendering: `{condition && <Component />}`
- Components unmount when hidden (not just `display: none`)
- Slight performance benefit: hidden components don't re-render

### State Dependencies

**Watch:** `showCertificatesView`
- Changed when entering/exiting certificates view
- Triggers re-render of parent component
- Ship elements conditionally mount/unmount

## Files Modified

**Frontend:**
- `/app/frontend/src/App.js`
  - Ship Select Button: Added `{!showCertificatesView && (...)}` wrapper (lines ~9201-9274)
  - Ship Basic Info Section: Added `{!showCertificatesView && (...)}` wrapper (lines ~9374-9515)

**Documentation:**
- This file: `/app/HIDE_SHIP_ELEMENTS_IN_CERTIFICATES_VIEW.md`

## Benefits

1. **Clearer UX:** No conflicting ship information
2. **Consistent Logic:** UI matches backend logic (all certificates, not ship-specific)
3. **Less Confusion:** Users understand they're viewing all certificates
4. **Cleaner Interface:** Removes unnecessary UI elements
5. **Better Context:** Ship/Status column provides necessary ship info

## Status
✅ Ship Select button hidden in Certificates View
✅ Ship Basic Info section hidden in Certificates View
✅ Elements reappear when returning to Crew List
✅ No breaking changes to other views
✅ Ready for testing
