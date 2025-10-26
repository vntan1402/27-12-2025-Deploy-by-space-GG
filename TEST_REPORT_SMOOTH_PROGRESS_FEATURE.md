# Test Report Smooth Progress Bar Feature

## Tổng Quan
Đã implement tính năng progress bar tăng dần mượt mà cho Test Report batch processing, thay thế progress bar nhảy đột ngột trước đây.

## Các Thay Đổi Chính

### 1. State Management Mới
```javascript
const [testReportSmoothProgress, setTestReportSmoothProgress] = useState(0); // 0-100
```
- Quản lý progress mượt mà từ 0-100% cho mỗi file đang xử lý

### 2. Helper Functions

#### `estimateFileProcessingTime(file, pageCount)`
Tính toán thời gian ước tính xử lý file dựa trên:
- **Base Time**: 30 giây (thời gian cơ bản)
- **File Size Factor**: +5 giây mỗi MB
- **Page Count Factor**: +2 giây mỗi trang (nếu có)

**Công thức:**
```
Estimated Time = 30s + (file_size_MB × 5s) + (page_count × 2s)
```

**Ví dụ:**
- File 1MB, không biết số trang: 30 + (1 × 5) = **35 giây**
- File 5MB, 10 trang: 30 + (5 × 5) + (10 × 2) = **75 giây**

#### `startSmoothProgress(setProgress, duration, maxProgress)`
Bắt đầu animation progress mượt mà:
- **duration**: Thời gian ước tính (từ `estimateFileProcessingTime`)
- **maxProgress**: Giới hạn tối đa (mặc định 90%)
- **Update Interval**: Cập nhật mỗi 100ms
- **Easing**: Sử dụng ease-out cubic function để progress chậm dần khi gần đích

**Returns:**
```javascript
{
  stop: () => void,      // Dừng animation (dùng khi có lỗi)
  complete: () => void   // Nhảy lên 100% (dùng khi thành công)
}
```

### 3. Processing Flow

#### Khi Bắt Đầu Batch:
```javascript
setTestReportSmoothProgress(0); // Reset về 0
```

#### Cho Mỗi File:
1. **Reset progress**: `setTestReportSmoothProgress(0)`
2. **Ước tính thời gian**: `estimateFileProcessingTime(file)`
3. **Bắt đầu animation**: Progress tăng dần từ 0 → 90% trong thời gian ước tính
4. **Xử lý API**: Analyze → Create Record → Upload
5. **Hoàn thành**:
   - Thành công: `progressController.complete()` → Nhảy lên 100%
   - Lỗi: `progressController.stop()` → Dừng và reset về 0
6. **Delay 500ms**: Để user thấy progress bar ở 100% trước khi chuyển file

### 4. UI Updates

#### Progress Modal (Expanded):
- **Progress Bar**: Gradient blue (from-blue-500 to-blue-600)
- **Smooth Animation**: `transition-all duration-500 ease-out`
- **Display**: Hiển thị % cùng text "Thời gian ước tính dựa trên kích thước file"

#### Minimized Floating Button:
- **Progress Bar**: White trên nền gradient blue
- **Smooth Animation**: Cùng transition như modal chính
- **Display**: Hiển thị % trong floating icon

## Lợi Ích

### 1. UX Tốt Hơn
- ✅ Progress tăng từ từ, mượt mà thay vì nhảy đột ngột
- ✅ User có cảm giác hệ thống đang hoạt động liên tục
- ✅ Giảm anxiety khi chờ đợi

### 2. Thông Tin Rõ Ràng
- ✅ User biết file đang được xử lý
- ✅ Ước tính thời gian dựa trên kích thước file
- ✅ Progress bar phản ánh tiến độ thực tế hơn

### 3. Feedback Trực Quan
- ✅ Progress tăng nhanh cho file nhỏ
- ✅ Progress tăng chậm cho file lớn
- ✅ Thấy rõ khi file hoàn thành (100%)

## Hướng Dẫn Test

### Test Case 1: Upload 1 File Nhỏ (< 1MB)
**Mục đích**: Kiểm tra progress bar cho file nhỏ

**Các bước:**
1. Vào Test Reports tab
2. Click "Add Test Report"
3. Chọn 1 file PDF nhỏ (< 1MB, ví dụ: Chemical_Suit.pdf ~200KB)
4. Quan sát progress modal

