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
- **URL**: https://vessel-manager-5.preview.emergentagent.com
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
