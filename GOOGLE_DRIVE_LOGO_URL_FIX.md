# Google Drive Logo URL Fix

## Issue
User đã add Google Drive link cho Company logo nhưng không hiển thị trên homepage do:
1. Google Drive sharing link format không phải direct image URL
2. URL format cần convert từ `/file/d/FILE_ID/view` sang `/uc?export=view&id=FILE_ID`

## Solution Applied

### 1. Database URL Conversion
Converted AMCSC company logo URL from:
```
https://drive.google.com/file/d/1bfLRWLdFSN_KURxy0qJazn15B9YOMHic/view?usp=drive_link
```

To direct image URL:
```
https://drive.google.com/uc?export=view&id=1bfLRWLdFSN_KURxy0qJazn15B9YOMHic
```

### 2. Frontend URL Handling
**File:** `frontend/src/App.js` (line ~13317)

**Before:**
```javascript
src={`${BACKEND_URL}${companyLogo}`}
```

**After:**
```javascript
src={companyLogo.startsWith('http') ? companyLogo : `${BACKEND_URL}${companyLogo}`}
```

**Logic:**
- If URL starts with `http/https` → Use URL as-is (external URL)
- If URL starts with `/` → Prepend BACKEND_URL (internal path)

## Google Drive URL Formats

### Sharing Link (❌ Not Direct)
```
https://drive.google.com/file/d/FILE_ID/view
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
https://drive.google.com/file/d/FILE_ID/view?usp=drive_link
```

### Direct Image URL (✅ Works)
```
https://drive.google.com/uc?export=view&id=FILE_ID
https://drive.google.com/uc?id=FILE_ID
```

### Thumbnail URL
```
https://drive.google.com/thumbnail?id=FILE_ID
```

## Conversion Script

```python
import re

def convert_google_drive_url(url):
    """Convert Google Drive sharing link to direct image URL"""
    # Extract file ID
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return url
```

## Frontend Auto-Conversion (Recommended)

Add this helper function to automatically convert Google Drive URLs when user pastes:

```javascript
const convertGoogleDriveUrl = (url) => {
  // Check if it's a Google Drive sharing link
  if (url.includes('drive.google.com/file/d/')) {
    const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
    if (match) {
      const fileId = match[1];
      return `https://drive.google.com/uc?export=view&id=${fileId}`;
    }
  }
  return url;
};

// Use in onChange handler:
onChange={(e) => {
  const url = e.target.value;
  const convertedUrl = convertGoogleDriveUrl(url);
  setCompanyData(prev => ({ ...prev, logo_url: convertedUrl }));
}}
```

## Known Limitations

### Google Drive Permissions
- File must have "Anyone with the link can view" permission
- Private files won't display
- File owner needs to share publicly

### CORS/Cross-Origin Issues
- Preview environment may block external images
- Google Drive may restrict embedding
- Solution: Download and upload to server instead

### Alternative Solutions

1. **Download and Re-upload:**
   - Download logo from Google Drive
   - Upload to server using file upload feature
   - More reliable, no external dependencies

2. **Use Direct CDN:**
   - Host logo on image CDN (Imgur, Cloudinary, etc.)
   - Better performance and reliability

3. **Company Server:**
   - Host on company's own server/website
   - Full control over permissions

## Testing

### Check if URL works:
```bash
curl -I "https://drive.google.com/uc?export=view&id=FILE_ID"
```

Should return `HTTP/2 303` redirect to `drive.usercontent.google.com`

### Browser Test:
Open URL directly in browser:
```
https://drive.google.com/uc?export=view&id=1bfLRWLdFSN_KURxy0qJazn15B9YOMHic
```

Should show the image directly.

## Recommendation for Users

**Best Practice:**
1. ✅ Upload logo file directly (most reliable)
2. ✅ Host on company website
3. ✅ Use image CDN services
4. ⚠️ Google Drive links (may have permission/CORS issues)

**If using Google Drive:**
- Make sure file is publicly accessible
- Use direct image URL format (`/uc?export=view&id=`)
- Test URL in browser first
- Be aware of embedding restrictions

## Date
January 20, 2025
