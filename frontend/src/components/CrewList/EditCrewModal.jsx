import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { crewService } from '../../services/crewService';
import { shipService } from '../../services/shipService';
import { RANK_OPTIONS } from '../../utils/constants';

export const EditCrewModal = ({ 
  crew,
  onClose, 
  onSuccess,
  onDelete
}) => {
  const { language } = useAuth();
  
  // Form state - initialize with crew data
  const [formData, setFormData] = useState({
    full_name: crew.full_name || '',
    full_name_en: crew.full_name_en || '',
    sex: crew.sex || 'M',
    date_of_birth: crew.date_of_birth ? crew.date_of_birth.split('T')[0] : '',
    place_of_birth: crew.place_of_birth || '',
    place_of_birth_en: crew.place_of_birth_en || '',
    passport: crew.passport || '',
    nationality: crew.nationality || '',
    passport_expiry_date: crew.passport_expiry_date ? crew.passport_expiry_date.split('T')[0] : '',
    rank: crew.rank || '',
    seamen_book: crew.seamen_book || '',
    status: crew.status || 'Sign on',
    ship_sign_on: crew.ship_sign_on || '-',
    place_sign_on: crew.place_sign_on || '',
    date_sign_on: crew.date_sign_on ? crew.date_sign_on.split('T')[0] : '',
    date_sign_off: crew.date_sign_off ? crew.date_sign_off.split('T')[0] : ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ships, setShips] = useState([]);
  const [loadingShips, setLoadingShips] = useState(false);
  
  // Fetch ships on mount
  useEffect(() => {
    const fetchShips = async () => {
      try {
        setLoadingShips(true);
        const response = await shipService.getAll();
        if (response.data) {
          setShips(response.data);
        }
      } catch (error) {
        console.error('Error fetching ships:', error);
        toast.error(
          language === 'vi' 
            ? 'Không thể tải danh sách tàu' 
            : 'Failed to load ships list'
        );
      } finally {
        setLoadingShips(false);
      }
    };
    
    fetchShips();
  }, [language]);
  
  // Handle form submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.full_name || !formData.date_of_birth || !formData.place_of_birth || !formData.passport) {
      toast.error(language === 'vi' 
        ? 'Vui lòng điền đầy đủ các trường bắt buộc!'
        : 'Please fill in all required fields!');
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      // Update crew member
      const updateData = {
        ...formData,
        // Remove empty optional fields
        full_name_en: formData.full_name_en || undefined,
        place_of_birth_en: formData.place_of_birth_en || undefined,
        nationality: formData.nationality || undefined,
        passport_expiry_date: formData.passport_expiry_date || undefined,
        rank: formData.rank || undefined,
        seamen_book: formData.seamen_book || undefined,
        place_sign_on: formData.place_sign_on || undefined,
        date_sign_on: formData.date_sign_on || undefined,
        date_sign_off: formData.date_sign_off || undefined
      };
      
      await crewService.update(crew.id, updateData);
      
      toast.success(language === 'vi' 
        ? 'Cập nhật thuyền viên thành công!'
        : 'Crew member updated successfully!');
      
      // Callback and close
      onSuccess();
      onClose();
      
    } catch (error) {
      console.error('Error updating crew member:', error);
      toast.error(language === 'vi' 
        ? `Lỗi khi cập nhật: ${error.response?.data?.detail || error.message}`
        : `Update error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Chỉnh sửa thuyền viên' : 'Edit Crew Member'}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {crew.full_name} - {crew.passport}
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Row 1: Full Name (Vietnamese), Full Name (English), Sex */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Họ tên (Tiếng Việt)' : 'Full Name (Vietnamese)'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Họ tên (Tiếng Anh)' : 'Full Name (English)'}
                </label>
                <input
                  type="text"
                  value={formData.full_name_en}
                  onChange={(e) => setFormData({...formData, full_name_en: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Giới tính' : 'Sex'}
                </label>
                <select
                  value={formData.sex}
                  onChange={(e) => setFormData({...formData, sex: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="M">M</option>
                  <option value="F">F</option>
                </select>
              </div>
            </div>
            
            {/* Row 2: Date of Birth, Passport, Nationality */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày sinh' : 'Date of Birth'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Hộ chiếu' : 'Passport'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.passport}
                  onChange={(e) => setFormData({...formData, passport: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Quốc tịch' : 'Nationality'}
                </label>
                <input
                  type="text"
                  value={formData.nationality}
                  onChange={(e) => setFormData({...formData, nationality: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            {/* Row 3: Place of Birth (Vietnamese), Place of Birth (English), Passport Expiry */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Nơi sinh (Tiếng Việt)' : 'Place of Birth (Vietnamese)'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.place_of_birth}
                  onChange={(e) => setFormData({...formData, place_of_birth: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Nơi sinh (Tiếng Anh)' : 'Place of Birth (English)'}
                </label>
                <input
                  type="text"
                  value={formData.place_of_birth_en}
                  onChange={(e) => setFormData({...formData, place_of_birth_en: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày hết hạn hộ chiếu' : 'Passport Expiry Date'}
                </label>
                <input
                  type="date"
                  value={formData.passport_expiry_date}
                  onChange={(e) => setFormData({...formData, passport_expiry_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            {/* Row 4: Rank, Seamen Book, Status */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Chức vụ' : 'Rank'}
                </label>
                <select
                  value={formData.rank}
                  onChange={(e) => setFormData({...formData, rank: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{language === 'vi' ? '-- Chọn chức vụ --' : '-- Select Rank --'}</option>
                  {RANK_OPTIONS.map(rank => (
                    <option key={rank.value} value={rank.value}>
                      {rank.value} - {language === 'vi' ? rank.label_vi : rank.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Sổ thuyền viên' : 'Seamen Book'}
                </label>
                <input
                  type="text"
                  value={formData.seamen_book}
                  onChange={(e) => setFormData({...formData, seamen_book: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="Sign on">{language === 'vi' ? 'Đang làm việc' : 'Sign on'}</option>
                  <option value="Standby">{language === 'vi' ? 'Chờ' : 'Standby'}</option>
                  <option value="Leave">{language === 'vi' ? 'Nghỉ phép' : 'Leave'}</option>
                </select>
              </div>
            </div>
            
            {/* Row 5: Ship Sign On, Place Sign On, Date Sign On */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
                  {loadingShips && (
                    <span className="ml-2 text-xs text-gray-500">
                      {language === 'vi' ? '(Đang tải...)' : '(Loading...)'}
                    </span>
                  )}
                </label>
                <select
                  value={formData.ship_sign_on}
                  onChange={(e) => setFormData({...formData, ship_sign_on: e.target.value})}
                  disabled={loadingShips}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="-">
                    {language === 'vi' ? '-- Chọn tàu --' : '-- Select Ship --'}
                  </option>
                  {ships.map((ship) => (
                    <option key={ship.id} value={ship.name}>
                      {ship.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On'}
                </label>
                <input
                  type="text"
                  value={formData.place_sign_on}
                  onChange={(e) => setFormData({...formData, place_sign_on: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
                </label>
                <input
                  type="date"
                  value={formData.date_sign_on}
                  onChange={(e) => setFormData({...formData, date_sign_on: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            {/* Row 6: Date Sign Off */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
                  {formData.date_sign_off && (
                    <span className="ml-2 text-xs text-orange-600 font-medium">
                      {language === 'vi' ? '(Tự động: Standby, Tàu "-")' : '(Auto: Standby, Ship "-")'}
                    </span>
                  )}
                </label>
                <input
                  type="date"
                  value={formData.date_sign_off}
                  onChange={(e) => {
                    const newDateSignOff = e.target.value;
                    
                    // Auto-update Status and Ship Sign On when Date Sign Off is filled
                    if (newDateSignOff) {
                      setFormData({
                        ...formData, 
                        date_sign_off: newDateSignOff,
                        status: 'Standby',
                        ship_sign_on: '-'
                      });
                      
                      // Show info toast
                      toast.info(
                        language === 'vi'
                          ? '✨ Tự động: Trạng thái → "Standby", Tàu → "-"'
                          : '✨ Auto-updated: Status → "Standby", Ship → "-"',
                        { duration: 3000 }
                      );
                    } else {
                      // Just update date_sign_off, don't change status/ship
                      setFormData({...formData, date_sign_off: newDateSignOff});
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            {/* Submit Buttons */}
            <div className="flex justify-between items-center pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={() => onDelete(crew)}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center space-x-2"
              >
                <span>🗑️</span>
                <span>{language === 'vi' ? 'Xóa' : 'Delete'}</span>
              </button>
              
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  disabled={isSubmitting}
                >
                  {language === 'vi' ? 'Hủy' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>{language === 'vi' ? 'Đang xử lý...' : 'Processing...'}</span>
                    </>
                  ) : (
                    <>
                      <span>💾</span>
                      <span>{language === 'vi' ? 'Cập nhật' : 'Update'}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
