/**
 * System Audit Log Service
 * API calls for system audit logs
 */
import api from './api';

const crewAuditLogService = {
  /**
   * Get filtered audit logs with pagination
   */
  async getAuditLogs(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      // Add filters to params
      if (filters.entityType && filters.entityType !== 'all') params.append('entity_type', filters.entityType);
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.action && filters.action !== 'all') params.append('action', filters.action);
      if (filters.performedBy && filters.performedBy !== 'all') params.append('performed_by', filters.performedBy);
      if (filters.shipName && filters.shipName !== 'all') params.append('ship_name', filters.shipName);
      if (filters.entityId) params.append('entity_id', filters.entityId);
      if (filters.search) params.append('search', filters.search);
      if (filters.skip !== undefined) params.append('skip', filters.skip);
      if (filters.limit !== undefined) params.append('limit', filters.limit);
      
      const response = await api.get(`/api/audit-logs?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      throw error;
    }
  },

  /**
   * Get single audit log by ID
   */
  async getAuditLogById(logId) {
    try {
      const response = await api.get(`/api/audit-logs/${logId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching audit log:', error);
      throw error;
    }
  },

  /**
   * Get audit logs for specific crew member
   */
  async getAuditLogsByCrew(crewId, limit = 50) {
    try {
      const response = await api.get(`/api/audit-logs/crew/${crewId}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching crew audit logs:', error);
      throw error;
    }
  },

  /**
   * Get unique users for filter dropdown
   */
  async getUniqueUsers() {
    try {
      const response = await api.get('/api/audit-logs/filters/users');
      return response.data;
    } catch (error) {
      console.error('Error fetching unique users:', error);
      throw error;
    }
  },

  /**
   * Get unique ships for filter dropdown
   */
  async getUniqueShips() {
    try {
      const response = await api.get('/api/audit-logs/filters/ships');
      return response.data;
    } catch (error) {
      console.error('Error fetching unique ships:', error);
      throw error;
    }
  },

  /**
   * Trigger manual cleanup of expired logs (system admin only)
   */
  async cleanupExpiredLogs() {
    try {
      const response = await api.delete('/api/crew-audit-logs/cleanup');
      return response.data;
    } catch (error) {
      console.error('Error cleaning up logs:', error);
      throw error;
    }
  }
};

export default crewAuditLogService;
