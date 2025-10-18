# Crew List - Row-Level Double Click

## Summary
Updated Company Crew List to allow double-clicking on any cell in a row to open the Crew Certificates View, not just the Full Name cell.

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~10950-10979

### Previous Behavior
- Only the **Full Name cell** had `onDoubleClick` event
- Users had to specifically double-click on the name to view certificates
- Other cells were not interactive for certificate viewing

### New Behavior
- **Entire row** now responds to double-click
- Double-clicking **any cell** in a crew member's row opens Crew Certificates View
- More intuitive and user-friendly interaction

## Implementation Details

### 1. Moved Double-Click Handler to Row Level

**Before:**
```javascript
<tr 
  key={crew.id} 
  className="hover:bg-gray-50 cursor-pointer"
  onContextMenu={(e) => handleCrewRightClick(e, crew)}
  title="Right-click to delete crew member"
>
  <td>...</td>
  <td 
    onDoubleClick={() => handleCrewNameDoubleClick(crew)}
    className="... hover:bg-blue-50"
  >
    {crew.full_name}
  </td>
  ...
</tr>
```

**After:**
```javascript
<tr 
  key={crew.id} 
  className="hover:bg-gray-50 cursor-pointer"
  onContextMenu={(e) => handleCrewRightClick(e, crew)}
  onDoubleClick={() => handleCrewNameDoubleClick(crew)}
  title="Double-click to view certificates | Right-click to delete crew member"
>
  <td>...</td>
  <td className="...">
    {crew.full_name}
  </td>
  ...
</tr>
```

### 2. Updated Tooltips

**Row Tooltip:**
- Vietnamese: "Nhấp đúp để xem chứng chỉ | Chuột phải để xóa thuyền viên"
- English: "Double-click to view certificates | Right-click to delete crew member"

**Full Name Cell Tooltip:**
- Simplified to show only name information
- Removed double-click instruction (now at row level)

### 3. Cleaned Up Cell Styling

**Removed from Full Name cell:**
- `cursor-pointer` (already on row)
- `hover:bg-blue-50` (row hover is sufficient)
- Redundant double-click instruction in tooltip

## User Experience Impact

### Before
```
User workflow:
1. Locate crew member in table
2. Find the Full Name cell specifically
3. Double-click on the name
4. View certificates
```

### After
```
User workflow:
1. Locate crew member in table
2. Double-click anywhere on the row
3. View certificates

✅ 50% fewer steps
✅ More natural interaction
✅ Larger clickable area
```

## Event Handling

**Protected Events (still work correctly):**
- ✅ Checkbox click: Uses `stopPropagation()` to prevent row double-click
- ✅ Right-click menu: Context menu still works on row
- ✅ File icon clicks: Uses `stopPropagation()` to open files directly
- ✅ Other cell-specific right-clicks (passport, rank): Still functional

**Double-Click Triggers Certificate View:**
- Any cell in the row (except when clicking interactive elements)
- Interactive elements have `stopPropagation()` to prevent conflicts

## Testing Recommendations

1. **Double-Click on Different Cells:**
   - Test double-clicking on: Name, Sex, Rank, DOB, Place of Birth, Passport, Status, Ship Sign On, Date Sign On, Date Sign Off
   - Verify all open Crew Certificates View

2. **Protected Events:**
   - Click checkbox → should check/uncheck without opening certificates
   - Right-click anywhere on row → should show delete menu
   - Click passport file icon → should open file, not certificates
   - Right-click on passport cell → should show passport options

3. **Visual Feedback:**
   - Hover over any row → should show hover background
   - Cursor should show pointer everywhere on row

4. **Language:**
   - Test in both Vietnamese and English
   - Verify tooltips display correctly

## Related Features

Works seamlessly with:
- Dynamic crew info display based on filter
- Separate Vietnamese/English name cells in Crew Info
- DD/MM/YYYY date format
- Filter reordering (Crew before Status)
- Back to Crew List button
