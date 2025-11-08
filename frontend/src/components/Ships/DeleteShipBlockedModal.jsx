import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Modal to display when ship deletion is blocked due to crew or documents
 */
const DeleteShipBlockedModal = ({ isOpen, onClose, ship, blockingItems }) => {
  const { language } = useAuth();

  if (!isOpen || !ship || !blockingItems) return null;

  // Find crew and documents blocking items
  const crewItem = blockingItems.find(item => item.type === 'crew');
  const documentsItem = blockingItems.find(item => item.type === 'documents');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-yellow-50">
          <h3 className="text-xl font-bold text-yellow-700 flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            {language === 'vi' ? 'Không thể xóa tàu' : 'Cannot Delete Ship'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="p-6">
          {/* Warning Message */}
          <div className="mb-6">
            <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-yellow-100 rounded-full">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            
            <h4 className="text-lg font-semibold text-gray-900 text-center mb-2">
              {language === 'vi' 
                ? `Không thể xóa tàu "${ship.name}"`
                : `Cannot delete ship "${ship.name}"`
              }
            </h4>
            
            <p className="text-sm text-gray-600 text-center mb-6">
              {language === 'vi' 
                ? 'Tàu này vẫn còn thuyền viên hoặc tài liệu. Vui lòng xử lý các mục sau trước khi xóa tàu:'
                : 'This ship still has crew members or documents. Please handle the following items before deleting the ship:'
              }
            </p>
          </div>

          {/* Crew Section */}
          {crewItem && (
            <div className="mb-6 border border-blue-200 rounded-lg p-4 bg-blue-50">
              <div className="flex items-center mb-3">
                <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <h5 className="font-semibold text-blue-900">
                  {language === 'vi' 
                    ? `${crewItem.count} Thuyền viên đang Sign On`
                    : `${crewItem.count} Crew Members Signed On`
                  }
                </h5>
              </div>
              
              <p className="text-sm text-blue-800 mb-3">
                {language === 'vi' 
                  ? 'Vui lòng Sign Off các thuyền viên sau khỏi tàu trước khi xóa:'
                  : 'Please sign off the following crew members before deleting the ship:'
                }
              </p>
              
              <ul className="list-disc list-inside space-y-1 max-h-40 overflow-y-auto">
                {crewItem.items.map((crewName, index) => (
                  <li key={index} className="text-sm text-blue-900">
                    {crewName}
                  </li>
                ))}
              </ul>
              
              <div className="mt-3 p-2 bg-blue-100 rounded text-xs text-blue-800">
                <strong>{language === 'vi' ? 'Hướng dẫn:' : 'Instructions:'}</strong>
                {language === 'vi' 
                  ? ' Vào Crew Records → Crew List → Chọn crew → Sign Off → Chọn "Standby" hoặc đổi sang tàu khác'
                  : ' Go to Crew Records → Crew List → Select crew → Sign Off → Choose "Standby" or transfer to another ship'
                }
              </div>
            </div>
          )}

          {/* Documents Section */}
          {documentsItem && (
            <div className="mb-6 border border-orange-200 rounded-lg p-4 bg-orange-50">
              <div className="flex items-center mb-3">
                <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h5 className="font-semibold text-orange-900">
                  {language === 'vi' 
                    ? `${documentsItem.count} Tài liệu/Chứng chỉ`
                    : `${documentsItem.count} Documents/Certificates`
                  }
                </h5>
              </div>
              
              <p className="text-sm text-orange-800 mb-3">
                {language === 'vi' 
                  ? 'Tàu này có các tài liệu sau. Vui lòng xóa hoặc chuyển sang tàu khác trước:'
                  : 'This ship has the following documents. Please delete or transfer to another ship first:'
                }
              </p>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                {documentsItem.breakdown.certificates > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Chứng chỉ:' : 'Certificates:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.certificates}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.survey_reports > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Báo cáo Survey:' : 'Survey Reports:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.survey_reports}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.audit_reports > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Báo cáo Audit:' : 'Audit Reports:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.audit_reports}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.test_reports > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Báo cáo Test:' : 'Test Reports:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.test_reports}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.drawings_manuals > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Drawings & Manuals:' : 'Drawings & Manuals:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.drawings_manuals}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.approval_documents > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Approval Docs:' : 'Approval Docs:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.approval_documents}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.crew_certificates > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'CC Crew:' : 'Crew Certs:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.crew_certificates}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.audit_certificates > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'CC Audit:' : 'Audit Certs:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.audit_certificates}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.other_documents > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Tài liệu khác:' : 'Other Docs:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.other_documents}</span>
                  </div>
                )}
                
                {documentsItem.breakdown.other_audit_documents > 0 && (
                  <div className="flex justify-between p-2 bg-orange-100 rounded">
                    <span className="text-orange-900">
                      {language === 'vi' ? 'Audit Docs khác:' : 'Other Audit Docs:'}
                    </span>
                    <span className="font-semibold text-orange-900">{documentsItem.breakdown.other_audit_documents}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Button */}
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all font-medium"
            >
              {language === 'vi' ? 'Đã hiểu' : 'Understood'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteShipBlockedModal;
