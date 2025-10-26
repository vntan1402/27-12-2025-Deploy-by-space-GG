# Fix: Parallel Processing với Smooth Progress Bar

## Vấn Đề
Khi upload nhiều files song song (parallel), progress bar nhảy qua nhảy lại vì:
- Tất cả files đang xử lý **cùng lúc** (staggered với 5s delay)
- Tất cả files **dùng chung 1 state** `testReportSmoothProgress`
- Khi File 2 bắt đầu và reset về 0%, progress bar nhảy từ 50% của File 1 xuống 0%

## Giải Pháp Implemented

### 1. File-Specific Progress Tracking
**State mới:**
```javascript
const [testReportFileProgressMap, setTestReportFileProgressMap] = useState({});
// Ví dụ: { "file1.pdf": 45, "file2.pdf": 78, "file3.pdf": 0 }

const [testReportCurrentFileName, setTestReportCurrentFileName] = useState('');
// File nào đang được hiển thị trong UI
```

### 2. Helper Function Mới
**`startSmoothProgressForFile()`** - Quản lý progress cho 1 file cụ thể:
```javascript
startSmoothProgressForFile(
  filename,              // "file1.pdf"
  setProgressMap,        // Update map của tất cả files
  setCurrentProgress,    // Update progress hiển thị
  currentFileName,       // File nào đang được hiển thị
  duration,              // Thời gian ước tính
  maxProgress            // Max 90%
)
```

**Logic:**
- Update progress vào Map: `{ "file1.pdf": 45 }`
- **CHỈ** update UI progress **NẾU** file đó đang được hiển thị
- Các files khác xử lý "im lặng" ở background

### 3. Auto-Switch Current File
Khi file hiện tại hoàn thành → Tự động chuyển sang file tiếp theo:

```javascript
// Tìm file tiếp theo chưa hoàn thành
const nextFile = files.find((f, i) => 
  !results.find(r => r.filename === f.name) && i > index
);

if (nextFile) {
  setTestReportCurrentFileName(nextFile.name);
  setTestReportSmoothProgress(0); // Reset cho file mới
}
```

### 4. Enhanced UI Display

**Before (old):**
```
Đang xử lý file 2/5
Progress: ▓▓▓▓▓▓░░░░ 60%
Thời gian ước tính dựa trên kích thước file
```

**After (new):**
```
Đã hoàn thành 2/5 files
Đang xử lý: Chemical_Suit.pdf
Progress: ▓▓▓▓▓▓░░░░ 60%
File hiện tại
```

## Cách Hoạt Động

### Scenario: Upload 3 files

**T=0s: Bắt đầu**
```
File 1 (Chemical_Suit.pdf) → Bắt đầu xử lý
  - currentFileName = "Chemical_Suit.pdf"
  - smoothProgress = 0% → 45% → 90%
  - Map: { "Chemical_Suit.pdf": 45 }

File 2 (Co2.pdf) → Chờ (sẽ bắt đầu sau 5s)
File 3 (Life_Raft.pdf) → Chờ (sẽ bắt đầu sau 10s)
```

**T=5s: File 2 bắt đầu**
```
File 1 → Đang ở 75%
  - Vẫn hiển thị trong UI
  - Map: { "Chemical_Suit.pdf": 75 }

File 2 → Bắt đầu xử lý ở BACKGROUND
  - KHÔNG hiển thị trong UI
  - Map: { "Chemical_Suit.pdf": 75, "Co2.pdf": 0 }
  - Progress bar VẪN hiển thị 75% (từ File 1)

File 3 → Chờ
```

**T=8s: File 1 hoàn thành**
```
File 1 → 100% → DONE
  - Auto-switch: currentFileName = "Co2.pdf"
  - smoothProgress reset về giá trị hiện tại của File 2

File 2 → Đang ở 25% (đã chạy được 3s)
  - BẮT ĐẦU hiển thị trong UI
  - Progress bar nhảy mượt từ 100% → 25% của File 2
  - Map: { "Chemical_Suit.pdf": 100, "Co2.pdf": 25 }

File 3 → Chờ
```

**T=10s: File 3 bắt đầu**
```
File 1 → DONE
File 2 → Đang ở 45% (hiển thị trong UI)
File 3 → Bắt đầu ở BACKGROUND
  - Map: { ..., "Co2.pdf": 45, "Life_Raft.pdf": 0 }
```

