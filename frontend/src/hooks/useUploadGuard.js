import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

/**
 * Custom hook to guard AI upload features when software is expired
 * @returns {Object} - { isSoftwareExpired, checkAndWarn }
 */
export const useUploadGuard = () => {
  const { isSoftwareExpired, language } = useAuth();
  
  /**
   * Check if software is expired and show warning toast
   * @returns {boolean} - true if upload allowed, false if blocked
   */
  const checkAndWarn = () => {
    console.log('🔍 [useUploadGuard] checkAndWarn called, isSoftwareExpired:', isSoftwareExpired);
    
    if (isSoftwareExpired) {
      const message = language === 'vi' 
        ? '⚠️ Phần mềm hết hạn sử dụng! Không thể dùng tính năng AI. Vui lòng sử dụng nhập liệu bằng tay.'
        : '⚠️ Software expired! Cannot use AI features. Please use manual entry.';
      
      console.log('🚫 [useUploadGuard] Software expired! Showing toast and blocking upload');
      
      toast.error(message, { 
        duration: 5000,
        position: 'top-center'
      });
      
      return false; // Block upload
    }
    
    console.log('✅ [useUploadGuard] Software not expired, allowing upload');
    return true; // Allow upload
  };
  
  return { 
    isSoftwareExpired, 
    checkAndWarn 
  };
};
