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
        ? 'Phần mềm hết hạn sử dụng! Không thể dùng tính năng AI. Vui lòng sử dụng nhập liệu bằng tay.'
        : 'Software expired! Cannot use AI features. Please use manual entry.';
      
      console.log('🚫 [useUploadGuard] Software expired! Showing toast and blocking upload');
      
      toast.error(message, { 
        duration: 6000,
        position: 'top-center',
        style: {
          fontSize: '18px',
          fontWeight: '600',
          padding: '20px 30px',
          maxWidth: '600px',
          textAlign: 'center',
          background: '#FEF2F2',
          border: '2px solid #FCA5A5',
          color: '#991B1B',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          position: 'fixed'
        },
        icon: '⚠️'
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
