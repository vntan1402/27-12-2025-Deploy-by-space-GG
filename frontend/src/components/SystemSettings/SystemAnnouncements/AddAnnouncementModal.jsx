import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../../contexts/LanguageContext';
import systemAnnouncementService from '../../../services/systemAnnouncementService';
import toast from 'react-hot-toast';

const AddAnnouncementModal = ({ announcement, onClose, onSuccess }) => {
  const { language } = useLanguage();
  const isEdit = !!announcement;

  const [formData, setFormData] = useState({
    title_vn: '',
    title_en: '',
    content_vn: '',
    content_en: '',
    type: 'info',
    priority: 5,
    is_active: true,
    start_date: '',
    end_date: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (announcement) {
      // Format dates for datetime-local input
      const formatDateForInput = (isoString) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
      };

      setFormData({
        title_vn: announcement.title_vn || '',
        title_en: announcement.title_en || '',
        content_vn: announcement.content_vn || '',
        content_en: announcement.content_en || '',
        type: announcement.type || 'info',
        priority: announcement.priority || 5,
        is_active: announcement.is_active !== undefined ? announcement.is_active : true,
        start_date: formatDateForInput(announcement.start_date),
        end_date: formatDateForInput(announcement.end_date)
      });
    }
  }, [announcement]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.title_vn.trim()) {
      newErrors.title_vn = language === 'vi' ? 'Vui lòng nhập tiêu đề (VN)' : 'Please enter title (VN)';
    }
    if (!formData.title_en.trim()) {
      newErrors.title_en = language === 'vi' ? 'Vui lòng nhập tiêu đề (EN)' : 'Please enter title (EN)';
    }
    if (!formData.content_vn.trim()) {
      newErrors.content_vn = language === 'vi' ? 'Vui lòng nhập nội dung (VN)' : 'Please enter content (VN)';
    }
    if (!formData.content_en.trim()) {
      newErrors.content_en = language === 'vi' ? 'Vui lòng nhập nội dung (EN)' : 'Please enter content (EN)';
    }
    if (!formData.start_date) {
      newErrors.start_date = language === 'vi' ? 'Vui lòng chọn ngày bắt đầu' : 'Please select start date';
    }
    if (!formData.end_date) {
      newErrors.end_date = language === 'vi' ? 'Vui lòng chọn ngày kết thúc' : 'Please select end date';
    }

    // Validate dates
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      if (end < start) {
        newErrors.end_date = language === 'vi' 
          ? 'Ngày kết thúc phải sau ngày bắt đầu' 
          : 'End date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Convert datetime-local to ISO string
      const submitData = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString()
      };

      if (isEdit) {
        await systemAnnouncementService.updateAnnouncement(announcement.id, submitData);
        toast.success(language === 'vi' ? 'Đã cập nhật thông báo' : 'Announcement updated');
      } else {
        await systemAnnouncementService.createAnnouncement(submitData);
        toast.success(language === 'vi' ? 'Đã tạo thông báo' : 'Announcement created');
      }

      onSuccess();
    } catch (error) {
      console.error('Error saving announcement:', error);
      const message = error.response?.data?.detail || (language === 'vi' ? 'Lỗi lưu thông báo' : 'Error saving announcement');
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">
            {isEdit 
              ? (language === 'vi' ? 'Chỉnh sửa thông báo' : 'Edit Announcement')
              : (language === 'vi' ? 'Tạo thông báo mới' : 'Create New Announcement')}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title VN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Tiêu đề (Tiếng Việt)' : 'Title (Vietnamese)'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="title_vn"
              value={formData.title_vn}
              onChange={handleChange}
              maxLength={200}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.title_vn ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Cập nhật hệ thống..."
            />
            {errors.title_vn && <p className="text-red-500 text-sm mt-1">{errors.title_vn}</p>}
          </div>

          {/* Title EN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Tiêu đề (Tiếng Anh)' : 'Title (English)'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="title_en"
              value={formData.title_en}
              onChange={handleChange}
              maxLength={200}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.title_en ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="System Update..."
            />
            {errors.title_en && <p className="text-red-500 text-sm mt-1">{errors.title_en}</p>}
          </div>

          {/* Content VN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Nội dung (Tiếng Việt)' : 'Content (Vietnamese)'} <span className="text-red-500">*</span>
            </label>
            <textarea
              name="content_vn"
              value={formData.content_vn}
              onChange={handleChange}
              maxLength={1000}
              rows={4}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.content_vn ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Hệ thống sẽ bảo trì từ 22:00-23:00 ngày 15/01/2025..."
            />
            <div className="flex justify-between items-center mt-1">
              {errors.content_vn && <p className="text-red-500 text-sm">{errors.content_vn}</p>}
              <p className="text-gray-400 text-sm ml-auto">{formData.content_vn.length}/1000</p>
            </div>
          </div>

          {/* Content EN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Nội dung (Tiếng Anh)' : 'Content (English)'} <span className="text-red-500">*</span>
            </label>
            <textarea
              name="content_en"
              value={formData.content_en}
              onChange={handleChange}
              maxLength={1000}
              rows={4}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.content_en ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="System maintenance from 22:00-23:00 on 15/01/2025..."
            />
            <div className="flex justify-between items-center mt-1">
              {errors.content_en && <p className="text-red-500 text-sm">{errors.content_en}</p>}
              <p className="text-gray-400 text-sm ml-auto">{formData.content_en.length}/1000</p>
            </div>
          </div>

          {/* Type and Priority Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'vi' ? 'Loại' : 'Type'}
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="info">ℹ️ Info</option>
                <option value="warning">⚠️ Warning</option>
                <option value="success">✅ Success</option>
                <option value="error">❌ Error</option>
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'vi' ? 'Ưu tiên' : 'Priority'}
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                  <option key={num} value={num}>{num}</option>
                ))}
              </select>
              <p className="text-gray-400 text-xs mt-1">
                {language === 'vi' ? 'Số cao hơn = hiển thị trước' : 'Higher number = show first'}
              </p>
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'vi' ? 'Ngày bắt đầu' : 'Start Date'} <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.start_date ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'vi' ? 'Ngày kết thúc' : 'End Date'} <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                name="end_date"
                value={formData.end_date}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.end_date ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.end_date && <p className="text-red-500 text-sm mt-1">{errors.end_date}</p>}
            </div>
          </div>

          {/* Active Checkbox */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label className="ml-2 text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Kích hoạt thông báo' : 'Activate announcement'}
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  {language === 'vi' ? 'Đang lưu...' : 'Saving...'}
                </span>
              ) : (
                isEdit 
                  ? (language === 'vi' ? 'Cập nhật' : 'Update')
                  : (language === 'vi' ? 'Tạo' : 'Create')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddAnnouncementModal;
