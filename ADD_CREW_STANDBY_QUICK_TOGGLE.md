# Add Crew Modal - Standby Quick Toggle & Dynamic Title

## Summary
Enhanced "Add New Crew Member" modal header with:
1. Dynamic title that shows "For Standby Crew" when in Standby mode
2. Quick toggle button to instantly switch between normal and Standby mode

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~14313-14395

## Enhancements

### 1. Dynamic Title Display

**Logic:**
- **When Status = Standby**: Shows "for: Standby Crew" (orange text)
- **When Status ≠ Standby**: Shows "for: [Ship Name]" (blue text)
- **No ship selected**: Shows nothing

**Implementation:**
```javascript
{newCrewData.status === 'Standby' ? (
  <span className="text-xl font-medium text-orange-600">
    for: <span className="font-bold">Standby Crew</span>
  </span>
) : selectedShip ? (
  <span className="text-xl font-medium text-gray-800">
    for: <span className="font-bold text-blue-600">{selectedShip.name}</span>
  </span>
) : null}
```

**Visual:**
```
Normal Mode:
┌─────────────────────────────────────────────┐
│ Add New Crew Member for: BROTHER 36    [×] │
│                              ↑ blue          │
└─────────────────────────────────────────────┘

Standby Mode:
┌─────────────────────────────────────────────┐
│ Add New Crew Member for: Standby Crew  [×] │
│                              ↑ orange        │
└─────────────────────────────────────────────┘
```

### 2. Standby Quick Toggle Button

**New Button Features:**
- Positioned between title and close (×) button
- **Active state** (Standby mode): Orange background (🟠 Standby)
- **Inactive state** (Normal mode): Gray background (⚪ Standby)
- One-click toggle between modes
- Auto-handles all related field changes

**Button States:**

**Inactive (Normal Mode):**
```
┌─────────────────┐
│ ⚪ Standby      │  ← Gray button
└─────────────────┘
Click → Switch to Standby Mode
```

**Active (Standby Mode):**
```
┌─────────────────┐
│ 🟠 Standby      │  ← Orange button
└─────────────────┘
Click → Switch back to Normal Mode
```

**Implementation:**
```javascript
<button
  onClick={() => {
    if (newCrewData.status === 'Standby') {
      // Switch back to Sign on mode
      setNewCrewData({
        ...newCrewData,
        status: 'Sign on',
        ship_sign_on: selectedShip?.name || '-'
      });
    } else {
      // Switch to Standby mode
      setNewCrewData({
        ...newCrewData,
        status: 'Standby',
        ship_sign_on: '-'
      });
    }
  }}
  className={newCrewData.status === 'Standby'
    ? 'bg-orange-500 text-white hover:bg-orange-600'
    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
  }
>
  <span>{newCrewData.status === 'Standby' ? '🟠' : '⚪'}</span>
  <span>Standby</span>
</button>
```

### 3. Auto-Sync on Toggle

**When clicking "Standby" button:**

**From Normal → Standby:**
- ✅ Status = "Standby"
- ✅ Ship Sign On = "-"
- ✅ Fields hide (Place/Date Sign On, Date Sign Off)
- ✅ Ship dropdown disables
- ✅ Title changes to "For Standby Crew"
- ✅ Button turns orange

**From Standby → Normal:**
- ✅ Status = "Sign on"
- ✅ Ship Sign On = selected ship (or "-" if no ship)
- ✅ Fields reappear
- ✅ Ship dropdown enables
- ✅ Title changes to "for: [Ship Name]"
- ✅ Button turns gray

## User Experience

### Before
```
To switch to Standby mode:
1. Scroll down to Status dropdown
2. Click dropdown
3. Select "Standby"
4. Manually verify Ship Sign On
5. Check if fields are correct

❌ Multiple steps
❌ Need to scroll
❌ Not obvious it's in Standby mode
```

### After
```
To switch to Standby mode:
1. Click "Standby" button in header

✅ One click
✅ No scrolling needed
✅ Visual feedback:
   - Orange button
   - Orange "For Standby Crew" text
   - Fields automatically adjust
   - Status badge appears

To switch back:
1. Click orange "Standby" button again

✅ Instant toggle
✅ All settings revert
```

## Visual Layout

### Complete Header Layout

