import { useState } from 'react';

/**
 * Custom hook for CRUD operations with loading and error states
 * @param {Object} services - Object containing CRUD service functions
 * @param {Function} services.getAll - Function to fetch all items
 * @param {Function} services.create - Function to create an item
 * @param {Function} services.update - Function to update an item
 * @param {Function} services.delete - Function to delete an item
 * @returns {Object} CRUD operations and states
 */
export const useCRUD = (services) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all items
  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await services.getAll();
      setItems(data);
      return data;
    } catch (err) {
      const errorMessage = err.message || 'Failed to fetch items';
      setError(errorMessage);
      console.error('useCRUD fetchAll error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Create a new item
  const create = async (itemData) => {
    try {
      setLoading(true);
      setError(null);
      const newItem = await services.create(itemData);
      setItems(prev => [...prev, newItem]);
      return newItem;
    } catch (err) {
      const errorMessage = err.message || 'Failed to create item';
      setError(errorMessage);
      console.error('useCRUD create error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update an existing item
  const update = async (itemId, itemData) => {
    try {
      setLoading(true);
      setError(null);
      const updatedItem = await services.update(itemId, itemData);
      setItems(prev => prev.map(item => 
        item.id === itemId ? updatedItem : item
      ));
      return updatedItem;
    } catch (err) {
      const errorMessage = err.message || 'Failed to update item';
      setError(errorMessage);
      console.error('useCRUD update error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete an item
  const remove = async (itemId) => {
    try {
      setLoading(true);
      setError(null);
      await services.delete(itemId);
      setItems(prev => prev.filter(item => item.id !== itemId));
      return true;
    } catch (err) {
      const errorMessage = err.message || 'Failed to delete item';
      setError(errorMessage);
      console.error('useCRUD remove error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    items,
    loading,
    error,
    fetchAll,
    create,
    update,
    remove
  };
};
