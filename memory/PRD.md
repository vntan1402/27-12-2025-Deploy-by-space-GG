# Maritime Document Management System - PRD

## Original Problem Statement
Build and enhance a Maritime Document Management System for managing ships, certificates, and documents with Google Drive integration.

## Core Features
- Ship management with certificates tracking
- Document upload and management (PDF, JPG)
- Google Drive integration for file storage
- AI-powered certificate analysis (Gemini, Document AI)
- Background task processing for long-running operations

## Tech Stack
- **Frontend**: React, Tailwind CSS, Axios
- **Backend**: FastAPI, Pydantic, Motor (async MongoDB)
- **Database**: MongoDB
- **Integrations**: Google Drive (Apps Script proxy), Google AI

## Key User Credentials
- Demo User: `admin1` / `123456`
- System Admin: `system_admin` / `YourSecure@Pass2024`

---

## Changelog

### 2026-01-18: Background Folder Upload V2
**Status**: Completed ✅

**Problem**: "Add Other Document" feature failed for large file uploads (124 files) due to request size limits.

**Solution Implemented**:
1. Created V2 upload strategy:
   - Frontend creates task first (metadata only, no files)
   - Frontend uploads files one-by-one sequentially with 1s delay
   - Backend tracks progress per file
   - GlobalFloatingProgress displays progress and persists across navigation

2. New API endpoints:
   - `POST /api/other-documents/background-upload-folder/create-task`
   - `POST /api/other-documents/background-upload-folder/{task_id}/upload-file`
   - `GET /api/other-documents/background-upload-folder/{task_id}`

3. Bug fixes:
   - Fixed `'OtherDocumentService' has no attribute '_get_gdrive_config'` by using `GDriveConfigRepository.get_by_company()` directly

**Files Modified**:
- `/app/backend/app/services/background_upload_service.py` - Added V2 upload methods
- `/app/backend/app/api/v1/other_documents.py` - Added new endpoints
- `/app/frontend/src/components/OtherDocuments/AddOtherDocumentModal.jsx` - V2 upload logic
- `/app/frontend/src/components/OtherDocuments/OtherDocumentsTable.jsx` - Removed legacy props

---

## Roadmap

### P0 (Critical)
- [x] Background folder upload for large file counts
- [ ] User validation of upload functionality

### P1 (High Priority)
- [ ] Retry mechanism for failed file uploads
- [ ] Cancel ongoing upload task feature

### P2 (Medium Priority)
- [ ] Bulk file operations optimization
- [ ] Upload progress persistence in localStorage

### P3 (Low Priority/Future)
- [ ] Drag and drop folder upload
- [ ] Upload queue management UI
