# Ship Select Button in Add New Crew Member Modal

## Summary
Added a "Ship Select" dropdown button to the left of the "Standby Crew" button in the "Add New Crew Member" modal, allowing users to change the selected ship directly within the modal.

## Problem
Users could not change the selected ship while adding a new crew member. They had to:
1. Close the modal
2. Select a different ship
3. Re-open the "Add New Crew Member" modal

This created unnecessary friction in the workflow.

## Solution
Added a "Ship Select" dropdown button in the modal header that:
- Displays to the left of the "Standby Crew" toggle button
- Shows a beautiful dropdown list of all available ships
- Updates the selected ship and auto-fills `ship_sign_on` field
- Only appears when NOT in Standby mode (hidden when Standby is active)

## Implementation Details

### Code Changes

#### 1. Added State for Dropdown
**File:** `frontend/src/App.js`  
**Line:** ~917

```javascript
const [showShipDropdown, setShowShipDropdown] = useState(false);
```

#### 2. Ship Select Button in Modal Header  
**File:** `frontend/src/App.js`  
**Lines:** ~14391-14438

```javascript
{/* Ship Select Dropdown - Only show when NOT in Standby mode */}
{newCrewData.status !== 'Standby' && (
  <div className="relative">
    <button
      onClick={(e) => {
        e.stopPropagation();
        setShowShipDropdown(!showShipDropdown);
      }}
      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-medium text-sm transition-all flex items-center space-x-2 shadow-md"
    >
      <span>🚢</span>
      <span>{language === 'vi' ? 'Chọn tàu' : 'Ship Select'}</span>
      <span className="text-xs">▾</span>
    </button>
    
    {/* Ship Dropdown Menu */}
    {showShipDropdown && (
      <div className="absolute left-0 top-full mt-2 bg-white rounded-lg shadow-2xl border border-gray-200 py-2 min-w-[250px] z-[60] max-h-[400px] overflow-y-auto">
        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b border-gray-100">
          {language === 'vi' ? 'Chọn tàu từ công ty của bạn' : 'Select ship from your company'}
        </div>
        {ships.map(ship => (
          <button
            key={ship.id}
            onClick={() => {
              setSelectedShip(ship);
              setNewCrewData({
                ...newCrewData,
                ship_sign_on: ship.name,
                status: 'Sign on'
              });
              setShowShipDropdown(false);
              console.log(`🚢 Ship changed to: ${ship.name} in Add Crew Modal`);
            }}
            className={`w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors flex items-center justify-between ${
              selectedShip?.id === ship.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
            }`}
          >
            <div className="flex items-center space-x-3">
              <span className="text-xl">🚢</span>
              <div>
                <div className="font-semibold text-gray-800">{ship.name}</div>
                <div className="text-xs text-gray-500">
                  {ship.imo ? `IMO: ${ship.imo}` : ''} {ship.flag ? `• ${ship.flag}` : ''}
                </div>
              </div>
            </div>
            {selectedShip?.id === ship.id && (
              <span className="text-blue-600 font-bold">✓</span>
            )}
          </button>
        ))}
      </div>
    )}
  </div>
)}
```

#### 3. Click Outside Handler
**File:** `frontend/src/App.js`  
**Lines:** ~1894-1909

```javascript
// Handle click outside for Ship dropdown in Add Crew Modal
useEffect(() => {
  const handleClickOutside = (event) => {
    if (showShipDropdown) {
      const shipDropdown = document.querySelector('.absolute.left-0.top-full.mt-2.bg-white.rounded-lg.shadow-2xl');
      const shipButton = event.target.closest('button');
      
      if (shipDropdown && !shipDropdown.contains(event.target) && 
          !shipButton?.textContent.includes('Ship Select') && 
          !shipButton?.textContent.includes('Chọn tàu')) {
        setShowShipDropdown(false);
      }
    }
  };

  if (showShipDropdown) {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }
}, [showShipDropdown]);
```

## Features

### Visual Design
- **Purple gradient button** with ship emoji (🚢) and dropdown arrow (▾)
- Matches the modern, professional UI style
- Clear hover states and transitions
- Shadow effects for depth

### Dropdown Menu
- **White card** with shadow and border
- **Header section** with descriptive text
- **Ship list items** with:
  - Ship name (bold)
  - IMO number and flag (smaller text)
  - Ship emoji icon
  - Checkmark for currently selected ship
  - Blue highlight for selected ship with left border accent
- **Hover effects** on each ship item
- **Scrollable** when many ships (max-height: 400px)

### Behavior
- **Conditional visibility**: Only shows when `newCrewData.status !== 'Standby'`
- **Auto-update**: When ship is selected:
  - Updates `selectedShip` state
  - Sets `newCrewData.ship_sign_on` to ship name
  - Sets `newCrewData.status` to 'Sign on'
  - Closes dropdown automatically
- **Click outside to close**: Dropdown closes when clicking elsewhere
- **Console logging**: Logs ship changes for debugging

## User Experience

### Before
1. User opens "Add New Crew Member" modal
2. Realizes they need to add crew to a different ship
3. Must close modal
4. Click different ship in sidebar/header
5. Re-open "Add New Crew Member" modal
6. Start filling form again

### After  
1. User opens "Add New Crew Member" modal
2. Clicks "Ship Select" button in modal header
3. Selects desired ship from dropdown
4. `ship_sign_on` field is automatically updated
5. Continues filling form without interruption

## Integration with Existing Features
- **Works alongside Standby Crew toggle**: Both buttons are in the header
- **Hidden in Standby mode**: Ship Select disappears when "Standby Crew" is active (since standby crew don't have a ship)
- **Respects modal state**: Dropdown closes when modal is minimized/closed
- **Bilingual support**: Button text in English and Vietnamese

## Visual Layout

```
┌─────────────────────────────────────────────────┐
│  Add New Crew Member for: BROTHER 36            │
│                                                 │
│  [🚢 Ship Select ▾]  [⚪ Standby Crew]  [−] [×] │
└─────────────────────────────────────────────────┘
         │
         └─> Opens dropdown:
             ┌─────────────────────────────┐
             │ Select ship from your company│
             ├─────────────────────────────┤
             │ 🚢  BROTHER 36         ✓    │
             │     IMO: 8743531 • PANAMA   │
             ├─────────────────────────────┤
             │ 🚢  MINH ANH 09             │
             │     IMO: 8588911 • PANAMA   │
             └─────────────────────────────┘
```

## Technical Notes
- **z-index**: Set to 60 to ensure dropdown appears above modal content
- **Positioning**: Absolute positioning relative to button
- **Responsive**: Works on all screen sizes
- **Accessibility**: Clear hover states and visual feedback

## Testing
Verified functionality:
- ✅ Button appears to the left of Standby Crew toggle
- ✅ Button is purple gradient with ship emoji
- ✅ Dropdown opens on click
- ✅ Dropdown shows all ships with proper styling
- ✅ Currently selected ship is highlighted with checkmark
- ✅ Clicking a ship updates selectedShip and ship_sign_on
- ✅ Dropdown closes after selection
- ✅ Button hidden when in Standby mode
- ✅ Click outside closes dropdown

## Date
January 18, 2025
