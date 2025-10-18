# Crew Info - Separate Name Cells Layout

## Summary
Updated Crew Member Information section to display Vietnamese and English names in separate cells with a 4-column grid layout.

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~9561-9618

### Layout Change

**Previous Layout (3 columns):**
```
Row 1: [Full Name (both VN + EN)] | Rank              | Date of Birth
Row 2: Place of Birth             | Passport          | Status
Row 3: Ship Sign On               | -                 | -
```

**New Layout (4 columns):**
```
Row 1: Full Name (VN) | Full Name (EN) | Rank           | Date of Birth
Row 2: Place of Birth | Passport       | Status         | Ship Sign On
```

### Key Changes

1. **Grid Columns:** Changed from `grid-cols-3` to `grid-cols-4`

2. **Name Display:**
   - **Cell 1:** "Họ và tên (Việt)" / "Full Name (VN)" → displays `full_name`
   - **Cell 2:** "Họ và tên (Anh)" / "Full Name (EN)" → displays `full_name_en`
   - Both names have separate cells with their own labels

3. **Compact Layout:**
   - All 8 fields now fit in 2 rows instead of 3 rows
   - More efficient use of horizontal space
   - Better visual balance

### Field Display

**Row 1 (4 fields):**
1. Full Name (Vietnamese)
2. Full Name (English) 
3. Rank
4. Date of Birth (DD/MM/YYYY format)

**Row 2 (4 fields):**
5. Place of Birth
6. Passport
7. Status (with color coding)
8. Ship Sign On (with color coding)

### Labels (Bilingual)

- Vietnamese UI: "Họ và tên (Việt)" | "Họ và tên (Anh)"
- English UI: "Full Name (VN)" | "Full Name (EN)"

### Fallback Display

- If `full_name_en` is empty or null → displays "-"
- Both cells always visible, providing consistent layout

## Visual Improvements

**Before:**
- Names stacked vertically in one cell
- Harder to distinguish between Vietnamese and English names
- 3 rows with unbalanced spacing

**After:**
- Names side-by-side in separate cells
- Clear labeling for each name variant
- 2 compact rows with balanced layout
- Better visual hierarchy

## User Experience Impact

1. **Clarity:** Separate cells make it immediately clear which name is Vietnamese and which is English
2. **Consistency:** Both name fields always present, maintaining uniform layout
3. **Readability:** Side-by-side layout easier to scan than stacked layout
4. **Space Efficiency:** Reduced vertical height while maintaining readability

## Technical Implementation

```javascript
// 4-column grid
<div className="grid grid-cols-4 gap-4 text-sm">
  
  // Vietnamese name cell
  <div>
    <span className="font-semibold text-gray-700">
      {language === 'vi' ? 'Họ và tên (Việt):' : 'Full Name (VN):'}
    </span>
    <div className="ml-2 text-gray-900 font-medium uppercase">
      {displayCrewInfo.full_name || '-'}
    </div>
  </div>
  
  // English name cell  
  <div>
    <span className="font-semibold text-gray-700">
      {language === 'vi' ? 'Họ và tên (Anh):' : 'Full Name (EN):'}
    </span>
    <div className="ml-2 text-gray-900 font-medium uppercase">
      {displayCrewInfo.full_name_en || '-'}
    </div>
  </div>
  
  // ... other fields ...
</div>
```

## Testing Recommendations

1. **With Both Names:**
   - Select crew with both Vietnamese and English names
   - Verify both appear in separate cells
   - Check proper uppercase formatting

2. **Without English Name:**
   - Select crew with only Vietnamese name
   - Verify English name cell shows "-"
   - Confirm layout remains consistent

3. **Language Switching:**
   - Test in Vietnamese UI: labels show "Họ và tên (Việt)" / "Họ và tên (Anh)"
   - Test in English UI: labels show "Full Name (VN)" / "Full Name (EN)"

4. **Responsive Layout:**
   - Verify 4-column grid displays properly
   - Check spacing and alignment
   - Ensure all fields remain readable

## Related Features

This update works with:
- Dynamic crew info based on filter selection
- DD/MM/YYYY date format for Date of Birth
- Color-coded Status and Ship Sign On fields
- Filter reordering (Crew before Status)
