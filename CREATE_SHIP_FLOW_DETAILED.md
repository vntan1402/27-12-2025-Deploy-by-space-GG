# Flow Chi Tiết Khi Click Nút "Create Ship"

## Tổng Quan

```
Click "Create Ship" 
    ↓
Validate Form 
    ↓
Prepare API Data 
    ↓
Call Backend API 
    ↓
Show Success Toast (800ms)
    ↓
Close Modal
    ↓
Navigate to /certificates
    ↓
Background: Poll Google Drive Status
```

---

## Chi Tiết Từng Bước

### **Bước 1: User Click Button**

**Location:** Modal footer button
```jsx
<button 
  onClick={handleSubmit} // ← Triggers submission
  disabled={isSubmitting}
>
  {language === 'vi' ? 'TẠO TÀU' : 'CREATE SHIP'}
</button>
```

**Điều kiện:**
- ✅ Button không bị disabled (`isSubmitting = false`)
- ✅ Form được submit (không bị preventDefault từ đâu khác)

---

### **Bước 2: Form Validation (Line 392-403)**

```javascript
const handleSubmit = async (e) => {
  e.preventDefault(); // Ngăn form submit mặc định
  
  // Validate required fields (Ship Type is optional)
  if (!shipData.name || !shipData.imo_number || !shipData.class_society || 
      !shipData.flag || !shipData.company || !shipData.ship_owner) {
    toast.error('❌ Vui lòng điền đầy đủ các trường bắt buộc');
    return; // STOP nếu validation fail
  }
  
  setIsSubmitting(true); // Set loading state
  // ... continue
}
```

**Required Fields (BẮT BUỘC):**
- ✅ Ship Name (`name`)
- ✅ IMO Number (`imo_number`)
- ✅ Class Society (`class_society`)
- ✅ Flag (`flag`)
- ✅ Company (`company`)
- ✅ Ship Owner (`ship_owner`)

**Optional Fields:**
- Ship Type (`ship_type`) - CÓ THỂ để trống
- Tất cả các fields khác

**Nếu validation FAIL:**
- Show error toast
- Return sớm (không proceed)
- `isSubmitting` vẫn = `false`

---

### **Bước 3: Prepare API Data (Line 408-433)**

```javascript
const apiData = {
  // Basic Information
  name: shipData.name.trim(),
  imo: shipData.imo_number.trim(), // Note: Backend expects 'imo'
  ship_type: shipData.ship_type.trim() || null, // Optional
  class_society: shipData.class_society.trim(),
  flag: shipData.flag.trim(),
  
  // Technical Details
  gross_tonnage: shipData.gross_tonnage ? parseFloat(shipData.gross_tonnage) : null,
  deadweight: shipData.deadweight ? parseFloat(shipData.deadweight) : null,
  built_year: shipData.built_year ? parseInt(shipData.built_year) : null,
  delivery_date: convertDateInputToUTC(shipData.delivery_date),
  keel_laid: convertDateInputToUTC(shipData.keel_laid),
  ship_owner: shipData.ship_owner.trim(),
  company: shipData.company.trim(),
  
  // Docking Information (MM/YYYY → ISO datetime)
  last_docking: formatLastDockingForBackend(shipData.last_docking),
  last_docking_2: formatLastDockingForBackend(shipData.last_docking_2),
  next_docking: convertDateInputToUTC(shipData.next_docking),
  
  // Survey Information (Date → ISO datetime)
  last_special_survey: convertDateInputToUTC(shipData.last_special_survey),
  last_intermediate_survey: convertDateInputToUTC(shipData.last_intermediate_survey),
  special_survey_from_date: convertDateInputToUTC(shipData.special_survey_from_date),
  special_survey_to_date: convertDateInputToUTC(shipData.special_survey_to_date),
  
  // Anniversary Date
  anniversary_date_day: shipData.anniversary_date_day ? parseInt(...) : null,
  anniversary_date_month: shipData.anniversary_date_month ? parseInt(...) : null,
};
```

**Data Transformations:**
1. **String fields:** `.trim()` để remove whitespace
2. **Numbers:** `parseFloat()` hoặc `parseInt()`
3. **Dates:** Convert to ISO datetime format (UTC)
4. **Optional fields:** `|| null` nếu empty
5. **Field name mapping:** `imo_number` → `imo`

