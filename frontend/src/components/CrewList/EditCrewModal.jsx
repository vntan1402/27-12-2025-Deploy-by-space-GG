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
        console.log('Ships API response:', response);
        if (response.data) {
          console.log('Ships data:', response.data);
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
      
      // Get original values for comparison
      const originalStatus = crew.status;
      const originalShip = (crew.ship_sign_on || '').trim().toLowerCase();
      const newStatus = formData.status;
      const newShip = (formData.ship_sign_on || '').trim().toLowerCase();
      
      // Track date changes for assignment history update
      const originalDateSignOn = crew.date_sign_on ? crew.date_sign_on.split('T')[0] : null;
      const originalDateSignOff = crew.date_sign_off ? crew.date_sign_off.split('T')[0] : null;
      const newDateSignOn = formData.date_sign_on || null;
      const newDateSignOff = formData.date_sign_off || null;
      
      console.log('📅 Date comparison:', {
        originalDateSignOn,
        newDateSignOn,
        originalDateSignOff,
        newDateSignOff
      });
      
      const dateChanges = {};
      if (originalDateSignOn !== newDateSignOn && newDateSignOn) {
        dateChanges.date_sign_on = newDateSignOn;
        console.log('📅 Sign On date changed:', originalDateSignOn, '→', newDateSignOn);
      }
      if (originalDateSignOff !== newDateSignOff && newDateSignOff) {
        dateChanges.date_sign_off = newDateSignOff;
        console.log('📅 Sign Off date changed:', originalDateSignOff, '→', newDateSignOff);
      }
      
      // Determine which flow to use based on status and ship changes
      let needsFileMovement = false;
      
      // Case 1: Sign Off Flow
      // Original status was "Sign on" and new status is "Standby" (ship changed to "-")
      if (originalStatus === 'Sign on' && newStatus === 'Standby' && newShip === '-') {
        console.log('🔄 Sign Off Flow detected');
        needsFileMovement = true;
        
        // Update DB immediately with all fields including ship_sign_on and status
        const updateData = {
          full_name: formData.full_name,
          full_name_en: formData.full_name_en || null,
          sex: formData.sex,
          date_of_birth: formData.date_of_birth,
          place_of_birth: formData.place_of_birth,
          place_of_birth_en: formData.place_of_birth_en || null,
          passport: formData.passport,
          nationality: formData.nationality || null,
          passport_expiry_date: formData.passport_expiry_date || null,
          rank: formData.rank || null,
          seamen_book: formData.seamen_book || null,
          ship_sign_on: '-',
          status: 'Standby',
          place_sign_on: formData.place_sign_on || null,
          date_sign_on: formData.date_sign_on || null,
          date_sign_off: formData.date_sign_off || null
        };
        
        await crewService.update(crew.id, updateData);
        
        // Call sign off API in background for file movement and audit trail
        crewService.signOff(crew.id, {
          sign_off_date: formData.date_sign_off || new Date().toISOString().split('T')[0],
          notes: `Sign off via Edit Crew Member modal`
        }).catch(error => {
          console.error('Background sign off error:', error);
        });
        
        toast.success(
          language === 'vi' 
            ? '✅ Đã cập nhật thuyền viên. Files đang được di chuyển...'
            : '✅ Crew updated. Files are being moved in background...',
          { duration: 5000 }
        );
        
      }
      // Case 2: Sign On Flow
      // Original status was "Standby" and new status is "Sign on" (ship changed from "-" to a ship)
      else if (originalStatus === 'Standby' && newStatus === 'Sign on' && newShip !== '-' && newShip !== '') {
        console.log('🔄 Sign On Flow detected');
        needsFileMovement = true;
        
        // Update DB immediately with all fields including ship_sign_on and status
        const updateData = {
          full_name: formData.full_name,
          full_name_en: formData.full_name_en || null,
          sex: formData.sex,
          date_of_birth: formData.date_of_birth,
          place_of_birth: formData.place_of_birth,
          place_of_birth_en: formData.place_of_birth_en || null,
          passport: formData.passport,
          nationality: formData.nationality || null,
          passport_expiry_date: formData.passport_expiry_date || null,
          rank: formData.rank || null,
          seamen_book: formData.seamen_book || null,
          ship_sign_on: formData.ship_sign_on,
          status: 'Sign on',
          place_sign_on: formData.place_sign_on || null,
          date_sign_on: formData.date_sign_on || null,
          date_sign_off: null  // Clear sign off date when signing on
        };
        
        await crewService.update(crew.id, updateData);
        
        // Call sign on API in background for file movement and audit trail
        crewService.signOn(crew.id, {
          ship_name: formData.ship_sign_on,
          sign_on_date: formData.date_sign_on || new Date().toISOString().split('T')[0],
          place_sign_on: formData.place_sign_on || null,
          notes: `Sign on via Edit Crew Member modal to ${formData.ship_sign_on}`
        }).catch(error => {
          console.error('Background sign on error:', error);
        });
        
        toast.success(
          language === 'vi' 
            ? '✅ Đã cập nhật thuyền viên. Files đang được di chuyển...'
            : '✅ Crew updated. Files are being moved in background...',
          { duration: 5000 }
        );
        
      }
      // Case 3: Transfer Flow
      // Status remains "Sign on" but ship changed (from Ship A to Ship B)
      else if (originalStatus === 'Sign on' && newStatus === 'Sign on' && 
               originalShip !== newShip && 
               originalShip !== '' && originalShip !== '-' &&
               newShip !== '' && newShip !== '-') {
        console.log('🔄 Transfer Flow detected');
        needsFileMovement = true;
        
        // Update DB immediately with all fields including ship_sign_on
        const updateData = {
          full_name: formData.full_name,
          full_name_en: formData.full_name_en || null,
          sex: formData.sex,
          date_of_birth: formData.date_of_birth,
          place_of_birth: formData.place_of_birth,
          place_of_birth_en: formData.place_of_birth_en || null,
          passport: formData.passport,
          nationality: formData.nationality || null,
          passport_expiry_date: formData.passport_expiry_date || null,
          rank: formData.rank || null,
          seamen_book: formData.seamen_book || null,
          ship_sign_on: formData.ship_sign_on,
          status: 'Sign on',  // Status remains Sign on
          place_sign_on: formData.place_sign_on || null,
          date_sign_on: formData.date_sign_on || new Date().toISOString().split('T')[0],  // Use user input or current date
          date_sign_off: formData.date_sign_off || null
        };
        
        await crewService.update(crew.id, updateData);
        
        // Call transfer API in background for file movement and audit trail
        crewService.transferShip(crew.id, {
          to_ship_name: formData.ship_sign_on,
          transfer_date: new Date().toISOString().split('T')[0],
          notes: `Transfer via Edit Crew Member modal from ${crew.ship_sign_on} to ${formData.ship_sign_on}`
        }).catch(error => {
          console.error('Background transfer error:', error);
        });
        
        toast.success(
          language === 'vi' 
            ? '✅ Đã cập nhật thuyền viên. Files đang được di chuyển...'
            : '✅ Crew updated. Files are being moved in background...',
          { duration: 5000 }
        );
        
      }
      // Case 4: Regular Update (no file movement needed)
      else {
        console.log('🔄 Regular Update Flow');
        
        const updateData = {
          ...formData,
          // Convert empty strings to null for proper database update
          full_name_en: formData.full_name_en || null,
          place_of_birth_en: formData.place_of_birth_en || null,
          nationality: formData.nationality || null,
          passport_expiry_date: formData.passport_expiry_date || null,
          rank: formData.rank || null,
          seamen_book: formData.seamen_book || null,
          place_sign_on: formData.place_sign_on || null,
          date_sign_on: formData.date_sign_on || null,
          date_sign_off: formData.date_sign_off || null
        };
        
        await crewService.update(crew.id, updateData);
        
        toast.success(language === 'vi' 
          ? 'Cập nhật thuyền viên thành công!'
          : 'Crew member updated successfully!');
      }
      
      // Update assignment history dates if date_sign_on or date_sign_off changed
      if (Object.keys(dateChanges).length > 0) {
        console.log('📅 Date changes detected, updating assignment history:', dateChanges);
        try {
          await crewService.updateAssignmentDates(crew.id, dateChanges);
          console.log('✅ Assignment history dates updated successfully');
        } catch (error) {
          console.error('❌ Error updating assignment dates:', error);
          // Don't block the modal from closing, but log the error
        }
      }
      
      // Close modal immediately and refresh table
      onClose();
      onSuccess();
      
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
            
            {/* Row 2: Date of Birth, Passport, Passport Expiry Date */}
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
            
            {/* Row 3: Place of Birth (Vietnamese), Place of Birth (English), Nationality */}
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
                  <span className="ml-2 text-xs text-blue-600">
                    ({language === 'vi' ? 'Tự động' : 'Auto'})
                  </span>
                </label>
                <select
                  value={formData.status}
                  disabled={true}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 cursor-not-allowed text-gray-700"
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
                  onChange={(e) => {
                    const selectedShip = e.target.value;
                    
                    // Auto-update Status based on Ship selection
                    if (selectedShip === '-') {
                      // Sign off: Ship = "-" → Status = "Standby"
                      setFormData({
                        ...formData, 
                        ship_sign_on: selectedShip,
                        status: 'Standby'
                      });
                    } else {
                      // Sign on: Ship selected → Status = "Sign on"
                      setFormData({
                        ...formData, 
                        ship_sign_on: selectedShip,
                        status: 'Sign on'
                      });
                    }
                  }}
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
                  <option value="-">{language === 'vi' ? '- (Sign off)' : '- (Sign off)'}</option>
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