**Normal Mode:**
```
┌──────────────────────────────────────────────────────────────────┐
│  Add New Crew Member  for: BROTHER 36    [⚪ Standby]  [×]      │
│  ↑ title              ↑ ship name         ↑ toggle    ↑ close   │
└──────────────────────────────────────────────────────────────────┘
```

**Standby Mode:**
```
┌──────────────────────────────────────────────────────────────────┐
│  Add New Crew Member  for: Standby Crew  [🟠 Standby]  [×]      │
│  ↑ title              ↑ orange text       ↑ active    ↑ close   │
└──────────────────────────────────────────────────────────────────┘
```

## Color Coding

**Text Colors:**
- **Blue** (#2563eb): Ship name in normal mode → indicates active ship
- **Orange** (#ea580c): "Standby Crew" text → indicates standby status
- **Gray** (#1f2937): Normal title text

**Button Colors:**
- **Gray** (bg-gray-200): Inactive state → subtle, non-intrusive
- **Orange** (bg-orange-500): Active state → prominent, matches standby theme
- **White** text on orange: High contrast for readability

## Complete Feature Set

### Modal Header Components

1. **Title** (static)
   - "Add New Crew Member" / "Thêm thuyền viên mới"

2. **Context Text** (dynamic)
   - Shows "for: [Ship]" or "for: Standby Crew"
   - Color changes based on mode
   - Automatically updates on toggle

3. **Standby Toggle Button** (NEW)
   - Quick mode switcher
   - Visual state indicator
   - One-click operation

4. **Close Button** (existing)
   - Closes modal
   - Resets all states

### Interaction Flow

**Scenario 1: Adding Standby Crew**
```
1. Click "ADD NEW RECORD" → Crew Records
2. See modal: "Add New Crew Member for: BROTHER 36"
3. Click [⚪ Standby] button
4. Instantly see:
   - Title changes: "for: Standby Crew" (orange)
   - Button becomes: [🟠 Standby] (orange)
   - Status badge appears: "🟠 Chế độ Standby"
   - Ship field grays out
   - Place/Date fields disappear
5. Fill basic info (name, passport, etc.)
6. Submit → Crew saved to Standby folder
```

**Scenario 2: Starting with Ship, Switching to Standby**
```
1. Open modal from ship context
2. See: "Add New Crew Member for: SHIP NAME"
3. Start filling passport info
4. AI extracts → fields populated
5. Realize crew should be Standby
6. Click [⚪ Standby] button
7. Everything adjusts automatically
8. Continue and submit
```

**Scenario 3: Toggle Back and Forth**
```
1. Click [⚪ Standby] → Standby mode
2. Decide to assign to ship instead
3. Click [🟠 Standby] → Normal mode
4. Select ship from dropdown
5. Continue normally
```

## Benefits

### 1. Discoverability
- Button prominently placed in header
- Clear visual indicator of current mode
- Always visible (no scrolling needed)

### 2. Efficiency
- One click vs multiple steps
- No scrolling required
- Instant feedback

### 3. Clarity
- Title changes reflect current mode
- Color coding matches throughout UI
- Status always visible in header

### 4. Flexibility
- Easy to toggle back and forth
- Can change mind without starting over
- No data loss when switching modes

### 5. Professional UX
- Polished appearance
- Smooth transitions
- Consistent design language

## Testing Recommendations

1. **Toggle Functionality:**
   - Click Standby button when inactive
   - Verify all Standby mode features activate
   - Click Standby button when active
   - Verify return to normal mode

2. **Title Updates:**
   - Verify "For Standby Crew" appears in Standby mode
   - Verify ship name appears in normal mode
   - Check color coding (orange vs blue)

3. **Form Sync:**
   - Toggle to Standby → verify form adjusts
   - Toggle back → verify form restores
   - Fill data → toggle → verify data preserved

4. **Visual States:**
   - Check button colors (gray/orange)
   - Check emoji indicators (⚪/🟠)
   - Check hover effects

5. **Language Support:**
   - Test in Vietnamese
   - Test in English
   - Verify all text displays correctly

6. **Edge Cases:**
   - No ship selected + toggle Standby
   - With ship + toggle Standby
   - Passport uploaded + toggle mode
   - AI analysis in progress + toggle

## Related Features

Integrates with:
- Standby mode enhancements (field hiding, auto-sync)
- Status dropdown with badge
- Ship Sign On field behavior
- Automatic file movement to Standby folder
- Filter and display logic in crew list