**Date Conversion Examples:**
```javascript
// Input: "01/2024" (MM/YYYY)
// Output: "2024-01-01T00:00:00Z" (ISO datetime)

// Input: "2024-05-15" (YYYY-MM-DD)
// Output: "2024-05-15T00:00:00Z" (ISO datetime)
```

---

### **Bước 4: Call Backend API (Line 437)**

```javascript
console.log('Creating ship with data:', apiData); // Debug log

const response = await shipService.create(apiData);

console.log('Ship creation response:', response); // Debug log
```

**API Call Details:**
- **Endpoint:** `POST /api/ships`
- **Method:** `shipService.create(apiData)`
- **File:** `/app/frontend/src/services/shipService.js`
- **Headers:** Includes JWT authentication token
- **Timeout:** 30 seconds

**Backend Processing:**
1. Validate request data (Pydantic models)
2. Generate UUID for ship ID
3. Save ship to MongoDB
4. **Start background thread:** Create Google Drive folder structure
5. **Return immediately** (2-3 seconds) - không đợi Google Drive

**Response Structure:**
```javascript
{
  data: {
    id: "572706a6-e676-4f49-8838-d554cc364ed0",
    name: "MINH ANH 09",
    imo: "1234567",
    ship_type: "Bulk Carrier",
    class_society: "DNV GL",
    flag: "Vietnam",
    // ... all other fields
    created_at: "2024-01-15T10:30:00Z",
    gdrive_folder_status: null, // Initially not set
  }
}
```

---

### **Bước 5: Success Toast (Line 446-452)**

```javascript
if (response && response.data && response.data.id) {
  const shipId = response.data.id;
  const shipName = shipData.name;
  
  // Show success toast
  toast.success(`✅ Tạo tàu ${shipName} thành công!`);
  
  // Wait 800ms for user to see the toast
  await new Promise(resolve => setTimeout(resolve, 800));
  
  // ... continue
}
```

**Timeline:**
- `0ms`: Toast appears on screen
- `800ms`: Wait completes
- Toast stays visible for 3 seconds total (default toast duration)

**Purpose:** Give user time to SEE success message before modal closes

---

### **Bước 6: Close Modal (Line 455)**

```javascript
handleClose();
```

**handleClose() Function:**
```javascript
const handleClose = () => {
  // Reset all form fields to initial state
  setShipData({
    name: '',
    imo_number: '',
    ship_type: '',
    // ... all fields reset to empty
  });
  setPdfFile(null);
  setIsPdfAnalyzing(false);
  setUserCompanyName('');
  setIsSubmitting(false);
  
  // Call parent's onClose callback
  onClose(); // ← This sets showAddShipModal = false in HomePage
};
```

**Result:**
- ✅ Form completely reset
- ✅ Modal state clean
- ✅ `showAddShipModal = false` in HomePage
- ✅ Modal disappears from screen

---

### **Bước 7: Navigate to /certificates (Line 458-463)**

```javascript
// Notify parent component
if (onShipCreated) {
  onShipCreated(shipId, shipName); // ← Calls HomePage.handleShipCreated
} else {
  // Fallback
  navigate('/certificates');
}
```

**HomePage.handleShipCreated() Function:**
```javascript
const handleShipCreated = (shipId, shipName) => {
  // Ensure modal is closed
  setShowAddShipModal(false);
  
  // Navigate with state
  navigate('/certificates', { 
    state: { 
      refresh: true,
      newShipId: shipId,
      newShipName: shipName 
    } 
  });
};
```

**What Happens:**
1. Browser navigates to `/certificates` page
2. React Router passes `state` object
3. ClassAndFlagCert page loads
4. Page detects `location.state.refresh = true`
5. Triggers `fetchShips()` to reload ship list
6. New ship appears in list

**Timeline:**
- `0ms`: Navigation starts
- `500-1000ms`: Page loaded
- `1000-2000ms`: Ship list fetched from API
- `2000ms`: New ship visible in list

---

### **Bước 8: Background Google Drive Monitoring (Line 467-530)**

