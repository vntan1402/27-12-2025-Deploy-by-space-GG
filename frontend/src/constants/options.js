/**
 * Dropdown Options & Lists
 * 
 * Extracted from Frontend V1
 * All dropdown options for forms
 */

/**
 * Rank options for crew members
 * Supports both Vietnamese and English labels
 */
export const RANK_OPTIONS = [
  { value: 'CAPT', label_vi: 'Thuyền trưởng', label_en: 'CAPT' },
  { value: 'C/O', label_vi: 'Đại phó', label_en: 'C/O' },
  { value: '2/O', label_vi: 'Phó hai', label_en: '2/O' },
  { value: '3/O', label_vi: 'Phó ba', label_en: '3/O' },
  { value: 'CE', label_vi: 'Máy trưởng', label_en: 'CE' },
  { value: '2/E', label_vi: 'Máy hai', label_en: '2/E' },
  { value: '3/E', label_vi: 'Máy ba', label_en: '3/E' },
  { value: '4/E', label_vi: 'Máy tư', label_en: '4/E' },
  { value: 'BOSUN', label_vi: 'Thủy thủ trưởng', label_en: 'BOSUN' },
  { value: 'ABD', label_vi: 'Thuyền viên', label_en: 'ABD' },
  { value: 'ELEC', label_vi: 'Thợ điện', label_en: 'ELEC' },
  { value: 'FITTER', label_vi: 'Thợ máy', label_en: 'FITTER' },
  { value: 'ABE', label_vi: 'Thợ máy phổ thông', label_en: 'ABE' },
  { value: 'OSE', label_vi: 'Thợ máy tập sự', label_en: 'OSE' },
  { value: 'C/COOK', label_vi: 'Bếp trưởng', label_en: 'C/COOK' },
  { value: 'MESS', label_vi: 'Phục vụ', label_en: 'MESS' }
];

/**
 * Common certificate names (STCW, IMO compliant)
 */
export const COMMON_CERTIFICATE_NAMES = [
  'Certificate of Competency (COC)',
  'Certificate of Endorsement (COE)',
  'Seaman Book for COC',
  'Seaman book for GMDSS',
  'GMDSS Certificate',
  'Medical Certificate',
  'Basic Safety Training',
  'Advanced Fire Fighting',
  'Ship Security Officer',
  'Survival Craft and Rescue Boats',
  'Medical First Aid',
  'Medical Care',
  'Crowd Management',
  'Crisis Management and Human Behaviour',
  'Designated Security Duties'
];

/**
 * Certificate status options
 */
export const CERT_STATUS_OPTIONS = [
  { value: 'Valid', label: 'Valid', color: 'green' },
  { value: 'Expiring Soon', label: 'Expiring Soon', color: 'yellow' },
  { value: 'Expired', label: 'Expired', color: 'red' },
  { value: 'Unknown', label: 'Unknown', color: 'gray' }
];

/**
 * Ship type options
 */
export const SHIP_TYPE_OPTIONS = [
  'Bulk Carrier',
  'Container Ship',
  'Oil Tanker',
  'Chemical Tanker',
  'LNG Tanker',
  'LPG Tanker',
  'General Cargo',
  'Ro-Ro',
  'Passenger Ship',
  'Offshore Vessel',
  'Tug Boat',
  'Other'
];

/**
 * Ship flag options (common flags)
 */
export const SHIP_FLAG_OPTIONS = [
  'Vietnam',
  'Panama',
  'Liberia',
  'Marshall Islands',
  'Hong Kong',
  'Singapore',
  'Malta',
  'Bahamas',
  'Cyprus',
  'China',
  'Other'
];

/**
 * Crew status options
 */
export const CREW_STATUS_OPTIONS = [
  { value: 'active', label_vi: 'Đang làm việc', label_en: 'Active' },
  { value: 'standby', label_vi: 'Chờ tàu', label_en: 'Standby' },
  { value: 'resigned', label_vi: 'Đã nghỉ', label_en: 'Resigned' }
];

/**
 * User role options
 */
