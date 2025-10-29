import { useState, useMemo } from 'react';

/**
 * Custom hook for managing table sorting
 * @param {Array} data - Array of data to sort
 * @param {string} initialSortKey - Initial sort key (default: '')
 * @param {string} initialSortOrder - Initial sort order 'asc' or 'desc' (default: 'asc')
 * @returns {Object} { sortedData, sortKey, sortOrder, handleSort }
 */
export const useSort = (data, initialSortKey = '', initialSortOrder = 'asc') => {
  const [sortKey, setSortKey] = useState(initialSortKey);
  const [sortOrder, setSortOrder] = useState(initialSortOrder);

  const handleSort = (key) => {
    if (sortKey === key) {
      // Toggle sort order if clicking the same column
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new sort key and default to ascending
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !data) return data;

    const sorted = [...data].sort((a, b) => {
      let aVal = a[sortKey];
      let bVal = b[sortKey];

      // Handle null/undefined values
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      // Convert to lowercase for string comparison
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();

      // Compare values
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [data, sortKey, sortOrder]);

  return {
    sortedData,
    sortKey,
    sortOrder,
    handleSort
  };
};
