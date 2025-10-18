# Crew Info Bilingual Name Display Update

## Summary
Updated the Crew Member Information section to display both Vietnamese and English names simultaneously.

## Changes Made

**File:** `frontend/src/App.js`
**Lines:** ~9561-9581

### Previous Behavior
- Displayed only ONE name based on language setting:
  - If UI language is English AND `full_name_en` exists → show `full_name_en`
  - Otherwise → show `full_name` (Vietnamese)

### New Behavior
- **Always displays Vietnamese name** (`full_name`) as primary
- **Displays English name** (`full_name_en`) below if available
- Both names visible regardless of UI language setting

### Visual Layout
```
Họ và tên: NGUYEN VAN A
           Nguyen Van A
```

**Styling:**
- **Vietnamese Name** (primary):
  - Font: medium weight
  - Color: Dark gray (text-gray-900)
  - Transform: Uppercase
  
- **English Name** (secondary, if available):
  - Font: medium weight, smaller size (text-xs)
  - Color: Medium gray (text-gray-600)
  - Transform: Uppercase
  - Spacing: Small top margin (mt-0.5)

## User Experience Impact

**Before:**
- Users only saw one name depending on UI language
- Switching language changed displayed name

**After:**
- Users always see both names (Vietnamese primary, English secondary)
- Complete name information visible at all times
- Better for bilingual crew management

## Implementation Details

Changed from conditional single display:
```javascript
<span className="ml-2 text-gray-900 font-medium uppercase">
  {language === 'en' && displayCrewInfo.full_name_en 
    ? displayCrewInfo.full_name_en 
    : displayCrewInfo.full_name}
</span>
```

To stacked dual display:
```javascript
<div className="ml-2">
  <div className="text-gray-900 font-medium uppercase">
    {displayCrewInfo.full_name}
  </div>
  {displayCrewInfo.full_name_en && (
    <div className="text-gray-600 font-medium uppercase text-xs mt-0.5">
      {displayCrewInfo.full_name_en}
    </div>
  )}
</div>
```

## Testing Recommendations

1. Select a crew member with both Vietnamese and English names
2. Verify both names display (Vietnamese on top, English below)
3. Select a crew member with only Vietnamese name
4. Verify only Vietnamese name shows (no empty English line)
5. Test in both Vietnamese and English UI languages
6. Confirm display remains consistent regardless of language

## Related Changes

This update complements:
- Filter reordering (Crew before Status)
- Dynamic crew info based on filter selection
- DD/MM/YYYY date format for Date of Birth