export const USER_ROLE_OPTIONS = [
  { value: 'Admin', label: 'Admin', description: 'Full access' },
  { value: 'Manager', label: 'Manager', description: 'Manage data' },
  { value: 'Editor', label: 'Editor', description: 'Edit data' },
  { value: 'Viewer', label: 'Viewer', description: 'View only' }
];

/**
 * Document types
 */
export const DOCUMENT_TYPES = {
  CERTIFICATE: 'certificate',
  CREW_CERTIFICATE: 'crew_certificate',
  SURVEY_REPORT: 'survey_report',
  TEST_REPORT: 'test_report',
  DRAWINGS: 'drawings',
  MANUALS: 'manuals',
  OTHER: 'other',
  ISM: 'ism',
  ISPS: 'isps',
  MLC: 'mlc'
};

/**
 * Survey report types
 */
export const SURVEY_REPORT_TYPES = [
  'Annual Survey',
  'Intermediate Survey',
  'Renewal Survey',
  'Special Survey',
  'Class Survey',
  'SOLAS Survey',
  'MARPOL Survey',
  'ISM Audit',
  'ISPS Audit',
  'MLC Inspection',
  'Port State Control',
  'Flag State Inspection',
  'Other'
];

/**
 * Test report types
 */
export const TEST_REPORT_TYPES = [
  'Fire Extinguisher',
  'Life Raft',
  'Lifeboat',
  'EPIRB',
  'SART',
  'Fire Hose',
  'Breathing Apparatus',
  'Immersion Suit',
  'Life Jacket',
  'Hydrostatic Test',
  'Other'
];

/**
 * Language options
 */
export const LANGUAGE_OPTIONS = [
  { value: 'vi', label: 'Tiếng Việt', flag: '🇻🇳' },
  { value: 'en', label: 'English', flag: '🇬🇧' }
];

/**
 * Sort directions
 */
export const SORT_DIRECTIONS = {
  ASC: 'asc',
  DESC: 'desc'
};

/**
 * Date range presets
 */
export const DATE_RANGE_PRESETS = [
  { label: 'Today', days: 0 },
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
  { label: 'Last year', days: 365 }
];

/**
 * File size limits (in MB)
 */
export const FILE_SIZE_LIMITS = {
  PDF: 10,
  IMAGE: 5,
  EXCEL: 5,
  DEFAULT: 10
};

/**
 * Allowed file types
 */
export const ALLOWED_FILE_TYPES = {
  PDF: ['application/pdf'],
  IMAGE: ['image/jpeg', 'image/jpg', 'image/png'],
  EXCEL: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
  DOCUMENT: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
};

/**
 * Pagination defaults
 */
export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100]
};

/**
 * AI provider options
 */
export const AI_PROVIDER_OPTIONS = [
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'openai', label: 'OpenAI GPT' }
];

/**
 * AI model options per provider
 */
export const AI_MODEL_OPTIONS = {
  gemini: [
    { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (Latest)' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' }
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o (Latest)' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
  ]
};

/**
 * Expiry warning days
 */
export const EXPIRY_WARNING_DAYS = {
  CRITICAL: 7,
  WARNING: 30,
  INFO: 90
};

/**
 * Get label by language
 * 
 * @param {object} option - Option object with label_vi and label_en
 * @param {string} language - Language code ('vi' or 'en')
 * @returns {string} Localized label
 */
export const getLocalizedLabel = (option, language = 'vi') => {
  if (!option) return '';
  return language === 'vi' ? option.label_vi : option.label_en;
};

/**
 * Get rank label by value
 * 
 * @param {string} value - Rank value
 * @param {string} language - Language code
 * @returns {string} Rank label
 */
export const getRankLabel = (value, language = 'vi') => {
  const rank = RANK_OPTIONS.find(r => r.value === value);
  return rank ? getLocalizedLabel(rank, language) : value;
};

/**
 * Get status color by value
 * 
 * @param {string} status - Status value
 * @returns {string} Color name
 */
export const getStatusColor = (status) => {
  const statusOption = CERT_STATUS_OPTIONS.find(s => s.value === status);
  return statusOption ? statusOption.color : 'gray';
};
