import api from './api';

const BASE_URL = '/api/v1/company-certs';

export const companyCertService = {
  // Get all company certificates
  async getCompanyCerts(company = null) {
    const params = company ? { company } : {};
    const response = await api.get(BASE_URL, { params });
    return response.data;
  },

  // Get company certificate by ID
  async getCompanyCertById(certId) {
    const response = await api.get(`${BASE_URL}/${certId}`);
    return response.data;
  },

  // Create new company certificate
  async createCompanyCert(certData) {
    const response = await api.post(BASE_URL, certData);
    return response.data;
  },

  // Update company certificate
  async updateCompanyCert(certId, certData) {
    const response = await api.put(`${BASE_URL}/${certId}`, certData);
    return response.data;
  },

  // Delete company certificate
  async deleteCompanyCert(certId) {
    const response = await api.delete(`${BASE_URL}/${certId}`);
    return response.data;
  },

  // Bulk delete company certificates
  async bulkDeleteCompanyCerts(certIds) {
    const response = await api.post(`${BASE_URL}/bulk-delete`, {
      cert_ids: certIds
    });
    return response.data;
  }
};

export default companyCertService;