```javascript
// Wait 1 second after navigation
setTimeout(() => {
  // Show info toast
  toast.info('📁 Đang tạo folder Google Drive...');
  
  // Start async polling (non-blocking)
  (async () => {
    // Wait 3 seconds before first check
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Poll every 3 seconds, max 20 attempts (60 seconds total)
    let attempts = 0;
    const maxAttempts = 20;
    
    while (attempts < maxAttempts) {
      // Get ship details to check status
      const shipDetail = await shipService.getById(shipId);
      const status = shipDetail.data.gdrive_folder_status;
      
      if (status === 'completed') {
        toast.success('✅ Folder Google Drive tạo xong!');
        break; // Stop polling
      } else if (status === 'failed' || status === 'timeout' || status === 'error') {
        toast.warning('⚠️ Không thể tạo folder Google Drive');
        break; // Stop polling
      }
      
      // Status still pending, continue
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3s
    }
    
    // If 60 seconds elapsed without completion
    if (attempts >= maxAttempts) {
      toast.info('📁 Folder đang được tạo trong nền...');
    }
  })();
}, 1000); // Start after 1 second
```

**Polling Timeline:**
```
T+1s:  Show "Đang tạo folder..." toast
T+4s:  Poll #1 - Check status
T+7s:  Poll #2 - Check status
T+10s: Poll #3 - Check status
...
T+61s: Poll #20 - Last attempt
T+61s: If still no status, show "đang được tạo trong nền" toast
```

**Status Values:**
- `null` or not set: Still creating
- `"completed"`: ✅ Success
- `"failed"`: ❌ Error
- `"timeout"`: ⏰ Took too long (>180s)
- `"error"`: ❌ Exception

**What Backend Does (In Background Thread):**
1. Get company's Google Drive configuration
2. Call Google Apps Script Web App
3. Apps Script creates folder structure:
   - Main ship folder
   - Certificates subfolder
   - Crew subfolder
   - ISM subfolder
   - (And many more)
4. Update ship document with status: `gdrive_folder_status = "completed"`
5. Frontend polling detects the status change
6. Shows completion toast

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ USER CLICKS "CREATE SHIP" BUTTON                                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: FORM VALIDATION                                         │
│   - Check required fields (name, imo, class_society, etc.)     │
│   - If FAIL: Show error toast, return                          │
│   - If PASS: Set isSubmitting = true, continue                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: PREPARE API DATA                                        │
│   - Trim strings                                                │
│   - Convert dates to ISO datetime                              │
│   - Parse numbers                                               │
│   - Map field names (imo_number → imo)                         │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: CALL BACKEND API                                        │
│   POST /api/ships                                               │
│   ↓                                                             │
│   BACKEND PROCESSING (2-3 seconds):                            │
│   - Validate data                                               │
│   - Generate ship ID (UUID)                                     │
│   - Save to MongoDB                                             │
│   - Start background thread: Create Google Drive folder        │
│   - Return response immediately                                │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: SUCCESS TOAST (800ms)                                   │
│   - Show: "✅ Tạo tàu [NAME] thành công!"                       │
│   - Wait 800ms (user can see the message)                      │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: CLOSE MODAL                                             │
│   - handleClose() → Reset all form state                       │
│   - onClose() → Set showAddShipModal = false                   │
│   - Modal disappears                                            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: NAVIGATE TO /CERTIFICATES                               │
│   - onShipCreated(shipId, shipName)                            │
│   - HomePage.handleShipCreated()                               │
│   - navigate('/certificates', { state: { refresh: true } })    │
│   - ClassAndFlagCert page loads                                │
│   - Detects state.refresh → fetchShips()                       │
│   - New ship appears in list (1-2 seconds)                     │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: BACKGROUND MONITORING (NON-BLOCKING)                    │
│   setTimeout 1 second:                                          │
│   - Show: "📁 Đang tạo folder Google Drive..."                 │
│   - Start polling loop:                                         │
│     * Wait 3 seconds                                            │
│     * GET /api/ships/{shipId}                                   │
│     * Check gdrive_folder_status                               │
│     * If "completed": Show success toast, break                │
│     * If "failed": Show warning toast, break                   │
│     * If pending: Continue polling (max 20 attempts)           │
│   - After 60 seconds: Show "đang được tạo trong nền" toast    │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKGROUND THREAD (BACKEND) - INDEPENDENT                       │
│   - Get Google Drive config                                     │
│   - Call Apps Script (10-180 seconds)                          │
│   - Apps Script creates folder structure                       │
│   - Update ship: gdrive_folder_status = "completed"            │
│   - Frontend polling detects status                            │
│   - Show: "✅ Folder Google Drive tạo xong!"                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Timeline Visualization

