import { useState } from 'react';

/**
 * Custom hook for managing modal state
 * @param {boolean} initialState - Initial modal state (default: false)
 * @returns {Object} { isOpen, open, close, toggle }
 */
export const useModal = (initialState = false) => {
  const [isOpen, setIsOpen] = useState(initialState);

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);
  const toggle = () => setIsOpen(prev => !prev);

  return {
    isOpen,
    open,
    close,
    toggle
  };
};
