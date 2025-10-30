/**
 * API Endpoints Constants
 * 
 * Centralized API endpoint definitions
 */

/**
 * Base API URL (from environment)
 */
export const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/login',
  VERIFY_TOKEN: '/api/verify-token',
  
  // Ships
  SHIPS: '/api/ships',
  SHIP_BY_ID: (id) => `/api/ships/${id}`,
  SHIP_LOGO: (id) => `/api/ships/${id}/logo`,
  SHIP_ANALYZE_CERTIFICATE: '/api/analyze-ship-certificate',
  
  // Crew
  CREWS: '/api/crews',
  CREW_BY_ID: (id) => `/api/crews/${id}`,
  CREW_BULK_DELETE: '/api/crews/bulk-delete',
  CREW_MOVE_STANDBY_FILES: '/api/crew/move-standby-files',
  
  // Crew Passport
  PASSPORT_ANALYZE: '/api/passport/analyze-file',
  
  // Ship Certificates
  CERTIFICATES: '/api/certificates',
  CERTIFICATE_BY_ID: (id) => `/api/certificates/${id}`,
  CERTIFICATE_ANALYZE: '/api/certificates/analyze-file',
  CERTIFICATE_BULK_DELETE: '/api/certificates/bulk-delete',
  CERTIFICATE_CHECK_DUPLICATE: '/api/certificates/check-duplicate',
  CERTIFICATE_UPLOAD_FILES: (id) => `/api/certificates/${id}/upload-files`,
  CERTIFICATE_FILE_LINK: (id) => `/api/certificates/${id}/file-link`,
  
  // Crew Certificates
  CREW_CERTIFICATES: '/api/crew-certificates',
  CREW_CERTIFICATE_BY_ID: (id) => `/api/crew-certificates/${id}`,
  CREW_CERTIFICATE_ANALYZE: '/api/crew-certificates/analyze-file',
  CREW_CERTIFICATE_BULK_DELETE: '/api/crew-certificates/bulk-delete',
  CREW_CERTIFICATE_CHECK_DUPLICATE: '/api/crew-certificates/check-duplicate',
  CREW_CERTIFICATE_UPLOAD_FILES: (id) => `/api/crew-certificates/${id}/upload-files`,
  CREW_CERTIFICATE_FILE_LINK: (id) => `/api/crew-certificates/${id}/file-link`,
  
  // Survey Reports
  SURVEY_REPORTS: '/api/survey-reports',
  SURVEY_REPORT_BY_ID: (id) => `/api/survey-reports/${id}`,
  SURVEY_REPORT_ANALYZE: '/api/survey-reports/analyze-file',
  SURVEY_REPORT_BULK_DELETE: '/api/survey-reports/bulk-delete',
  SURVEY_REPORT_CHECK_DUPLICATE: '/api/survey-reports/check-duplicate',
  SURVEY_REPORT_UPLOAD_FILES: (id) => `/api/survey-reports/${id}/upload-files`,
  SURVEY_REPORT_FILE_LINK: (id) => `/api/survey-reports/${id}/file-link`,
  
  // Test Reports
  TEST_REPORTS: '/api/test-reports',
  TEST_REPORT_BY_ID: (id) => `/api/test-reports/${id}`,
  TEST_REPORT_ANALYZE: '/api/test-reports/analyze-file',
  TEST_REPORT_BULK_DELETE: '/api/test-reports/bulk-delete',
  TEST_REPORT_CHECK_DUPLICATE: '/api/test-reports/check-duplicate',
  TEST_REPORT_UPLOAD_FILES: (id) => `/api/test-reports/${id}/upload-files`,
  TEST_REPORT_FILE_LINK: (id) => `/api/test-reports/${id}/file-link`,
  
  // Drawings & Manuals
  DRAWINGS_MANUALS: '/api/drawings-manuals',
  DRAWINGS_MANUALS_BY_ID: (id) => `/api/drawings-manuals/${id}`,
  DRAWINGS_MANUALS_BULK_DELETE: '/api/drawings-manuals/bulk-delete',
  DRAWINGS_MANUALS_CHECK_DUPLICATE: '/api/drawings-manuals/check-duplicate',
  DRAWINGS_MANUALS_UPLOAD_FILE: (id) => `/api/drawings-manuals/${id}/upload-file`,
  DRAWINGS_MANUALS_FILE_LINK: (id) => `/api/drawings-manuals/${id}/file-link`,
  
  // Other Documents
  OTHER_DOCUMENTS: '/api/other-documents',
  OTHER_DOCUMENT_BY_ID: (id) => `/api/other-documents/${id}`,
  OTHER_DOCUMENT_BULK_DELETE: '/api/other-documents/bulk-delete',
  OTHER_DOCUMENT_CHECK_DUPLICATE: '/api/other-documents/check-duplicate',
  OTHER_DOCUMENT_UPLOAD_FILE: (id) => `/api/other-documents/${id}/upload-file`,
  OTHER_DOCUMENT_FILE_LINK: (id) => `/api/other-documents/${id}/file-link`,
  
  // ISM Documents
  ISM_DOCUMENTS: '/api/ism-documents',
  ISM_DOCUMENT_BY_ID: (id) => `/api/ism-documents/${id}`,
  ISM_DOCUMENT_BULK_DELETE: '/api/ism-documents/bulk-delete',
  ISM_DOCUMENT_UPLOAD_FILE: (id) => `/api/ism-documents/${id}/upload-file`,
  ISM_DOCUMENT_FILE_LINK: (id) => `/api/ism-documents/${id}/file-link`,
  
  // ISPS Documents
  ISPS_DOCUMENTS: '/api/isps-documents',
  ISPS_DOCUMENT_BY_ID: (id) => `/api/isps-documents/${id}`,
  ISPS_DOCUMENT_BULK_DELETE: '/api/isps-documents/bulk-delete',
  ISPS_DOCUMENT_UPLOAD_FILE: (id) => `/api/isps-documents/${id}/upload-file`,
  ISPS_DOCUMENT_FILE_LINK: (id) => `/api/isps-documents/${id}/file-link`,
  
  // MLC Documents
  MLC_DOCUMENTS: '/api/mlc-documents',
  MLC_DOCUMENT_BY_ID: (id) => `/api/mlc-documents/${id}`,
  MLC_DOCUMENT_BULK_DELETE: '/api/mlc-documents/bulk-delete',
  MLC_DOCUMENT_UPLOAD_FILE: (id) => `/api/mlc-documents/${id}/upload-file`,
  MLC_DOCUMENT_FILE_LINK: (id) => `/api/mlc-documents/${id}/file-link`,
  
  // Supply Documents
  SUPPLY_DOCUMENTS: '/api/supply-documents',
  SUPPLY_DOCUMENT_BY_ID: (id) => `/api/supply-documents/${id}`,
  SUPPLY_DOCUMENT_BULK_DELETE: '/api/supply-documents/bulk-delete',
  SUPPLY_DOCUMENT_UPLOAD_FILE: (id) => `/api/supply-documents/${id}/upload-file`,
  SUPPLY_DOCUMENT_FILE_LINK: (id) => `/api/supply-documents/${id}/file-link`,
  
  // Companies
  COMPANIES: '/api/companies',
  COMPANY_BY_ID: (id) => `/api/companies/${id}`,
  COMPANY_LOGO: (id) => `/api/companies/${id}/logo`,
  COMPANY_GDRIVE_CONFIG: (id) => `/api/companies/${id}/gdrive/config`,
  COMPANY_GDRIVE_CONFIGURE: (id) => `/api/companies/${id}/gdrive/configure`,
  COMPANY_GDRIVE_TEST_PROXY: (id) => `/api/companies/${id}/gdrive/configure-proxy`,
  COMPANY_GDRIVE_STATUS: (id) => `/api/companies/${id}/gdrive/status`,
  
  // Users
  USERS: '/api/users',
  USER_BY_ID: (id) => `/api/users/${id}`,
  
  // Google Drive
  GDRIVE_CONFIG: '/api/gdrive-config',
  GDRIVE_UPLOAD: '/api/gdrive/upload',
  
  // AI Configuration
  AI_CONFIG: '/api/ai-config',
};

/**
 * HTTP Methods
 */
export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH'
};

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503
};

/**
 * API Timeout (milliseconds)
 */
export const API_TIMEOUT = {
  DEFAULT: 30000, // 30 seconds
  FILE_UPLOAD: 60000, // 60 seconds
  AI_ANALYSIS: 90000, // 90 seconds
  LONG_RUNNING: 120000 // 2 minutes
};

/**
 * Request Headers
 */
export const REQUEST_HEADERS = {
  JSON: {
    'Content-Type': 'application/json'
  },
  FORM_DATA: {
    'Content-Type': 'multipart/form-data'
  }
};
