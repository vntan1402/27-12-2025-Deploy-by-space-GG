/**
 * Mock data for Crew Audit Logs
 * Used for UI development before backend is ready
 */

export const mockAuditLogs = [
  {
    id: 'log_001',
    entity_type: 'crew',
    entity_id: 'crew_123',
    entity_name: 'Nguyễn Văn A',
    company_id: 'company_1',
    ship_name: 'Ship XYZ', // Current or relevant ship
    action: 'UPDATE',
    action_category: 'DATA_CHANGE',
    performed_by: 'admin1',
    performed_by_id: 'user_001',
    performed_by_name: 'Admin User',
    performed_at: new Date().toISOString(),
    changes: [
      {
        field: 'ship_sign_on',
        field_label: 'Ship Sign On',
        old_value: 'Ship ABC',
        new_value: 'Ship XYZ',
        value_type: 'string'
      },
      {
        field: 'date_sign_on',
        field_label: 'Date Sign On',
        old_value: '2025-01-10',
        new_value: '2025-01-15',
        value_type: 'date'
      },
      {
        field: 'place_sign_on',
        field_label: 'Place Sign On',
        old_value: 'Port A',
        new_value: 'Port B',
        value_type: 'string'
      }
    ],
    notes: 'Bulk ship transfer via Ship Sign On modal',
    source: 'WEB_UI'
  },
  {
    id: 'log_002',
    entity_type: 'crew',
    entity_id: 'crew_124',
    entity_name: 'Trần Thị B',
    company_id: 'company_1',
    ship_name: '-', // Standby
    action: 'CREATE',
    action_category: 'LIFECYCLE',
    performed_by: 'user2',
    performed_by_id: 'user_002',
    performed_by_name: 'Editor User',
    performed_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    changes: [
      {
        field: 'full_name',
        field_label: 'Full Name',
        old_value: null,
        new_value: 'Trần Thị B',
        value_type: 'string'
      },
      {
        field: 'passport',
        field_label: 'Passport',
        old_value: null,
        new_value: 'ABC123456',
        value_type: 'string'
      },
      {
        field: 'rank',
        field_label: 'Rank',
        old_value: null,
        new_value: 'AB',
        value_type: 'string'
      },
      {
        field: 'status',
        field_label: 'Status',
        old_value: null,
        new_value: 'Standby',
        value_type: 'string'
      }
    ],
    notes: 'Created new crew member',
    source: 'WEB_UI'
  },
  {
    id: 'log_003',
    entity_type: 'crew',
    entity_id: 'crew_125',
    entity_name: 'Lê Văn C',
    company_id: 'company_1',
    action: 'SIGN_ON',
    action_category: 'STATUS_CHANGE',
    performed_by: 'admin1',
    performed_by_id: 'user_001',
    performed_by_name: 'Admin User',
    performed_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    changes: [
      {
        field: 'ship_sign_on',
        field_label: 'Ship Sign On',
        old_value: '-',
        new_value: 'Ship MNO',
        value_type: 'string'
      },
      {
        field: 'status',
        field_label: 'Status',
        old_value: 'Standby',
        new_value: 'Sign on',
        value_type: 'string'
      },
      {
        field: 'date_sign_on',
        field_label: 'Date Sign On',
        old_value: null,
        new_value: '2025-01-18',
        value_type: 'date'
      }
    ],
    notes: 'Crew signed on to Ship MNO',
    source: 'WEB_UI'
  },
  {
    id: 'log_004',
    entity_type: 'crew',
    entity_id: 'crew_126',
    entity_name: 'Phạm Minh D',
    company_id: 'company_1',
    action: 'SIGN_OFF',
    action_category: 'STATUS_CHANGE',
    performed_by: 'manager1',
    performed_by_id: 'user_003',
    performed_by_name: 'Manager User',
    performed_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
    changes: [
      {
        field: 'ship_sign_on',
        field_label: 'Ship Sign On',
        old_value: 'Ship PQR',
        new_value: '-',
        value_type: 'string'
      },
      {
        field: 'status',
        field_label: 'Status',
        old_value: 'Sign on',
        new_value: 'Standby',
        value_type: 'string'
      },
      {
        field: 'date_sign_off',
        field_label: 'Date Sign Off',
        old_value: null,
        new_value: '2025-01-17',
        value_type: 'date'
      }
    ],
    notes: 'Crew signed off from Ship PQR',
    source: 'WEB_UI'
  },
  {
    id: 'log_005',
    entity_type: 'crew',
    entity_id: 'crew_127',
    entity_name: 'Hoàng Thị E',
    company_id: 'company_1',
    action: 'DELETE',
    action_category: 'LIFECYCLE',
    performed_by: 'admin1',
    performed_by_id: 'user_001',
    performed_by_name: 'Admin User',
    performed_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
    changes: [
      {
        field: 'full_name',
        field_label: 'Full Name',
        old_value: 'Hoàng Thị E',
        new_value: null,
        value_type: 'string'
      },
      {
        field: 'passport',
        field_label: 'Passport',
        old_value: 'XYZ789012',
        new_value: null,
        value_type: 'string'
      },
      {
        field: 'status',
        field_label: 'Status',
        old_value: 'Leave',
        new_value: null,
        value_type: 'string'
      }
    ],
    notes: 'Crew member deleted from system',
    source: 'WEB_UI'
  },
  {
    id: 'log_006',
    entity_type: 'crew',
    entity_id: 'crew_128',
    entity_name: 'Võ Văn F',
    company_id: 'company_1',
    action: 'BULK_UPDATE',
    action_category: 'DATA_CHANGE',
    performed_by: 'admin1',
    performed_by_id: 'user_001',
    performed_by_name: 'Admin User',
    performed_at: new Date(Date.now() - 345600000).toISOString(), // 4 days ago
    changes: [
      {
        field: 'rank',
        field_label: 'Rank',
        old_value: 'OS',
        new_value: 'AB',
        value_type: 'string'
      }
    ],
    notes: 'Bulk rank update for multiple crew members',
    source: 'WEB_UI'
  },
  {
    id: 'log_007',
    entity_type: 'crew',
    entity_id: 'crew_129',
    entity_name: 'Đỗ Thị G',
    company_id: 'company_1',
    action: 'UPDATE',
    action_category: 'DATA_CHANGE',
    performed_by: 'editor1',
    performed_by_id: 'user_004',
    performed_by_name: 'Editor 2',
    performed_at: new Date(Date.now() - 432000000).toISOString(), // 5 days ago
    changes: [
      {
        field: 'passport_expiry_date',
        field_label: 'Passport Expiry Date',
        old_value: '2025-06-30',
        new_value: '2026-06-30',
        value_type: 'date'
      }
    ],
    notes: 'Updated passport expiry date',
    source: 'WEB_UI'
  }
];

// Generate more mock data for testing pagination
export const generateMoreMockLogs = (count = 50) => {
  const actions = ['UPDATE', 'CREATE', 'DELETE', 'SIGN_ON', 'SIGN_OFF', 'BULK_UPDATE'];
  const names = [
    'Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C', 'Phạm Minh D',
    'Hoàng Thị E', 'Võ Văn F', 'Đỗ Thị G', 'Bùi Văn H'
  ];
  const users = [
    { id: 'user_001', username: 'admin1', name: 'Admin User' },
    { id: 'user_002', username: 'user2', name: 'Editor User' },
    { id: 'user_003', username: 'manager1', name: 'Manager User' }
  ];
  
  const logs = [];
  
  for (let i = 0; i < count; i++) {
    const action = actions[Math.floor(Math.random() * actions.length)];
    const user = users[Math.floor(Math.random() * users.length)];
    const daysAgo = Math.floor(Math.random() * 30);
    
    logs.push({
      id: `log_${1000 + i}`,
      entity_type: 'crew',
      entity_id: `crew_${200 + i}`,
      entity_name: names[Math.floor(Math.random() * names.length)],
      company_id: 'company_1',
      action,
      action_category: action === 'CREATE' || action === 'DELETE' ? 'LIFECYCLE' : 'DATA_CHANGE',
      performed_by: user.username,
      performed_by_id: user.id,
      performed_by_name: user.name,
      performed_at: new Date(Date.now() - daysAgo * 86400000).toISOString(),
      changes: [
        {
          field: 'ship_sign_on',
          field_label: 'Ship Sign On',
          old_value: 'Ship ABC',
          new_value: 'Ship XYZ',
          value_type: 'string'
        }
      ],
      notes: `Auto-generated mock log #${i}`,
      source: 'WEB_UI'
    });
  }
  
  return logs;
};

export const allMockLogs = [...mockAuditLogs, ...generateMoreMockLogs(50)];
