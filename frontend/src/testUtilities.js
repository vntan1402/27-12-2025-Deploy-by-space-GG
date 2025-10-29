/**
 * Test Utilities
 * Quick test to verify utilities work correctly
 */

import {
  formatDateDisplay,
  convertDateInputToUTC,
  calculateCertStatus,
  daysUntilExpiry
} from './utils/dateHelpers';

import {
  removeVietnameseDiacritics,
  getAbbreviation,
  formatCrewName
} from './utils/textHelpers';

import {
  validateRequired,
  isValidEmail,
  validateCrewData
} from './utils/validators';

import {
  RANK_OPTIONS,
  COMMON_CERTIFICATE_NAMES,
  getRankLabel
} from './constants/options';

import { API_ENDPOINTS } from './constants/api';

// Test date helpers
console.log('=== Testing Date Helpers ===');
console.log('Format date:', formatDateDisplay('2024-01-15')); // Should be 15/01/2024
console.log('Convert to UTC:', convertDateInputToUTC('15/01/2024')); // Should be 2024-01-15T00:00:00Z
console.log('Days until expiry:', daysUntilExpiry('2025-12-31'));
console.log('Cert status:', calculateCertStatus('2024-12-31'));

// Test text helpers
console.log('\n=== Testing Text Helpers ===');
console.log('Remove diacritics:', removeVietnameseDiacritics('Nguyễn Văn A')); // Nguyen Van A
console.log('Abbreviation:', getAbbreviation('Maritime Authority')); // MA
console.log('Format crew name:', formatCrewName('nguyễn văn a')); // NGUYỄN VĂN A

// Test validators
console.log('\n=== Testing Validators ===');
console.log('Valid email:', isValidEmail('test@example.com')); // true
console.log('Invalid email:', isValidEmail('invalid')); // false
console.log('Required field:', validateRequired('', 'Name')); // Error message
console.log('Validate crew:', validateCrewData({
  full_name: 'John Doe',
  date_of_birth: '15/01/1990',
  passport: 'N1234567',
  place_of_birth: 'Vietnam'
}));

// Test constants
console.log('\n=== Testing Constants ===');
console.log('Rank options count:', RANK_OPTIONS.length); // 16
console.log('Certificate names count:', COMMON_CERTIFICATE_NAMES.length); // 15
console.log('Get rank label (VI):', getRankLabel('CAPT', 'vi')); // Thuyền trưởng
console.log('Get rank label (EN):', getRankLabel('CAPT', 'en')); // CAPT

// Test API endpoints
console.log('\n=== Testing API Endpoints ===');
console.log('Ships endpoint:', API_ENDPOINTS.SHIPS);
console.log('Ship by ID:', API_ENDPOINTS.SHIP_BY_ID('123'));
console.log('Certificate analyze:', API_ENDPOINTS.CERTIFICATE_ANALYZE);

console.log('\n✅ All utilities loaded successfully!');
