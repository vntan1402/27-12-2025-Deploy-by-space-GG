import React from 'react';

const IntroductionModal = ({ isOpen, onClose, language }) => {
  if (!isOpen) return null;

  const content = language === 'vi' ? {
    title: 'Giới thiệu Hệ thống',
    subtitle: 'Hệ thống Quản lý Giấy chứng nhận Tàu và Hàng hải',
    description: 'Hệ thống Quản lý Giấy chứng nhận Tàu và Hàng hải là một giải pháp toàn diện được thiết kế đặc biệt cho ngành hàng hải, giúp các doanh nghiệp số hóa và tự động hóa quy trình quản lý chứng chỉ và tài liệu hàng hải một cách thông minh và hiệu quả.',
    coreFeatures: 'Tính năng cốt lõi',
    aiFeatures: 'Tính năng Phân tích Tài liệu bằng AI',
    aiBenefits: 'Lợi ích của AI',
    useCases: 'Các Tình huống Ứng dụng Thực tế',
    close: 'Đóng'
  } : {
    title: 'System Introduction',
    subtitle: 'Ship & Maritime Certificate Management System',
    description: 'Ship & Maritime Certificate Management System is a comprehensive solution specifically designed for the maritime industry, helping businesses digitize and automate certificate and maritime document management processes intelligently and efficiently.',
    coreFeatures: 'Core Features',
    aiFeatures: 'AI Document Analysis Features',
    aiBenefits: 'AI Benefits',
    useCases: 'Real-World Use Cases',
    close: 'Close'
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{content.title}</h2>
            <p className="text-blue-100 text-sm mt-1">{content.subtitle}</p>
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

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Description */}
          <p className="text-gray-700 leading-relaxed mb-6">
            {content.description}
          </p>

          {/* Core Features */}
          <section className="mb-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <span className="text-2xl mr-2">🎯</span>
              {content.coreFeatures}
            </h3>
            
            {language === 'vi' ? (
              <>
                <FeatureItem 
                  title="1. Quản lý Giấy chứng nhận Thông minh"
                  items={[
                    'Quản lý chứng nhận của tàu: ISM, ISPS, MLC, Class, Flag',
                    'Quản lý chứng chỉ thuyền viên: STCW, COC, COP, Medical',
                    'Theo dõi hạn và cảnh báo tự động khi sắp hết hạn',
                    'Quản lý báo cáo đánh giá, Hồ sơ đăng kiểm, bản vẽ & sổ tay hướng dẫn'
                  ]}
                />

                <FeatureItem 
                  title="2. Tính năng Phân tích Tài liệu bằng AI 🤖"
                  subFeatures={[
                    {
                      title: 'a) Nhận dạng ký tự & Trích xuất dữ liệu bằng AI',
                      items: [
                        'Ứng dụng công nghệ AI tiên tiến để đọc và phân tích tài liệu PDF/hình ảnh',
                        'Tự động trích xuất: Tên chứng nhận, Số chứng nhận, Ngày cấp, Ngày hết hạn, Cơ quan cấp',
                        'Hỗ trợ nhiều định dạng: PDF, JPG, PNG, HEIC',
                        'Độ chính xác cao, giảm thiểu sai sót nhập liệu thủ công'
                      ]
                    },
                    {
                      title: 'b) Tự động Điền Thông minh',
                      items: [
                        'Chỉ cần tải tài liệu lên, hệ thống sẽ tự động điền toàn bộ thông tin',
                        'AI phân tích và hiểu ngữ cảnh theo từng loại chứng nhận',
                        'Tự động nhận dạng và chuyển đổi định dạng ngày tháng',
                        'Hỗ trợ các trường phức tạp: Lần Docking gần nhất, Loại tàu, Chu kỳ khảo sát'
                      ]
                    },
                    {
                      title: 'c) Xử lý Hàng loạt bằng AI',
                      items: [
                        'Tải lên nhiều chứng chỉ cùng lúc (5–10 tệp)',
                        'AI tự động phân tích và xử lý song song',
                        'Theo dõi tiến độ theo thời gian thực',
                        'Tiết kiệm đến 80% thời gian so với nhập liệu thủ công'
                      ]
                    },
                    {
                      title: 'd) Phân tích Chứng chỉ Thông minh',
                      items: [
                        'AI tự động tính ngày kỷ niệm (Anniversary Date)',
                        'Phân tích chu kỳ khảo sát định kỳ (Special Survey)',
                        'Cảnh báo hết hạn chứng chỉ',
                        'Kiểm tra tuân thủ tự động'
                      ]
                    }
                  ]}
                />

                <FeatureItem 
                  title="3. Quản lý Tàu & Thuyền viên"
                  items={[
                    'Cơ sở dữ liệu tập trung cho toàn bộ thông tin tàu',
                    'Hồ sơ thuyền viên chi tiết (Crew List)',
                    'Theo dõi quá trình lên/xuống tàu',
                    'Quản lý hộ chiếu & hồ sơ y tế'
                  ]}
                />

                <FeatureItem 
                  title="4. Tích hợp với Google Drive"
                  items={[
                    'Tự động tải chứng chỉ lên Google Drive',
                    'Thư mục được sắp xếp có cấu trúc',
                    'Đồng bộ hai chiều giữa hệ thống và Drive',
                    'Tự động sao lưu & khôi phục dữ liệu'
                  ]}
                />

                <FeatureItem 
                  title="5. Kiểm soát Truy cập Nhiều Cấp độ"
                  items={[
                    'Phân quyền theo vai trò: System Admin, Super Admin, Admin, Manager, Viewer',
                    'Phân quyền theo phòng ban: Operations, Commercial, Ship Crew, SSO, CSO',
                    'Cô lập dữ liệu theo công ty'
                  ]}
                />

                <FeatureItem 
                  title="6. Báo cáo & Thống kê"
                  items={[
                    'Bảng điều khiển chi tiết công ty kèm thống kê',
                    'Tính phí hàng tháng',
                    'Báo cáo chứng chỉ sắp hết hạn',
                    'Báo cáo tuân thủ kiểm toán'
                  ]}
                />
              </>
            ) : (
              <>
                <FeatureItem 
                  title="1. Smart Certificate Management"
                  items={[
                    'Ship Certificates Management: ISM, ISPS, MLC, Class, Flag',
                    'Crew Certificates Management: STCW, COC, COP, Medical',
                    'Automatic expiry tracking and renewal alerts',
                    'Audit reports, survey reports, drawings & manuals management'
                  ]}
                />

                <FeatureItem 
                  title="2. AI Document Analysis Features 🤖"
                  subFeatures={[
                    {
                      title: 'a) AI-Powered OCR & Data Extraction',
                      items: [
                        'Advanced AI technology to read and analyze PDF/image documents',
                        'Automatically extract: Certificate Name, Number, Issue Date, Expiry Date, Issued By',
                        'Multi-format support: PDF, JPG, PNG, HEIC',
                        'High accuracy, minimizing manual entry errors'
                      ]
                    },
                    {
                      title: 'b) Intelligent Auto-Fill',
                      items: [
                        'Simply upload document, system auto-fills all form fields',
                        'AI analyzes and understands context for each certificate type',
                        'Automatic date format recognition and conversion',
                        'Support for complex fields: Last Docking, Ship Type, Survey cycles'
                      ]
                    },
                    {
                      title: 'c) AI Batch Processing',
                      items: [
                        'Upload multiple certificates simultaneously (5-10 files)',
                        'AI automatically analyzes and processes in parallel',
                        'Real-time progress tracking per file',
                        'Save 80% time compared to manual entry'
                      ]
                    },
                    {
                      title: 'd) Smart Certificate Analysis',
                      items: [
                        'AI automatically calculates Anniversary Date',
                        'Analyzes Special Survey cycles',
                        'Certificate expiry alerts',
                        'Automatic compliance checking'
                      ]
                    }
                  ]}
                />

                <FeatureItem 
                  title="3. Ship & Crew Management"
                  items={[
                    'Centralized database for all ship information',
                    'Detailed crew records (Crew List)',
                    'Sign on/sign off tracking',
                    'Passport & medical records management'
                  ]}
                />

                <FeatureItem 
                  title="4. Google Drive Integration"
                  items={[
                    'Auto-upload certificates to Google Drive',
                    'Structured folders by organization',
                    'Two-way sync between system and Drive',
                    'Automatic backup & restore'
                  ]}
                />

                <FeatureItem 
                  title="5. Multi-Level Access Control"
                  items={[
                    'Role-based access: System Admin, Super Admin, Admin, Manager, Viewer',
                    'Department-based permissions: Operations, Commercial, Ship Crew, SSO, CSO',
                    'Company data isolation'
                  ]}
                />

                <FeatureItem 
                  title="6. Reports & Statistics"
                  items={[
                    'Company Details Dashboard with statistics',
                    'Monthly fee calculation',
                    'Certificate expiry reports',
                    'Audit compliance reports'
                  ]}
                />
              </>
            )}
          </section>

          {/* AI Benefits */}
          <section className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <span className="text-2xl mr-2">🚀</span>
              {content.aiBenefits}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {language === 'vi' ? (
                <>
                  <BenefitItem icon="✅" text="Tiết kiệm thời gian: Giảm 80% thời gian nhập dữ liệu" />
                  <BenefitItem icon="✅" text="Độ chính xác cao: AI giảm thiểu lỗi con người" />
                  <BenefitItem icon="✅" text="Xử lý nhanh: Xử lý đồng thời nhiều chứng chỉ" />
                  <BenefitItem icon="✅" text="Tự động hóa: Tự động điền, tính toán, cảnh báo" />
                  <BenefitItem icon="✅" text="Dễ sử dụng: Chỉ cần tải lên và để AI làm phần còn lại" />
                  <BenefitItem icon="✅" text="Linh hoạt: Cấu hình AI theo từng loại chứng chỉ" />
                </>
              ) : (
                <>
                  <BenefitItem icon="✅" text="Time Saving: Reduce 80% manual data entry time" />
                  <BenefitItem icon="✅" text="High Accuracy: AI minimizes human errors" />
                  <BenefitItem icon="✅" text="Fast Processing: Batch processing multiple certificates" />
                  <BenefitItem icon="✅" text="Automation: Auto-fill, auto-calculate, auto-alert" />
                  <BenefitItem icon="✅" text="Easy to Use: Upload and let AI do the rest" />
                  <BenefitItem icon="✅" text="Flexible: AI configuration for each certificate type" />
                </>
              )}
            </div>
          </section>

          {/* Use Cases */}
          <section className="mb-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <span className="text-2xl mr-2">🎓</span>
              {content.useCases}
            </h3>
            
            {language === 'vi' ? (
              <>
                <UseCaseItem 
                  title="Tình huống 1: Tải lên Chứng chỉ Tàu"
                  steps={[
                    'Người dùng tải tệp PDF chứng chỉ ISM Code lên',
                    'AI tự động đọc và trích xuất: Số chứng chỉ, Ngày cấp, Ngày hết hạn',
                    'Biểu mẫu tự động điền đầy đủ thông tin',
                    'Người dùng kiểm tra và xác nhận',
                    'Chứng chỉ được lưu và đồng bộ lên Google Drive'
                  ]}
                />

                <UseCaseItem 
                  title="Tình huống 2: Tải lên Hàng loạt Chứng chỉ Thuyền viên"
                  steps={[
                    'Người dùng tải lên 10 chứng chỉ thuyền viên (COC, Medical, Passport)',
                    'AI xử lý đồng thời cả 10 tệp',
                    'Thanh tiến trình hiển thị trạng thái theo thời gian thực',
                    'Kết quả lô: 9/10 thành công, 1 cần xem lại',
                    'Toàn bộ quá trình chỉ mất 2–3 phút'
                  ]}
                />

                <UseCaseItem 
                  title="Tình huống 3: Khởi tạo Tàu mới"
                  steps={[
                    'Người dùng tải lên tài liệu Thông tin Tàu',
                    'AI tự động trích xuất: Tên tàu, IMO, Cờ, Loại tàu, Lần Docking gần nhất',
                    'AI nhận dạng Loại tàu và tự động chọn từ danh sách',
                    'Ngày kỷ niệm và Chu kỳ khảo sát được tính tự động',
                    'Hồ sơ tàu được tạo đầy đủ chỉ trong vài giây'
                  ]}
                />
              </>
            ) : (
              <>
                <UseCaseItem 
                  title="Scenario 1: Upload Ship Certificate"
                  steps={[
                    'User uploads ISM Code certificate PDF',
                    'AI automatically reads and extracts: Certificate No, Issue Date, Expiry',
                    'Form auto-fills with complete information',
                    'User reviews and confirms',
                    'Certificate saved and synced to Google Drive'
                  ]}
                />

                <UseCaseItem 
                  title="Scenario 2: Batch Upload Crew Certificates"
                  steps={[
                    'User uploads 10 crew certificates (COC, Medical, Passport)',
                    'AI processes all 10 files in parallel',
                    'Real-time progress bar shows status',
                    'Batch Results: 9/10 success, 1 needs review',
                    'Entire process takes only 2-3 minutes'
                  ]}
                />

                <UseCaseItem 
                  title="Scenario 3: New Ship Onboarding"
                  steps={[
                    'User uploads Ship Particular document',
                    'AI auto-extracts: Ship Name, IMO, Flag, Type, Last Docking',
                    'Ship Type recognized by AI and selected from dropdown',
                    'Anniversary Date and Special Survey auto-calculated',
                    'Ship created with full information in seconds'
                  ]}
                />
              </>
            )}
          </section>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-all"
          >
            {content.close}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const FeatureItem = ({ title, items, subFeatures }) => (
  <div className="mb-4">
    <h4 className="font-semibold text-gray-800 mb-2">{title}</h4>
    {items && (
      <ul className="list-disc list-inside space-y-1 ml-4 text-gray-700 text-sm">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    )}
    {subFeatures && (
      <div className="ml-4 mt-2 space-y-3">
        {subFeatures.map((sub, index) => (
          <div key={index}>
            <p className="font-medium text-gray-700 text-sm mb-1">{sub.title}</p>
            <ul className="list-disc list-inside space-y-1 ml-4 text-gray-600 text-sm">
              {sub.items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    )}
  </div>
);

const BenefitItem = ({ icon, text }) => (
  <div className="flex items-start">
    <span className="text-green-600 mr-2">{icon}</span>
    <p className="text-gray-700 text-sm">{text}</p>
  </div>
);

const UseCaseItem = ({ title, steps }) => (
  <div className="mb-4 bg-blue-50 rounded-lg p-4">
    <h4 className="font-semibold text-blue-800 mb-2">{title}</h4>
    <ol className="list-decimal list-inside space-y-1 ml-4 text-gray-700 text-sm">
      {steps.map((step, index) => (
        <li key={index}>{step}</li>
      ))}
    </ol>
  </div>
);

export default IntroductionModal;
