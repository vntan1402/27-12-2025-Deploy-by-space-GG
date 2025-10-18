# Add Crew Modal - Floating Minimize Button

## Summary
Updated minimize functionality for "Add New Crew Member" modal to display a floating button in the bottom-right corner when minimized, matching the behavior of "Add Crew Certificate" modal.

## Changes Made

**File:** `frontend/src/App.js`

### Previous Behavior
- Click minimize (`−`) → Modal body collapsed
- Modal header remained visible
- Modal stayed in same position

### New Behavior
- Click minimize (`−`) → Entire modal disappears
- Floating button appears in bottom-right corner
- Click floating button → Modal restores to previous position

## Implementation

### 1. Hide Full Modal When Minimized

**Line:** ~14310
```javascript
// Before
{showAddCrewModal && (

// After
{showAddCrewModal && !isAddCrewModalMinimized && (
```

**Effect:**
- Modal only visible when NOT minimized
- Complete removal from view when minimized

### 2. Floating Button Component

**Location:** After modal closing tag, before Processing Results Modal
**Lines:** ~15054-15088

```javascript
{/* Add Crew Modal - Minimized Floating Button */}
{showAddCrewModal && isAddCrewModalMinimized && (
  <div 
    onClick={() => {
      console.log('📂 Restoring Add Crew modal...');
      setIsAddCrewModalMinimized(false);
    }}
    className="fixed bottom-6 right-6 z-[9999] cursor-pointer group"
  >
    <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-2xl shadow-2xl hover:shadow-3xl transition-all hover:scale-105 p-4 min-w-[280px]">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-white bg-opacity-20 rounded-full p-2">
            <span className="text-2xl">👤</span>
          </div>
          <div>
            <div className="font-bold text-sm">
              {language === 'vi' ? 'Thêm thuyền viên mới' : 'Add New Crew'}
            </div>
            <div className="text-xs text-green-100">
              {newCrewData.status === 'Standby' 
                ? (language === 'vi' ? 'Standby Crew' : 'Standby Crew')
                : selectedShip 
                  ? selectedShip.name 
                  : (language === 'vi' ? 'Đang soạn...' : 'In progress...')}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="bg-white bg-opacity-20 rounded-full p-1.5 group-hover:bg-opacity-30 transition-all">
            <span className="text-sm">↑</span>
          </div>
        </div>
      </div>
      <div className="mt-2 text-xs text-green-100">
        {language === 'vi' ? 'Click để mở lại' : 'Click to restore'}
      </div>
    </div>
  </div>
)}
```

## Visual Design

### Floating Button Layout

```
┌───────────────────────────────────────┐
│  👤  Thêm thuyền viên mới        ↑   │
│      BROTHER 36                       │
│                                        │
│  Click để mở lại                      │
└───────────────────────────────────────┘
```

**Components:**
1. **Icon (Left):** 👤 (person icon)
2. **Title:** "Thêm thuyền viên mới" / "Add New Crew"
3. **Subtitle:** Ship name or "Standby Crew" or "In progress"
4. **Restore Icon (Right):** ↑ in circle
5. **Bottom Text:** "Click để mở lại" / "Click to restore"

### Styling

**Colors:**
- Background: Gradient from green-600 to emerald-600
- Text: White
- Subtle text: green-100
- Icon background: White with 20% opacity

**Why Green?**
- Differentiates from Add Certificate modal (blue/indigo)
- Green = New/Add action
- Blue = Document/Certificate action

**Effects:**
- Shadow: shadow-2xl
- Hover: shadow-3xl + scale-105
- Rounded: rounded-2xl
- Smooth transitions

### Position

**Fixed positioning:**
- `bottom-6` → 24px from bottom
- `right-6` → 24px from right
- `z-[9999]` → Top layer (above everything)

**Behavior:**
- Always visible in viewport
- Doesn't scroll with page
- Stays in corner regardless of screen size

## Comparison: Add Crew vs Add Certificate

### Visual Differences

**Add Crew Modal (Minimized):**
```
┌───────────────────────────────────────┐
│  👤  Thêm thuyền viên mới        ↑   │ ← Green gradient
│      BROTHER 36                       │
│  Click để mở lại                      │
└───────────────────────────────────────┘
```

**Add Certificate Modal (Minimized):**
```
┌───────────────────────────────────────┐
│  📜  Thêm chứng chỉ              ↑   │ ← Blue gradient
│      Ho Sy Chuong                     │
│  Click để mở lại                      │
└───────────────────────────────────────┘
```

### Color Scheme

| Modal Type | Gradient | Icon | Purpose |
|------------|----------|------|---------|
| Add Crew | Green → Emerald | 👤 | Create new crew member |
| Add Certificate | Blue → Indigo | 📜 | Add certificate to crew |

### Subtitle Logic

**Add Crew:**
- Standby mode → "Standby Crew"
- Ship selected → Ship name
- No ship → "In progress"

**Add Certificate:**
- Crew selected → Crew full name
- No crew → "In progress"

## User Flow

### Scenario 1: Basic Minimize/Restore

```
1. User opens Add Crew modal
2. Starts filling form
3. Needs to check crew list
4. Clicks [−] minimize button
   → Modal disappears
   → Green floating button appears bottom-right
5. User checks crew list
6. Clicks floating button
   → Button disappears
   → Modal restores to previous position
7. User continues filling form
```

### Scenario 2: Standby Mode

