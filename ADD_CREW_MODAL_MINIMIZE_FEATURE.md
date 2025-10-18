# Add Crew Modal - Minimize Feature

## Summary
Added minimize/maximize functionality to "Add New Crew Member" modal, allowing users to temporarily collapse the modal while keeping it accessible.

## Changes Made

**File:** `frontend/src/App.js`

### 1. New State

**Line:** ~920
```javascript
const [isAddCrewModalMinimized, setIsAddCrewModalMinimized] = useState(false);
```

### 2. Minimize Button

**Location:** Modal header, between "Standby Crew" button and "×" (close) button

**Implementation:**
```javascript
{/* Minimize Button */}
<button
  onClick={() => setIsAddCrewModalMinimized(!isAddCrewModalMinimized)}
  className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
  title={isAddCrewModalMinimized 
    ? (language === 'vi' ? 'Mở rộng' : 'Maximize') 
    : (language === 'vi' ? 'Thu nhỏ' : 'Minimize')
  }
>
  {isAddCrewModalMinimized ? '□' : '−'}
</button>
```

**Icons:**
- **Minimized state (collapsed):** `□` (maximize icon)
- **Normal state (expanded):** `−` (minimize icon)

**Tooltips:**
- **Minimized:** "Mở rộng" / "Maximize"
- **Normal:** "Thu nhỏ" / "Minimize"

### 3. Conditional Body Rendering

**Implementation:**
```javascript
{/* Modal Body - Hidden when minimized */}
{!isAddCrewModalMinimized && (
  <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)] space-y-6">
    {/* All form content */}
  </div>
)}
```

**Effect:**
- When minimized: Only header visible
- When maximized: Full modal with all content

## Button Layout

### Modal Header

```
┌────────────────────────────────────────────────────────────────────┐
│  Add New Crew Member  for: BROTHER 36  [Standby Crew] [−] [×]    │
│  ↑ title              ↑ context         ↑ toggle      ↑min ↑close │
└────────────────────────────────────────────────────────────────────┘
```

**Button Order (Left to Right):**
1. **Standby Crew** - Toggle standby mode (blue button)
2. **Minimize** - Toggle minimize/maximize (`−` / `□`)
3. **Close** - Close modal (`×`)

## Visual States

### 1. Normal State (Expanded)

**Appearance:**
```
┌──────────────────────────────────────────────────┐
│ Add New Crew Member  for: BROTHER 36  [−] [×]  │
├──────────────────────────────────────────────────┤
│                                                   │
│  📄 From Passport (AI Analysis)                  │
│  [Drag & drop files]                             │
│                                                   │
│  ✏️ Crew Information (Manual Entry)              │
│  [Form fields...]                                │
│                                                   │
│                       [Cancel] [Add Crew Member] │
└──────────────────────────────────────────────────┘
```

**Icon:** `−` (minus sign)
**Tooltip:** "Thu nhỏ" / "Minimize"

### 2. Minimized State (Collapsed)

**Appearance:**
```
┌──────────────────────────────────────────────────┐
│ Add New Crew Member  for: BROTHER 36  [□] [×]  │
└──────────────────────────────────────────────────┘
```

**Icon:** `□` (maximize icon)
**Tooltip:** "Mở rộng" / "Maximize"
**Content:** Hidden (all form sections, buttons)

## Use Cases

### Use Case 1: Referencing Other Data
```
User Action:
1. Open Add Crew Member modal
2. Start filling form
3. Need to check something in crew list
4. Click [−] to minimize
5. Modal collapses to header bar
6. View crew list below
7. Click [□] to maximize
8. Continue filling form
```

### Use Case 2: Multi-tasking
```
User Action:
1. Upload passport files (batch processing starts)
2. Click [−] to minimize while processing
3. Work on other tasks (view certificates, check ship info)
4. Files process in background
5. Modal stays accessible (minimized header visible)
6. Click [□] when ready to check results
```

### Use Case 3: Screen Real Estate
```
User Action:
1. Small screen / many windows open
2. Open Add Crew modal
3. Modal takes up space
4. Click [−] to minimize
5. More screen space available
6. Modal header remains visible for quick access
7. Click [□] to restore when needed
```

## Behavior Details

