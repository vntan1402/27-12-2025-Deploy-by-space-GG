# Company Logo Upload and Display Feature

## Summary
Implemented complete functionality to upload, store, and display company logos in the "Add New Company" and "Edit Company" modals.

## Features Implemented

### 1. Backend API Endpoint
**File:** `backend/server.py`

#### New Endpoint: `POST /api/companies/{company_id}/upload-logo`
```python
@api_router.post("/companies/{company_id}/upload-logo")
async def upload_company_logo(
    company_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
)
```

**Features:**
- Validates company existence
- Validates file type (must be image)
- Generates unique filename with timestamp
- Saves to `/app/backend/uploads/company_logos/`
- Updates company record with `logo_url`
- Returns logo URL and success message

**Security:**
- Only Admin and Super Admin can upload logos
- File type validation (only images allowed)
- Unique filenames prevent overwriting

### 2. Database Model Update
**File:** `backend/server.py`

Added `logo_url` field to Company models:

```python
class CompanyBase(BaseModel):
    name_vn: str
    name_en: str
    address_vn: str
    address_en: str
    tax_id: str
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[Union[str, datetime]] = None
    logo_url: Optional[str] = None  # NEW FIELD
    # ... other fields
```

### 3. Frontend Upload Interface
**File:** `frontend/src/App.js`

#### Company Form Modal Features:

**Logo Upload Section:**
```javascript
<input
  type="file"
  accept="image/*"
  onChange={(e) => setLogoFile(e.target.files[0])}
  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
/>
```

**Features:**
- File input with image-only filter
- Shows current logo preview when editing
- Displays supported formats (JPG, PNG, GIF, max 5MB)
- Preview current logo with 64x64px thumbnail

**Upload Logic:**
```javascript
const handleSubmitWithLogo = async () => {
  try {
    setUploading(true);
    
    // First submit company data
    const result = await onSubmit();
    
    // Then upload logo if provided
    if (logoFile && result) {
      const companyId = result.id || companyData.id;
      if (companyId) {
        await handleLogoUpload(companyId);
      }
    }
  } catch (error) {
    console.error('Error submitting company:', error);
  } finally {
    setUploading(false);
  }
};
```

**Upload Process:**
1. User selects company data and logo file
2. Click "Create Company" or "Update Company"
3. Company data saved first
4. Logo uploaded to server with company ID
5. Company record updated with logo URL
6. Success toast notification
7. Company list refreshed to show new logo

### 4. Logo Display in Company List
**File:** `frontend/src/App.js`

**Companies Table:**
```javascript
<td className="border border-gray-300 px-4 py-3 text-center">
  {company.logo_url ? (
    <img 
      src={`${API}${company.logo_url}`} 
      alt={company.name_en} 
      className="w-12 h-12 object-contain mx-auto rounded"
      onError={(e) => {
        e.target.style.display = 'none';
        e.target.nextSibling.style.display = 'flex';
      }}
    />
  ) : null}
  <div 
    className={`w-12 h-12 bg-gray-200 rounded flex items-center justify-center mx-auto text-gray-500 text-xs ${company.logo_url ? 'hidden' : 'flex'}`}
  >
    {language === 'vi' ? 'Chưa có' : 'No Logo'}
  </div>
</td>
```

**Features:**
- Logo column in companies table
- 48x48px logo display
- Fallback placeholder when no logo
- Error handling (shows placeholder if image fails to load)
- Centered alignment
- Rounded corners for polished look

## File Storage

### Backend Directory Structure:
```
/app/backend/
└── uploads/
    └── company_logos/
        ├── company-uuid_1234567890.png
        ├── company-uuid_1234567891.jpg
        └── ...
```

### Static File Serving:
Already configured in `server.py`:
```python
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### URL Format:
- Stored in DB: `/uploads/company_logos/{company_id}_{timestamp}.{ext}`
- Accessed via: `http://localhost:8001/uploads/company_logos/{company_id}_{timestamp}.{ext}`
- Frontend uses: `${API}${company.logo_url}`

## User Experience

### Creating New Company with Logo:
1. Click "Add New Company" button
2. Fill in required fields (Name VN, Name EN, Tax ID)
3. Click "Choose File" under "Company Logo"
4. Select image file (JPG, PNG, GIF)
5. See file name appear
6. Click "Create Company"
7. Loading spinner appears
8. Success toast: "Company created successfully!" and "Logo uploaded successfully!"
9. Modal closes
10. Company list updates with new logo visible

### Editing Company Logo:
1. Click "Edit" button on company row
2. Current logo displayed in modal (if exists)
3. Can replace by choosing new file
4. Click "Update Company"
5. Logo uploads automatically
6. Company list refreshes with new logo

### Viewing Companies:
- Company list table shows logo in first column
- 48x48px thumbnail size
- Clear "No Logo" placeholder for companies without logos
- Professional rounded corners

## Technical Details

### File Upload Specifications:
- **Accepted formats:** JPG, PNG, GIF
- **Max size:** 5MB (can be adjusted)
- **Naming convention:** `{company_id}_{unix_timestamp}.{extension}`
- **Storage location:** `/app/backend/uploads/company_logos/`

### Error Handling:
- Invalid file type → HTTP 400 error
- Company not found → HTTP 404 error
- Upload failure → Toast error message
- Image load failure → Shows placeholder

### Permissions:
- **Upload:** Admin and Super Admin only
- **View:** All authenticated users can see logos

## Bilingual Support
All UI text supports Vietnamese and English:
- "Logo công ty" / "Company Logo"
- "Chưa có" / "No Logo"
- "Hỗ trợ: JPG, PNG, GIF (tối đa 5MB)" / "Supported: JPG, PNG, GIF (max 5MB)"
- "Logo hiện tại" / "Current logo"
- Success/error messages in both languages

## Benefits

1. **Professional Appearance:** Companies can display their branding
2. **Easy Identification:** Visual logos make companies easier to recognize
3. **Complete Profile:** Companies have full profile with logo
4. **User-Friendly:** Simple file upload interface
5. **Reliable Storage:** Logos stored securely on server
6. **Error Resilient:** Graceful fallbacks for missing/broken images

## Testing Checklist

✅ Upload logo when creating new company
✅ Upload logo when editing existing company
✅ Display logo in company list table
✅ Show placeholder when no logo exists
✅ Handle image load errors gracefully
✅ Validate file types (only images)
✅ Generate unique filenames
✅ Update company record with logo URL
✅ Admin/Super Admin permission check
✅ Bilingual support
✅ Responsive design (48x48px thumbnail)

## Date
January 20, 2025
