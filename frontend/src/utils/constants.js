/**
 * Application Constants
 * Main categories and configurations
 */

// Main Categories for Navigation
export const MAIN_CATEGORIES = [
  {
    key: 'crew',
    name_vi: 'Thông tin Thuyền viên',
    name_en: 'Crew Information',
    icon: '👥'
  },
  {
    key: 'ship_certificates',
    name_vi: 'Chứng chỉ Tàu',
    name_en: 'Ship Certificates',
    icon: '📜'
  },
  {
    key: 'crew_certificates',
    name_vi: 'Chứng chỉ Thuyền viên',
    name_en: 'Crew Certificates',
    icon: '🎓'
  },
  {
    key: 'survey_reports',
    name_vi: 'Báo cáo Khảo sát',
    name_en: 'Survey Reports',
    icon: '📋'
  },
  {
    key: 'test_reports',
    name_vi: 'Báo cáo Thử nghiệm',
    name_en: 'Test Reports',
    icon: '🧪'
  },
  {
    key: 'drawings',
    name_vi: 'Bản vẽ & Hướng dẫn',
    name_en: 'Drawings & Manuals',
    icon: '📊'
  },
  {
    key: 'other_docs',
    name_vi: 'Tài liệu khác',
    name_en: 'Other Documents',
    icon: '📄'
  },
  {
    key: 'mlc',
    name_vi: 'MLC',
    name_en: 'MLC Documents',
    icon: '⚓'
  }
];

// Sub-menu items for each category
export const SUB_MENU_ITEMS = {
  crew: [
    { key: 'crew_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'crew_passport', name_vi: 'Hộ chiếu', name_en: 'Passport' },
    { key: 'crew_summary', name_vi: 'Tổng hợp', name_en: 'Summary' }
  ],
  ship_certificates: [
    { key: 'cert_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'cert_expiring', name_vi: 'Sắp hết hạn', name_en: 'Expiring Soon' },
    { key: 'cert_expired', name_vi: 'Đã hết hạn', name_en: 'Expired' }
  ],
  crew_certificates: [
    { key: 'crew_cert_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'crew_cert_expiring', name_vi: 'Sắp hết hạn', name_en: 'Expiring Soon' },
    { key: 'crew_cert_expired', name_vi: 'Đã hết hạn', name_en: 'Expired' }
  ],
  survey_reports: [
    { key: 'survey_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'survey_recent', name_vi: 'Gần đây', name_en: 'Recent' }
  ],
  test_reports: [
    { key: 'test_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'test_recent', name_vi: 'Gần đây', name_en: 'Recent' }
  ],
  drawings: [
    { key: 'drawing_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'manual_list', name_vi: 'Hướng dẫn', name_en: 'Manuals' }
  ],
  other_docs: [
    { key: 'other_list', name_vi: 'Danh sách', name_en: 'List' }
  ],
  mlc: [
    { key: 'mlc_list', name_vi: 'Danh sách', name_en: 'List' }
  ]
};
