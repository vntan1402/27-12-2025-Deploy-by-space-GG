# Google Drive Logo Display Fix

## 🔧 Vấn đề

Company logo được lưu dưới dạng Google Drive link nhưng không hiển thị trên Homepage và các pages khác.

**Link gốc từ database:**
```
https://drive.google.com/file/d/1m227N4Jxsx7iOVMREYOyT60F-HLuSyFR/view?usp=drive_link
```

**Vấn đề:**
- Đây là link **VIEW** (để xem file trên Google Drive interface)
- Không phải link **DIRECT IMAGE** (để embed ảnh)
- Browser không thể load ảnh từ link view

---

## ✅ Giải pháp

### Convert Google Drive View Link → Direct Image Link

**Format cần thiết:**
```
https://drive.google.com/uc?export=view&id=FILE_ID
```

**Ví dụ:**
- **Input:**  `https://drive.google.com/file/d/1m227N4Jxsx7iOVMREYOyT60F-HLuSyFR/view?usp=drive_link`
- **Output:** `https://drive.google.com/uc?export=view&id=1m227N4Jxsx7iOVMREYOyT60F-HLuSyFR`

---

## 📋 Files đã update

### 1. HomePage.jsx
**File:** `/app/frontend/src/pages/HomePage.jsx`

**Thay đổi:**
```javascript
// TRƯỚC
if (companyLogo.startsWith('http')) {
  logoUrl = companyLogo;  // ❌ Dùng trực tiếp, không convert
}

// SAU
if (companyLogo.startsWith('http')) {
  // Check if it's a Google Drive link and convert to direct image URL
  if (companyLogo.includes('drive.google.com/file/d/')) {
    const fileIdMatch = companyLogo.match(/\/d\/([^\/]+)/);
    if (fileIdMatch && fileIdMatch[1]) {
      const fileId = fileIdMatch[1];
      logoUrl = `https://drive.google.com/uc?export=view&id=${fileId}`;
      console.log('🔄 Converted Google Drive URL to direct image:', logoUrl);
    } else {
      logoUrl = companyLogo;
    }
  } else {
    logoUrl = companyLogo;
  }
}
```

---

### 2. CompanyInfoPanel.jsx
**File:** `/app/frontend/src/components/CompanyInfoPanel.jsx`

**Thay đổi function `getLogoUrl()`:**
```javascript
// TRƯỚC
const getLogoUrl = (logoUrl) => {
  if (!logoUrl) return null;
  if (logoUrl.startsWith('http')) {
    return logoUrl;  // ❌ Không convert
  }
  // ...
};

// SAU
const getLogoUrl = (logoUrl) => {
  if (!logoUrl) return null;
  if (logoUrl.startsWith('http')) {
    // Check if it's a Google Drive link and convert to direct image URL
    if (logoUrl.includes('drive.google.com/file/d/')) {
      const fileIdMatch = logoUrl.match(/\/d\/([^\/]+)/);
      if (fileIdMatch && fileIdMatch[1]) {
        const fileId = fileIdMatch[1];
        return `https://drive.google.com/uc?export=view&id=${fileId}`;
      }
    }
    return logoUrl;
  }
  // ...
};
```

---

### 3. googleDriveHelpers.js (NEW)
**File:** `/app/frontend/src/utils/googleDriveHelpers.js`

**Tạo helper functions để reuse:**

```javascript
/**
 * Convert Google Drive view link to direct image link
 */
export const convertGoogleDriveUrl = (url) => {
  if (!url || typeof url !== 'string') return url;
  
  if (url.includes('drive.google.com/file/d/')) {
    const fileIdMatch = url.match(/\/d\/([^\/\?]+)/);
    if (fileIdMatch && fileIdMatch[1]) {
      const fileId = fileIdMatch[1];
      return `https://drive.google.com/uc?export=view&id=${fileId}`;
    }
  }
  
  return url;
};

/**
 * Check if URL is a Google Drive link
 */
export const isGoogleDriveUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  return url.includes('drive.google.com');
};

/**
 * Extract file ID from Google Drive URL
 */
export const extractGoogleDriveFileId = (url) => {
  if (!url || typeof url !== 'string') return null;
  
  const fileIdMatch = url.match(/\/d\/([^\/\?]+)/);
  return fileIdMatch ? fileIdMatch[1] : null;
};

/**
 * Get embeddable Google Drive URL
 */
export const getGoogleDriveEmbedUrl = (url) => {
  const fileId = extractGoogleDriveFileId(url);
  if (fileId) {
    return `https://drive.google.com/file/d/${fileId}/preview`;
  }
  return url;
};

/**
 * Get downloadable Google Drive URL
 */