**Kết quả mong đợi:**
- ✅ Progress bar bắt đầu từ 0%
- ✅ Tăng dần mượt mà từ 0% → 90% trong khoảng 30-35 giây
- ✅ Nhảy lên 100% khi hoàn thành
- ✅ Giữ ở 100% trong 500ms rồi đóng modal
- ✅ Không có giật lag

### Test Case 2: Upload 1 File Lớn (> 3MB)
**Mục đích**: Kiểm tra progress bar điều chỉnh theo kích thước file

**Các bước:**
1. Vào Test Reports tab
2. Click "Add Test Report"
3. Chọn 1 file PDF lớn (> 3MB, ví dụ: Co2.pdf ~500KB)
4. Quan sát progress modal

**Kết quả mong đợi:**
- ✅ Progress bar tăng **chậm hơn** so với file nhỏ
- ✅ Thời gian ước tính dài hơn (45-60 giây)
- ✅ Vẫn mượt mà, không giật
- ✅ Đạt 100% khi API hoàn thành

### Test Case 3: Upload Nhiều Files
**Mục đích**: Kiểm tra progress reset giữa các files

**Các bước:**
1. Vào Test Reports tab
2. Click "Add Test Report"
3. Chọn 3-5 files PDF
4. Quan sát progress modal

**Kết quả mong đợi:**
- ✅ File 1: Progress 0% → 90% → 100%
- ✅ **Reset về 0%** trước khi bắt đầu File 2
- ✅ File 2: Progress 0% → 90% → 100%
- ✅ **Reset về 0%** trước khi bắt đầu File 3
- ✅ Cứ tiếp tục như vậy
- ✅ Text hiển thị đúng "Đang xử lý file 1/5, 2/5, 3/5..."

### Test Case 4: Upload File Lỗi
**Mục đích**: Kiểm tra progress xử lý lỗi

**Các bước:**
1. Vào Test Reports tab
2. Click "Add Test Report"
3. Chọn 1 file không hợp lệ (ví dụ: .txt đổi extension thành .pdf)
4. Quan sát progress modal

**Kết quả mong đợi:**
- ✅ Progress bar bắt đầu tăng
- ✅ Khi gặp lỗi, progress **dừng ngay**
- ✅ Progress **reset về 0%**
- ✅ Hiển thị error message
- ✅ Chuyển sang file tiếp theo (nếu có)

### Test Case 5: Minimize Modal
**Mục đích**: Kiểm tra progress trong floating button

**Các bước:**
1. Bắt đầu batch upload
2. Click minimize button (icon -)
3. Quan sát floating button ở bottom-left

**Kết quả mong đợi:**
- ✅ Floating button hiển thị progress bar
- ✅ Progress bar **vẫn mượt mà** như modal chính
- ✅ % hiển thị chính xác
- ✅ Click vào floating button để expand lại

### Test Case 6: Progress vs Actual Time
**Mục đích**: So sánh progress ước tính vs thực tế

**Các bước:**
1. Upload file và bấm giờ thực tế
2. So sánh thời gian progress bar vs thực tế API

**Kết quả mong đợi:**
- ✅ Progress bar đạt 90% trong thời gian ước tính
- ✅ Nếu API nhanh hơn: nhảy từ 50% → 100%
- ✅ Nếu API chậm hơn: progress "đợi" ở 90% cho đến khi API xong
- ✅ Không bao giờ vượt quá 90% cho đến khi API confirm

## Technical Notes

### Performance
- **Update Frequency**: 100ms (10 lần/giây)
- **CPU Impact**: Minimal (chỉ update 1 state mỗi 100ms)
- **Memory**: Negligible (1 interval per file)

### Edge Cases Handled
1. **API faster than estimate**: Progress nhảy từ current → 100%
2. **API slower than estimate**: Progress "đợi" ở 90%
3. **Error during processing**: Progress stop và reset
4. **Multiple files**: Progress reset giữa các files

### Browser Compatibility
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Next Steps

Sau khi test thành công cho Test Reports, sẽ áp dụng tương tự cho:
1. **Survey Reports** batch processing
2. **Drawings & Manuals** batch processing

## Files Modified
- `/app/frontend/src/App.js`:
  - Added `testReportSmoothProgress` state
  - Added `estimateFileProcessingTime` helper
  - Added `startSmoothProgress` helper  
  - Updated `processSingleTestReportInBatch` logic
  - Updated Progress Modal UI
  - Updated Minimized Floating Button UI
