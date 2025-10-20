# Submenu Key Rename: inspection_records → class_survey_reports

## Change Summary

Renamed the submenu key from `inspection_records` to `class_survey_reports` for better consistency and clarity.

## Reason for Change

- **Old key:** `inspection_records` - Generic and unclear
- **New key:** `class_survey_reports` - More specific and consistent with the feature name
- Avoids confusion with the existing `survey_reports` key (which is for "Test Report")

## Files Modified

**File:** `/app/frontend/src/App.js`

### Changes Made:

1. **useEffect hook** (line ~1882-1886)
   ```javascript
   // OLD
   if (selectedShip && selectedSubMenu === 'inspection_records') {
   
   // NEW
   if (selectedShip && selectedSubMenu === 'class_survey_reports') {
   ```

2. **Category mapping** (line ~5651)
   ```javascript
   // OLD
   'inspection_records': 'inspection_records',
   
   // NEW
   'class_survey_reports': 'class_survey_reports',
   ```

3. **SubMenu items definition** (line ~8665)
   ```javascript
   // OLD
   { key: 'inspection_records', name: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report' },
   
   // NEW
   { key: 'class_survey_reports', name: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report' },
   ```

4. **Conditional rendering** (line ~10439)
   ```javascript
   // OLD
   {selectedCategory === 'documents' && selectedSubMenu === 'inspection_records' && (
   
   // NEW
   {selectedCategory === 'documents' && selectedSubMenu === 'class_survey_reports' && (
   ```

5. **Categories arrays** (lines ~20126, ~21185)
   ```javascript
   // OLD
   const categories = ['certificates', 'inspection_records', 'survey_reports', 'drawings_manuals', 'other_documents'];
   
   // NEW
   const categories = ['certificates', 'class_survey_reports', 'survey_reports', 'drawings_manuals', 'other_documents'];
   ```

6. **Category name mapping** (line ~21192)
   ```javascript
   // OLD
   inspection_records: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report',
   
   // NEW
   class_survey_reports: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report',
   ```

7. **Modal submenu items** (line ~22839)
   ```javascript
   // OLD
   { key: 'inspection_records', name: 'Class Survey Report' },
   
   // NEW
   { key: 'class_survey_reports', name: 'Class Survey Report' },
   ```

## Current Submenu Structure

```
CLASS & FLAG CERT (documents)
├── Certificates (certificates)
├── Class Survey Report (class_survey_reports) ← Updated key
├── Test Report (survey_reports)
├── Drawings & Manuals (drawings_manuals)
└── Other Documents (other_documents)
```

## Impact

- **Frontend:** All references updated, no breaking changes
- **Backend:** No changes needed (uses `survey_reports` collection)
- **Database:** No changes needed
- **User Experience:** No visible changes, same display names

## Testing

✅ Frontend compiled successfully
✅ All occurrences of `inspection_records` replaced
✅ No errors in frontend logs

## Notes

- The display name remains "Class Survey Report" (English) / "Hồ sơ Đăng kiểm" (Vietnamese)
- The backend API endpoints remain unchanged (`/api/survey-reports`)
- The database collection remains `survey_reports`
- Only the frontend submenu key changed for consistency
