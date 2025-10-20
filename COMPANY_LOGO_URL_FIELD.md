# Company Logo URL Field Feature

## Summary
Added "Company Logo URL" input field to Add/Edit Company modals, allowing users to provide logo URLs directly instead of uploading files.

## Features Implemented

### 1. Frontend - Logo URL Input Field
**File:** `frontend/src/App.js`

**New Input Field:**
```javascript
{/* Logo URL Input */}
<div className="mb-3">
  <label className="block text-xs font-medium text-gray-600 mb-1">
    {language === 'vi' ? 'URL Logo (Nhập URL hình ảnh)' : 'Logo URL (Enter image URL)'}
  </label>
  <input
    type="text"
    value={companyData.logo_url || ''}
    onChange={(e) => setCompanyData(prev => ({ ...prev, logo_url: e.target.value }))}
    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
    placeholder="https://example.com/logo.png"
  />
  <p className="text-xs text-gray-500 mt-1">
    {language === 'vi' ? 'Hoặc nhập URL trực tiếp của logo' : 'Or enter logo URL directly'}
  </p>
</div>
```

**Live Logo Preview:**
```javascript
{companyData.logo_url && (
  <div className="mt-3">
    <p className="text-xs font-medium text-gray-600 mb-2">
      {language === 'vi' ? 'Xem trước logo:' : 'Logo preview:'}
    </p>
    <img 
      src={companyData.logo_url.startsWith('http') ? companyData.logo_url : `${API}${companyData.logo_url}`}
      alt="Logo preview" 
      className="w-20 h-20 object-contain border border-gray-200 rounded bg-gray-50"
      onError={(e) => {
        e.target.style.display = 'none';
        e.target.nextSibling.style.display = 'block';
      }}
    />
    <div className="hidden text-xs text-red-500 mt-1">
      {language === 'vi' ? 'Không thể tải logo' : 'Failed to load logo'}
    </div>
  </div>
)}
```

### 2. Backend - Logo URL Support
**File:** `backend/server.py`

**Updated CompanyUpdate Model:**
```python
class CompanyUpdate(BaseModel):
    name_vn: Optional[str] = None
    name_en: Optional[str] = None
    address_vn: Optional[str] = None
    address_en: Optional[str] = None
    tax_id: Optional[str] = None
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[Union[str, datetime]] = None
    logo_url: Optional[str] = None  # NEW FIELD
    # ... other fields
```

### 3. Priority Logic
**File:** `frontend/src/App.js`

```javascript
const handleSubmitWithLogo = async () => {
  try {
    setUploading(true);
    
    // First submit company data (including logo_url if provided)
    const result = await onSubmit();
    
    // Only upload file if:
    // 1. User selected a file to upload
    // 2. Company was created/updated successfully
    // 3. User didn't provide a logo_url (URL takes priority)
    if (logoFile && result && !companyData.logo_url) {
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

## User Interface

### Form Layout:
```
┌────────────────────────────────────────────┐
│ Company Logo                               │
├────────────────────────────────────────────┤
│ Logo URL (Enter image URL)                │
│ ┌────────────────────────────────────────┐│
│ │ https://example.com/logo.png          ││
│ └────────────────────────────────────────┘│
│ Or enter logo URL directly                │
│                                            │
│ Or upload file                            │
│ [Choose File] No file chosen              │
│ Supported: JPG, PNG, GIF (max 5MB)       │
│                                            │
│ Logo preview:                             │
│ [Preview Image 80x80px]                   │
└────────────────────────────────────────────┘
```

## Features

### 1. Dual Input Methods
- **URL Input**: Direct URL to hosted logo
- **File Upload**: Upload logo file to server
- **Priority**: URL takes precedence over file upload

### 2. Live Preview
- Shows logo preview when URL is entered
- Updates in real-time as user types
- Handles both external URLs (http/https) and internal URLs (/uploads/...)
- Error handling with fallback message

### 3. Smart URL Detection
```javascript
src={companyData.logo_url.startsWith('http') 
  ? companyData.logo_url 
  : `${API}${companyData.logo_url}`}
