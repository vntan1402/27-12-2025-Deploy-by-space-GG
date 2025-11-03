/**
 * Application Constants
 * Main categories and configurations
 */

// Main Categories for Navigation (6 categories from V1)
export const MAIN_CATEGORIES = [
  {
    key: 'ship_certificates',
    name_vi: 'Class & Flag Cert',
    name_en: 'Class & Flag Cert',
    icon: '📜'
  },
  {
    key: 'crew',
    name_vi: 'Crew Records',
    name_en: 'Crew Records',
    icon: '👥'
  },
  {
    key: 'ism',
    name_vi: 'ISM - ISPS - MLC',
    name_en: 'ISM - ISPS - MLC',
    icon: '📋'
  },
  {
    key: 'isps',
    name_vi: 'Safety Management System',
    name_en: 'Safety Management System',
    icon: '🛡️'
  },
  {
    key: 'mlc',
    name_vi: 'Technical Infor',
    name_en: 'Technical Infor',
    icon: '⚓'
  },
  {
    key: 'supplies',
    name_vi: 'Supplies',
    name_en: 'Supplies',
    icon: '📦'
  }
];

// Sub-menu tabs shown in main content area (not in sidebar)
export const SUB_MENU_ITEMS = {
  ship_certificates: [
    { key: 'certificates', name_vi: 'Certificates', name_en: 'Certificates' },
    { key: 'class_survey', name_vi: 'Class Survey Report', name_en: 'Class Survey Report' },
    { key: 'test_report', name_vi: 'Test Report', name_en: 'Test Report' },
    { key: 'drawings', name_vi: 'Drawings & Manuals', name_en: 'Drawings & Manuals' },
    { key: 'other_docs', name_vi: 'Other Documents', name_en: 'Other Documents' }
  ],
  crew: [
    { key: 'crew_list', name_vi: 'Crew List', name_en: 'Crew List' },
    { key: 'crew_certificates', name_vi: 'Crew Certificates', name_en: 'Crew Certificates' }
  ],
  ism: [
    { key: 'ism_list', name_vi: 'ISM Documents', name_en: 'ISM Documents' }
  ],
  isps: [
    { key: 'isps_list', name_vi: 'ISPS Documents', name_en: 'ISPS Documents' }
  ],
  mlc: [
    { key: 'mlc_list', name_vi: 'MLC Documents', name_en: 'MLC Documents' }
  ],
  supplies: [
    { key: 'supplies_list', name_vi: 'Supplies List', name_en: 'Supplies List' }
  ]
};

// Crew rank options (maritime positions)
export const RANK_OPTIONS = [
  { value: 'Capt', label: 'Captain', label_vi: 'Thuyền trưởng' },
  { value: 'C/O', label: 'Chief Officer', label_vi: 'Đại phó' },
  { value: '2/O', label: 'Second Officer', label_vi: 'Phó hai' },
  { value: '3/O', label: 'Third Officer', label_vi: 'Phó ba' },
  { value: '4/O', label: 'Fourth Officer', label_vi: 'Phó tư' },
  { value: 'Bosun', label: 'Bosun', label_vi: 'Thủy thủ trưởng' },
  { value: 'AB', label: 'Able Seaman', label_vi: 'Thủy thủ có bằng' },
  { value: 'OS', label: 'Ordinary Seaman', label_vi: 'Thủy thủ thường' },
  { value: 'C/E', label: 'Chief Engineer', label_vi: 'Máy trưởng' },
  { value: '2/E', label: 'Second Engineer', label_vi: 'Máy hai' },
  { value: '3/E', label: 'Third Engineer', label_vi: 'Máy ba' },
  { value: '4/E', label: 'Fourth Engineer', label_vi: 'Máy tư' },
  { value: 'ETO', label: 'Electro-Technical Officer', label_vi: 'Sĩ quan điện' },
  { value: 'Electrician', label: 'Electrician', label_vi: 'Thợ điện' },
  { value: 'Fitter', label: 'Fitter', label_vi: 'Thợ máy' },
  { value: 'Oiler', label: 'Oiler', label_vi: 'Thợ dầu' },
  { value: 'Wiper', label: 'Wiper', label_vi: 'Thợ lau' },
  { value: 'Pumpman', label: 'Pumpman', label_vi: 'Thợ bơm' },
  { value: 'Cook', label: 'Cook', label_vi: 'Đầu bếp' },
  { value: 'Messman', label: 'Messman', label_vi: 'Phục vụ' },
  { value: 'Steward', label: 'Steward', label_vi: 'Phục vụ trưởng' },
  { value: 'Cadet', label: 'Cadet', label_vi: 'Sinh viên thực tập' }
];
