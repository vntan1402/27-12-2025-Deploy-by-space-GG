/**
 * Position Helpers for Tooltips and Context Menus
 * Auto-adjusts position to keep elements within viewport bounds
 */

/**
 * Calculate smart position for tooltip
 * @param {DOMRect} rect - Element's bounding rectangle
 * @param {number} tooltipWidth - Width of tooltip
 * @param {number} tooltipHeight - Max height of tooltip
 * @returns {object} - {x, y} coordinates
 */
export const calculateTooltipPosition = (rect, tooltipWidth = 300, tooltipHeight = 200) => {
  let x = rect.left;
  let y = rect.bottom + 5; // Default: show below element
  
  // Check if tooltip would overflow right edge
  if (x + tooltipWidth > window.innerWidth) {
    x = window.innerWidth - tooltipWidth - 10; // 10px padding from edge
  }
  
  // Check if tooltip would overflow left edge
  if (x < 10) {
    x = 10;
  }
  
  // Check if tooltip would overflow bottom edge
  if (y + tooltipHeight > window.innerHeight) {
    y = rect.top - tooltipHeight - 5; // Show above element instead
  }
  
  // Check if tooltip would overflow top edge (after moving above)
  if (y < 10) {
    y = 10;
  }
  
  return { x, y };
};

/**
 * Calculate smart position for context menu
 * @param {MouseEvent} e - Mouse event
 * @param {number} menuWidth - Approximate width of menu
 * @param {number} menuHeight - Approximate height of menu
 * @returns {object} - {x, y} coordinates
 */
export const calculateContextMenuPosition = (e, menuWidth = 200, menuHeight = 250) => {
  let x = e.clientX;
  let y = e.clientY;
  
  // Check if menu would overflow right edge
  if (x + menuWidth > window.innerWidth) {
    x = window.innerWidth - menuWidth - 10; // 10px padding from edge
  }
  
  // Check if menu would overflow bottom edge
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 10; // 10px padding from edge
  }
  
  // Ensure minimum distance from edges
  x = Math.max(10, x);
  y = Math.max(10, y);
  
  return { x, y };
};

/**
 * Calculate smart position for dropdown
 * @param {DOMRect} rect - Trigger element's bounding rectangle
 * @param {number} dropdownWidth - Width of dropdown
 * @param {number} dropdownHeight - Height of dropdown
 * @returns {object} - {x, y, placement} coordinates and placement direction
 */
export const calculateDropdownPosition = (rect, dropdownWidth = 200, dropdownHeight = 300) => {
  let x = rect.left;
  let y = rect.bottom + 5; // Default: show below
  let placement = 'bottom';
  
  // Check if dropdown would overflow right edge
  if (x + dropdownWidth > window.innerWidth) {
    x = rect.right - dropdownWidth; // Align to right edge of trigger
  }
  
  // Check if dropdown would overflow left edge
  if (x < 10) {
    x = 10;
  }
  
  // Check if dropdown would overflow bottom edge
  if (y + dropdownHeight > window.innerHeight) {
    y = rect.top - dropdownHeight - 5; // Show above instead
    placement = 'top';
  }
  
  // Check if dropdown would overflow top edge (after moving above)
  if (y < 10) {
    y = rect.bottom + 5; // Revert to below
    placement = 'bottom';
  }
  
  return { x, y, placement };
};