**T=15s: File 2 hoàn thành**
```
File 1 → DONE
File 2 → 100% → DONE
  - Auto-switch: currentFileName = "Life_Raft.pdf"

File 3 → Đang ở 35% (đã chạy được 5s)
  - BẮT ĐẦU hiển thị trong UI
  - Progress bar nhảy từ 100% → 35% của File 3
```

## Lợi Ích

### 1. Không Còn Nhảy Qua Nhảy Lại
✅ **Before**: Progress 50% → 0% → 30% → 10% → 60% (chaotic!)
✅ **After**: Progress 0% → 90% → 100% → [chuyển file] → 0% → 90% → 100%

### 2. Xử Lý Song Song Vẫn Hoạt Động
✅ Backend vẫn nhận files song song (staggered 5s)
✅ API processing time không tăng
✅ Rate limiting vẫn được tôn trọng

### 3. User Experience Tốt Hơn
✅ Rõ ràng file nào đang được xử lý
✅ Progress bar mượt mà cho file hiện tại
✅ Biết được tổng số files đã hoàn thành

### 4. Background Processing
✅ Files khác vẫn xử lý ở background
✅ Không làm chậm tốc độ batch processing
✅ UI chỉ hiển thị 1 file tại 1 thời điểm (clean & focused)

## Technical Details

### Progress Update Flow
```
processSingleTestReportInBatch(file1.pdf)
  ↓
startSmoothProgressForFile("file1.pdf", ...)
  ↓
setInterval(100ms) → Update progress
  ↓
If (file1.pdf === currentFileName)
  → Update UI: setTestReportSmoothProgress(45)
Else
  → Silent update: progressMap["file1.pdf"] = 45
```

### State Management
```javascript
// Global states
testReportFileProgressMap = {
  "Chemical_Suit.pdf": 100,
  "Co2.pdf": 45,
  "Life_Raft.pdf": 0
}

testReportCurrentFileName = "Co2.pdf"
testReportSmoothProgress = 45  // Hiển thị trong UI
```

### Performance
- **Update Frequency**: 100ms per file (10 FPS)
- **CPU Impact**: Minimal (1 interval per file)
- **Memory**: ~1KB per file (progress map)
- **Parallel Files**: Unlimited (nhưng UI chỉ hiển thị 1)

## Testing Guide

### Test Case 1: Upload 2 Files
**Files**: Chemical_Suit.pdf (200KB), Co2.pdf (500KB)

**Expected:**
1. File 1 starts → Progress 0% → 90%
2. File 1 name displays: "Chemical_Suit.pdf"
3. After 5s: File 2 starts ở background (không thấy gì thay đổi)
4. File 1 completes → 100%
5. **Instant switch** to File 2
6. Progress continues from File 2's current progress (~25%)
7. File 2 completes → 100%

**Result:**
✅ NO jumping back to 0% when File 2 starts
✅ Smooth transition between files
✅ Current filename always correct

### Test Case 2: Upload 5 Files
**Purpose**: Verify multiple files in queue

**Expected:**
- Only 1 file name shown at a time
- Progress bar never jumps chaotically
- Each file completes before UI switches to next
- Overall counter increases: 0/5 → 1/5 → 2/5 → 3/5 → 4/5 → 5/5

### Test Case 3: Error in Middle File
**Files**: File1.pdf, InvalidFile.pdf, File3.pdf

**Expected:**
- File1 → Progress normal → 100%
- Switch to InvalidFile → Progress starts → ERROR → Reset to 0%
- Immediately switch to File3 → Continue processing
- No stuck state

## Migration Notes

### Changed Files
- `/app/frontend/src/App.js`:
  - Added `testReportFileProgressMap` state
  - Added `testReportCurrentFileName` state
  - Added `startSmoothProgressForFile()` helper
  - Updated `processSingleTestReportInBatch()` to use new helper
  - Updated batch loop to auto-switch current file
  - Enhanced UI to show current filename

### Backward Compatibility
✅ Overall progress counter still works: `current/total`
✅ Same batch processing logic (parallel with stagger)
✅ Same API calls and backend interaction
✅ Only UI display logic changed

## Future Enhancements

### Potential Improvements:
1. **Show all files progress**: Hiển thị list tất cả files với mini progress bars
2. **Queue visualization**: Hiển thị files đang chờ, đang xử lý, đã xong
3. **Estimated time remaining**: Dựa trên average time per file
4. **Pause/Resume**: Cho phép user tạm dừng batch processing

### Apply to Other Modules:
- Survey Reports batch processing
- Drawings & Manuals batch processing
