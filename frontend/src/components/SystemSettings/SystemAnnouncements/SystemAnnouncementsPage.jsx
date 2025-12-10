import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../../contexts/LanguageContext';
import systemAnnouncementService from '../../../services/systemAnnouncementService';
import AddAnnouncementModal from './AddAnnouncementModal';
import toast from 'react-hot-toast';

const SystemAnnouncementsPage = () => {
  const { language } = useLanguage();
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const loadAnnouncements = async () => {
    try {
      setLoading(true);
      const data = await systemAnnouncementService.getAllAnnouncements();
      setAnnouncements(data);
    } catch (error) {
      toast.error(language === 'vi' ? 'Lỗi tải thông báo' : 'Error loading announcements');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingAnnouncement(null);
    setShowModal(true);
  };

  const handleEdit = (announcement) => {
    setEditingAnnouncement(announcement);
    setShowModal(true);
  };

  const handleDelete = (id) => {
    setDeletingId(id);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      await systemAnnouncementService.deleteAnnouncement(deletingId);
      toast.success(language === 'vi' ? 'Đã xóa thông báo' : 'Announcement deleted');
      loadAnnouncements();
    } catch (error) {
      toast.error(language === 'vi' ? 'Lỗi xóa thông báo' : 'Error deleting announcement');
    } finally {
      setShowDeleteConfirm(false);
      setDeletingId(null);
    }
  };

  const handleToggleActive = async (announcement) => {
    try {
      await systemAnnouncementService.updateAnnouncement(announcement.id, {
        is_active: !announcement.is_active
      });
      toast.success(language === 'vi' ? 'Đã cập nhật' : 'Updated');
      loadAnnouncements();
    } catch (error) {
      toast.error(language === 'vi' ? 'Lỗi cập nhật' : 'Error updating');
    }
  };

  const getStatusBadge = (announcement) => {
    const now = new Date();
    const startDate = new Date(announcement.start_date);
    const endDate = new Date(announcement.end_date);

    if (!announcement.is_active) {
      return <span className="px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-600">⚫ Inactive</span>;
    }
    if (now < startDate) {
      return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">🟡 Scheduled</span>;
    }
    if (now > endDate) {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-700">🔴 Expired</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">🟢 Active</span>;
  };

  const getTypeBadge = (type) => {
    const badges = {
      info: <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">ℹ️ Info</span>,
      warning: <span className="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700">⚠️ Warning</span>,
      success: <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">✅ Success</span>,
      error: <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-700">❌ Error</span>
    };
    return badges[type] || badges.info;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Thông báo hệ thống' : 'System Announcements'}
          </h1>
          <p className="text-gray-600 mt-1">
            {language === 'vi' 
              ? 'Quản lý thông báo hiển thị trên trang đăng nhập'
              : 'Manage announcements displayed on login page'}
          </p>
        </div>
        <button
          onClick={handleAdd}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {language === 'vi' ? 'Tạo thông báo' : 'Create Announcement'}
        </button>
      </div>

      {/* Announcements List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : announcements.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">📢</div>
          <p className="text-gray-500">
            {language === 'vi' ? 'Chưa có thông báo nào' : 'No announcements yet'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {language === 'vi' ? 'Tiêu đề' : 'Title'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {language === 'vi' ? 'Loại' : 'Type'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {language === 'vi' ? 'Thời gian' : 'Duration'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {language === 'vi' ? 'Hành động' : 'Actions'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {announcements.map(announcement => (
                <tr key={announcement.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {language === 'vi' ? announcement.title_vn : announcement.title_en}
                    </div>
                    <div className="text-sm text-gray-500 truncate max-w-md">
                      {language === 'vi' ? announcement.content_vn : announcement.content_en}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getTypeBadge(announcement.type)}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(announcement)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div>{new Date(announcement.start_date).toLocaleDateString()}</div>
                    <div className="text-gray-400">→</div>
                    <div>{new Date(announcement.end_date).toLocaleDateString()}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleActive(announcement)}
                        className={`p-2 rounded hover:bg-gray-100 transition-colors ${
                          announcement.is_active ? 'text-green-600' : 'text-gray-400'
                        }`}
                        title={announcement.is_active ? 'Deactivate' : 'Activate'}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleEdit(announcement)}
                        className="p-2 rounded hover:bg-blue-50 text-blue-600 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(announcement.id)}
                        className="p-2 rounded hover:bg-red-50 text-red-600 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <AddAnnouncementModal
          announcement={editingAnnouncement}
          onClose={() => {
            setShowModal(false);
            setEditingAnnouncement(null);
          }}
          onSuccess={() => {
            setShowModal(false);
            setEditingAnnouncement(null);
            loadAnnouncements();
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {language === 'vi' ? 'Xác nhận xóa' : 'Confirm Delete'}
            </h3>
            <p className="text-gray-600 mb-6">
              {language === 'vi' 
                ? 'Bạn có chắc chắn muốn xóa thông báo này?'
                : 'Are you sure you want to delete this announcement?'}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                {language === 'vi' ? 'Xóa' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemAnnouncementsPage;