import React, { useState, useEffect } from 'react';

const UserGuideModal = ({ isOpen, onClose, language }) => {
  if (!isOpen) return null;

  const [expandedSection, setExpandedSection] = useState(null);
  const [baseFee, setBaseFee] = useState(900000); // Default value

  // Fetch base fee when modal opens
  useEffect(() => {
    const fetchBaseFee = async () => {
      try {
        const api = (await import('../services/api')).default;
        const response = await api.get('/api/system-settings/base-fee');
        if (response.data && response.data.base_fee !== undefined) {
          setBaseFee(response.data.base_fee);
        }
      } catch (error) {
        console.error('Error fetching base fee:', error);
        // Keep default value if error
      }
    };

    if (isOpen) {
      fetchBaseFee();
    }
  }, [isOpen]);

  const toggleSection = (index) => {
    setExpandedSection(expandedSection === index ? null : index);
  };

  const content = language === 'vi' ? {
    title: 'Hướng dẫn Sử dụng',
    subtitle: 'Các thao tác cơ bản trong Hệ thống',
    close: 'Đóng',
    sections: [
      {
        icon: '👤',
        title: '1. Tạo User Mới',
        color: 'blue',
        steps: [
          { step: '1', text: 'Đăng nhập với tài khoản có quyền quản lý (Admin trở lên)' },
          { step: '2', text: 'Vào menu "System Settings" → "User Management"' },
          { step: '3', text: 'Click nút "➕ Add User" ở góc trên bên phải' },
          { step: '4', text: 'Điền thông tin bắt buộc:', details: [
            'Username (tên đăng nhập)',
            'Full Name (họ tên đầy đủ)',
            'Password (mật khẩu)',
            'Role (vai trò: Admin, Manager, Viewer...)',
            'Department (phòng ban)',
            'Company (công ty - tự động fill nếu không phải Super Admin)',
            'Zalo, Gmail (thông tin liên hệ)'
          ]},
          { step: '5', text: 'Click "Create" để tạo user mới' },
          { step: '6', text: 'User sẽ xuất hiện trong danh sách và có thể đăng nhập ngay' }
        ],
        tips: [
          '💡 Role và Department sẽ quyết định quyền truy cập của user',
          '💡 Super Admin có thể tạo user cho tất cả companies',
          '💡 Admin chỉ có thể tạo user cho company của mình'
        ]
      },
      {
        icon: '🚢',
        title: '2. Thêm Tàu Mới',
        color: 'blue',
        steps: [
          { step: '1', text: 'Vào trang "Ship Management" từ sidebar' },
          { step: '2', text: 'Click nút "➕ Add Ship"' },
          { step: '3', text: 'Chọn phương thức thêm tàu:', details: [
            'Manual Entry: Nhập thông tin thủ công',
            'AI Auto-fill: Upload Ship Particular document và để AI tự động điền'
          ]},
          { step: '4', text: 'Điền/Xác nhận thông tin tàu:', details: [
            'Ship Name (tên tàu) - bắt buộc',
            'IMO Number (số IMO)',
            'Call Sign (hô hiệu)',
            'Flag (cờ)',
            'Ship Type (loại tàu - AI tự động nhận diện)',
            'Last Docking Date (AI trích xuất)',
            'Built Date, Gross Tonnage, DWT...'
          ]},
          { step: '5', text: 'Điền thông tin Anniversary Date và Special Survey' },
          { step: '6', text: 'Click "Add Ship" để hoàn tất' }
        ],
        tips: [
          '🤖 Sử dụng AI Auto-fill để tiết kiệm 80% thời gian nhập liệu',
          '💡 AI tự động tính Anniversary Date từ Last Docking',
          '📁 Tàu mới sẽ tự động tạo folder trên Google Drive'
        ]
      },
      {
        icon: '📜',
        title: '3. Thêm Giấy Chứng Nhận & Báo Cáo',
        color: 'blue',
        steps: [
          { step: '1', text: 'Chọn loại certificate/report từ menu:', details: [
            'ISM-ISPS-MLC (Audit Certificates)',
            'Class & Flag Certificates (Ship Certificates)',
            'Survey Reports, Drawings & Manuals, Test Reports...'
          ]},
          { step: '2', text: 'Chọn tàu từ dropdown hoặc table' },
          { step: '3', text: 'Click "➕ Add Certificate"' },
          { step: '4', text: 'Upload file PDF/Image của certificate' },
          { step: '5', text: 'AI tự động trích xuất thông tin:', details: [
            'Certificate Name',
            'Certificate Number',
            'Issue Date',
            'Expiry Date',
            'Issued By'
          ]},
          { step: '6', text: 'Kiểm tra và chỉnh sửa thông tin nếu cần' },
          { step: '7', text: 'Click "Add" để lưu certificate' },
          { step: '8', text: 'File tự động upload lên Google Drive và rename theo chuẩn' }
        ],
        tips: [
          '🤖 AI đọc và điền form tự động - bạn chỉ cần review',
          '📊 Hệ thống tự động tính expiry alerts',
          '📁 Mọi file đều được backup tự động trên Google Drive'
        ]
      },
      {
        icon: '👨‍✈️',
        title: '4. Thêm Thuyền Viên',
        color: 'blue',
        steps: [
          { step: '1', text: 'Vào trang "Crew Records" từ sidebar' },
          { step: '2', text: 'Click nút "➕ Add Crew Member"' },
          { step: '3', text: 'Điền thông tin cơ bản:', details: [
            'Full Name (họ tên)',
            'Rank (chức vụ: Captain, Chief Engineer, AB...)',
            'Passport Number',
            'Date of Birth',
            'Nationality'
          ]},
          { step: '4', text: 'Điền thông tin Sign On/Off:', details: [
            'Ship Sign On (tàu đang làm việc)',
            'Sign On Date',
            'Sign Off Date (nếu đã xuống tàu)'
          ]},
          { step: '5', text: 'Upload Passport File và Summary File (nếu có)' },
          { step: '6', text: 'Click "Add Crew" để lưu thông tin' }
        ],
        tips: [
          '📋 Có thể upload passport file và AI sẽ trích xuất thông tin',
          '🚢 Crew có thể được assign vào nhiều tàu theo thời gian',
          '📁 Files tự động lưu vào thư mục Crew trên Google Drive'
        ]
      },
      {
        icon: '🎫',
        title: '5. Giấy Chứng Nhận Thuyền Viên',
        color: 'blue',
        steps: [
          { step: '1', text: 'Vào trang "Crew Records"' },
          { step: '2', text: 'Chọn thuyền viên từ danh sách' },
          { step: '3', text: 'Tab "Crew Certificates" sẽ hiển thị' },
          { step: '4', text: 'Click "➕ Add Certificate"' },
          { step: '5', text: 'Chọn loại certificate:', details: [
            'COC (Certificate of Competency)',
            'COP (Certificate of Proficiency)',
            'Medical Certificate',
            'STCW Certificates',
            'Passport',
            'Seaman Book'
          ]},
          { step: '6', text: 'Upload file certificate' },
          { step: '7', text: 'AI tự động điền: Certificate No, Issue Date, Expiry Date, Issued By' },
          { step: '8', text: 'Review và click "Add" để lưu' }
        ],
        tips: [
          '🤖 Batch Upload: Upload nhiều certificates cùng lúc (5-10 files)',
          '⏰ Auto expiry alerts cho certificates sắp hết hạn',
          '📊 Dashboard hiển thị tổng hợp certificates của toàn bộ crew'
        ]
      },
      {
        icon: '🖱️',
        title: '6. Sử Dụng Context Menu',
        color: 'blue',
        steps: [
          { step: '1', text: 'Context Menu xuất hiện khi:', details: [
            'Right-click trên table row',
            'Click vào icon 3 chấm (⋮) ở cuối mỗi row'
          ]},
          { step: '2', text: 'Các actions thường có:', details: [
            '📝 Edit - Sửa thông tin',
            '🗑️ Delete - Xóa record',
            '👁️ View Details - Xem chi tiết',
            '📄 View Certificate - Xem file PDF',
            '📥 Download - Tải file về',
            '🔄 Sync from Drive - Đồng bộ từ Google Drive',
            '📤 Move to Drive - Di chuyển lên Drive'
          ]},
          { step: '3', text: 'Chọn action muốn thực hiện' },
          { step: '4', text: 'Confirm nếu là action quan trọng (Delete)' }
        ],
        tips: [
          '⚡ Context menu là cách nhanh nhất để thao tác',
          '🔒 Một số actions yêu cầu quyền Admin',
          '💡 Hover để xem tooltip giải thích từng action'
        ]
      },
      {
        icon: '📦',
        title: '7. Batch Upload - Upload Hàng Loạt',
        color: 'blue',
        steps: [
          { step: '1', text: 'Có 2 loại Batch Upload:', details: [
            'Ship Certificates Batch Upload',
            'Crew Certificates Batch Upload'
          ]},
          { step: '2', text: 'Cách sử dụng Ship Certificates Batch:', details: [
            'Vào Class & Flag Certificates',
            'Click "📦 Batch Upload"',
            'Chọn ship từ dropdown',
            'Upload 5-10 files cùng lúc (PDF/Images)',
            'AI xử lý song song tất cả files',
            'Xem real-time progress cho từng file',
            'Review kết quả trong Batch Results modal'
          ]},
          { step: '3', text: 'Cách sử dụng Crew Certificates Batch:', details: [
            'Vào Crew Records',
            'Chọn crew member',
            'Click "📦 Batch Upload"',
            'Upload nhiều certificates (COC, Medical, Passport...)',
            'AI tự động phân loại và trích xuất',
            'Xem kết quả tổng hợp'
          ]},
          { step: '4', text: 'Batch Results hiển thị:', details: [
            'Tổng số files uploaded',
            'Số files thành công',
            'Số files cần review',
            'Chi tiết lỗi (nếu có)'
          ]}
        ],
        tips: [
          '🚀 Tiết kiệm 80% thời gian so với upload từng file',
          '🤖 AI xử lý parallel - càng nhiều file càng nhanh',
          '✅ Tất cả files đều được validate trước khi lưu'
        ]
      },
      {
        icon: '⚡',
        title: '8. Bulk Actions - Thao Tác Hàng Loạt',
        color: 'blue',
        steps: [
          { step: '1', text: 'Bulk Actions cho phép:', details: [
            'Xóa nhiều records cùng lúc',
            'Export nhiều records ra Excel/CSV',
            'Update status hàng loạt',
            'Download nhiều files cùng lúc'
          ]},
          { step: '2', text: 'Cách sử dụng:', details: [
            'Tick checkbox ở đầu mỗi row muốn chọn',
            'Hoặc tick "Select All" để chọn tất cả',
            'Nút Bulk Actions sẽ xuất hiện ở top',
            'Chọn action muốn thực hiện',
            'Confirm để thực thi'
          ]},
          { step: '3', text: 'Bulk Delete - Xóa hàng loạt:', details: [
            'Chọn nhiều certificates/records',
            'Click "🗑️ Bulk Delete"',
            'Confirm deletion',
            'Hệ thống xóa và update Google Drive tự động'
          ]},
          { step: '4', text: 'Bulk Export:', details: [
            'Chọn records cần export',
            'Click "📥 Export Selected"',
            'File Excel/CSV sẽ được tạo và download'
          ]}
        ],
        tips: [
          '⚡ Bulk actions nhanh hơn 10x so với từng action riêng lẻ',
          '🔒 Bulk delete có confirm để tránh xóa nhầm',
          '📊 Bulk export giữ nguyên format và structure'
        ]
      },
      {
        icon: '🎯',
        title: '9. Các Tính Năng Khác',
        color: 'blue',
        features: [
          {
            name: '🔍 Advanced Search & Filters',
            description: 'Tìm kiếm và lọc nhanh theo nhiều tiêu chí',
            details: [
              'Search by name, number, date range',
              'Filter by status, type, company',
              'Save filter presets'
            ]
          },
          {
            name: '📊 Dashboard & Reports',
            description: 'Xem tổng quan và báo cáo',
            details: [
              'Certificate expiry dashboard',
              'Upcoming surveys timeline',
              'Company statistics',
              'Crew certificates status'
            ]
          },
          {
            name: '🔔 Expiry Alerts',
            description: 'Cảnh báo tự động certificates sắp hết hạn',
            details: [
              'Email/notification alerts',
              'Customizable alert thresholds (30, 60, 90 days)',
              'Alert dashboard'
            ]
          },
          {
            name: '📁 Google Drive Sync',
            description: 'Đồng bộ hai chiều với Google Drive',
            details: [
              'Auto upload on certificate create',
              'Sync from Drive to system',
              'Auto rename files to standard',
              'Backup & restore'
            ]
          },
          {
            name: '🔐 Role-Based Access Control',
            description: 'Phân quyền chi tiết theo role và department',
            details: [
              'System Admin: Full access',
              'Super Admin: Company-wide access',
              'Admin: Company management',
              'Manager: Limited access',
              'Viewer: Read-only'
            ]
          },
          {
            name: '🌐 Multi-language Support',
            description: 'Hỗ trợ đa ngôn ngữ',
            details: [
              'Vietnamese (Tiếng Việt)',
              'English',
              'Toggle ngay trong app'
            ]
          },
          {
            name: '📱 Responsive Design',
            description: 'Hoạt động mượt mà trên mọi thiết bị',
            details: [
              'Desktop, Tablet, Mobile',
              'Touch-friendly interface',
              'Adaptive layout'
            ]
          },
          {
            name: '⚙️ AI Configuration',
            description: 'Cấu hình AI extraction rules',
            details: [
              'Customize per certificate type',
              'AI learning from feedback',
              'Template management'
            ]
          }
        ]
      },
      {
        icon: '💰',
        title: '10. Tính Phí Hàng Tháng',
        color: 'blue',
        steps: [
          { step: '1', text: 'Đăng nhập với tài khoản có quyền Admin trở lên' },
          { step: '2', text: 'Vào "System Settings" → "Company Management"' },
          { step: '3', text: 'Double-click vào company row để mở Company Details Modal' },
          { step: '4', text: 'Xem thông tin thống kê:', details: [
            'Total Ships: Tổng số tàu có certificates',
            'Office Staff: Nhân viên văn phòng (không bao gồm thuyền viên)',
            'Crew Members: Tổng số thuyền viên',
            'Active Users: Số users đang hoạt động'
          ]},
          { step: '5', text: 'Click nút "💰 Tính Phí" ở góc trên bên phải' },
          { step: '6', text: 'Hệ thống tính toán và hiển thị:', details: [
            'Phí hàng tháng xuất hiện bên cạnh tên công ty',
            'Toast notification hiển thị kết quả',
            'Breakdown chi tiết trong console logs'
          ]}
        ],
        formula: {
          title: 'Công Thức Tính Phí (Base Fee giai đoạn 1 là 900,000 VND)',
          main: 'Phí Hàng Tháng = (Total Ships × Base Fee) + (Office Staff × 0.1 × Base Fee) + (Crew Members × 0.025 × Base Fee)',
          breakdown: [
            {
              label: 'Total Ships × Base Fee',
              example: `5 tàu × ${baseFee.toLocaleString('vi-VN')} ₫ = ${(5 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Phí theo số lượng tàu có certificates'
            },
            {
              label: 'Office Staff × 0.1 × Base Fee',
              example: `10 nhân viên × ${(0.1 * baseFee).toLocaleString('vi-VN')} ₫ = ${(10 * 0.1 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Phí theo số nhân viên văn phòng (10% Base Fee mỗi người)'
            },
            {
              label: 'Crew Members × 0.025 × Base Fee',
              example: `50 thuyền viên × ${(0.025 * baseFee).toLocaleString('vi-VN')} ₫ = ${(50 * 0.025 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Phí theo số thuyền viên (2.5% Base Fee mỗi người)'
            },
            {
              label: 'Tổng Phí',
              example: `${(5 * baseFee).toLocaleString('vi-VN')} + ${(10 * 0.1 * baseFee).toLocaleString('vi-VN')} + ${(50 * 0.025 * baseFee).toLocaleString('vi-VN')} = ${(5 * baseFee + 10 * 0.1 * baseFee + 50 * 0.025 * baseFee).toLocaleString('vi-VN')} ₫/tháng`,
              description: 'Tổng phí hàng tháng phải thanh toán'
            }
          ]
        },
        notes: [
          '📌 Base Fee: Được thiết lập bởi System Admin/Super Admin',
          '📌 Chỉ tính ships có ít nhất 1 certificate',
          '📌 Office Staff không bao gồm users có department "Ship Crew"',
          '📌 Crew Members được đếm từ Crew Records',
          '📌 Tính năng chỉ dành cho Admin trở lên'
        ]
      }
    ]
  } : {
    title: 'User Guide',
    subtitle: 'Basic Operations in the System',
    close: 'Close',
    sections: [
      {
        icon: '👤',
        title: '1. Create New User',
        color: 'blue',
        steps: [
          { step: '1', text: 'Login with management privileges (Admin or higher)' },
          { step: '2', text: 'Go to "System Settings" → "User Management"' },
          { step: '3', text: 'Click "➕ Add User" button at top right' },
          { step: '4', text: 'Fill required information:', details: [
            'Username (login name)',
            'Full Name',
            'Password',
            'Role (Admin, Manager, Viewer...)',
            'Department',
            'Company (auto-filled if not Super Admin)',
            'Zalo, Gmail (contact info)'
          ]},
          { step: '5', text: 'Click "Create" to add new user' },
          { step: '6', text: 'User will appear in list and can login immediately' }
        ],
        tips: [
          '💡 Role and Department determine user access rights',
          '💡 Super Admin can create users for all companies',
          '💡 Admin can only create users for their own company'
        ]
      },
      {
        icon: '🚢',
        title: '2. Add New Ship',
        color: 'blue',
        steps: [
          { step: '1', text: 'Go to "Ship Management" from sidebar' },
          { step: '2', text: 'Click "➕ Add Ship" button' },
          { step: '3', text: 'Choose input method:', details: [
            'Manual Entry: Fill information manually',
            'AI Auto-fill: Upload Ship Particular document for AI extraction'
          ]},
          { step: '4', text: 'Fill/Confirm ship information:', details: [
            'Ship Name (required)',
            'IMO Number',
            'Call Sign',
            'Flag',
            'Ship Type (AI auto-detects)',
            'Last Docking Date (AI extracts)',
            'Built Date, Gross Tonnage, DWT...'
          ]},
          { step: '5', text: 'Fill Anniversary Date and Special Survey info' },
          { step: '6', text: 'Click "Add Ship" to complete' }
        ],
        tips: [
          '🤖 Use AI Auto-fill to save 80% data entry time',
          '💡 AI automatically calculates Anniversary Date from Last Docking',
          '📁 New ship automatically creates folder on Google Drive'
        ]
      },
      {
        icon: '📜',
        title: '3. Add Certificates & Reports',
        color: 'blue',
        steps: [
          { step: '1', text: 'Select certificate/report type from menu:', details: [
            'ISM-ISPS-MLC (Audit Certificates)',
            'Class & Flag Certificates (Ship Certificates)',
            'Survey Reports, Drawings & Manuals, Test Reports...'
          ]},
          { step: '2', text: 'Select ship from dropdown or table' },
          { step: '3', text: 'Click "➕ Add Certificate"' },
          { step: '4', text: 'Upload PDF/Image file of certificate' },
          { step: '5', text: 'AI automatically extracts:', details: [
            'Certificate Name',
            'Certificate Number',
            'Issue Date',
            'Expiry Date',
            'Issued By'
          ]},
          { step: '6', text: 'Review and edit information if needed' },
          { step: '7', text: 'Click "Add" to save certificate' },
          { step: '8', text: 'File auto-uploads to Google Drive with standard naming' }
        ],
        tips: [
          '🤖 AI reads and fills form automatically - you just review',
          '📊 System automatically calculates expiry alerts',
          '📁 All files backed up automatically on Google Drive'
        ]
      },
      {
        icon: '👨‍✈️',
        title: '4. Add Crew Member',
        color: 'blue',
        steps: [
          { step: '1', text: 'Go to "Crew Records" from sidebar' },
          { step: '2', text: 'Click "➕ Add Crew Member"' },
          { step: '3', text: 'Fill basic information:', details: [
            'Full Name',
            'Rank (Captain, Chief Engineer, AB...)',
            'Passport Number',
            'Date of Birth',
            'Nationality'
          ]},
          { step: '4', text: 'Fill Sign On/Off information:', details: [
            'Ship Sign On (current ship)',
            'Sign On Date',
            'Sign Off Date (if already signed off)'
          ]},
          { step: '5', text: 'Upload Passport File and Summary File (if any)' },
          { step: '6', text: 'Click "Add Crew" to save' }
        ],
        tips: [
          '📋 Can upload passport file and AI will extract information',
          '🚢 Crew can be assigned to multiple ships over time',
          '📁 Files automatically saved to Crew folder on Google Drive'
        ]
      },
      {
        icon: '🎫',
        title: '5. Crew Certificates',
        color: 'blue',
        steps: [
          { step: '1', text: 'Go to "Crew Records"' },
          { step: '2', text: 'Select crew member from list' },
          { step: '3', text: '"Crew Certificates" tab will display' },
          { step: '4', text: 'Click "➕ Add Certificate"' },
          { step: '5', text: 'Select certificate type:', details: [
            'COC (Certificate of Competency)',
            'COP (Certificate of Proficiency)',
            'Medical Certificate',
            'STCW Certificates',
            'Passport',
            'Seaman Book'
          ]},
          { step: '6', text: 'Upload certificate file' },
          { step: '7', text: 'AI auto-fills: Certificate No, Issue Date, Expiry Date, Issued By' },
          { step: '8', text: 'Review and click "Add" to save' }
        ],
        tips: [
          '🤖 Batch Upload: Upload multiple certificates at once (5-10 files)',
          '⏰ Auto expiry alerts for certificates nearing expiration',
          '📊 Dashboard shows certificate summary for all crew'
        ]
      },
      {
        icon: '🖱️',
        title: '6. Using Context Menu',
        color: 'blue',
        steps: [
          { step: '1', text: 'Context Menu appears when:', details: [
            'Right-click on table row',
            'Click 3-dot icon (⋮) at end of each row'
          ]},
          { step: '2', text: 'Common actions available:', details: [
            '📝 Edit - Edit information',
            '🗑️ Delete - Delete record',
            '👁️ View Details - View details',
            '📄 View Certificate - View PDF file',
            '📥 Download - Download file',
            '🔄 Sync from Drive - Sync from Google Drive',
            '📤 Move to Drive - Move to Drive'
          ]},
          { step: '3', text: 'Select desired action' },
          { step: '4', text: 'Confirm if critical action (Delete)' }
        ],
        tips: [
          '⚡ Context menu is the fastest way to operate',
          '🔒 Some actions require Admin privileges',
          '💡 Hover to see tooltip explaining each action'
        ]
      },
      {
        icon: '📦',
        title: '7. Batch Upload',
        color: 'blue',
        steps: [
          { step: '1', text: 'Two types of Batch Upload:', details: [
            'Ship Certificates Batch Upload',
            'Crew Certificates Batch Upload'
          ]},
          { step: '2', text: 'How to use Ship Certificates Batch:', details: [
            'Go to Class & Flag Certificates',
            'Click "📦 Batch Upload"',
            'Select ship from dropdown',
            'Upload 5-10 files at once (PDF/Images)',
            'AI processes all files in parallel',
            'View real-time progress for each file',
            'Review results in Batch Results modal'
          ]},
          { step: '3', text: 'How to use Crew Certificates Batch:', details: [
            'Go to Crew Records',
            'Select crew member',
            'Click "📦 Batch Upload"',
            'Upload multiple certificates (COC, Medical, Passport...)',
            'AI auto-categorizes and extracts',
            'View summary results'
          ]},
          { step: '4', text: 'Batch Results displays:', details: [
            'Total files uploaded',
            'Successful files count',
            'Files needing review count',
            'Error details (if any)'
          ]}
        ],
        tips: [
          '🚀 Save 80% time compared to uploading individual files',
          '🤖 AI parallel processing - more files, faster',
          '✅ All files validated before saving'
        ]
      },
      {
        icon: '⚡',
        title: '8. Bulk Actions',
        color: 'blue',
        steps: [
          { step: '1', text: 'Bulk Actions allow:', details: [
            'Delete multiple records at once',
            'Export multiple records to Excel/CSV',
            'Update status in bulk',
            'Download multiple files at once'
          ]},
          { step: '2', text: 'How to use:', details: [
            'Tick checkbox at start of each row to select',
            'Or tick "Select All" to select all',
            'Bulk Actions button appears at top',
            'Select desired action',
            'Confirm to execute'
          ]},
          { step: '3', text: 'Bulk Delete:', details: [
            'Select multiple certificates/records',
            'Click "🗑️ Bulk Delete"',
            'Confirm deletion',
            'System deletes and updates Google Drive automatically'
          ]},
          { step: '4', text: 'Bulk Export:', details: [
            'Select records to export',
            'Click "📥 Export Selected"',
            'Excel/CSV file will be created and downloaded'
          ]}
        ],
        tips: [
          '⚡ Bulk actions 10x faster than individual actions',
          '🔒 Bulk delete has confirmation to prevent mistakes',
          '📊 Bulk export preserves format and structure'
        ]
      },
      {
        icon: '🎯',
        title: '9. Other Features',
        color: 'blue',
        features: [
          {
            name: '🔍 Advanced Search & Filters',
            description: 'Quick search and filter by multiple criteria',
            details: [
              'Search by name, number, date range',
              'Filter by status, type, company',
              'Save filter presets'
            ]
          },
          {
            name: '📊 Dashboard & Reports',
            description: 'View overview and reports',
            details: [
              'Certificate expiry dashboard',
              'Upcoming surveys timeline',
              'Company statistics',
              'Crew certificates status'
            ]
          },
          {
            name: '🔔 Expiry Alerts',
            description: 'Automatic alerts for certificates nearing expiration',
            details: [
              'Email/notification alerts',
              'Customizable alert thresholds (30, 60, 90 days)',
              'Alert dashboard'
            ]
          },
          {
            name: '📁 Google Drive Sync',
            description: 'Two-way sync with Google Drive',
            details: [
              'Auto upload on certificate create',
              'Sync from Drive to system',
              'Auto rename files to standard',
              'Backup & restore'
            ]
          },
          {
            name: '🔐 Role-Based Access Control',
            description: 'Detailed permissions by role and department',
            details: [
              'System Admin: Full access',
              'Super Admin: Company-wide access',
              'Admin: Company management',
              'Manager: Limited access',
              'Viewer: Read-only'
            ]
          },
          {
            name: '🌐 Multi-language Support',
            description: 'Multi-language support',
            details: [
              'Vietnamese (Tiếng Việt)',
              'English',
              'Toggle directly in app'
            ]
          },
          {
            name: '📱 Responsive Design',
            description: 'Works smoothly on all devices',
            details: [
              'Desktop, Tablet, Mobile',
              'Touch-friendly interface',
              'Adaptive layout'
            ]
          },
          {
            name: '⚙️ AI Configuration',
            description: 'Configure AI extraction rules',
            details: [
              'Customize per certificate type',
              'AI learning from feedback',
              'Template management'
            ]
          }
        ]
      },
      {
        icon: '💰',
        title: '10. Monthly Fee Calculation',
        color: 'blue',
        steps: [
          { step: '1', text: 'Login with Admin privileges or higher' },
          { step: '2', text: 'Go to "System Settings" → "Company Management"' },
          { step: '3', text: 'Double-click on company row to open Company Details Modal' },
          { step: '4', text: 'View statistics:', details: [
            'Total Ships: Ships with certificates',
            'Office Staff: Office employees (excluding crew)',
            'Crew Members: Total crew count',
            'Active Users: Currently active users'
          ]},
          { step: '5', text: 'Click "💰 Calculate Fee" button at top right' },
          { step: '6', text: 'System calculates and displays:', details: [
            'Monthly fee appears next to company name',
            'Toast notification shows result',
            'Detailed breakdown in console logs'
          ]}
        ],
        formula: {
          title: 'Fee Calculation Formula',
          main: 'Monthly Fee = (Total Ships × Base Fee) + (Office Staff × 0.1 × Base Fee) + (Crew Members × 0.025 × Base Fee)',
          breakdown: [
            {
              label: 'Total Ships × Base Fee',
              example: `5 ships × ${baseFee.toLocaleString('vi-VN')} ₫ = ${(5 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Fee based on number of ships with certificates'
            },
            {
              label: 'Office Staff × 0.1 × Base Fee',
              example: `10 staff × ${(0.1 * baseFee).toLocaleString('vi-VN')} ₫ = ${(10 * 0.1 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Fee based on office employees (10% Base Fee per person)'
            },
            {
              label: 'Crew Members × 0.025 × Base Fee',
              example: `50 crew × ${(0.025 * baseFee).toLocaleString('vi-VN')} ₫ = ${(50 * 0.025 * baseFee).toLocaleString('vi-VN')} ₫`,
              description: 'Fee based on crew members (2.5% Base Fee per person)'
            },
            {
              label: 'Total Fee',
              example: `${(5 * baseFee).toLocaleString('vi-VN')} + ${(10 * 0.1 * baseFee).toLocaleString('vi-VN')} + ${(50 * 0.025 * baseFee).toLocaleString('vi-VN')} = ${(5 * baseFee + 10 * 0.1 * baseFee + 50 * 0.025 * baseFee).toLocaleString('vi-VN')} ₫/month`,
              description: 'Total monthly fee payable'
            }
          ]
        },
        notes: [
          '📌 Base Fee: Set by System Admin/Super Admin',
          '📌 Only counts ships with at least 1 certificate',
          '📌 Office Staff excludes users with "Ship Crew" department',
          '📌 Crew Members counted from Crew Records',
          '📌 Feature available for Admin and above'
        ]
      }
    ]
  };

  const getColorClasses = (color) => {
    const colors = {
      blue: 'from-blue-100 to-blue-200',
      green: 'from-green-100 to-green-200',
      purple: 'from-purple-100 to-purple-200',
      indigo: 'from-indigo-100 to-indigo-200',
      orange: 'from-orange-100 to-orange-200',
      pink: 'from-pink-100 to-pink-200',
      teal: 'from-teal-100 to-teal-200',
      red: 'from-red-100 to-red-200',
      gray: 'from-gray-100 to-gray-200'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4"
      style={{ 
        zIndex: 999999, 
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex'
      }}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden"
        style={{ 
          zIndex: 1000000,
          position: 'relative'
        }}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              <span className="mr-3">📚</span>
              {content.title}
            </h2>
            <p className="text-purple-100 text-sm mt-1">{content.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content - Accordion Style */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-3">
            {content.sections.map((section, index) => (
              <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Section Header - Clickable */}
                <button
                  onClick={() => toggleSection(index)}
                  className={`w-full p-4 flex items-center justify-between bg-gradient-to-r ${getColorClasses(section.color)} hover:opacity-90 transition-all border-2 border-blue-300`}
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">{section.icon}</span>
                    <h3 className="text-lg font-bold text-left text-gray-800">{section.title}</h3>
                  </div>
                  <svg 
                    className={`w-5 h-5 transform transition-transform text-gray-700 ${expandedSection === index ? 'rotate-180' : ''}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Section Content - Expandable */}
                {expandedSection === index && (
                  <div className="p-4 bg-gray-50">
                    {section.steps && (
                      <div className="space-y-4">
                        {section.steps.map((stepItem, stepIndex) => (
                          <div key={stepIndex} className="flex">
                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm mr-3">
                              {stepItem.step}
                            </div>
                            <div className="flex-1">
                              <p className="text-gray-800 font-medium">{stepItem.text}</p>
                              {stepItem.details && (
                                <ul className="mt-2 ml-4 space-y-1">
                                  {stepItem.details.map((detail, detailIndex) => (
                                    <li key={detailIndex} className="text-sm text-gray-600 flex items-start">
                                      <span className="mr-2">•</span>
                                      <span>{detail}</span>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          </div>
                        ))}

                        {/* Tips Section */}
                        {section.tips && (
                          <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                            <p className="font-semibold text-yellow-800 mb-2">💡 Tips:</p>
                            <ul className="space-y-1">
                              {section.tips.map((tip, tipIndex) => (
                                <li key={tipIndex} className="text-sm text-yellow-700">{tip}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Formula Section */}
                        {section.formula && (
                          <div className="mt-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg p-4">
                            <p className="font-bold text-green-800 mb-3 text-lg">📐 {section.formula.title}</p>
                            <div className="bg-white rounded p-3 mb-3 border border-green-200">
                              <p className="font-mono font-bold text-green-700 text-center">
                                {section.formula.main}
                              </p>
                            </div>
                            <div className="space-y-3">
                              {section.formula.breakdown.map((item, idx) => (
                                <div key={idx} className="bg-white rounded p-3 border border-green-100">
                                  <div className="flex items-start justify-between mb-1">
                                    <span className="font-semibold text-gray-800">{item.label}</span>
                                    <span className="font-mono text-green-600 font-bold">{item.example}</span>
                                  </div>
                                  <p className="text-sm text-gray-600">{item.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Notes Section */}
                        {section.notes && (
                          <div className="mt-4 bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                            <p className="font-semibold text-blue-800 mb-2">📋 {language === 'vi' ? 'Lưu ý' : 'Important Notes'}:</p>
                            <ul className="space-y-1">
                              {section.notes.map((note, noteIndex) => (
                                <li key={noteIndex} className="text-sm text-blue-700">{note}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {section.features && (
                      <div className="space-y-3">
                        {section.features.map((feature, featureIndex) => (
                          <div key={featureIndex} className="bg-white rounded-lg p-4 border border-gray-200">
                            <h4 className="font-bold text-gray-800 mb-1">{feature.name}</h4>
                            <p className="text-sm text-gray-600 mb-2">{feature.description}</p>
                            <ul className="ml-4 space-y-1">
                              {feature.details.map((detail, detailIndex) => (
                                <li key={detailIndex} className="text-sm text-gray-600 flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{detail}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-2 rounded-lg font-medium transition-all shadow-md hover:shadow-lg"
          >
            {content.close}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserGuideModal;
