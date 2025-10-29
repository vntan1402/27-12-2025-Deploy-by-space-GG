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
    name_vi: 'ISM Records',
    name_en: 'ISM Records',
    icon: '📋'
  },
  {
    key: 'isps',
    name_vi: 'ISPS Records',
    name_en: 'ISPS Records',
    icon: '🛡️'
  },
  {
    key: 'mlc',
    name_vi: 'MLC Records',
    name_en: 'MLC Records',
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
    { key: 'certificates', name_vi: 'Certificates', name_en: 'Certificates' },
    { key: 'passport', name_vi: 'Passport', name_en: 'Passport' }
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