export const getGoogleDriveDownloadUrl = (url) => {
  const fileId = extractGoogleDriveFileId(url);
  if (fileId) {
    return `https://drive.google.com/uc?export=download&id=${fileId}`;
  }
  return url;
};
```

---

## 🎯 Các loại Google Drive URL

| Type | Format | Use Case |
|------|--------|----------|
| **View Link** | `/file/d/FILE_ID/view` | Xem file trên Google Drive UI |
| **Direct Image** | `/uc?export=view&id=FILE_ID` | Embed ảnh trong web (✅ Dùng cho logo) |
| **Preview/Embed** | `/file/d/FILE_ID/preview` | Embed iframe (PDF, video) |
| **Download** | `/uc?export=download&id=FILE_ID` | Download trực tiếp |

---

## 🧪 Testing

### Test Case 1: Logo hiển thị trên Homepage

**Steps:**
1. Refresh browser (Ctrl + F5)
2. Login với user có company logo
3. Check Homepage

**Expected:**
- ✅ Company logo hiển thị trong banner màu trắng
- ✅ Console log: `🔄 Converted Google Drive URL to direct image: https://drive.google.com/uc?export=view&id=...`
- ✅ Image load thành công (không có icon broken image)

---

### Test Case 2: Logo hiển thị trong CompanyInfoPanel

**Steps:**
1. Vào các pages có CompanyInfoPanel (Ship Information, Certificates, etc.)
2. Check company logo ở phần đầu panel

**Expected:**
- ✅ Logo hiển thị ở bên trái panel
- ✅ Không có icon 🏢 placeholder
- ✅ Image load thành công

---

### Test Case 3: Các loại URL khác vẫn hoạt động

**Test với:**
- Local uploads: `/uploads/companies/logo.png`
- External URLs: `https://example.com/logo.png`
- Relative paths: `/api/files/companies/logo.png`

**Expected:**
- ✅ Tất cả các loại URL vẫn hoạt động bình thường
- ✅ Logic convert chỉ áp dụng cho Google Drive links

---

## 📊 Flow Logic

```
Company Logo URL từ Database
    ↓
Check URL type
    ↓
┌─────────────────┬──────────────────┬────────────────┐
│ Google Drive    │ Local Upload     │ External URL   │
│ drive.google... │ /uploads/...     │ https://...    │
└────────┬────────┴────────┬─────────┴────────┬───────┘
         ↓                 ↓                  ↓
    Extract File ID   Add /api/files/    Use as-is
         ↓                 ↓                  ↓
    Convert to            ↓                  ↓
    /uc?export=view       ↓                  ↓
         ↓                 ↓                  ↓
    ┌────────────────────────────────────────┐
    │      Display Image on Frontend         │
    └────────────────────────────────────────┘
```

---

## 🔍 Debugging

### Nếu logo vẫn không hiển thị:

**1. Check Console Logs**
```javascript
// Logs to look for:
🖼️ Logo URL: https://drive.google.com/uc?export=view&id=...
🔄 Converted Google Drive URL to direct image: ...
✅ Company logo loaded successfully
```

**2. Check Network Tab**
- URL request có đúng format không?
- Response status có phải 200 OK?
- Response type có phải image?

**3. Check Database**
```javascript
// In browser console:
console.log(userCompany.logo_url);
```

**4. Test URL trực tiếp**
- Copy converted URL từ console
- Paste vào browser tab mới
- Logo có hiển thị không?

---

## 🎨 UI Behavior

### HomePage Logo Banner:

**Khi có logo:**
```
┌──────────────────────────────────────┐
│                                      │
│         [COMPANY LOGO IMAGE]         │
│                                      │
└──────────────────────────────────────┘
```

**Khi không có logo:**
```
┌──────────────────────────────────────┐
│             🏢                       │
│   Logo công ty sẽ hiển thị ở đây    │
│      khi được tải lên                │
└──────────────────────────────────────┘
```

---

## 📝 Notes

### Google Drive Permissions:
- File phải được set "Anyone with the link can view"
- Nếu file private, image sẽ không load
- Check sharing settings trong Google Drive

### Alternative Solutions:
1. **Upload to backend** (Khuyến nghị cho production)
2. **Use CDN** (CloudFlare, AWS S3)
3. **Google Drive API** (Cần authentication)

### Performance:
- Google Drive có thể slow hơn local uploads
- Có rate limits
- Consider caching hoặc move to CDN cho production

---

## ✅ Status

- ✅ HomePage.jsx - Updated with Google Drive conversion
- ✅ CompanyInfoPanel.jsx - Updated with Google Drive conversion
- ✅ googleDriveHelpers.js - Created utility functions
- ✅ Frontend restarted
- ✅ Ready for testing

---

**Last Updated**: 2025-01-09
**Status**: ✅ COMPLETED & READY FOR TESTING