```
TIME    | USER SEES                          | FRONTEND                    | BACKEND
--------|------------------------------------|-----------------------------|------------------
0s      | Click "Create Ship"                | handleSubmit()              | -
0s      | -                                  | Validate form               | -
0s      | -                                  | Prepare API data            | -
0.5s    | Loading indicator                  | POST /api/ships             | Receive request
1s      | Loading...                         | Waiting for response        | Validate data
2s      | Loading...                         | Waiting for response        | Save to MongoDB
2s      | Loading...                         | Waiting for response        | Start BG thread
2.5s    | ✅ "Tạo tàu thành công!"            | Receive response            | Return 200 OK
3.3s    | Modal closing (fade out)           | Wait 800ms                  | -
3.5s    | Navigate to /certificates          | handleClose()               | -
4s      | Ship list page loads               | onShipCreated()             | -
5s      | Ship appears in list!              | fetchShips()                | GET /api/ships
5.5s    | 📁 "Đang tạo folder..."            | setTimeout(1000)            | -
8.5s    | -                                  | Poll #1                     | Creating folder
11.5s   | -                                  | Poll #2                     | Creating folder
14.5s   | -                                  | Poll #3                     | Creating folder
...     | User can work normally             | Poll #4-20                  | Creating folder
35s     | ✅ "Folder Drive tạo xong!"         | Status = "completed"        | Folder done!
```

---

## Error Handling

### **Validation Error:**
```javascript
if (!shipData.name || !shipData.imo_number || ...) {
  toast.error('❌ Vui lòng điền đầy đủ các trường bắt buộc');
  return; // Stop execution
}
```

### **API Error:**
```javascript
catch (error) {
  console.error('Failed to create ship:', error);
  const errorMessage = error.response?.data?.detail || error.message;
  toast.error(`❌ ${errorMessage}`);
  setIsSubmitting(false); // Re-enable button
}
```

### **Google Drive Error:**
```javascript
// Frontend polling detects error status
if (status === 'failed' || status === 'timeout' || status === 'error') {
  toast.warning('⚠️ Không thể tạo folder Google Drive');
  // Ship data is still safe in database!
}
```

---

## Key Points

### **✅ Non-Blocking Design:**
- Database operation: 2-3 seconds (BLOCKING)
- Google Drive operation: 10-180 seconds (NON-BLOCKING, runs in background)
- User can continue working immediately

### **✅ User Feedback:**
- Immediate success toast (800ms visible)
- Navigation happens quickly
- Background toast for Google Drive
- Completion notification when done

### **✅ Data Safety:**
- Ship data saved to database FIRST
- Even if Google Drive fails, ship data is preserved
- Status tracked in database for debugging

### **✅ Performance:**
- Total blocking time: ~3 seconds
- User sees ship in list within 5 seconds
- Background operations don't affect UX

---

## Success Criteria

- ✅ Form validates correctly
- ✅ API call succeeds (200 OK)
- ✅ Ship created in database
- ✅ Success toast visible for 800ms
- ✅ Modal closes smoothly
- ✅ Navigation to /certificates works
- ✅ Ship appears in list within 5 seconds
- ✅ Google Drive toast appears
- ✅ Completion toast appears (10-60 seconds)
- ✅ User can create multiple ships without logout

---

## Console Logs (Debug)

**Expected sequence:**
```
1. "Creating ship with data: {name: 'MINH ANH 09', imo: '1234567', ...}"
2. "Ship creation response: {data: {id: '572706a6-...', name: 'MINH ANH 09', ...}}"
3. "Closing Add Ship modal"
4. "Refreshing ship list after new ship creation: {refresh: true, newShipId: '572706a6-...', ...}"
5. (After 1 second) No log, but "Đang tạo folder..." toast appears
6. (Every 3 seconds) Polling GET /api/ships/{shipId} in network tab
7. (When done) "Folder Google Drive tạo xong!" toast appears
```