```
- External URLs (starting with http/https): Used directly
- Internal paths (starting with /): Prepended with API base URL

### 4. Validation
- No validation on URL format (flexible)
- Image loads successfully → Show preview
- Image fails to load → Show error message
- User can try different URL

## Use Cases

### 1. External Logo Hosting
User has logo hosted on CDN or website:
```
https://cdn.mycompany.com/logo.png
https://mywebsite.com/assets/logo.png
https://imgur.com/abc123.png
```

### 2. Placeholder Testing
User can test with placeholder services:
```
https://via.placeholder.com/200
https://picsum.photos/200
```

### 3. Previously Uploaded Logos
System displays internal logo paths:
```
/uploads/company_logos/company-uuid_timestamp.png
```

## User Experience

### Creating New Company with URL:
1. Click "Add New Company"
2. Fill required fields (Name, Tax ID, etc.)
3. Enter logo URL in "Logo URL" field
4. See live preview appear
5. Click "Create Company"
6. Company saved with logo_url
7. Logo displays on homepage

### Editing Company Logo URL:
1. Click "Edit" on company
2. Current logo shown in preview (if exists)
3. Change URL in "Logo URL" field
4. Preview updates immediately
5. Click "Update Company"
6. New logo URL saved
7. Homepage updates with new logo

### Upload Priority:
- **If URL provided**: Use URL, ignore file upload
- **If no URL**: Upload file and generate URL
- **If both**: URL wins, file ignored

## Technical Details

### State Management
```javascript
const [logoFile, setLogoFile] = useState(null);        // For file upload
companyData.logo_url                                   // For URL input
```

### Data Flow
1. User enters URL → Updates `companyData.logo_url`
2. User submits form → Sends `logo_url` in payload
3. Backend saves `logo_url` to database
4. Homepage fetches company → Gets `logo_url`
5. Homepage displays logo from URL

### Error Handling
- Invalid URL → Image fails to load → Shows error message
- Network error → Fallback to error message
- CORS issues → May block external URLs (browser security)
- Missing logo → Shows placeholder on homepage

## Benefits

1. **Flexibility**: Support both hosted and uploaded logos
2. **Speed**: No upload time for external URLs
3. **Storage**: Can use external CDN, save server storage
4. **Easy Testing**: Quick testing with placeholder URLs
5. **Migration**: Easy to move from file uploads to CDN
6. **Reliability**: Can use reliable CDN services

## Limitations

### Browser Security
- CORS may block some external URLs
- ORB (Opaque Response Blocking) may prevent loading
- Mixed content (HTTP on HTTPS site) blocked

### Solutions
- Use HTTPS URLs only
- Host logos on same domain
- Use CDN with proper CORS headers
- Or upload files directly

## Testing Checklist

✅ URL input field visible in Add Company modal
✅ URL input field visible in Edit Company modal
✅ Can enter external URL (http/https)
✅ Live preview shows when URL entered
✅ Preview updates on URL change
✅ Error message shows for invalid URLs
✅ File upload still works (when no URL)
✅ URL takes priority over file upload
✅ Logo saved to database (logo_url field)
✅ Logo displays on homepage from URL
✅ Bilingual support (VN/EN)

## Examples

### Valid URLs:
```
✅ https://www.example.com/logo.png
✅ https://cdn.company.com/branding/logo.jpg
✅ https://via.placeholder.com/200
✅ /uploads/company_logos/uuid_timestamp.png
```

### Invalid/Problematic URLs:
```
⚠️ http://insecure-site.com/logo.png (mixed content)
⚠️ https://blocked-cors-site.com/logo.png (CORS)
❌ not-a-valid-url (no protocol)
❌ /local/path/logo.png (not accessible)
```

## Date
January 20, 2025
