import React from 'react';

const ContactModal = ({ isOpen, onClose, language }) => {
  if (!isOpen) return null;

  const content = language === 'vi' ? {
    title: 'Liên Hệ',
    subtitle: 'Thông tin hỗ trợ và liên hệ',
    close: 'Đóng',
    description: 'Để biết thêm chi tiết thông tin vui lòng liên hệ:',
    zaloLabel: 'Zalo',
    contacts: [
      {
        name: 'Vũ Ngọc Tân',
        phone: '0989357282'
      },
      {
        name: 'Tân PMDS',
        phone: '0904049398'
      }
    ]
  } : {
    title: 'Contact',
    subtitle: 'Support and Contact Information',
    close: 'Close',
    description: 'For more detailed information, please contact:',
    zaloLabel: 'Zalo',
    contacts: [
      {
        name: 'Vũ Ngọc Tân',
        phone: '0989357282'
      },
      {
        name: 'Tân PMDS',
        phone: '0904049398'
      }
    ]
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              <span className="mr-3">📞</span>
              {content.title}
            </h2>
            <p className="text-green-100 text-sm mt-1">{content.subtitle}</p>
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
        <div className="p-8 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Description */}
          <div className="mb-6 text-center">
            <p className="text-lg text-gray-700 font-medium">{content.description}</p>
          </div>

          {/* Zalo Section */}
          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-6 border-2 border-blue-200">
            <div className="flex items-center justify-center mb-6">
              <div className="bg-blue-600 text-white rounded-full p-3 mr-3">
                <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-blue-700">{content.zaloLabel}</h3>
            </div>

            {/* Contact Cards */}
            <div className="space-y-4">
              {content.contacts.map((contact, index) => (
                <div 
                  key={index}
                  className="bg-white rounded-lg p-5 shadow-md border border-blue-100 hover:shadow-lg transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      <div className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-full p-2 mr-4">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-gray-800">{contact.name}</p>
                        <p className="text-sm text-gray-500">Zalo Contact</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <a 
                        href={`tel:${contact.phone}`}
                        className="inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-lg transition-all shadow-md hover:shadow-lg"
                      >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        {contact.phone}
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700 font-medium">
                  {language === 'vi' 
                    ? 'Chúng tôi sẽ hỗ trợ bạn trong giờ hành chính (8:00 - 17:00) từ Thứ 2 đến Thứ 6.'
                    : 'We will support you during business hours (8:00 AM - 5:00 PM) from Monday to Friday.'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white px-6 py-2 rounded-lg font-medium transition-all shadow-md hover:shadow-lg"
          >
            {content.close}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContactModal;
