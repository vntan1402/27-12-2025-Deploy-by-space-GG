/**
 * Services Index
 * 
 * Central export for all API services
 * Import services from here for consistency
 */

// Base API
export { default as api } from './api';

// Auth
export * from './authService';

// Ships & Companies
export * from './shipService';
export * from './companyService';

// Crew
export * from './crewService';

// Certificates
export * from './shipCertificateService';  // Ship certificates
export * from './crewCertificateService';  // Crew certificates
export * from './auditCertificateService'; // Audit certificates (ISM-ISPS-MLC)

// Reports
export * from './surveyReportService';
export * from './auditReportService';  // Audit reports (ISM-ISPS-MLC)
export * from './testReportService';

// Documents
export * from './drawingsService';
export * from './otherDocsService';

// ISM/ISPS/MLC - Services removed (not used)
// Frontend uses auditReportService for audit reports
// and auditCertificateService for audit certificates

// Users
export * from './userService';

// AI Config & Google Drive
export * from './aiConfigService';
export * from './gdriveService';