### What Happens on Minimize
- ✅ Modal header stays visible
- ✅ Modal body content hidden
- ✅ Modal position preserved (drag position maintained)
- ✅ All form data preserved (state unchanged)
- ✅ Background overlay remains (modal still active)
- ✅ Processing continues (passport analysis, etc.)

### What Happens on Maximize
- ✅ Modal body content restored
- ✅ Form state intact (no data loss)
- ✅ Scroll position reset to top
- ✅ Same position as before minimize

### State Preservation

**During minimize/maximize:**
- ✅ Form fields retain values
- ✅ Standby mode stays active/inactive
- ✅ Uploaded files remain attached
- ✅ Analysis results preserved
- ✅ Modal position unchanged

## Technical Implementation

### State Management
```javascript
// State declaration
const [isAddCrewModalMinimized, setIsAddCrewModalMinimized] = useState(false);

// Toggle function
onClick={() => setIsAddCrewModalMinimized(!isAddCrewModalMinimized)}

// Conditional rendering
{!isAddCrewModalMinimized && (
  <div>...</div>
)}
```

### CSS Classes
- Button: `text-gray-400 hover:text-gray-600 text-2xl font-bold`
- Same styling as close button (×)
- Consistent with other modal controls

### Icons
- Minimize: `−` (U+2212 MINUS SIGN)
- Maximize: `□` (U+25A1 WHITE SQUARE)
- Simple, universal symbols

## Comparison with Other Modal

### Add Crew Certificate Modal
- Also has minimize feature
- Same icon style (`□` / `−`)
- Consistent UX across modals

### Implementation Pattern
```javascript
// Both modals follow same pattern:
const [isModalMinimized, setIsModalMinimized] = useState(false);

{!isModalMinimized && (
  <div className="modal-body">...</div>
)}
```

## User Experience

### Benefits

1. **Flexibility**
   - Keep modal open while viewing other content
   - Don't lose form progress
   - Quick access to restore

2. **Screen Space**
   - Minimize when not actively using
   - Header bar is non-intrusive
   - More room for other tasks

3. **Workflow Efficiency**
   - No need to close and reopen
   - Form data preserved
   - Context maintained

4. **Visual Clarity**
   - Clear icons indicate state
   - Tooltips guide action
   - Consistent with system patterns

### User Actions

**To Minimize:**
- Click `−` button in header
- Modal collapses to header bar

**To Maximize:**
- Click `□` button in header
- Modal expands with all content

**To Close:**
- Click `×` button (always available)
- Modal closes completely

## Testing Recommendations

### Test Case 1: Basic Toggle
1. Open Add Crew modal
2. Click minimize button (`−`)
3. Verify:
   - ✅ Only header visible
   - ✅ Icon changes to `□`
   - ✅ Tooltip shows "Maximize"
4. Click maximize button (`□`)
5. Verify:
   - ✅ Full modal restored
   - ✅ Icon changes to `−`
   - ✅ Tooltip shows "Minimize"

### Test Case 2: Data Preservation
1. Open modal
2. Fill some form fields
3. Minimize modal
4. Maximize modal
5. Verify:
   - ✅ All filled data still present
   - ✅ Form state unchanged

### Test Case 3: Standby Mode
1. Open modal
2. Activate Standby mode (orange button)
3. Minimize modal
4. Maximize modal
5. Verify:
   - ✅ Still in Standby mode
   - ✅ Fields still hidden/disabled
   - ✅ Mode persists

### Test Case 4: Batch Processing
1. Upload multiple passport files
2. Processing starts
3. Minimize modal
4. Wait for processing to complete
5. Maximize modal
6. Verify:
   - ✅ Processing completed
   - ✅ Results available

### Test Case 5: Modal Dragging
1. Drag modal to new position
2. Minimize modal
3. Maximize modal
4. Verify:
   - ✅ Position preserved
   - ✅ Modal at same location

### Test Case 6: Language Toggle
1. Minimize modal
2. Check tooltip (Vietnamese)
3. Change language to English
4. Check tooltip (English)
5. Verify:
   - ✅ Tooltips translate correctly

## Future Enhancements

### Potential Additions (Not Implemented)
- Smooth animation on minimize/maximize
- Remember minimize state (localStorage)
- Keyboard shortcut (e.g., Ctrl+M)
- Double-click header to toggle

## Related Features

Works with:
- Modal dragging functionality
- Standby mode toggle
- Form validation
- Passport batch upload
- All form fields and sections
