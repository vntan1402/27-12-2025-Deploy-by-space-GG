# Add Crew Form - Standby Mode Enhancement

## Summary
Improved "Add New Crew" form to make adding Standby crew members easier and more intuitive with smart field management and visual feedback.

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~14800-14950

## Enhancements

### 1. Status Dropdown - Visual Feedback

**Before:**
```javascript
<select value={newCrewData.status}>
  <option value="Sign on">Đang trên tàu</option>
  <option value="Standby">Chờ</option>
  <option value="Leave">Nghỉ phép</option>
</select>
```

**After:**
- **Visual Badge**: Shows "🟠 Chế độ Standby" / "🟠 Standby Mode" when Standby is selected
- **Clearer Text**: "Chờ (Standby)" instead of just "Chờ"
- **Auto-sync**: Automatically sets `ship_sign_on = "-"` when Standby is selected

```javascript
<label>
  Trạng thái
  {newCrewData.status === 'Standby' && (
    <span className="ml-2 text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full">
      🟠 Chế độ Standby
    </span>
  )}
</label>
```

### 2. Ship Sign On Field - Smart Behavior

**Features:**
- **Auto-disabled** when Status = Standby
- **Visual hint**: Shows "(Tự động: -)" / "(Auto: -)" 
- **Grayed out**: Clear visual indication it's locked
- **Two-way sync maintained**:
  - Status = Standby → Ship = "-" (auto-set)
  - Ship = "-" → Status = Standby (existing)

```javascript
<select
  value={newCrewData.ship_sign_on}
  disabled={newCrewData.status === 'Standby'}
  className={newCrewData.status === 'Standby' 
    ? 'bg-gray-100 text-gray-500 cursor-not-allowed' 
    : ''
  }
>
```

### 3. Conditional Field Display

**Hidden when Status = Standby:**
- ❌ Place Sign On
- ❌ Date Sign On  
- ❌ Date Sign Off

**Logic:**
```javascript
{newCrewData.status !== 'Standby' && (
  <div>
    <label>Place Sign On</label>
    <input ... />
  </div>
)}
```

**Why?**
- These fields are not applicable for new Standby crew
- Reduces form clutter
- Prevents confusion about what to fill
- Cleaner, more focused interface

### 4. Two-Way Synchronization

**Complete sync chain:**

```
User Action                    → Auto Updates
─────────────────────────────────────────────
Select Status = "Standby"      → Ship Sign On = "-"
                               → Hide: Place/Date Sign On, Date Sign Off

Select Ship Sign On = "-"      → Status = "Standby"
                               → Hide fields

Fill Date Sign Off             → Status = "Standby"
                               → Ship Sign On = "-"
                               → Hide fields

Change Status to "Sign on"     → Enable Ship Sign On dropdown
                               → Show all fields
```

## User Experience

### Before
```
Steps to add Standby crew:
1. Fill basic info (name, DOB, etc.)
2. Select Status = "Standby"
3. Manually set Ship Sign On = "-"
4. Leave Place Sign On empty (confusing)
5. Leave Date Sign On empty (confusing)
6. Leave Date Sign Off empty (confusing)
7. Submit

⚠️ Confusion: Should I fill sign on/off fields?
⚠️ Many manual steps
```

### After
```
Steps to add Standby crew:
1. Fill basic info (name, DOB, etc.)
2. Select Status = "Standby"
   ✅ Ship automatically set to "-"
   ✅ Unnecessary fields disappear
   ✅ Clear orange badge shows "Standby Mode"
3. Submit

✅ Clear visual feedback
✅ Fewer fields to worry about
✅ Automatic field management
```

## Visual Indicators

### Standby Mode Active
- **Badge**: Orange badge next to Status label
- **Disabled field**: Ship Sign On grayed out with "(Auto: -)"
- **Hidden fields**: Place Sign On, Date Sign On, Date Sign Off removed
- **Cleaner form**: Less visual clutter

### Normal Mode (Sign on/Leave)
- No badge
- All fields visible
- Ship Sign On dropdown active
- Full functionality

## Form States

### State 1: Normal Mode (Sign on)
```
Required Fields:
✓ Full Name
✓ Sex, Rank, DOB
✓ Place of Birth, Passport

Optional Fields:
○ Status (default: Sign on)
○ Ship Sign On (dropdown of ships)
○ Place Sign On
○ Date Sign On
○ Date Sign Off
```

### State 2: Standby Mode
```
Required Fields:
✓ Full Name
✓ Sex, Rank, DOB
✓ Place of Birth, Passport

Optional Fields:
○ Status (set to: Standby)
○ Ship Sign On (locked to: "-")

Hidden Fields:
× Place Sign On
× Date Sign On
× Date Sign Off
```

## Benefits

1. **Reduced Cognitive Load**
   - Fewer decisions to make
   - Clear visual state
   - No ambiguous empty fields

2. **Error Prevention**
   - Can't forget to set Ship = "-"
   - Can't accidentally fill wrong fields
   - Automatic validation

3. **Faster Workflow**
   - Less scrolling (fewer fields)
   - Automatic field management
   - One selection triggers all changes

4. **Better UX**
   - Clear feedback with badge
   - Professional appearance
   - Intuitive behavior

## Testing Recommendations

1. **Standby Mode Activation:**
   - Select Status = "Standby"
   - Verify orange badge appears
   - Verify Ship Sign On locked to "-"
   - Verify Place/Date fields hidden

2. **Mode Switching:**
   - Start with Standby
   - Change to Sign on
   - Verify all fields reappear
   - Verify Ship dropdown enabled

3. **Two-way Sync:**
   - Set Ship = "-" first
   - Verify Status changes to Standby
   - Verify fields hide automatically

4. **Form Submission:**
   - Add Standby crew
   - Verify saved with ship_sign_on = "-"
   - Verify files go to Standby Crew folder

5. **Language Toggle:**
   - Test in Vietnamese
   - Test in English
   - Verify badge and hints display correctly

## Related Features

Works with:
- Automatic file movement to "Standby Crew" folder
- Status change auto-moves files
- Crew list display
- Certificate upload logic