```
1. User opens Add Crew modal
2. Clicks [⚪ Standby Crew] → Activates Standby mode
3. Starts uploading passports
4. Clicks [−] minimize button
5. Floating button shows:
   👤 Thêm thuyền viên mới
      Standby Crew ← Orange text indicates mode
   Click để mở lại
6. Passports process in background
7. User clicks floating button → Restores modal
```

### Scenario 3: Multiple Modals

```
1. User opens Add Crew modal
2. Clicks [−] minimize
   → Green button appears bottom-right
3. User navigates to certificates
4. Opens Add Certificate modal
5. Clicks minimize on certificate modal
   → Blue button appears above green button
6. Two floating buttons visible:
   [Blue - Add Certificate]  ← Top
   [Green - Add Crew]         ← Bottom
7. Click either to restore respective modal
```

## State Management

### Minimize State

**Variable:** `isAddCrewModalMinimized`
**Type:** `boolean`
**Default:** `false`

**Toggle:** Click minimize button in modal header
```javascript
onClick={() => setIsAddCrewModalMinimized(!isAddCrewModalMinimized)}
```

**Restore:** Click floating button
```javascript
onClick={() => setIsAddCrewModalMinimized(false)}
```

### Preserved State

**During minimize/restore:**
- ✅ Form field values
- ✅ Standby mode status
- ✅ Selected ship
- ✅ Uploaded passport files
- ✅ Analysis results
- ✅ Modal position (drag position)
- ✅ Batch processing progress

## Technical Details

### Z-Index Layering

```
z-[9999]  → Floating buttons (topmost)
z-50      → Modals
z-40      → Overlays
z-30      → Sticky headers
z-10      → Normal elements
```

**Why 9999?**
- Ensures floating button always visible
- Above all modals and overlays
- Prevents any element from covering it

### CSS Classes Breakdown

**Container:**
```css
fixed          → Fixed positioning
bottom-6       → 24px from bottom
right-6        → 24px from right
z-[9999]       → Highest layer
cursor-pointer → Shows clickable
group          → For hover effects on children
```

**Card:**
```css
bg-gradient-to-r from-green-600 to-emerald-600  → Gradient background
text-white                                       → White text
rounded-2xl                                      → Large rounded corners
shadow-2xl                                       → Large shadow
hover:shadow-3xl                                 → Larger shadow on hover
transition-all                                   → Smooth transitions
hover:scale-105                                  → Slightly enlarge on hover
p-4                                              → Padding
min-w-[280px]                                    → Minimum width
```

**Icon Container:**
```css
bg-white bg-opacity-20  → Semi-transparent white
rounded-full            → Circular
p-2                     → Padding
```

**Text Colors:**
```css
font-bold text-sm       → Bold title
text-xs text-green-100  → Small, light subtitle
```

## Responsive Behavior

### Desktop (>1024px)
- Floating button: 24px from corner
- Full size: min-width 280px
- Hover effects active

### Tablet (768px - 1024px)
- Same positioning
- Slightly smaller spacing acceptable
- Touch-friendly size maintained

### Mobile (<768px)
- Floating button: Still 24px from corner
- Min-width maintained for readability
- Touch target large enough (44px minimum)
- No hover effects (touch device)

## Accessibility

### Keyboard Navigation
- Tab to floating button
- Enter/Space to restore modal
- Focus visible outline

### Screen Readers
- Announce: "Restore Add Crew modal"
- Reads subtitle information
- Click action clear

### Visual Indicators
- Clear icon (👤) indicates purpose
- Text describes action ("Click to restore")
- Hover effects provide feedback
- High contrast colors

## Testing Recommendations

### Test Case 1: Basic Flow
1. Open Add Crew modal
2. Click minimize button
3. Verify:
   - ✅ Modal disappears
   - ✅ Green floating button appears bottom-right
   - ✅ Subtitle shows ship/Standby
4. Click floating button
5. Verify:
   - ✅ Button disappears
   - ✅ Modal restores
   - ✅ Form data intact

### Test Case 2: Standby Mode
1. Open modal
2. Activate Standby mode
3. Minimize
4. Verify:
   - ✅ Floating button shows "Standby Crew"
5. Restore
6. Verify:
   - ✅ Still in Standby mode

### Test Case 3: Dual Modals
1. Open Add Crew modal → Minimize
2. Open Add Certificate modal → Minimize
3. Verify:
   - ✅ Two floating buttons visible
   - ✅ Green (Add Crew) at bottom
   - ✅ Blue (Add Certificate) above it
4. Click each button
5. Verify:
   - ✅ Correct modal restores

### Test Case 4: Position
1. Drag modal to new position
2. Minimize
3. Restore
4. Verify:
   - ✅ Modal returns to dragged position

### Test Case 5: Processing
1. Upload multiple passports
2. Minimize while processing
3. Check floating button visible
4. Wait for processing to complete
5. Restore
6. Verify:
   - ✅ Processing completed
   - ✅ Results shown

### Test Case 6: Responsive
1. Test on different screen sizes
2. Verify:
   - ✅ Button always visible
   - ✅ Always in bottom-right corner
   - ✅ Doesn't overflow screen

## Future Enhancements

**Potential additions (not implemented):**
- Badge showing number of filled fields
- Progress bar for batch upload
- Animation on minimize/restore
- Drag floating button to different corner
- Keyboard shortcut to restore

## Related Features

Works with:
- Modal dragging functionality
- Standby mode toggle
- Form state preservation
- Batch passport upload
- Add Certificate modal minimize
