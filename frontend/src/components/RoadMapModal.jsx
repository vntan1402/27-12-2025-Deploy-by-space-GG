import React from 'react';

const RoadMapModal = ({ isOpen, onClose, language }) => {
  if (!isOpen) return null;

  const content = language === 'vi' ? {
    title: 'Lộ Trình Phát Triển',
    subtitle: 'Hệ thống Quản lý Giấy chứng nhận Tàu và Hàng hải',
    note: 'Lộ trình trên là tiến độ dự kiến, có thể thay đổi tùy thuộc tình hình thực tế',
    close: 'Đóng',
    milestones: [
      {
        date: '28/11/2025',
        phase: 'Giai đoạn 1',
        status: 'Chạy thử',
        title: 'Phase 1 Pilot Testing',
        description: 'Chạy thử giai đoạn 1',
        features: [
          'Upload giấy chứng nhận',
          'Quản lý giấy chứng nhận',
          'Quản lý hồ sơ tàu',
          'Quản lý hồ sơ thuyền viên',
          'Cập nhật, sửa chữa các lỗi phát sinh'
        ],
        icon: '🚀',
        color: 'blue'
      },
      {
        date: '14/02/2026',
        phase: 'Giai đoạn 1 - 2',
        status: 'Hoàn thiện & Chạy thử',
        title: 'Phase 1 Complete + Phase 2 Pilot',
        description: 'Hoàn thiện giai đoạn 1 và chạy thử giai đoạn 2',
        features: [
          '✅ Hoàn thiện giai đoạn 1',
          'Liên kết Zalo Chatbot',
          'Trợ lý AI thông minh',
          'Tương tác tự động với người dùng'
        ],
        icon: '🤖',
        color: 'green'
      },
      {
        date: '15/05/2026',
        phase: 'Giai đoạn 2 - 3',
        status: 'Hoàn thiện & Chạy thử',
        title: 'Phase 2 Complete + Phase 3 Pilot',
        description: 'Hoàn thiện giai đoạn 2 và chạy thử giai đoạn 3',
        features: [
          '✅ Hoàn thiện giai đoạn 2',
          'Tích hợp hệ thống Quản lý An toàn',
          'Tích hợp MLC (Maritime Labour Convention)',
          'Quản lý tuân thủ tự động'
        ],
        icon: '🛡️',
        color: 'purple'
      },
      {
        date: '16/09/2026',
        phase: 'Hoàn Thành',
        status: 'Ra mắt chính thức',
        title: 'Complete System Launch',
        description: 'Hoàn thiện toàn bộ hệ thống',
        features: [
          '✅ Tất cả tính năng hoàn thiện',
          'Hệ thống ổn định và tối ưu',
          'Hỗ trợ toàn diện',
          'Sẵn sàng triển khai rộng rãi'
        ],
        icon: '🎉',
        color: 'orange'
      }
    ]
  } : {
    title: 'Development Roadmap',
    subtitle: 'Ship & Maritime Certificate Management System',
    note: 'The roadmap is the expected timeline and may change depending on actual circumstances',
    close: 'Close',
    milestones: [
      {
        date: '28/11/2025',
        phase: 'Phase 1',
        status: 'Pilot Testing',
        title: 'Phase 1 Pilot Testing',
        description: 'Phase 1 pilot testing launch',
        features: [
          'Certificate upload',
          'Certificate management',
          'Ship records management',
          'Crew records management',
          'Bug fixes and updates'
        ],
        icon: '🚀',
        color: 'blue'
      },
      {
        date: '14/02/2026',
        phase: 'Phase 1 - 2',
        status: 'Complete & Pilot',
        title: 'Phase 1 Complete + Phase 2 Pilot',
        description: 'Complete Phase 1 and launch Phase 2 pilot',
        features: [
          '✅ Phase 1 complete',
          'Zalo Chatbot integration',
          'AI Assistant',
          'Automated user interaction'
        ],
        icon: '🤖',
        color: 'green'
      },
      {
        date: '15/05/2026',
        phase: 'Phase 2 - 3',
        status: 'Complete & Pilot',
        title: 'Phase 2 Complete + Phase 3 Pilot',
        description: 'Complete Phase 2 and launch Phase 3 pilot',
        features: [
          '✅ Phase 2 complete',
          'Safety Management System integration',
          'MLC (Maritime Labour Convention) integration',
          'Automated compliance management'
        ],
        icon: '🛡️',
        color: 'purple'
      },
      {
        date: '16/09/2026',
        phase: 'Complete',
        status: 'Official Launch',
        title: 'Complete System Launch',
        description: 'Full system completion',
        features: [
          '✅ All features complete',
          'Stable and optimized system',
          'Comprehensive support',
          'Ready for wide deployment'
        ],
        icon: '🎉',
        color: 'orange'
      }
    ]
  };

  const getColorClasses = (color) => {
    const colors = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-700',
        icon: 'bg-blue-500',
        line: 'bg-blue-300'
      },
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-700',
        icon: 'bg-green-500',
        line: 'bg-green-300'
      },
      purple: {
        bg: 'bg-purple-50',
        border: 'border-purple-200',
        text: 'text-purple-700',
        icon: 'bg-purple-500',
        line: 'bg-purple-300'
      },
      orange: {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-700',
        icon: 'bg-orange-500',
        line: 'bg-orange-300'
      }
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              <span className="mr-3">🗺️</span>
              {content.title}
            </h2>
            <p className="text-indigo-100 text-sm mt-1">{content.subtitle}</p>
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
          {/* Timeline */}
          <div className="relative">
            {/* Vertical Line */}
            <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-300 via-green-300 via-purple-300 to-orange-300"></div>

            {/* Milestones */}
            <div className="space-y-8">
              {content.milestones.map((milestone, index) => {
                const colors = getColorClasses(milestone.color);
                return (
                  <div key={index} className="relative pl-20">
                    {/* Timeline Icon */}
                    <div className={`absolute left-0 w-16 h-16 ${colors.icon} rounded-full flex items-center justify-center text-3xl shadow-lg z-10 border-4 border-white`}>
                      {milestone.icon}
                    </div>

                    {/* Milestone Card */}
                    <div className={`${colors.bg} border-2 ${colors.border} rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]`}>
                      {/* Date & Status */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <span className={`px-4 py-1 ${colors.icon} text-white text-sm font-bold rounded-full`}>
                            📅 {milestone.date}
                          </span>
                          <span className={`px-3 py-1 bg-white ${colors.text} text-xs font-semibold rounded-full border-2 ${colors.border}`}>
                            {milestone.status}
                          </span>
                        </div>
                      </div>

                      {/* Phase Title */}
                      <h3 className={`text-xl font-bold ${colors.text} mb-2`}>
                        {milestone.phase}
                      </h3>

                      {/* Description */}
                      <p className="text-gray-700 font-medium mb-4">
                        {milestone.description}
                      </p>

                      {/* Features List */}
                      <div className="space-y-2">
                        {milestone.features.map((feature, idx) => (
                          <div key={idx} className="flex items-start">
                            <span className="text-gray-500 mr-2 mt-1">
                              {feature.startsWith('✅') ? '✅' : '•'}
                            </span>
                            <span className={`text-sm ${feature.startsWith('✅') ? 'font-semibold text-gray-800' : 'text-gray-700'}`}>
                              {feature.replace('✅ ', '')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Note */}
          <div className="mt-8 bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-yellow-800 font-medium">
                <span className="font-bold">📌 {language === 'vi' ? 'Lưu ý' : 'Note'}:</span> {content.note}
              </p>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 text-center border border-blue-200">
              <div className="text-3xl font-bold text-blue-700">4</div>
              <div className="text-xs text-gray-600 mt-1">{language === 'vi' ? 'Giai đoạn' : 'Phases'}</div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 text-center border border-green-200">
              <div className="text-3xl font-bold text-green-700">10</div>
              <div className="text-xs text-gray-600 mt-1">{language === 'vi' ? 'Tháng' : 'Months'}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center border border-purple-200">
              <div className="text-3xl font-bold text-purple-700">3</div>
              <div className="text-xs text-gray-600 mt-1">{language === 'vi' ? 'Tính năng chính' : 'Major Features'}</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 text-center border border-orange-200">
              <div className="text-3xl font-bold text-orange-700">100%</div>
              <div className="text-xs text-gray-600 mt-1">{language === 'vi' ? 'Hoàn thành' : 'Completion'}</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-all shadow-md hover:shadow-lg"
          >
            {content.close}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RoadMapModal;
