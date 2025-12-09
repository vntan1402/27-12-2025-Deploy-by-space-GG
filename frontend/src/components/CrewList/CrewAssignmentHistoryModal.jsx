import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { crewService } from '../../services/crewService';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const CrewAssignmentHistoryModal = ({ crew, onClose }) => {
  const { language } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [historyData, setHistoryData] = useState([]);
  const [shipAssignments, setShipAssignments] = useState([]);
  const [filteredAssignments, setFilteredAssignments] = useState([]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // Filter state
  const [filterActionType, setFilterActionType] = useState('All');

  useEffect(() => {
    const fetchAssignmentHistory = async () => {
      try {
        setLoading(true);
        const response = await crewService.getAssignmentHistory(crew.id, { limit: 100, skip: 0 });
        
        if (response.success && response.history) {
          setHistoryData(response.history);
          
          // Transform history into ship assignments
          const assignments = transformToShipAssignments(response.history);
          setShipAssignments(assignments);
          setFilteredAssignments(assignments);
        } else {
          setHistoryData([]);
          setShipAssignments([]);
          setFilteredAssignments([]);
        }
      } catch (error) {
        console.error('Error fetching assignment history:', error);
        toast.error(
          language === 'vi'
            ? 'Không thể tải lịch sử thay đổi'
            : 'Failed to load assignment history'
        );
        setHistoryData([]);
        setShipAssignments([]);
        setFilteredAssignments([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAssignmentHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [crew.id]);

  /**
   * Transform history records into ship assignment rows
   * Each row represents one ship with sign on/off dates
   */
  const transformToShipAssignments = (history) => {
    if (!history || history.length === 0) return [];

    console.log('📋 Raw history data:', history);

    // Sort history by action_date ascending (oldest first)
    const sortedHistory = [...history].sort((a, b) => 
      new Date(a.action_date) - new Date(b.action_date)
    );

    const shipMap = new Map();

    sortedHistory.forEach((record) => {
      const { 
        id,  // Record ID for unique key
        action_type, 
        from_ship, 
        to_ship, 
        action_date, 
        performed_by,
        sign_on_date,
        sign_on_by,
        sign_off_date,
        sign_off_by
      } = record;
      
      console.log('Processing record:', { id, action_type, from_ship, to_ship, action_date, sign_on_date, sign_off_date });

      // Handle SIGN_ON: crew joins a ship
      if (action_type === 'SIGN_ON' && to_ship) {
        // Use record ID as unique key to allow multiple assignments to same ship
        const uniqueKey = id || `${to_ship}_${action_date}`;
        
        if (!shipMap.has(uniqueKey)) {
          shipMap.set(uniqueKey, {
            ship_name: to_ship,
            sign_on_date: sign_on_date || action_date,  // Use sign_on_date field if available
            sign_on_by: sign_on_by || performed_by,
            sign_off_date: sign_off_date || null,  // Read from record
            sign_off_by: sign_off_by || null,  // Read from record
            action_type: action_type
          });
        }
      }

      // Handle SHIP_TRANSFER: crew leaves from_ship and joins to_ship
      if (action_type === 'SHIP_TRANSFER') {
        // Step 1: Find and close the from_ship assignment (search by ship name with no sign_off_date)
        if (from_ship) {
          // Find the open assignment for from_ship
          for (const [key, assignment] of shipMap.entries()) {
            if (assignment.ship_name === from_ship && !assignment.sign_off_date) {
              assignment.sign_off_date = action_date;
              assignment.sign_off_by = performed_by;
              break;  // Only close the first open assignment
            }
          }
        }

        // Step 2: Create new to_ship assignment with unique key
        if (to_ship) {
          const uniqueKey = id || `${to_ship}_${action_date}`;
          shipMap.set(uniqueKey, {
            ship_name: to_ship,
            sign_on_date: action_date,
            sign_on_by: performed_by,
            sign_off_date: null,
            sign_off_by: null,
            action_type: action_type
          });
        }
      }

      // Handle SIGN_OFF: crew leaves the ship
      if (action_type === 'SIGN_OFF' && from_ship) {
        // Try to find the ship assignment
        if (shipMap.has(from_ship)) {
          const assignment = shipMap.get(from_ship);
          if (!assignment.sign_off_date) {
            assignment.sign_off_date = action_date;
            assignment.sign_off_by = performed_by;
            assignment.action_type = action_type;
          }
        } else {
          // SIGN_OFF without prior SIGN_ON record (data inconsistency or missing SIGN_ON)
          // Create a ship entry with sign off only
          console.warn(`⚠️ SIGN_OFF for ${from_ship} but no prior SIGN_ON found. Creating entry.`);
          shipMap.set(from_ship, {
            ship_name: from_ship,
            sign_on_date: null,  // Unknown
            sign_on_by: null,
            sign_off_date: action_date,
            sign_off_by: performed_by,
            action_type: action_type
          });
        }
      }
    });

    console.log('📊 Final shipMap:', Array.from(shipMap.values()));

    // Convert map to array and sort by sign_on_date descending (newest first)
    return Array.from(shipMap.values()).sort((a, b) => 
      new Date(b.sign_on_date) - new Date(a.sign_on_date)
    );
  };

  // Apply filter
  useEffect(() => {
    if (filterActionType === 'All') {
      setFilteredAssignments(shipAssignments);
    } else {
      const filtered = shipAssignments.filter(
        (assignment) => assignment.action_type === filterActionType
      );
      setFilteredAssignments(filtered);
    }
    setCurrentPage(1); // Reset to first page when filter changes
  }, [filterActionType, shipAssignments]);

  // Pagination
  const totalPages = Math.ceil(filteredAssignments.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentPageData = filteredAssignments.slice(startIndex, endIndex);

  // Export to CSV
  const handleExportCSV = () => {
    try {
      const headers = [
        language === 'vi' ? 'Tên tàu' : 'Ship Name',
        language === 'vi' ? 'Ngày Sign On' : 'Sign On Date',
        language === 'vi' ? 'Người Sign On' : 'Sign On By',
        language === 'vi' ? 'Ngày Sign Off' : 'Sign Off Date',
        language === 'vi' ? 'Người Sign Off' : 'Sign Off By'
      ];

      const csvData = filteredAssignments.map((assignment) => [
        assignment.ship_name,
        formatDateDisplay(assignment.sign_on_date),
        assignment.sign_on_by || '-',
        assignment.sign_off_date ? formatDateDisplay(assignment.sign_off_date) : '-',
        assignment.sign_off_by || '-'
      ]);

      const csvContent = [
        headers.join(','),
        ...csvData.map((row) => row.join(','))
      ].join('\n');

      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${crew.full_name}_assignment_history_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();

      toast.success(
        language === 'vi' ? 'Đã xuất file CSV thành công!' : 'CSV exported successfully!'
      );
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error(
        language === 'vi' ? 'Lỗi khi xuất file CSV' : 'Error exporting CSV'
      );
    }
  };

  // Export to PDF (using browser print)
  const handleExportPDF = () => {
    // Create a printable version
    const printWindow = window.open('', '_blank');
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>${language === 'vi' ? 'Lịch sử thay đổi' : 'Assignment History'} - ${crew.full_name}</title>
          <style>
            body { 
              font-family: Arial, sans-serif; 
              padding: 20px;
              font-size: 12px;
            }
            h1 { 
              font-size: 18px; 
              margin-bottom: 20px;
              text-align: center;
            }
            table { 
              width: 100%; 
              border-collapse: collapse; 
              margin-top: 10px;
            }
            th, td { 
              border: 1px solid #ddd; 
              padding: 8px; 
              text-align: left;
            }
            th { 
              background-color: #f3f4f6; 
              font-weight: bold;
            }
            tr:nth-child(even) {
              background-color: #f9fafb;
            }
            .footer {
              margin-top: 20px;
              text-align: center;
              font-size: 10px;
              color: #666;
            }
          </style>
        </head>
        <body>
          <h1>${language === 'vi' ? 'Lịch sử thay đổi' : 'Assignment History'} - ${crew.full_name}</h1>
          <table>
            <thead>
              <tr>
                <th>${language === 'vi' ? 'Tên tàu' : 'Ship Name'}</th>
                <th>${language === 'vi' ? 'Ngày Sign On' : 'Sign On Date'}</th>
                <th>${language === 'vi' ? 'Người Sign On' : 'Sign On By'}</th>
                <th>${language === 'vi' ? 'Ngày Sign Off' : 'Sign Off Date'}</th>
                <th>${language === 'vi' ? 'Người Sign Off' : 'Sign Off By'}</th>
              </tr>
            </thead>
            <tbody>
              ${filteredAssignments.map((assignment) => `
                <tr>
                  <td>${assignment.ship_name}</td>
                  <td>${formatDateDisplay(assignment.sign_on_date)}</td>
                  <td>${assignment.sign_on_by || '-'}</td>
                  <td>${assignment.sign_off_date ? formatDateDisplay(assignment.sign_off_date) : '-'}</td>
                  <td>${assignment.sign_off_by || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <div class="footer">
            ${language === 'vi' ? 'Xuất ngày' : 'Exported on'}: ${new Date().toLocaleDateString()}
          </div>
        </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // Wait for content to load before printing
    printWindow.onload = () => {
      printWindow.print();
      // Close window after print dialog is closed (user may cancel)
      printWindow.onafterprint = () => {
        printWindow.close();
      };
    };

    toast.success(
      language === 'vi' ? 'Đang chuẩn bị file PDF...' : 'Preparing PDF...'
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              📋 {language === 'vi' ? 'Lịch sử thay đổi' : 'Assignment History'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {crew.full_name} - {crew.passport}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold w-8 h-8 flex items-center justify-center"
          >
            ×
          </button>
        </div>

        {/* Toolbar - Filter and Export */}
        <div className="px-6 py-4 border-b border-gray-200 flex flex-wrap items-center gap-4">
          {/* Filter by Action Type */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              🔍 {language === 'vi' ? 'Lọc theo:' : 'Filter by:'}
            </label>
            <select
              value={filterActionType}
              onChange={(e) => setFilterActionType(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="All">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="SIGN_ON">{language === 'vi' ? '✅ Sign On' : '✅ Sign On'}</option>
              <option value="SIGN_OFF">{language === 'vi' ? '🛑 Sign Off' : '🛑 Sign Off'}</option>
              <option value="SHIP_TRANSFER">{language === 'vi' ? '🔄 Chuyển tàu' : '🔄 Transfer'}</option>
            </select>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={handleExportCSV}
              disabled={filteredAssignments.length === 0}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              📥 CSV
            </button>
            <button
              onClick={handleExportPDF}
              disabled={filteredAssignments.length === 0}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              📄 PDF
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">
                  {language === 'vi' ? 'Đang tải...' : 'Loading...'}
                </p>
              </div>
            </div>
          ) : filteredAssignments.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📋</div>
              <p className="text-gray-600 text-lg">
                {language === 'vi' 
                  ? 'Chưa có lịch sử thay đổi' 
                  : 'No assignment history yet'}
              </p>
            </div>
          ) : (
            <>
              {/* Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r border-gray-200">
                        {language === 'vi' ? 'STT' : 'No.'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r border-gray-200">
                        {language === 'vi' ? 'Tên tàu' : 'Ship Name'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r border-gray-200">
                        {language === 'vi' ? 'Ngày Sign On' : 'Sign On Date'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r border-gray-200">
                        {language === 'vi' ? 'Người Sign On' : 'Sign On By'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r border-gray-200">
                        {language === 'vi' ? 'Ngày Sign Off' : 'Sign Off Date'}
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">
                        {language === 'vi' ? 'Người Sign Off' : 'Sign Off By'}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {currentPageData.map((assignment, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-gray-200">
                          {startIndex + index + 1}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r border-gray-200">
                          {assignment.ship_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-gray-200">
                          {assignment.sign_on_date ? formatDateDisplay(assignment.sign_on_date) : (
                            <span className="text-gray-400 italic">
                              {language === 'vi' ? 'Không rõ' : 'Unknown'}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 border-r border-gray-200">
                          {assignment.sign_on_by || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-gray-200">
                          {assignment.sign_off_date ? formatDateDisplay(assignment.sign_off_date) : (
                            <span className="text-green-600 font-medium">
                              {language === 'vi' ? '✓ Đang làm việc' : '✓ Currently working'}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {assignment.sign_off_by || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                  <div className="text-sm text-gray-600">
                    {language === 'vi' 
                      ? `Hiển thị ${startIndex + 1}-${Math.min(endIndex, filteredAssignments.length)} trong tổng số ${filteredAssignments.length} bản ghi`
                      : `Showing ${startIndex + 1}-${Math.min(endIndex, filteredAssignments.length)} of ${filteredAssignments.length} records`}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 border border-gray-300 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {language === 'vi' ? '← Trước' : '← Previous'}
                    </button>
                    <span className="text-sm text-gray-600">
                      {language === 'vi' ? `Trang ${currentPage} / ${totalPages}` : `Page ${currentPage} of ${totalPages}`}
                    </span>
                    <button
                      onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1.5 border border-gray-300 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {language === 'vi' ? 'Sau →' : 'Next →'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
