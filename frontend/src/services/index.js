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

// Reports
export * from './surveyReportService';
export * from './testReportService';

// Documents
export * from './drawingsService';
export * from './otherDocsService';

// ISM/ISPS/MLC
export * from './ismService';
export * from './ispsService';
export * from './mlcService';

// Users
export * from './userService';

// AI Config & Google Drive
export * from './aiConfigService';
export * from './gdriveService';
