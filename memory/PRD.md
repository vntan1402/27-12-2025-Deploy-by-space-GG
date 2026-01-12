# Ship Management System - PRD

## Original Problem Statement
Hệ thống quản lý tàu biển (Ship Management System) - ứng dụng full-stack (React + FastAPI + MongoDB) được triển khai trên Google Cloud Run.

## Core Requirements
1. Quản lý chứng chỉ tàu (Certificates)
2. Quản lý Class Survey Reports
3. Quản lý Test Reports, Drawings & Manuals, Other Documents
4. Quản lý thông tin tàu và thuyền viên
5. Hệ thống ISM-ISPS-MLC
6. Safety Management System
7. Technical Information
8. Supplies Management

## Tech Stack
- **Frontend**: React, TailwindCSS, Shadcn UI, Axios
- **Backend**: FastAPI, Python
- **Database**: MongoDB Atlas
- **Deployment**: Google Cloud Run with Buildpacks
- **AI Integration**: Google Gemini for document extraction

## What's Been Implemented

### 2025-01-11: Class Survey Report Performance Refactoring
**Status**: COMPLETED ✅

**Problem**: Trang "Class Survey Report" load chậm do frontend phải fetch tất cả certificates từ API để tính toán `expiry_date` và `status` cho mỗi survey report.

**Solution**: Di chuyển logic tính toán `expiry_date` và `status` sang backend:
- Khi tạo/update survey report, backend tự động tính toán `expiry_date` dựa trên:
  - `issued_date` + 18 tháng
  - Anniversary Date và Special Survey Cycle của tàu
  - Lấy giá trị MIN giữa 2 giá trị trên
- `status` được tính dựa trên `expiry_date` vs today:
  - "Valid": > 30 ngày còn lại
  - "Due Soon": <= 30 ngày còn lại
  - "Expired": đã hết hạn

**Files Changed**:
- `/app/frontend/src/components/ClassSurveyReport/ClassSurveyReportList.jsx` - Xóa logic fetch certificates và calculate expiry
- `/app/backend/app/services/survey_report_service.py` - Thêm logic calculate expiry khi create/update
- `/app/backend/app/utils/ship_calculations.py` - Function `calculate_survey_report_expiry()`
- `/app/backend/app/models/survey_report.py` - Thêm field `expiry_date`

**Test Results**: 
- Backend: 8/8 tests PASSED
- Frontend: 6/6 tests PASSED

### 2025-01-11: Performance Optimization - AuthContext Token Verification
**Status**: COMPLETED ✅

**Problem**: Trang "Class Survey Report" load chậm (3.62s) do `verify-token` API block UI render.

**Solution**: Optimize AuthContext để render UI ngay lập tức:
1. **Instant UI render**: Load user từ localStorage trước → UI hiển thị ngay
2. **Background token verification**: Verify token trong background, không block UI
3. **Non-blocking flow**: Set `loading=false` ngay sau khi restore user từ localStorage

**Files Changed**:
- `/app/frontend/src/contexts/AuthContext.jsx` - Refactor useEffect và thêm `verifyTokenBackground()`

**Result**: UI render nhanh hơn đáng kể, verify-token chạy trong background.

### 2025-01-11: Fix Expiry Date Calculation Logic (v2)
**Status**: COMPLETED ✅

**Problem**: Logic tính expiry_date cần xem xét window ±3 tháng của Anniversary Date.

**Logic mới**:
1. Tính window của Anniversary năm issued:
   - Window Open = Anniversary - 3 tháng
   - Window Close = Anniversary + 3 tháng

2. Nếu `issued_date >= window_open` (trong hoặc sau window):
   - Survey của năm đó đã HOÀN THÀNH
   - Next survey = Anniversary năm SAU + 3 tháng

3. Nếu `issued_date < window_open` (trước window):
   - Survey này thuộc cycle năm TRƯỚC
   - Survey năm đó CHƯA hoàn thành
   - Next survey = Anniversary năm đó + 3 tháng

**Ví dụ** (Anniversary = 20 Dec, Window 2025: 20/09/2025 → 20/03/2026):
- issued = 29/12/2025 (trong window) → expiry = 20/03/2027 ✅
- issued = 01/06/2025 (trước window) → expiry = 20/03/2026 ✅
- issued = 20/09/2025 (đúng window_open) → expiry = 20/03/2027 ✅

**Files Changed**:
- `/app/backend/app/utils/ship_calculations.py` - Function `calculate_survey_report_expiry()`

### 2025-01-11: UI Enhancement - Expiry Date Column & Edit Modal Layout
**Status**: COMPLETED ✅

**Changes**:
1. **Bảng Class Survey Report**: Thêm cột "Ngày hết hạn" (Expiry Date) vào giữa cột "Ngày cấp" và "Cấp bởi"
2. **Edit Survey Report Modal**: Bố trí lại layout:
   - Row 3: Cấp bởi | **Ngày hết hạn** (mới)
   - Row 4: Tên Surveyor | **Tình trạng** (chuyển xuống cùng dòng)

**Files Changed**:
- `/app/frontend/src/components/ClassSurveyReport/ClassSurveyReportList.jsx` - Thêm cột Expiry Date trong table header và body
- `/app/frontend/src/components/ClassSurveyReport/EditSurveyReportModal.jsx` - Thêm field expiry_date, bố trí lại layout

### Previous Completed Work (Session trước)
1. **Critical Deployment Fix** - Sửa lỗi REACT_APP_BACKEND_URL hardcoded at build-time
2. **UI Bug Fix (Other Docs)** - Sửa toast "Upload Failed" cho successful uploads
3. **UI Enhancement (Upcoming Surveys)** - Xóa cột "Last Endorse", thêm filter "Ship Name"
4. **Backend Fix** - Sửa lỗi 500 khi upload Test Report và Drawing & Manual

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High Priority)
- None currently - awaiting user feedback

### P2 (Medium Priority)
- Performance monitoring for production deployment
- Additional AI features for document analysis

## Test Credentials

### Preview Environment
- **URL**: https://marineapp.preview.emergentagent.com
- **Username**: admin1
- **Password**: 123456

### Production Environment
- Admin user created on startup via environment variables
- **Username**: admin
- **Password**: Admin@123456

## 3rd Party Integrations
- **Google Gemini**: AI data extraction (requires `GOOGLE_AI_API_KEY`)
- **MongoDB Atlas**: Production database (via `MONGO_URL`)
- **Google Drive**: File storage integration

## Architecture Notes
- Frontend uses runtime environment variable injection via `start.sh` script
- Backend prioritizes database name from `MONGO_URL` connection string
- All backend routes prefixed with `/api`
