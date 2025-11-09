import { useAuth } from '../contexts/AuthContext';

/**
 * Show centered warning modal
 */
const showCenteredWarning = (message) => {
  // Create overlay
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
  `;

  // Create warning box
  const warningBox = document.createElement('div');
  warningBox.style.cssText = `
    background: #FEF2F2;
    border: 3px solid #F87171;
    border-radius: 12px;
    padding: 30px 40px;
    max-width: 600px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    animation: slideIn 0.3s ease-out;
  `;

  warningBox.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
      <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
      <div style="font-size: 20px; font-weight: 600; color: #991B1B; line-height: 1.6;">
        ${message}
      </div>
    </div>
  `;

  overlay.appendChild(warningBox);
  document.body.appendChild(overlay);

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateY(-50px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);

  // Track if already removed
  let isRemoved = false;

  // Remove function
  const removeModal = () => {
    if (isRemoved) return;
    isRemoved = true;

    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.3s ease-out';
    
    setTimeout(() => {
      // Check if elements still exist in DOM before removing
      if (overlay.parentNode) {
        document.body.removeChild(overlay);
      }
      if (style.parentNode) {
        document.head.removeChild(style);
      }
    }, 300);
  };

  // Auto remove after 4 seconds
  const autoCloseTimer = setTimeout(removeModal, 4000);

  // Click to close
  overlay.addEventListener('click', () => {
    clearTimeout(autoCloseTimer);
    removeModal();
  });
};

/**
 * Custom hook to guard AI upload features when software is expired
 * @returns {Object} - { isSoftwareExpired, checkAndWarn }
 */
export const useUploadGuard = () => {
  const { isSoftwareExpired, language } = useAuth();
  
  /**
   * Check if software is expired and show warning
   * @returns {boolean} - true if upload allowed, false if blocked
   */
  const checkAndWarn = () => {
    console.log('🔍 [useUploadGuard] checkAndWarn called, isSoftwareExpired:', isSoftwareExpired);
    
    if (isSoftwareExpired) {
      const message = language === 'vi' 
        ? 'Phần mềm hết hạn sử dụng!<br/>Không thể dùng tính năng AI.<br/>Vui lòng sử dụng nhập liệu bằng tay.'
        : 'Software expired!<br/>Cannot use AI features.<br/>Please use manual entry.';
      
      console.log('🚫 [useUploadGuard] Software expired! Showing warning and blocking upload');
      
      showCenteredWarning(message);
      
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
